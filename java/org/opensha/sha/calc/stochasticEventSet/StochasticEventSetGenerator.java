package org.opensha.sha.calc.stochasticEventSet;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;

import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.data.TimeSpan;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;

import org.opensha.sha.earthquake.rupForecastImpl.GEM1.GEM1ERF;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;

import org.opensha.sha.magdist.IncrementalMagFreqDist;

/**
 * 
 * This class provide methods for the creation of sets of seismicity histories
 * (given as and array list of SeismHist objects) representative of a given
 * Earthquake Rupture Forecast.
 * 
 * @author Marco Pagani, Damiano Monelli
 * 
 */
public class StochasticEventSetGenerator {

	private ArrayList<SeismHist> sHList; // A list of seismicity histories
	private Map<String, ProbEqkRupture> srcMapping; // maps source name with ruptures

	// contructor
	public StochasticEventSetGenerator() {
		this.sHList = new ArrayList<SeismHist>();
		this.srcMapping = new HashMap<String, ProbEqkRupture>();
	}

	/**
	 * This method resamples the ERF and creates a set of seismicity histories.
	 * In case a fleName is specified (i.e. is not 'null') this method creates a
	 * file containing the information necessary to reproduce the created
	 * seismicity history. The generation of each event of each seismicity
	 * history consists firstly in the selection of one source, then in the
	 * selection of a magnitude interval and finally of a rupture.
	 * 
	 * 
	 * @param srcDataList
	 *            ArrayList of GEM source data
	 * @param numSH
	 *            Number of seismicity histories to generate
	 * @param timeS
	 *            The time span to be used to generate the Seismicity Histories
	 *            (i.e. usually it's 50 years)
	 * @param fleNme
	 *            Name of the rupture list file (can be null)
	 * @throws IOException
	 */
	public ArrayList<SeismHist> CreateSetsF(
			ArrayList<GEMSourceData> srcDataList, int numSH, TimeSpan timeS,
			File fleNme) throws IOException {

		ArrayList<Double> prbMag;
		SeismHist sh;

		double sum = 0.0;
		double acc;
		double chk;
		double rnd;
		double m;
		double mWdt = 0.1;
		double mMin, mMax;
		double prb;
		int cnt;

		// Open rupture list file
		// Current format:
		//
		boolean logFle = false;
		BufferedWriter outFle = null;
		BufferedWriter outFleGmt = null;
		if (fleNme != null) {
			logFle = true;
			outFle = new BufferedWriter(new FileWriter(fleNme));
			outFle.write(String
					.format("<?xml version=\"1.0\" encoding=\"UTF-8\"?>"));
			outFle.write(String.format("<SeismicityHistories num=\"%d\">\n",
					numSH));
			outFle.write(String.format("<List>\n"));
			outFleGmt = new BufferedWriter(new FileWriter(fleNme + ".gmt"));
		}

		// Duration of seismicity histories
		double tme = timeS.getDuration();

		// Time span (very short) used to generate the ERF
		TimeSpan tms = new TimeSpan(TimeSpan.NONE, TimeSpan.YEARS); // Start and
																	// duration
																	// units
		tms.setDuration(1.0);

		// Earthquake rupture forecast
		GEM1ERF erf = new GEM1ERF(srcDataList);
		erf.setTimeSpan(tms);
		erf.updateForecast();

		// Info
		System.out.printf(
				"\nCreating stochastic event sets using %d sources\n",
				erf.getNumSources());
		System.out.println("Number of seismicity histories " + numSH);

		// Define the container for the number of events to generate by each
		// source
		int[] evGen = new int[erf.getNumSources()];

		double[] deltaEvents = new double[erf.getNumSources()];
		double[] accumulator = new double[erf.getNumSources()];

		int addEv[] = new int[erf.getNumSources()];

		// Find the number of events to generate by each source in the
		// investigation time
		// using the information contained in the ERF
		for (int j = 0; j < erf.getNumSources(); j++) {

			// Get the probabilistic earthquake rupture
			ProbEqkSource src = erf.getSource(j);

			// This is the total probability
			double prbx = src.computeTotalProb();

			// Rate of occurrence
			double lam = -Math.log(1.0 - prbx);

			System.out.println("StochasticEventSetGen lam: " + lam);

			// Find the number of events occurring during the investigation time
			deltaEvents[j] = (lam * tms.getDuration() * tme)
					- Math.floor(lam * tms.getDuration() * tme);
			evGen[j] = (int) Math.floor(lam * tms.getDuration() * tme);

			System.out.printf("Source %d (%30s) nev %d\n", j, erf.getSource(j)
					.getName(), evGen[j]);
		}

		// Create numSH "seismicity histories"
		int nH = 0;
		int cev = 0;
		while (nH < numSH) {

			// Info
			if ((Math.abs(Math.round(nH / 50.0) * 50.0 - nH)) < 1.0e-3)
				System.out.printf("   -- Seismicity history: %4d/%4d\n", nH,
						numSH - 1);

			// Create an array list where we collect all the ruptures
			ArrayList<ProbEqkRupture> rupl = new ArrayList<ProbEqkRupture>();

			// Create a new seismicity history
			sh = new SeismHist();

			// For each source randomly select one rupture and create seismicity
			// histories
			for (int j = 0; j < erf.getNumSources(); j++) {
				cev++;

				// Update the accumulator for this source
				addEv[j] = 0;
				accumulator[j] += deltaEvents[j];
				if (accumulator[j] >= 1) {
					accumulator[j] -= 1;
					addEv[j] = 1;
				}
				System.out.printf("Accum: %5.2f addEv: %d\n", accumulator[j],
						addEv[j]);

				// Get the source
				ProbEqkSource src = erf.getSource(j);

				// Create an array List containing the probability of occurrence
				// for discrete intervals of magnitude
				prbMag = new ArrayList<Double>();

				// Find the probability of occurrence for each magnitude
				// interval
				// Problem: the probability of occurrence obtained from a
				// ProbEqkSource
				// using the method computeTotalProbAbove already accounts for
				// time.
				//
				// This is not the best way of selecting events. Better to use a
				// MFD to sample magnitudes (this was implemented on 2009.09.18
				// using
				// a commented method available in the ProbEqkSource class)
				IncrementalMagFreqDist mfd = src.computeMagProbDist();

				mMax = mfd.getMaxX();
				mMin = mfd.getMinX();
				mWdt = mfd.getDelta();
				mfd.setTolerance(0.1 * mfd.getDelta());
				m = mMin;
				cnt = 0;
				sum = 0.0;

				while (m < mMax - mWdt) {
					// Get the rate for the given magnitude
					prb = mfd.getIncrRate(m);
					// Update the container
					prbMag.add(prb);
					// Normalizing factor
					sum += prb;
					// Update counters
					m = m + mWdt;
					cnt++;
				}

				// Normalize the weights for distinct magnitude intervals - It's
				// actually stupid to
				// repeat this for the generation of each seismicity history
				chk = 0.0;
				for (int i = 0; i < cnt; i++) {
					prb = prbMag.get(i);
					// System.out.println(prb);
					if (prb > 0.0) {
						prbMag.set(i, prb / sum); // Now a normalized weight
						chk = chk + prb / sum;
					}
				}
				if (Math.abs(chk - 1.0) > 1e-3)
					System.out.println("=== Normalization not correct ===");

				// Get magnitudes and ruptures -
				for (int k = 0; k < (evGen[j] + addEv[j]); k++) {

					// Select a magnitude interval
					rnd = Math.random();
					acc = prbMag.get(0);
					cnt = 0;
					while (acc < rnd) {
						if (cnt < prbMag.size()) {
							cnt++;
							acc = acc + prbMag.get(cnt);
						} else {
							System.out
									.println("Error: cnt > prbMag # of elements");
							break;
						}
					}

					// Source index
					int idxMag = cnt;
					// System.out.printf(" m [%5.3f,%5.3f[ \n",mMin+mWdt*idxMag,mMin+mWdt*(idxMag+1));

					// Get the ruptures for the selected source (within a
					// specific magnitude interval)
					ArrayList<ProbEqkRupture> rupList = erf.getRupturesMag(j,
							mMin + mWdt * idxMag, mMin + mWdt * (idxMag + 1));

					// Find the index of the rupture
					int idxRup = (int) (Math.round(Math.random()
							* rupList.size()) - 1);
					if (idxRup < 0)
						idxRup = 0;

					// Get the rupture
					ProbEqkRupture rpt = new ProbEqkRupture();
					rpt = rupList.get(idxRup);

					// Add the rupture to the list
					sh.addEvent(k, rpt);

					// Update the rupture list file
					if (logFle) {

						// Seismicity history number, rupture number, rupture
						// index
						outFle.write(String
								.format("   <Event shNum=\"%d\" srcNum=\"%d\" rupNum=\"%d\" rupIdx=\"%d\">\n",
										nH, j, k, idxRup));
						// outFle.write(String.format("%5d %5d %5d %5d\n",nH,j,k,idxRup));

						// Update the GMT file
						// outFleGmt.write(String.format("> -Z %.2f\n",rpt.getMag()));
						for (Location loc : rpt.getRuptureSurface()
								.getLocationList()) {
							outFleGmt.write(String.format("%6.2f %5.2f %d\n",
									loc.getLongitude(), loc.getLatitude(), k));
						}

					}

					// Update source mapping
					// TODO
					String code = String.format("%04d_%05d", j, k);
					srcMapping.put(code, rpt);
				}
			}

			// Updating seismicity histories list
			sHList.add(sh);

			// Seismicity histories counter
			nH++;
		}

		if (logFle) {
			outFle.write(String.format("</List>\n", numSH));
			outFle.write(String.format("</SeismicityHistories>\n"));
			outFle.close();
			outFleGmt.write(String.format(">"));
			outFleGmt.close();
		}
		return sHList;
	}

