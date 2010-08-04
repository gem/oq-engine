package scratch.kevin.faultParticipationProbs;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.lang.reflect.Array;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;

import org.opensha.commons.data.Container2D;
import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.commons.util.threads.Task;
import org.opensha.commons.util.threads.TaskProgressListener;
import org.opensha.commons.util.threads.ThreadedTaskComputer;
import org.opensha.refFaultParamDb.calc.sectionDists.FaultSectDistRecord;
import org.opensha.refFaultParamDb.calc.sectionDists.SmartSurfaceFilter;
import org.opensha.refFaultParamDb.vo.FaultSectionPrefData;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.UCERF2;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.MeanUCERF2.MeanUCERF2;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data.finalReferenceFaultParamDb.DeformationModelPrefDataFinal;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.faultSurface.SimpleFaultData;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;
import org.opensha.sha.magdist.SummedMagFreqDist;

public class SAF_Closest_Pt_Test implements TaskProgressListener {

	private static final double gridSpacing = 1.0;
	
	private static final boolean QUICK_TEST = false;
	private static final boolean TIME_DEPENDENT = true;

	private ArrayList<ProbEqkSource> sources;

	private ArrayList<FaultProbPairing> faults;

	private static final SmartSurfaceFilter filter = new SmartSurfaceFilter(2, 5, 150);
	private static final boolean fastDist = true;
	private static double filterDistThresh = 10d;
	private static double closestThresh = 7.5d;

	private double minMag;
	private double maxMag;
	private int numMagBins;
	private int duration;

	private long calcStartTime = 0;
	private int numAssigned = 0;
	private int numUnassigned = 0;
	
	private DecimalFormat df = new DecimalFormat("00.00");
	private DecimalFormat pdf = new DecimalFormat("00.00%");
	
	private ArrayList<Location> unassignedLocs = new ArrayList<Location>();

	public SAF_Closest_Pt_Test(DeformationModelPrefDataFinal data, int defModel, ArrayList<ProbEqkSource> sources,
			double minMag, double maxMag, int numMagBins, int duration) {
		this.sources = sources;
		this.minMag = minMag;
		this.maxMag = maxMag;
		this.numMagBins = numMagBins;
		this.duration = duration;

		faults = new ArrayList<FaultProbPairing>();

		for (int faultSectionId : data.getFaultSectionIdsForDeformationModel(defModel)) {
			FaultSectionPrefData fault = data.getFaultSectionPrefData(defModel, faultSectionId);
			SimpleFaultData simpleFaultData = fault.getSimpleFaultData(false);
			StirlingGriddedSurface surface = new StirlingGriddedSurface(simpleFaultData, gridSpacing, gridSpacing);

			faults.add(new FaultProbPairing(surface, fault.getName(), faultSectionId, fault.getAveLongTermSlipRate()));
		}
	}

	public void loadMFDs() throws InterruptedException {
		calcStartTime = System.currentTimeMillis();
		System.out.println("Preparing calc tasks");
		ArrayList<MFDCalcTask> tasks = new ArrayList<MFDCalcTask>();
		// source first approach
		for (ProbEqkSource source : sources) {
			// first see if we can skip any faults
			ArrayList<FaultProbPairing> faultsForSource = getFaultsForSource(source);
			System.out.println("Using " + faultsForSource.size() + "/" + faults.size()
					+ " faults for source '" + source.getName() + "'");
			
			for (int rupID=0; rupID<source.getNumRuptures(); rupID++) {
				ProbEqkRupture rup = source.getRupture(rupID);
				tasks.add(new MFDCalcTask(rup, faultsForSource));
			}
		}
		if (QUICK_TEST) {
			System.out.println("Orig had " + tasks.size() + " tasks");
//			Collections.shuffle(tasks);
			while (tasks.size() > 300) // TODO REMOVE THIS SPEED HACK!!!
				tasks.remove(tasks.size() -1);
		}
		printTimes(sources.size(), 1d);
		calcStartTime = System.currentTimeMillis();
		
		ThreadedTaskComputer comp = new ThreadedTaskComputer(tasks, true);
		comp.setProgressTimer(this, 1);
		int procs = Runtime.getRuntime().availableProcessors();
		System.out.println("Starting calculation with " + procs + " processors!");
		comp.computThreaded(procs);
		System.out.println("DONE!");
		
		taskProgressUpdate(tasks.size(), 0, tasks.size());
	}
	
