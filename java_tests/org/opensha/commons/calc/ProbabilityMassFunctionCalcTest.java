package org.opensha.commons.calc;

import static org.junit.Assert.assertEquals;

import org.junit.Test;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;

/**
 * This class provides tests for the ProbabilityMassFunctionCalc class
 * 
 * @author damianomonelli
 * 
 */
public class ProbabilityMassFunctionCalcTest {

    // tolerance
    double tolerance = 1e-10;

    @Test
    public void evenlyDiscretizedPOEfromGaussianDist() {
        /**
         * This test compares the PMF for a Gaussian distribution (mean zero,
         * standard deviation one) explicitly calculated using the method
         * GaussianDistCalc.getExceedProb and the formula PMF((I1+I2)/2) =
         * POE(I1) - POE(I2) with the PMF obtained by using the method
         * ProbabilityMassFunctionCalc.getPMFfromPOE and passing as input a POE
         * for a Gaussian distribution obtained with the same method
         * GaussianDistCalc.getExceedProb
         */

        // POE parameters
        double minX = -9.0;
        double maxX = 9.0;
        int numVal = 19;

        EvenlyDiscretizedFunc poe = getGaussianPOE(minX, maxX, numVal);
        EvenlyDiscretizedFunc pmf1 = ProbabilityMassFunctionCalc.getPMF(poe);

        // compute PMF directly via GaussianDistCalc.getExceedProb method
        // the PMF values are calculated for the bins' middle points.
        // that's why the minimum is shifted by half delta
        // and the number of values is reduced by a factor of 1
        double delta = (maxX - minX) / (numVal - 1);
        EvenlyDiscretizedFunc pmf2 =
                getGaussianPMF(minX + delta / 2, numVal - 1, delta);

        // compare the 2 pmfs
        comparePMFs(pmf1, pmf2);
    }

    @Test(expected = IllegalArgumentException.class)
    public void evenlyDiscretizedPOEWith2Values() {
        /**
         * This test checks the behaviour of the getPMFfromPOE method when a POE
         * with only 2 values is passed (using the same strategy of the
         * probabilityMassFunctionCalcWithGaussianDistribution test)
         */

        // POE parameters
        double minX = -1.0;
        double maxX = 1.0;
        int numVal = 2;

        // calculate POE values for Gaussian distribution
        EvenlyDiscretizedFunc poe = getGaussianPOE(minX, maxX, numVal);
        // compute PMF using the getPMFfromPOE method
        EvenlyDiscretizedFunc pmf1 = ProbabilityMassFunctionCalc.getPMF(poe);
    }

    @Test(expected = IllegalArgumentException.class)
    public void evenlyDiscretizedPOEWith1Value() {
        /**
         * This test check the behaviour of the getPMFfromPOE method when a POE
         * function with only one values is passed
         */
        EvenlyDiscretizedFunc poe = new EvenlyDiscretizedFunc(0.0, 0.0, 1);
        poe.set(0, 1.0);
        EvenlyDiscretizedFunc pmf = ProbabilityMassFunctionCalc.getPMF(poe);
    }

    @Test(expected = IllegalArgumentException.class)
    public void nullEvenlyDiscretizedPOE() {
        /**
         * This test check the behaviour of the getPMFfromPOE method when a null
         * poe is passed
         */
        EvenlyDiscretizedFunc poe = null;
        EvenlyDiscretizedFunc pmf = ProbabilityMassFunctionCalc.getPMF(poe);
    }

    @Test(expected = IllegalArgumentException.class)
    public void evenlyDiscretizedPOEWithNonDecreasingValues() {
        /**
         * This test checks the behaviour of the getPMFfromPOE method when non
         * decreasing POE values are passed.
         */
        EvenlyDiscretizedFunc poe = new EvenlyDiscretizedFunc(0.0, 3.0, 4);
        poe.set(0, 1.0);
        poe.set(1, 0.9);
        poe.set(2, 0.7);
        poe.set(3, 0.8);
        EvenlyDiscretizedFunc pmf = ProbabilityMassFunctionCalc.getPMF(poe);
    }

    @Test(expected = IllegalArgumentException.class)
    public void evenlyDiscretizedPOEWithNegativeValues() {
        /**
         * This test checks the behavior of the getPMFfromPOE method when
         * negative POE values are passed.
         */
        EvenlyDiscretizedFunc poe = new EvenlyDiscretizedFunc(0.0, 3.0, 4);
        poe.set(0, 1.0);
        poe.set(1, 0.9);
        poe.set(2, 0.8);
        poe.set(3, -0.7);
        EvenlyDiscretizedFunc pmf = ProbabilityMassFunctionCalc.getPMF(poe);
    }