	/**
	 * Constructor for the set of seismicity histories. The provided ERF must
	 * contain a TimeSpan that is representative of the investigation time (e.g.
	 * for classical PSHA analyses this corresponds to 50 years). In case a
	 * fleName is specified this method creates a file containing the
	 * information necessary to reproduce the created seismicity history.
	 * 
	 * @param erf
	 *            Earthquake rupture forecast
	 * @param inpErf
	 *            GEM standard input to ERF object
	 * @param numSH
	 *            Number of seismicity histories to generate
	 * @param duration
	 *            The duration of the Seismicity Histories (i.e. classically 50
	 *            years)
	 * @param fleNme
	 *            Name of the rupture list file (can be null)
	 * @throws IOException
	 */
	public ArrayList<SeismHist> CreateSets(ArrayList<GEMSourceData> inpErf,
			int numSH, TimeSpan timeS, String fleNme) throws IOException {
		ArrayList<Double> prbMag;
		SeismHist sh;

		double sum = 0.0;
		double acc;
		double chk;
		double rnd;
		double m;
		double mWdt = 0.1;
		double mMin, mMax;
		double prb;
		double[] wei;
		int cnt;
		int nsrc;

		// Open rupture list file
		// Current format:
		//
		boolean logFle = false;
		BufferedWriter outFle = null;
		if (fleNme != null) {
			logFle = true;
			outFle = new BufferedWriter(new FileWriter(fleNme));
			outFle.write(String
					.format("<?xml version=\"1.0\" encoding=\"UTF-8\"?>"));
			outFle.write(String.format("<SeismicityHistories num=\"%d\">\n",
					numSH));
			outFle.write(String.format("<List>\n"));
		}

		// Create the ERF
		double tme = timeS.getDuration();
		timeS.setDuration(1.0);
		GEM1ERF erf = new GEM1ERF(inpErf);

		// Info
		System.out.printf(
				"\nCreating stochastic event sets using %d sources\n",
				erf.getNumSources());

		// // Get the number of sources in the Earthquake Rupture Forecast and
		// instantiate a
		// // weight vector
		// nsrc = erf.getNumSources();
		// wei = new double[nsrc];
		//
		// // Set weights to the sources using their probability of generating
		// an event
		// for (int i=0; i < nsrc; i++){
		// ProbEqkSource src = erf.getSource(i);
		// wei[i] = src.computeTotalProb();
		// sum = sum + wei[i];
		// }
		//
		// // Normalize the generated weights
		// chk = 0.0;
		// for (int i=0; i < nsrc; i++){
		// wei[i] = wei[i] / sum;
		// chk = chk + wei[i];
		// System.out.printf("Weight of source %d (%20s): %f\n",i,erf.getSource(i).getName(),wei[i]);
		// }
		//
		// // Check - Throw an exception?
		// // TODO
		// if ( Math.abs(1.0-chk)>1e-4) {
		// System.out.printf("Normalization not completed: %6.4f != 1.0\n",chk);
		// }

		// Define the container for the number of events to generate by each
		// source
		int[] evGen = new int[erf.getNumSources()];

		// Find the number of events to generate by each source in the
		// investigation time
		// using the information contained in the ERF
		for (int j = 0; j < erf.getNumSources(); j++) {

			// Get the probabilistic earthquake rupture
			ProbEqkSource src = erf.getSource(j);

			// This is the total probability
			double prbx = src.computeTotalProb();

			// Annual rate of occurrence
			double lam = -Math.log(1.0 - prbx);

			// Find the number of events occurring during the investigation time
			// evGen[j] = (int) Math.round(lam*timeS.getDuration());
			evGen[j] = (int) Math.round(lam * timeS.getDuration()
					* Math.round(tme));

			System.out.printf("Source %d (%20s) nev %d\n", j, erf.getSource(j)
					.getName(), evGen[j]);
		}

		// Create numSH "seismicity histories"
		int nH = 0;
		int cev = 0;
		while (nH < numSH) {

			// Info
			if ((Math.abs(Math.round(nH / 50.0) * 50.0 - nH)) < 1.0e-3)
				System.out.printf("   -- Seismicity history: %4d/%4d\n", nH,
						numSH - 1);

			// Create an array list where we collect all the ruptures
			ArrayList<ProbEqkRupture> rupl = new ArrayList<ProbEqkRupture>();

			// Create a new seismicity history
			sh = new SeismHist();

			// For each source randomly select one rupture for each event and
			// create seismicity histories
			for (int j = 0; j < erf.getNumSources(); j++) {
				cev++;

				// Get the source
				ProbEqkSource src = erf.getSource(j);

				// Create an array List containing the probability of occurrence
				// for discrete intervals of magnitude
				prbMag = new ArrayList<Double>();

				// Find the probability of occurrence for each magnitude
				// interval
				// Problem: the probability of occurrence obtained from a
				// ProbEqkSource
				// using the method computeTotalProbAbove already accounts for
				// time.
				//
				// This is not the correct way of selecting events. Better to
				// use a
				// MFD to sample magnitudes (this was implemented on 2009.09.18
				// using
				// a commented method available in the ProbEqkSource class)
				IncrementalMagFreqDist mfd = src.computeMagProbDist();

				mMax = mfd.getMaxX();
				mMin = mfd.getMinX();
				mWdt = mfd.getDelta();
				mfd.setTolerance(0.1 * mfd.getDelta());
				m = mMin;
				cnt = 0;
				sum = 0.0;

				while (m < mMax - mWdt) {
					// Get the rate for the given magnitude
					prb = mfd.getIncrRate(m);
					// Update the container
					prbMag.add(prb);
					// Normalizing factor
					sum += prb;
					// Update counters
					m = m + mWdt;
					cnt++;
				}

				// Normalize the weights for distinct magnitude intervals
				chk = 0.0;
				for (int i = 0; i < cnt; i++) {
					prb = prbMag.get(i);
					// System.out.println(prb);
					if (prb > 0.0) {
						prbMag.set(i, prb / sum); // Now a normalized weight
						chk = chk + prb / sum;
					}
				}
				if (Math.abs(chk - 1.0) > 1e-3)
					System.out.println("=== Normalization not correct ===");

				// Get magnitudes and ruptures
				for (int k = 0; k < evGen[j]; k++) {

					// Select a magnitude interval
					rnd = Math.random();
					acc = prbMag.get(0);
					cnt = 0;
					while (acc < rnd) {
						if (cnt < prbMag.size()) {
							cnt++;
							acc = acc + prbMag.get(cnt);
						} else {
							System.out
									.println("Error: cnt > prbMag # of elements");
							break;
						}
					}

					// Source index
					int idxMag = cnt;
					// System.out.printf(" m [%5.3f,%5.3f[ \n",mMin+mWdt*idxMag,mMin+mWdt*(idxMag+1));

					// Get the ruptures for the selected source (within a
					// specific magnitude interval)
					ArrayList<ProbEqkRupture> rupList = erf.getRupturesMag(j,
							mMin + mWdt * idxMag, mMin + mWdt * (idxMag + 1));

					// Find the index of the rupture
					int idxRup = (int) (Math.round(Math.random()
							* rupList.size()) - 1);
					if (idxRup < 0)
						idxRup = 0;

					// Get the rupture
					ProbEqkRupture rpt = new ProbEqkRupture();
					rpt = rupList.get(idxRup);

					// Add the rupture to the list
					sh.addEvent(k, rpt);

					// Update the rupture list file
					if (logFle) {
						// Seismicity history number, rupture number, rupture
						// index
						outFle.write(String
								.format("   <Event shNum=\"%d\" srcNum=\"%d\" rupNum=\"%d\" rupIdx=\"%d\">\n",
										nH, j, k, idxRup));
						// outFle.write(String.format("%5d %5d %5d %5d\n",nH,j,k,idxRup));
					}

					// Update source mapping
					// TODO
					String code = String.format("%04d_%05d", j, k);
					srcMapping.put(code, rpt);
				}
			}

			// Updating seismicity histories list
			sHList.add(sh);

			// Seismicity histories counter
			nH++;
		}

		if (logFle) {
			outFle.write(String.format("</List>\n", numSH));
			outFle.write(String.format("</SeismicityHistories>\n"));
			outFle.close();
		}
		return sHList;
	}