	private static synchronized void addResampledMagRate(SummedMagFreqDist mfd, double mag, double meanAnnualRate) {
		mfd.addResampledMagRate(mag, meanAnnualRate, true);
	}
	
	private class MFDCalcTask implements Task {
		
		private ProbEqkRupture rup;
		private ArrayList<FaultProbPairing> faultsForRup;
		
		public MFDCalcTask(ProbEqkRupture rup, ArrayList<FaultProbPairing> faultsForRup) {
			this.rup = rup;
			this.faultsForRup = faultsForRup;
		}

		@Override
		public void compute() {
			double mag = rup.getMag();
			double meanAnnualRate = rup.getMeanAnnualRate(duration);
			for (Location rupPt : rup.getRuptureSurface()) {
				SummedMagFreqDist closestMFD = getClosestMFD(faultsForRup, rupPt);
				if (closestMFD == null) {
					numUnassigned++;
					unassignedLocs.add(rupPt);
				} else {
					numAssigned++;
					addResampledMagRate(closestMFD, mag, meanAnnualRate);
				}
			}
		}
		
	}
	
	/**
	 * returns the median...array must be sorted
	 * 
	 * @param m
	 * @return
	 */
	private static double median(double[] m) {
		int middle = (m.length)/2;  // subscript of middle element
		if (m.length%2 == 1) {
			// Odd number of elements -- return the middle one.
			return m[middle];
		} else {
			// Even number -- return average of middle two
			// Must cast the numbers to double before dividing.
			return (m[middle-1] + m[middle]) / 2.0;
		}
	}
	
	public void writeFiles(String dir, float[] mags, boolean colMedian) throws IOException {
		File pDirFile = new File(dir + File.separator + "prob");
		File rDirFile = new File(dir + File.separator + "rate");
		if (!pDirFile.exists())
			pDirFile.mkdirs();
		if (!rDirFile.exists())
			rDirFile.mkdirs();
		for (FaultProbPairing fault : faults) {
			if (fault.hasValues()) {
				String safeName = fault.getSafeName();
				String rateFileName = rDirFile.getAbsolutePath() + File.separator + "rate_" + safeName + ".txt";
				String probFileName = pDirFile.getAbsolutePath() + File.separator + "prob_" + safeName + ".txt";
				Container2D<Double>[] rates = new Container2D[mags.length];
				Container2D<Double>[] probs = new Container2D[mags.length];
				for (int i=0; i<mags.length; i++) {
					rates[i] = fault.getRatesForMag(mags[i]);
					probs[i] = fault.getProbsForMag(mags[i], rates[i]);
				}
				FileWriter rfw = new FileWriter(rateFileName);
				FileWriter pfw = new FileWriter(probFileName);
				
				String header = "#lat\tlon\tdepth";
				for (float mag : mags) {
					header += "\t" + mag;
				}
				
				rfw.write(header + "\n");
				pfw.write(header + "\n");
				
				for (int col=0; col<fault.getSurface().getNumCols(); col++) {
					double[] colMedProbVals = null;
					double[] colMedRateVals = null;
					if (colMedian) {
						colMedProbVals = new double[probs.length];
						colMedRateVals = new double[probs.length];
						for (int i=0; i<mags.length; i++) {
							double[] colProbVals = new double[fault.getSurface().getNumRows()];
							double[] colRateVals = new double[fault.getSurface().getNumRows()];
							for (int row=0; row<fault.getSurface().getNumRows(); row++) {
								colProbVals[row] = probs[i].get(row, col);
								colRateVals[row] = rates[i].get(row, col);
							}
							Arrays.sort(colProbVals);
							Arrays.sort(colMedRateVals);
							colMedProbVals[i] = median(colProbVals);
							colMedRateVals[i] = median(colRateVals);
						}
					}
					for (int row=0; row<fault.getSurface().getNumRows(); row++) {
						Location loc = fault.getSurface().get(row, col);
						String locStr = loc.getLatitude() + "\t" + loc.getLongitude() + "\t" + loc.getDepth();
						String rLine = locStr;
						String pLine = locStr;
						for (int i=0; i<mags.length; i++) {
							double rateVal, probVal;
							if (colMedian) {
								rateVal = colMedRateVals[i];
								probVal = colMedProbVals[i];
							} else {
								rateVal = rates[i].get(row, col);
								probVal = probs[i].get(row, col);
							}
							rLine += "\t" + rateVal;
							pLine += "\t" + probVal;
						}
						rfw.write(rLine + "\n");
						pfw.write(pLine + "\n");
					}
				}
				rfw.close();
				pfw.close();
			}
		}
		if (unassignedLocs.size() > 0) {
			FileWriter ufw = new FileWriter(dir + File.separator + "unassigned.txt");
			for (Location loc : unassignedLocs) {
				ufw.write(loc.getLatitude() + "\t" + loc.getLongitude() + "\t" + loc.getDepth() + "\n");
			}
			ufw.close();
		}
	}

