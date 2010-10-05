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
 * This class provide methods for the creation of stochastic event sets (each
 * given as an array list of EqkRupture objects) representative of a given
 * Earthquake Rupture Forecast.
 * 
 * @author Damiano Monelli
 * 
 */
public class StochasticEventSetGenerator {

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
	 * @return:
	 * {@link ArrayList} of {@link EqkRupture} representing the sampled events.
	 */
	public static ArrayList<EqkRupture> getStochasticEvenSetFromPoissonianERF(
			EqkRupForecast erf, Random rn) {

		validateInput(erf,rn);
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
	 * @return {@link ArrayList} of {@link ArrayList} of {@link EqkRupture}.
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
	 * Check if the ERF contains only Poissonian sources
	 * @param erf
	 */
	private static Boolean isErfPoissonian(EqkRupForecast erf) {
		for (ProbEqkSource src : (ArrayList<ProbEqkSource>) erf.getSourceList())
			if (src.isSourcePoissonian() == false)
				throw new IllegalArgumentException("Sources must be Poissonian");
		return true;
	}

	private static Boolean validateInput(EqkRupForecast erf, Random rn){
		if (erf == null) {
			throw new IllegalArgumentException(
					"Earthquake rupture forecast cannot be null");
		}

		if (rn == null) {
			throw new IllegalArgumentException(
					"Random number generator cannot be null");
		}
		return true;
	}
}