	/**
	 * This method provides the effective number of seismicity histories
	 * composing the set.
	 * 
	 * @return Number of seismicity histories
	 */
	public int getNumHistories() {
		return sHList.size();
	}

	/**
	 * This method supplies the set of seismicity histories composing the whole
	 * set.
	 * 
	 * @return Set of seismicity histories
	 */
	public ArrayList<SeismHist> getSeismHist() {
		return this.sHList;
	}

	/**
	 * This method provides the comprehensive list of Probabilistic Earthquake
	 * Ruptures being part of the set of seismicity histories.
	 * 
	 * @return Group of probabilistic earthquakes ruptures
	 */
	public ArrayList<EqkRupture> getEqkRupList() {
		ArrayList<EqkRupture> eqkRupList = new ArrayList<EqkRupture>();
		Iterator<SeismHist> iterSes = this.getSeismHist().iterator();
		// Iterate through the seismicity histories
		while (iterSes.hasNext()) {
			SeismHist sHtmp = iterSes.next();
			Iterator<ProbEqkRupture> iterRup = sHtmp.getRuptures().iterator();
			// Iterate through the events of one seismicity history
			while (iterRup.hasNext()) {
				EqkRupture rup = iterRup.next();

				eqkRupList.add(rup);
			}
		}
		return eqkRupList;
	}