	private SummedMagFreqDist getClosestMFD(ArrayList<FaultProbPairing> faultsForSource, Location rupPt) {
		SummedMagFreqDist closestMFD = null;
		double closestDist = Double.MAX_VALUE;
		for (FaultProbPairing fault : faultsForSource) {
			EvenlyGriddedSurfaceAPI faultSurface = fault.getSurface();
			for (int row=0; row<faultSurface.getNumRows(); row++) {
				for (int col=0; col<faultSurface.getNumCols(); col++) {
					Location faultPt = faultSurface.get(row, col);
					double dist;
					if (fastDist)
						dist = LocationUtils.linearDistanceFast(rupPt, faultPt);
					else
						dist = LocationUtils.linearDistance(rupPt, faultPt);
					if (dist < closestDist && dist < closestThresh) {
						closestMFD = fault.getMFDs().get(row, col);
						closestDist = dist;
					}
				}
			}
		}
		return closestMFD;
	}

	private ArrayList<FaultProbPairing> getFaultsForSource(ProbEqkSource source) {
		EvenlyGriddedSurfaceAPI sourceSurface = source.getSourceSurface();

		ArrayList<FaultProbPairing> faultsForSource = new ArrayList<FaultProbPairing>();

		for (FaultProbPairing fault : faults) {
			Double slip = fault.getSlipRate();
			if (slip.isNaN() || slip <= 0)
				continue;
			EvenlyGriddedSurfaceAPI faultSurface = fault.getSurface();
			FaultSectDistRecord dists = new FaultSectDistRecord(0, faultSurface, 1, sourceSurface);
			if (dists.calcMinCornerMidptDist(fastDist) > filter.getCornerMidptFilterDist())
				continue;
			if (dists.calcIsWithinDistThresh(filterDistThresh, filter, fastDist))
				faultsForSource.add(fault);
		}

		return faultsForSource;
	}

	private class FaultProbPairing implements NamedObjectAPI {
		private EvenlyGriddedSurfaceAPI surface;
		private Container2D<SummedMagFreqDist> mfds;
		private String name;
		private int sectionID;
		private double slipRate;
		
		public FaultProbPairing(EvenlyGriddedSurfaceAPI surface, String name, int sectionID, double slip) {
			this.surface = surface;
			this.name = name;
			this.sectionID = sectionID;
			this.slipRate = slip;
			mfds = new Container2D<SummedMagFreqDist>(surface.getNumRows(), surface.getNumCols());
			for (int row=0; row<mfds.getNumRows(); row++) {
				for (int col=0; col<mfds.getNumCols(); col++) {
					mfds.set(row, col, new SummedMagFreqDist(minMag, maxMag, numMagBins));
				}
			}
		}

		public EvenlyGriddedSurfaceAPI getSurface() {
			return surface;
		}

		public Container2D<SummedMagFreqDist> getMFDs() {
			return mfds;
		}

		@Override
		public String getName() {
			return name;
		}

		public int getSectionID() {
			return sectionID;
		}
		
		public String getSafeName() {
			String safeName = getName();
			safeName = safeName.replaceAll("\\(", "");
			safeName = safeName.replaceAll("\\)", "");
			safeName = safeName.replaceAll(" ", "_");
			return safeName;
		}
		
		private boolean hasValues() {
			for (SummedMagFreqDist mfd : getMFDs()) {
				if (mfd != null && mfd.getNum() > 0)
					return true;
			}
			return false;
		}
		
		public Container2D<Double> getRatesForMag(double mag) {
			Container2D<Double> rates = new Container2D<Double>(surface.getNumRows(), surface.getNumCols());
			
			for (int row=0; row<rates.getNumRows(); row++) {
				for (int col=0; col<rates.getNumCols(); col++) {
					rates.set(row, col, getRateForMag(row, col, mag));
				}
			}
			
			return rates;
		}
		
