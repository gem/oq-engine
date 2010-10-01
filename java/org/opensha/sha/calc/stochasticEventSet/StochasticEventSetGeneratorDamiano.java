package org.opensha.sha.calc.stochasticEventSet;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Random;

import org.opensha.commons.data.TimeSpan;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;

import org.opensha.sha.earthquake.rupForecastImpl.GEM1.GEM1ERF;

import org.opensha.sha.magdist.IncrementalMagFreqDist;

/**
 * 
 * This class provide methods for the creation of a stochastic event set (given
 * as an array list of EqkRupture objects) representative of a given Earthquake
 * Rupture Forecast.
 * 
 * @author Damiano Monelli
 * 
 */
public class StochasticEventSetGeneratorDamiano {

	private static boolean D = true;

	/**
	 * Generate a stochastic event set from a Poissonian ERF. Sampling of the
	 * Poissonian pdf is based on the inverse transform method as described in
	 * "Computational Statistics Handbook with Matlab", Martinez & Martinez, Ed.
	 * Champman & Hall, pag. 103
	 * 
	 * @param erf
	 *            {@link EqkRupForecast} earthquake rupture forecast
	 * @param rn
	 *            {@link Random} random number generator
	 * @return
	 */
	public static ArrayList<EqkRupture> getStochasticEvenSetFromPoissonianERF(
			EqkRupForecast erf, Random rn) {

		isErfPoissonian(erf);

		ArrayList<EqkRupture> stochasticEventSet = new ArrayList<EqkRupture>();
		for (int is = 0; is < erf.getNumSources(); is++) {
			ProbEqkSource src = erf.getSource(is);
			for (int ir = 0; ir < src.getNumRuptures(); ir++) {
				ProbEqkRupture rup = src.getRupture(ir);
				double numExpectedRup = -Math.log(1 - rup.getProbability());
				EqkRupture eqk = new EqkRupture(rup.getMag(), rup.getAveRake(),
						rup.getRuptureSurface(), rup.getHypocenterLocation());
				// sample Poisson distribution
				// that is get number of rupture realizations given
				// numExpectedRup
				int nRup = 0;
				boolean flag = true;
				double u = rn.nextDouble();
				int i = 0;
				double p = Math.exp(-numExpectedRup);
				double F = p;
				while (flag == true) {
					if (u <= F) {
						nRup = i;
						flag = false;
					} else {
						p = numExpectedRup * p / (i + 1);
						i = i + 1;
						F = F + p;
					}
				}
				for (int j = 0; j < nRup; j++)
					stochasticEventSet.add(eqk);
			}
		}
		return stochasticEventSet;
	}

	/**
	 * Generate multiple stochastic event sets by calling the
	 * getStochasticEvenSetFromPoissonianERF method.
	 * 
	 * @param erf
	 *            {@link EqkRupForecast} earthquake rupture forecast
	 * @param num
	 *            number of stachastic event sets
	 * @param rn
	 *            {@link Random} random number generator
	 * @return
	 */
	public static ArrayList<ArrayList<EqkRupture>> getMultipleStochasticEvenSetsFromPoissonianERF(
			EqkRupForecast erf, int num, Random rn) {

		ArrayList<ArrayList<EqkRupture>> multiStocEventSet = new ArrayList<ArrayList<EqkRupture>>();
		for (int i = 0; i < num; i++) {
			multiStocEventSet
					.add(getStochasticEvenSetFromPoissonianERF(erf, rn));
		}
		return multiStocEventSet;
	}

	/**
	 * This method resamples the ERF and creates a stochastic event set from a
	 * GEM1ERF. The generation of a stochastic event set consists firstly in the
	 * selection of one source, then in the selection of a magnitude interval
	 * and finally of a rupture.
	 * 
	 * @param erf
	 *            GEM1ERF
	 * @return ArrayList<ProbEqkRupture>
	 * @throws IOException
	 */

	public static ArrayList<EqkRupture> getStochasticEventSetFromGEM1ERF(
			GEM1ERF erf, Random rn) {

		ArrayList<Double> prbMag;

		double sum = 0.0;
		double acc;
		double chk;
		double rnd;
		double m;
		double mWdt = 0.1;
		double mMin, mMax;
		double prb;
		int cnt;

		// Duration of seismicity histories
		double tme = erf.getTimeSpan().getDuration();

		// Time span (very short) used to generate the ERF
		TimeSpan tms = new TimeSpan(TimeSpan.NONE, TimeSpan.YEARS); // Start and
																	// duration
																	// units
		tms.setDuration(1.0);

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

		// Create an array list where we collect all the ruptures
		ArrayList<EqkRupture> rupl = new ArrayList<EqkRupture>();

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
				rnd = rn.nextDouble();
				acc = prbMag.get(0);
				cnt = 0;
				while (acc < rnd) {
					if (cnt < prbMag.size()) {
						cnt++;
						acc = acc + prbMag.get(cnt);
					} else {
						System.out.println("Error: cnt > prbMag # of elements");
						break;
					}
				}

				// Source index
				int idxMag = cnt;
				// System.out.printf(" m [%5.3f,%5.3f[ \n",mMin+mWdt*idxMag,mMin+mWdt*(idxMag+1));

				// Get the ruptures for the selected source (within a
				// specific magnitude interval)
				ArrayList<ProbEqkRupture> rupList = erf.getRupturesMag(j, mMin
						+ mWdt * idxMag, mMin + mWdt * (idxMag + 1));

				// Find the index of the rupture
				int idxRup = (int) (Math
						.round(rn.nextDouble() * rupList.size()) - 1);
				if (idxRup < 0)
					idxRup = 0;

				// Get the rupture
				ProbEqkRupture rpt = new ProbEqkRupture();
				rpt = rupList.get(idxRup);

				EqkRupture eqk = new EqkRupture(rpt.getMag(), rpt.getAveRake(),
						rpt.getRuptureSurface(), rpt.getHypocenterLocation());
				rupl.add(eqk);
			}
		}
		return rupl;
	}

	public static ArrayList<ArrayList<EqkRupture>> getMultipleStochasticEvenSetsFromGEM1ERF(
			GEM1ERF erf, int num, Random rn) {

		ArrayList<ArrayList<EqkRupture>> multiStocEventSet = new ArrayList<ArrayList<EqkRupture>>();
		for (int i = 0; i < num; i++) {
			multiStocEventSet.add(getStochasticEventSetFromGEM1ERF(erf, rn));
		}
		return multiStocEventSet;
	}

	private static void isErfPoissonian(EqkRupForecast erf) {
		for (ProbEqkSource src : (ArrayList<ProbEqkSource>) erf.getSourceList())
			if (src.isSourcePoissonian() == false)
				throw new IllegalArgumentException("Sources must be Poissonian");
	}
}
