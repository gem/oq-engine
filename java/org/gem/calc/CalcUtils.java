package org.gem.calc;

import org.opensha.commons.data.function.DiscretizedFuncAPI;

public class CalcUtils
{
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
}