		public Container2D<Double> getProbsForMag(double mag) {
			return getProbsForMag(mag, getRatesForMag(mag));
		}
		
		public Container2D<Double> getProbsForMag(double mag, Container2D<Double> rates) {
			Container2D<Double> probs = new Container2D<Double>(surface.getNumRows(), surface.getNumCols());
			
			for (int row=0; row<rates.getNumRows(); row++) {
				for (int col=0; col<rates.getNumCols(); col++) {
					probs.set(row, col, getProbForRate(rates.get(row, col)));
				}
			}
			
			return probs;
		}
		
		public double getRateForMag(int row, int col, double mag) {
			SummedMagFreqDist mfd = mfds.get(row, col);
			if (mfd.getNum() == 0)
				return 0;
			EvenlyDiscretizedFunc cumDist  = mfd.getCumRateDist();
			double predictedRate = cumDist.getInterpolatedY(mag);
			return predictedRate;
		}
		
		private double getProbForRate(double rate) {
			return 1-Math.exp(-rate*duration);
		}
		
		public double getSlipRate() {
			return slipRate;
		}
	}
	
	public static void main(String args[]) throws IOException, InterruptedException {
		if (QUICK_TEST)
			System.err.println("WARNING: RUNNING IN QUICK TEST MODE!!!!!");
		DeformationModelPrefDataFinal data = new DeformationModelPrefDataFinal();
		int defModel = 82;
		int duration = 30;
		double minMag=5.0, maxMag=9.00;
		int numMagBins = 41; // number of Mag bins
		System.out.println("Instantiating forecast");
		EqkRupForecastAPI erf = new MeanUCERF2();
		erf.getAdjustableParameterList().getParameter(UCERF2.BACK_SEIS_NAME).setValue(UCERF2.BACK_SEIS_EXCLUDE);
		if (!TIME_DEPENDENT) {
			System.out.println("Setting params for Poisson model!");
			erf.getAdjustableParameterList().getParameter(UCERF2.PROB_MODEL_PARAM_NAME)
				.setValue(UCERF2.PROB_MODEL_POISSON);
			erf.getTimeSpan().setDuration(30d, TimeSpan.YEARS);
		}
		System.out.println("Updating forecast");
		erf.updateForecast();
		ArrayList<ProbEqkSource> sources = new ArrayList<ProbEqkSource>();
		// for now just SAF
		for (int i=0; i<erf.getNumSources(); i++) {
			ProbEqkSource source = erf.getSource(i);
//			if (!QUICK_TEST || i==128)
			if (!QUICK_TEST || source.getName().toLowerCase().contains("andreas"))
				sources.add(source);
		}
		SAF_Closest_Pt_Test calc =
			new SAF_Closest_Pt_Test(data, defModel, sources, minMag, maxMag, numMagBins, duration);
		calc.loadMFDs();
		float[] mags = new float[numMagBins];
		for (int i=0; i<numMagBins; i++) {
			mags[i] =(float)(minMag + 0.1*(float)i);
		}
		String dirName = "pp_files";
		if (!TIME_DEPENDENT) {
			dirName += File.separator + "poisson";
		}
		calc.writeFiles(dirName, mags, false);
		calc.writeFiles(dirName + File.separator + "colMedian", mags, true);
	}
	
	private void printTimes(int tasksDone, double pDone) {
		long end = System.currentTimeMillis();
		double secs = (end - calcStartTime) / 1000d;
		double mins = secs / 60d;
		double estTotMins = mins / pDone;
		double estMinsLeft = estTotMins - mins;
		double tasksPerMin = (double)tasksDone / mins;
		System.out.println("Time spent: " + df.format(mins) + " mins ("
				+ df.format(estMinsLeft) + " mins left,\t" + df.format(tasksPerMin) +" tasks/min)");
	}

	@Override
	public void taskProgressUpdate(int tasksDone, int tasksLeft, int totalTasks) {
		double precent = (double)tasksDone / (double)totalTasks;
		int totPts = numAssigned + numUnassigned;
		double precentAssigned = (double)numAssigned / (double)totPts;
		System.out.println("Taks completed:\t" + tasksDone + "/" + totalTasks + "\t(" + pdf.format(precent) + ")"
				+ "\tAssigned:\t" + numAssigned + "/" + totPts + "\t(" + pdf.format(precentAssigned) + ")");
		printTimes(tasksDone, precent);
	}

}