    @Test(expected = IllegalArgumentException.class)
    public void evenlyDiscretizedPOEWithGreaterThan1Values() {
        /**
         * This test checks the behavior of the getPMFfromPOE method when
         * greater than 1 POE values are passed.
         */
        EvenlyDiscretizedFunc poe = new EvenlyDiscretizedFunc(0.0, 3.0, 4);
        poe.set(0, 1.1);
        poe.set(1, 0.9);
        poe.set(2, 0.8);
        poe.set(3, 0.7);
        EvenlyDiscretizedFunc pmf = ProbabilityMassFunctionCalc.getPMF(poe);
    }

    /**
     * This test compares the PMF values obtained by using the
     * getArbitrarilyDiscretizedGaussianPOE method with POE values obtained from
     * a Gaussian Distribution and the PMF values calculated explicitly using
     * the method GaussianDistCalc.getExceedProb and the formula PMF((I1+I2)/2)
     * = POE(I1) - POE(I2)
     */
    @Test
    public void arbitrarilyDiscretizedPOEfromGaussianDist() {
        // define Gaussian POE values for not-evenly spaced values
        double[] xVals = { -10, -5, -2.5, -0.5, 0.5, 2.5, 5, 10 };
        ArbitrarilyDiscretizedFunc poe =
                getArbitrarilyDiscretizedGaussianPOE(xVals);

        ArbitrarilyDiscretizedFunc pmf1 =
                ProbabilityMassFunctionCalc.getPMF(poe);

        ArbitrarilyDiscretizedFunc pmf2 =
                getArbitrarilyDiscretizedGaussianPMF(xVals);

        comparePMFs(pmf1, pmf2);
    }

    /**
     * This test performs a similar test of
     * probabilityMassFunctionCalcWithArbitraryDiscretizedPOE but considering an
     * ArbitrarilyDiscretizedFunc POE with only 2 values
     */
    @Test(expected = IllegalArgumentException.class)
    public void arbitrarilyDiscretizedPOEWith2Values() {
        // define Gaussian POE values for not-evenly spaced values
        double[] xVals = { -0.5, 0.5 };
        ArbitrarilyDiscretizedFunc poe =
                getArbitrarilyDiscretizedGaussianPOE(xVals);

        ArbitrarilyDiscretizedFunc pmf1 =
                ProbabilityMassFunctionCalc.getPMF(poe);
    }

    /**
     * This test check the behaviour of the getPMFfromArbitrarilyDiscretizedPOE
     * method when a POE function with only one values is passed
     */
    @Test(expected = IllegalArgumentException.class)
    public void arbitrarilyDiscretizedPOEWith1Value() {
        ArbitrarilyDiscretizedFunc poe = new ArbitrarilyDiscretizedFunc();
        poe.set(0.0, 1.0);
        ArbitrarilyDiscretizedFunc pmf =
                ProbabilityMassFunctionCalc.getPMF(poe);
    }

    /**
     * This test check the behaviour of the getPMFfromArbitrarilyDiscretizedPOE
     * method when a null poe is passed
     */
    @Test(expected = IllegalArgumentException.class)
    public void nullArbitrarilyDiscretizedPOE() {
        ArbitrarilyDiscretizedFunc poe = null;
        ArbitrarilyDiscretizedFunc pmf =
                ProbabilityMassFunctionCalc.getPMF(poe);
    }

    /**
     * This test check the behavior of the getPMFfromArbitrarilyDiscretizedPOE
     * method when non decreasing POE values are passed.
     */
    @Test(expected = IllegalArgumentException.class)
    public void arbitrarilyDiscretizedPOEWithNonDecreasingValues() {
        ArbitrarilyDiscretizedFunc poe = new ArbitrarilyDiscretizedFunc();
        poe.set(0.0, 1.0);
        poe.set(1.0, 0.9);
        poe.set(2.0, 0.7);
        poe.set(3.0, 0.8);
        ArbitrarilyDiscretizedFunc pmf =
                ProbabilityMassFunctionCalc.getPMF(poe);
    }

    @Test(expected = IllegalArgumentException.class)
    public void arbitrarilyDiscretizedPoeWithNegativeValues() {
        /**
         * This test checks the behavior of the
         * getPMFfromArbitrarilyDiscretizedPOE method when negative POE values
         * are passed.
         */
        ArbitrarilyDiscretizedFunc poe = new ArbitrarilyDiscretizedFunc();
        poe.set(0.0, 1.0);
        poe.set(1.0, 0.9);
        poe.set(2.0, 0.8);
        poe.set(3.0, -0.7);
        ArbitrarilyDiscretizedFunc pmf =
                ProbabilityMassFunctionCalc.getPMF(poe);
    }

