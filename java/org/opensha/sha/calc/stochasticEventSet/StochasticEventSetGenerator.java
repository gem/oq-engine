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
     * @return: {@link ArrayList} of {@link EqkRupture} representing the sampled
     *          events.
     */
    public static ArrayList<EqkRupture> getStochasticEventSetFromPoissonianERF(
            EqkRupForecast erf, Random rn) {

        validateInput(erf, rn);

        ArrayList<EqkRupture> stochasticEventSet = new ArrayList<EqkRupture>();
        for (int sourceIdx = 0; sourceIdx < erf.getNumSources(); sourceIdx++) {
            ProbEqkSource src = erf.getSource(sourceIdx);
            for (int ruptureIdx = 0; ruptureIdx < src.getNumRuptures(); ruptureIdx++) {
                ProbEqkRupture rup = src.getRupture(ruptureIdx);
                double numExpectedRup = -Math.log(1 - rup.getProbability());
                EqkRupture eqk =
                        new EqkRupture(rup.getMag(), rup.getAveRake(),
                                rup.getRuptureSurface(),
                                rup.getHypocenterLocation());
                // sample Poisson distribution using inverse transfom method
                // p is the Poisson probability
                // F is the cumulative distribution function
                // get number of rupture realizations (nRup) given
                // number of expected ruptures (numExpectedRup). nRup copies of
                // the same rupture are then added to the stochastic event set.
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
     *            number of stochastic event sets
     * @param rn
     *            {@link Random} random number generator
     * @return {@link ArrayList} of {@link ArrayList} of {@link EqkRupture}.
     */
    public static ArrayList<ArrayList<EqkRupture>>
            getMultipleStochasticEventSetsFromPoissonianERF(EqkRupForecast erf,
                    int num, Random rn) {

        ArrayList<ArrayList<EqkRupture>> multiStocEventSet =
                new ArrayList<ArrayList<EqkRupture>>();
        for (int i = 0; i < num; i++) {
            multiStocEventSet.add(getStochasticEventSetFromPoissonianERF(erf,
                    rn));
        }
        return multiStocEventSet;
    }

    /**
     * Check if the ERF contains only Poissonian sources
     * 
     * @param erf
     */
    private static Boolean ensurePoissonian(EqkRupForecast erf) {
        for (ProbEqkSource src : (ArrayList<ProbEqkSource>) erf.getSourceList())
            if (src.isSourcePoissonian() == false)
                throw new IllegalArgumentException("Sources must be Poissonian");
        return true;
    }

    private static Boolean validateInput(EqkRupForecast erf, Random rn) {
        if (erf == null) {
            throw new IllegalArgumentException(
                    "Earthquake rupture forecast cannot be null");
        }

        if (rn == null) {
            throw new IllegalArgumentException(
                    "Random number generator cannot be null");
        }

        ensurePoissonian(erf);

        return true;
    }
}