	/**
	 * This method creates a file containing information on the generated
	 * seismicity histories
	 * 
	 */
	public void createINFOfile(String outdir) {
		String filename = outdir + "eqkRupturesINFO.dat";
		try {

			// Open buffer
			BufferedWriter out = new BufferedWriter(new FileWriter(filename));

			// Create list of keywords
			Set<String> strset = srcMapping.keySet();

			Iterator<String> iter = strset.iterator();
			while (iter.hasNext()) {
				String str = iter.next();
				String[] strArr = str.split("_");
				ProbEqkRupture rup = srcMapping.get(str);
				out.write(String.format("%s %s %5.2f\n", strArr[0], strArr[1],
						rup.getMag()));
			}

			// // Iterator
			// Iterator<SeismHist> iter = this.sHList.iterator();
			// // Iterate through the eqkRuptures
			// while (iter.hasNext()) {
			// // Get the seismicity history
			// SeismHist sh = iter.next();
			// // Create iteraror
			// Iterator<ProbEqkRupture> iterER = sh.getRuptures().iterator();
			// // Print
			// while (iterER.hasNext()){
			// ProbEqkRupture rup = iterER.next();
			// out.write(String.format("%10.5f %10.5f\n",loc.getLongitude(),loc.getLatitude()));
			// }
			// }
			out.close();
		} catch (IOException e) {
			System.out.println("There was a problem:" + e);
		}
	}

