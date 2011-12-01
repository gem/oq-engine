package org.gem.calc;

import java.util.Arrays;

import org.apache.commons.collections.Closure;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.earthquake.ProbEqkSource;

public class CalcUtils
{
    /**
     * Throw this if an input validation check fails. (Input to a constructor,
     * method, etc.)
     */
    public static class InputValidationException extends RuntimeException
    {
        public InputValidationException(String msg)
        {
            super(msg);
        }
    }

    /**
     * Extract a GMV (Ground Motion Value) for a given curve and PoE
     * (Probability of Exceedance) value.
     *
     * IML (Intensity Measure Level) values make up the X-axis of the curve.
     * IMLs are arranged in ascending order. The lower the IML value, the
     * higher the PoE value (Y value) on the curve. Thus, it is assumed that
     * hazard curves will always have a negative slope.
     *
     * If the input poe value is > the max Y value in the curve, extrapolate
     * and return the X value corresponding to the max Y value (the first Y
     * value).
     * If the input poe value is < the min Y value in the curve, extrapolate
     * and return the X value corresponding to the min Y value (the last Y
     * value).
     * Otherwise, interpolate an X value in the curve given the input PoE.
     * @param hazardCurve
     * @param poe Probability of Exceedance value
     * @return GMV corresponding to the input poe
     */
    public static Double getGMV(DiscretizedFuncAPI hazardCurve, double poe)
    {
        if (poe > hazardCurve.getY(0))
        {
            return hazardCurve.getX(0);
        }
        else if (poe < hazardCurve.getY(hazardCurve.getNum() - 1))
        {
            return hazardCurve.getX(hazardCurve.getNum() - 1);
        }
        else
        {
            return hazardCurve.getFirstInterpolatedX(poe);
        }
    }

    /**
     * Useful for doing a single-line check if a value is null.
     * This is nice for validating input.
     */
    public static final Closure notNull = new Closure()
    {

        public void execute(Object o)
        {
            if (o == null)
            {
                throw new InputValidationException("Unexpected null value");
            }
        }
    };

    /**
     * Useful for checking if an array is sorted. If the array is not sorted
     * in ascending order, an InputValidationException is thrown.
     */
    public static final Closure isSorted = new Closure()
    {

        public void execute(Object o) {
            if (o instanceof Object[])
            {
                Object[] oArray = (Object[]) o;
                Object[] sorted = Arrays.copyOf(oArray, oArray.length);
                Arrays.sort(sorted);
                if (!Arrays.equals(sorted, oArray))
                {
                    throw new InputValidationException("Array must be arranged in ascending order.");
                }
            }
        }
    };

    /**
     * Useful for checking that an array contains at least `len` elements.
     * @param len
     * @return A Closure that throws an InputValidationException if the minimum
     * length of an input array is not met.
     */
    public static final Closure lenGE(final int len)
    {
        return new Closure ()
        {
            public void execute(Object o)
            {
                if (o instanceof Object[])
                {
                    Object[] oArray = (Object[]) o;
                    if (oArray.length < len)
                    {
                        throw new InputValidationException("Array must have a length >= " + len);
                    }
                }
            }
            
        };
    }

    /**
     * Given an Earthquake Rupture Forecast, check each Source verify that it is
     * a poissonian source. If any non-poissonian sources are detected in the
     * ERF, throw a RuntimeException. (Currently, we do not support
     * non-poissonian sources.)
     * @param erf
     */
    public static void assertPoissonian(EqkRupForecastAPI erf)
    {
        for (int i = 0; i < erf.getSourceList().size(); i++)
        {
            ProbEqkSource source = erf.getSource(i);
            if (!source.isPoissonianSource()) {
                throw new RuntimeException(
                        "Sources must be Poissonian. (Non-Poissonian source are not currently supported.)");
            }
        }
    }
}
