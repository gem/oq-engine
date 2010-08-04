package scratch.kevin.faultParticipationProbs;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.lang.reflect.Array;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;

import org.opensha.commons.data.Container2D;
import org.opensha.commons.data.NamedObjectAPI;
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
import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.UCERF2;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.MeanUCERF2.MeanUCERF2;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data.finalReferenceFaultParamDb.DeformationModelPrefDataFinal;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.faultSurface.SimpleFaultData;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;
import org.opensha.sha.magdist.SummedMagFreqDist;

public class SAF_Closest_Pt_Test_with_rake implements TaskProgressListener {

	private static final double gridSpacing = 1.0;
	private static final double halfGridSpacing = gridSpacing * 0.5d;
	
	private static final boolean QUICK_TEST = false;

	private ArrayList<ProbEqkSource> sources;

	private ArrayList<FaultProbPairing> faults;

	private static final SmartSurfaceFilter filter = new SmartSurfaceFilter(2, 5, 150);
	private static final boolean fastDist = true;
	private static double filterDistThresh = 10d;
	private static double closestThresh = 10d;

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

	public SAF_Closest_Pt_Test_with_rake(DeformationModelPrefDataFinal data, int defModel, ArrayList<ProbEqkSource> sources,
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
			FocalMechanism fm = new FocalMechanism(getStrikeEst(surface), fault.getAveDip(), fault.getAveRake());
			faults.add(new FaultProbPairing(surface, fault.getName(), faultSectionId,
					fault.getAveLongTermSlipRate(), fm));
		}
	}
	
	private static double getStrikeEst(EvenlyGriddedSurfaceAPI surface) {
		Location pt1 = surface.get(0, 0);
		Location pt2 = surface.get(0, surface.getNumCols()-1);
		return LocationUtils.azimuth(pt2, pt1);
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
			EvenlyGriddedSurfaceAPI rupSurface = rup.getRuptureSurface();
			FocalMechanism fm = new FocalMechanism(getStrikeEst(rupSurface), Double.NaN, rup.getAveRake());
			double meanAnnualRate = rup.getMeanAnnualRate(duration);
			for (Location rupPt : rupSurface) {
				SummedMagFreqDist closestMFD = getClosestMFD(faultsForRup, rupPt, fm);
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
	
	public void writeFiles(String dir, float[] mags) throws IOException {
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
				
				for (int row=0; row<fault.getSurface().getNumRows(); row++) {
					for (int col=0; col<fault.getSurface().getNumCols(); col++) {
						Location loc = fault.getSurface().get(row, col);
						String locStr = loc.getLatitude() + "\t" + loc.getLongitude() + "\t" + loc.getDepth();
						String rLine = locStr;
						String pLine = locStr;
						for (int i=0; i<mags.length; i++) {
							rLine += "\t" + rates[i].get(row, col);
							pLine += "\t" + probs[i].get(row, col);
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
	
	private static double angleSubtract(double a1, double a2) {
		if (a1 > a2) {
			double temp = a2;
			a2 = a1;
			a1 = temp;
		}
		double result = a2 - a1;
		if (result > 180d)
			result = (a1 + 360d) - a2;
		return result;
	}

	private SummedMagFreqDist getClosestMFD(ArrayList<FaultProbPairing> faultsForSource,
			Location rupPt, FocalMechanism rupFM) {
		if (faultsForSource.size() == 0)
			return null;
		SummedMagFreqDist closestMFD = null;
		ArrayList<FaultPtDistRecord> dists = new ArrayList<FaultPtDistRecord>();
		for (FaultProbPairing fault : faultsForSource) {
			FaultPtDistRecord dist = new FaultPtDistRecord(fault, rupPt, rupFM);
			dist.compute();
			dists.add(dist);
		}
		// filter out ones with opposite rake's or stikes
		for (int i=dists.size()-1; i>=0; i--) {
			FaultPtDistRecord dist = dists.get(i);
			double rakeDiff = dist.rakeDiff;
			double strikeDiff = dist.strikeDiff;
			if (rakeDiff > 30 || strikeDiff > 60) {
//				System.err.println("Filtering out because rakeDiff=" + rakeDiff + " and strikeDiff=" + strikeDiff);
				dists.remove(i);
			}
		}
		if (dists.size() == 0)
			return null;
		Collections.sort(dists, new FaultPtDistRecordComparator());
		FaultPtDistRecord best = dists.get(0);
		if (best.closestRow < 0)
			return null;
		FaultProbPairing fault = best.fault;
		closestMFD = fault.getMFDs().get(best.closestRow, best.closestCol);
//		double closestDist = dists.get(0).closestDist;
//		if (closestDist > dists.get(1).closestDist)
//			throw new RuntimeException("sorting didn't work!");
//		if (closestDist > halfGridSpacing) {
//			// it's not really close, lets look for a better match
//			FaultPtDistRecord[] topRecords = new FaultPtDistRecord[dists.size()];
//			double[] topColDists = new double[dists.size()];
//			int minTopColDistI  = -1;
//			double minTopColDist  = Double.MAX_VALUE;
//			for (int i=0; i<topColDists.length; i++) {
//				topColDists[i] = dists.get(i).calcTopOfColDist();
//				if (topColDists[i] < minTopColDist) {
//					minTopColDist = topColDists[i];
//					minTopColDistI = i;
//				}
//			}
//			if (minTopColDistI != 0) {
//				// the closest top col dist isn't the closest normal dist
//				
//			}
//		}
		
		return closestMFD;
	}
	
	private static class FaultPtDistRecordComparator implements Comparator<FaultPtDistRecord> {

		@Override
		public int compare(FaultPtDistRecord dist1, FaultPtDistRecord dist2) {
			return Double.compare(dist1.score, dist2.score);
		}
		
	}
	
	private class FaultPtDistRecord {
		
		private EvenlyGriddedSurfaceAPI faultSurface;
		private Location rupPt;
		private Location closestPt = null;
		private int closestRow = -1;
		private int closestCol = -1;
		private double closestDist = Double.MAX_VALUE;
		private double horizDist = Double.MAX_VALUE;
		private double vertDist = Double.MAX_VALUE;
		private FocalMechanism rupFM;
		private FaultProbPairing fault;
		private double rakeDiff;
		private double strikeDiff;
		private double score = Double.MAX_VALUE;
		
		public FaultPtDistRecord(FaultProbPairing fault, Location rupPt, FocalMechanism rupFM) {
			this.fault = fault;
			this.faultSurface = fault.getSurface();
			this.rupPt = rupPt;
			this.rupFM = rupFM;
		}
		
		public void compute() {
			for (int row=0; row<faultSurface.getNumRows(); row++) {
				for (int col=0; col<faultSurface.getNumCols(); col++) {
					Location faultPt = faultSurface.get(row, col);
					double dist, h, v;
//					LocationUtils.hT
					if (fastDist) {
						h = LocationUtils.horzDistanceFast(rupPt, faultPt);
					} else {
						h = LocationUtils.horzDistance(rupPt, faultPt);
					}
					v = Math.abs(LocationUtils.vertDistance(rupPt, faultPt));
					dist = Math.sqrt(h*h + v*v);
					if (dist < closestDist && dist < closestThresh) {
						this.closestRow = row;
						this.closestCol = col;
						this.closestPt = faultPt;
						this.horizDist = h;
						this.vertDist = v;
						closestDist = dist;
					}
				}
			}
			rakeDiff = angleSubtract(rupFM.getRake(), fault.getFocalMechanism().getRake());
			strikeDiff = angleSubtract(rupFM.getStrike(), fault.getFocalMechanism().getStrike());
			if (strikeDiff > 90)
				strikeDiff = Math.abs(strikeDiff - 180d);
			score = getScore();
		}
		
		private double getScore() {
			double score = horizDist * 10; 	// 10 pts/KM
			score += vertDist * 25;			// 25 pts/KM
//			score += rakeDiff * 5;			// 5 pts/degree
//			score += strikeDiff * 0.3;			// 0.2 pt/degree
			
			return score;
		}
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
		private FocalMechanism fm;
		
		public FaultProbPairing(EvenlyGriddedSurfaceAPI surface, String name, int sectionID,
				double slip, FocalMechanism fm) {
			this.surface = surface;
			this.name = name;
			this.sectionID = sectionID;
			this.slipRate = slip;
			this.fm = fm;
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
		
		public FocalMechanism getFocalMechanism() {
			return fm;
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
		System.out.println("Updating forecast");
		erf.updateForecast();
		ArrayList<ProbEqkSource> sources = new ArrayList<ProbEqkSource>();
		// for now just SAF
		for (int i=0; i<erf.getNumSources(); i++) {
			ProbEqkSource source = erf.getSource(i);
			if (!QUICK_TEST || i==128)
				sources.add(source);
		}
		SAF_Closest_Pt_Test_with_rake calc =
			new SAF_Closest_Pt_Test_with_rake(data, defModel, sources, minMag, maxMag, numMagBins, duration);
		calc.loadMFDs();
		float[] mags = new float[numMagBins];
		for (int i=0; i<numMagBins; i++) {
			mags[i] =(float)(minMag + 0.1*(float)i);
		}
		calc.writeFiles("pp_files", mags);
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