	/**
	 * This method creates two GMT-ready files. One file contains finite size
	 * ruptures, the other one includes point sources.
	 * 
	 */
	public void createGMTfile(String outdir) {
		boolean isPoint = false;
		// Output filename
		String filenamePoint = outdir + "eqkRupturesPoints.gmt";
		String filename = outdir + "eqkRuptures.gmt";
		// EqkRuptures iterator
		try {
			// Open buffer
			BufferedWriter out = new BufferedWriter(new FileWriter(filename));
			BufferedWriter outPoint = new BufferedWriter(new FileWriter(
					filenamePoint));
			Iterator<EqkRupture> iter = this.getEqkRupList().iterator();
			// Iterate through the eqkRuptures
			while (iter.hasNext()) {
				isPoint = false;
				if (!isPoint)
					out.write(String.format("> \n"));
				EqkRupture eqkrup = iter.next();
				// Get the rupture perimeter
				LocationList loclist = eqkrup.getRuptureSurface()
						.getSurfacePerimeterLocsList();
				// Check if we're considering point sources
				if (loclist.size() < 2)
					isPoint = true;
				// Creater iterator
				Iterator<Location> iterLoc = loclist.iterator();
				// Print
				while (iterLoc.hasNext()) {
					Location loc = iterLoc.next();
					if (isPoint) {
						outPoint.write(String.format("%10.5f %10.5f %5.2f\n",
								loc.getLongitude(), loc.getLatitude(),
								eqkrup.getMag()));
					} else {
						out.write(String.format("%10.5f %10.5f\n",
								loc.getLongitude(), loc.getLatitude()));
					}
				}
			}
			out.write(String.format(">\n"));
			out.close();
			outPoint.close();
		} catch (IOException e) {
			System.out.println("There was a problem:" + e);
		}
	}

}
