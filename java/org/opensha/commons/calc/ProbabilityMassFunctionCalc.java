package org.opensha.commons.calc;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.ListIterator;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;

/**
 * This class provide methods for calculating a probability mass function (PMF)
 * from a probability of exceedance function (POE). The class is declared final
 * so that it can be made inline and therefore be faster when executing. This
 * can be important because this class can be called many times when calculating
 * PMFs for many hazard curves.
 * 
 * @author damianomonelli
 * 
 */

public final class ProbabilityMassFunctionCalc {
    /**
     * Return the appropriate type of PMF, based on the type of the input POE
     * (even or arbitrarily discretized).
     */
    public static DiscretizedFunc getPMF(DiscretizedFunc poe) {
        if (poe instanceof EvenlyDiscretizedFunc) {
            return getPMF((EvenlyDiscretizedFunc) poe);
        }
        if (poe instanceof ArbitrarilyDiscretizedFunc) {
            return getPMF((ArbitrarilyDiscretizedFunc) poe);
        }
        throw new IllegalArgumentException(
                "Poe must be either evenly or arbitrarily discretized");
    }

    /**
     * This method compute a PMF from a POE function assuming both to be evenly
     * discretized.
     * 
     * @param poe
     *            EvenlyDiscretizedFunc POE function
     * @return EvenlyDiscretizedFunc PMF. PMF values refer to middle points of
     *         POEs bins.
     * @exception IllegalArgumentException
     *                poe is null, poe contains less than 2 values (NOTE: In
     *                theory the only situation we should avoid is
     *                poe.getNum()==1 (because in this case the formula cannot
     *                be applied). The case poe.getNum()==2 is avoided here
     *                because the resulting PMF would have only one value, and
     *                when an EvenlyDiscretizedFunc is defined with only one
     *                value, than the delta parameter is overwritten in the
     *                constructor and set to 0. This can cause some problems
     *                later on, for instance when the PMF object is asked for
     *                the delta value (for instance when saving the pmf in a XML
     *                file). From the practical point of view this may not be a
     *                big issue because we can expect that POE functions are
     *                usually defined for more than 2 values), poe values are
     *                not in the range [0,1], and poe values are not in
     *                descending order.
     */
    public static EvenlyDiscretizedFunc getPMF(EvenlyDiscretizedFunc poe) {
        validatePOE(poe);

        // Number of values == number of bins' middle points, e.g.
        // the number of values in the POE but decreased by 1
        int numVal = poe.getNum() - 1;

        // bin width (same as POE given that the POE is evenly spaced)
        double binWidth = poe.getDelta();

        // minimum value (the middle point of the first bin)
        double minVal = poe.getX(0) + binWidth / 2;

        EvenlyDiscretizedFunc pmf =
                new EvenlyDiscretizedFunc(minVal, numVal, binWidth);
        for (int i = 0; i < numVal; i++) {
            double val = poe.getY(i) - poe.getY(i + 1);
            pmf.set(i, val);
        }
        return pmf;
    }

    /**
     * This method calculate probability mass function (PMF) values from an
     * arbitrarily discretized probability of exceedence (POE) function.
     * 
     * @param poe
     *            ArbitrarilyDiscretizedFunc containing POE values
     * @return ArbitrarilyDiscretizedFunc containing PMF values. PMF values
     *         refer to the middle points of the POE bins.
     * @exception IllegalArgumentException
     *                poe is null, poe contains less than 2 values (NOTE: In
     *                theory the only situation we should avoid is
     *                poe.getNum()==1 (because in this case the formula cannot
     *                be applied). The case poe.getNum()==2 is avoided here
     *                because the resulting PMF would have only one value, and
     *                when an EvenlyDiscretizedFunc is defined with only one
     *                value, than the delta parameter is overwritten in the
     *                constructor and set to 0. This can cause some problems
     *                later on, for instance when the PMF object is asked for
     *                the delta value (for instance when saving the pmf in a XML
     *                file). From the practical point of view this may not be a
     *                big issue because we can expect that POE functions are
     *                usually defined for more than 2 values), poe values are
     *                not in the range [0,1], and poe values are not in
     *                descending order.
     */
    public static ArbitrarilyDiscretizedFunc getPMF(
            ArbitrarilyDiscretizedFunc poe) {

        validatePOE(poe);

        ArbitrarilyDiscretizedFunc pmf = new ArbitrarilyDiscretizedFunc();
        for (int i = 0; i < poe.getNum() - 1; i++) {
            double x1 = poe.getX(i);
            double x2 = poe.getX(i + 1);
            double xMean = (x1 + x2) / 2;
            double val = poe.getY(i) - poe.getY(i + 1);
            pmf.set(xMean, val);
        }
        return pmf;
    }

    /**
     * Sanity check the incoming POE object for valid PMF output
     * 
     * @param poe
     * @return Boolean
     */
    private static Boolean validatePOE(DiscretizedFuncAPI poe) {

        if (poe == null) {
            throw new IllegalArgumentException("POE function cannot be null");
        }

        if (poe.getNum() <= 2) {
            throw new IllegalArgumentException(
                    "POE function must contain >2 values");
        }

        if (poeValuesAreBetween0and1(poe) == false) {
            throw new IllegalArgumentException(
                    "POE function values must be (0 <= values <= 1)");
        }

        if (poeValuesAreDescending(poe) == false) {
            throw new IllegalArgumentException(
                    "POE function values must be in descending order");
        }
        return true;
    }

    /**
     * This method checks if POE values are in descending order
     * 
     * @param poe
     * @return Boolean
     */
    private static Boolean poeValuesAreDescending(DiscretizedFuncAPI poe) {
        for (int i = 0; i < poe.getNum() - 1; i++) {
            if (poe.getY(i + 1) > poe.getY(i))
                return false;
        }
        return true;
    }

    /**
     * This method checks that POE values are between 0 and 1
     * 
     * @param poe
     * @return Boolean
     */
    private static Boolean poeValuesAreBetween0and1(DiscretizedFuncAPI poe) {
        ListIterator<Double> valIter = poe.getYValuesIterator();
        while (valIter.hasNext()) {
            double val = valIter.next();
            if (val < 0 || val > 1)
                return false;
        }
        return true;
    }
}