    @Test(expected = IllegalArgumentException.class)
    public void arbitrarilyDiscretizedPoeWithGreaterThan1Values() {
        /**
         * This test checks the behavior of the
         * getPMFfromArbitrarilyDiscretizedPOE method when greater than 1 POE
         * values are passed.
         */
        ArbitrarilyDiscretizedFunc poe = new ArbitrarilyDiscretizedFunc();
        poe.set(0.0, 1.1);
        poe.set(1.0, 0.9);
        poe.set(2.0, 0.8);
        poe.set(3.0, 0.7);
        ArbitrarilyDiscretizedFunc pmf =
                ProbabilityMassFunctionCalc.getPMF(poe);
    }

    /**
     * Get probability of exceedence (poe) values for a Gaussian distribution
     * (mean=0,std=1) using the method GaussianDistCalc.getExceedProb
     * 
     * @param minX
     *            : minimum value for which computing the poe
     * @param maxX
     *            : maximum value for which computing the poe
     * @param numVal
     *            : number of values for which computing the poe (together with
     *            minX and maxX controls the spacing)
     * @return: probability of exceedence values in a EvenlyDiscretizerFunc
     *          object
     */
    private EvenlyDiscretizedFunc getGaussianPOE(double minX, double maxX,
            int numVal) {
        EvenlyDiscretizedFunc poe =
                new EvenlyDiscretizedFunc(minX, maxX, numVal);
        for (int i = 0; i < numVal; i++) {
            double valX = poe.getX(i);
            poe.set(i, GaussianDistCalc.getExceedProb(valX));
        }
        return poe;
    }

    /**
     * Get probability of exceedence values for a set values
     * 
     * @param xVals
     *            : double[] array containing values for which calculating POE
     * @return an ArbitrarilyDiscretizedFunc containing POE values
     */
    private ArbitrarilyDiscretizedFunc getArbitrarilyDiscretizedGaussianPOE(
            double[] xVals) {
        ArbitrarilyDiscretizedFunc poe = new ArbitrarilyDiscretizedFunc();
        for (int i = 0; i < xVals.length; i++) {
            poe.set(xVals[i], GaussianDistCalc.getExceedProb(xVals[i]));
        }
        return poe;
    }

    /**
     * Get probability mass function (PMF) values for a Gaussian distribution
     * (mean=0,std=1) using the GaussianDistCalc.getExceedProb method and using
     * the formula PMF((I1+I2)/2) = POE(I1) - POE(I2)
     * 
     * @param minX
     *            : minimum (bin's middle point) value for which calculating the
     *            PMF
     * @param numVal
     *            : number of values for which computing the PMF
     * @param delta
     *            : binwidth associated to each PMF value
     * @return probability mass function values in a EvenlyDiscretized object
     */
    private EvenlyDiscretizedFunc getGaussianPMF(double minX, int numVal,
            double delta) {
        EvenlyDiscretizedFunc pmf =
                new EvenlyDiscretizedFunc(minX, numVal, delta);
        for (int i = 0; i < numVal; i++) {
            double x1 = pmf.getX(i) - delta / 2;
            double x2 = pmf.getX(i) + delta / 2;
            double val =
                    GaussianDistCalc.getExceedProb(x1)
                            - GaussianDistCalc.getExceedProb(x2);
            pmf.set(i, val);
        }
        return pmf;
    }

    /**
     * Get a Gaussian (mean=0,std=1) probability mass function (PMF) for a set
     * of values (assumed to be not-evenly spaced) using the
     * GaussianDistCalc.getExceedProb method and using the formula
     * PMF((I1+I2)/2) = POE(I1) - POE(I2)
     * 
     * @param xVals
     *            : double[] containing bins' limits
     * @return ArbitrarilyDiscretizedFunc containing PMF values referring to
     *         bins' middle points.
     */
    private ArbitrarilyDiscretizedFunc getArbitrarilyDiscretizedGaussianPMF(
            double[] xVals) {
        ArbitrarilyDiscretizedFunc pmf = new ArbitrarilyDiscretizedFunc();
        for (int i = 0; i < xVals.length - 1; i++) {
            double x1 = xVals[i];
            double x2 = xVals[i + 1];
            double xMean = (x1 + x2) / 2;
            double val =
                    GaussianDistCalc.getExceedProb(x1)
                            - GaussianDistCalc.getExceedProb(x2);
            pmf.set(xMean, val);
        }
        return pmf;
    }

    /**
     * Compare probability mass functions
     * 
     * @param pmf1
     * @param pmf2
     */
    private void comparePMFs(DiscretizedFuncAPI pmf1, DiscretizedFuncAPI pmf2) {
        int numVal1 = pmf1.getNum();
        int numVal2 = pmf2.getNum();
        assertEquals(numVal1, numVal2, 0.0);
        for (int i = 0; i < numVal1; i++) {
            assertEquals(pmf1.getX(i), pmf2.getX(i), tolerance);
            assertEquals(pmf1.getY(i), pmf2.getY(i), tolerance);
        }
    }
}
