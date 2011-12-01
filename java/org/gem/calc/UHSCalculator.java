package org.gem.calc;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.util.TectonicRegionType;
import static org.gem.Utils.digitize;
import static org.gem.calc.CalcUtils.getGMV;
import static org.gem.calc.CalcUtils.isSorted;
import static org.gem.calc.CalcUtils.notNull;
import static org.gem.calc.CalcUtils.lenGE;
import static org.gem.calc.CalcUtils.assertPoissonian;

import static org.apache.commons.collections.CollectionUtils.forAllDo;

public class UHSCalculator
{

    private Double[] periods;
    private Double[] poes;
    private Double[] imls;
    private EqkRupForecastAPI erf;
    private Map<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> imrMap;
    private double maxDistance;
    private Map<Double, DiscretizedFuncAPI> hazCurveMap;

    /**
     * @param periods
     *            SA (Spectral Acceleration) periods which represent the x-axis
     *            values of a UHS.
     * @param poes
     *            Probability of Exceedance levels. One UHS will be computed per
     *            PoE value.
     * @param imls
     *            List of Intensity Measure Level values (x-axis of hazard
     *            curves and y-axis of UHS), with natrual log (Math.log) applied
     *            to each value.
     * @param erf
     *            Earthquake Rupture Forecast
     * @param imrMap
     *            Map of GMPEs, keyed by TectonicRegionType
     * @param maxDistance
     *            Maximum distance (in km) from the site of interest for a
     *            source to be considered in the calculation. (This corresponds
     *            to the MAXIMUM_DISTANCE job config param.)
     */
    public UHSCalculator(
            Double[] periods,
            Double[] poes,
            Double[] imls,
            EqkRupForecastAPI erf,
            Map<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> imrMap,
            double maxDistance)
    {
        this.periods = periods;
        this.poes = poes;
        this.imls = imls;
        this.erf = erf;
        this.imrMap = imrMap;
        this.maxDistance = maxDistance;

        validateInput();

        hazCurveMap = new HashMap<Double, DiscretizedFuncAPI>();
        for (double period : this.periods)
        {
            hazCurveMap.put(period, initHazCurve(this.imls));
        }
    }

    private void validateInput()
    {
        assertPoissonian(this.erf);
        notNull.execute(this.periods);
        forAllDo(Arrays.asList(this.periods), notNull);
        isSorted.execute(this.periods);
        lenGE(1).execute(this.periods);

        notNull.execute(this.imls);
        forAllDo(Arrays.asList(this.imls), notNull);
        isSorted.execute(this.imls);
        lenGE(1).execute(this.poes);

        notNull.execute(this.poes);
        forAllDo(Arrays.asList(this.poes), notNull);
        lenGE(2).execute(this.imls);
    }

    /**
     * Compute a list of UHS results (1 per PoE). Each result is 1D array
     * representing the y-axis values of the UHS curve; x-axis values of UHS
     * curves are the specified SA period values.
     * 
     * This method computes Hazard Curves to produce the UHS results. The following
     * equation is used to compute the Hazard Curves:
     * 
     * Hazard Curve Equation for Poissonian Sources (no official title)
     * Published in Seismological Research Letters, Vol. 74
     * Title: OpenSHA - A Developing Community-Modeling Environment for Seismic Hazard Analysis
     * Author: Field et al. (2003)
     * 
     * @param site
     *            The site of interest for this computation.
     * @return list of UHS results (1 per PoE)
     */
    public List<Double[]> computeUHS(Site site)
    {
        // Final results of the calculation
        List<Double[]> uhsResults = new ArrayList<Double[]>();
        for (int is = 0; is < erf.getNumSources(); is++)
        {
            ProbEqkSource source = erf.getSource(is);

            // Ignore sources located > maxDistance
            // from the site of the interest:
            if (source.getMinDistance(site) > maxDistance)
            {
                continue;
            }

            TectonicRegionType trt = source.getTectonicRegionType();
            ScalarIntensityMeasureRelationshipAPI imr = imrMap.get(trt);
            if (imr == null)
            {
                throw new RuntimeException(
                        "No GMPE defined for the tectonic region type" + "'"
                                + trt.toString() + "'.");

            }
            imr.setUserMaxDistance(maxDistance);
            imr.setSite(site);

            PeriodParam periodParam = ((SA_Param) imr
                    .getParameter(SA_Param.NAME)).getPeriodParam();
            List<Double> imrPeriodList = periodParam.getAllowedDoubles();

            for (int ir = 0; ir < source.getNumRuptures(); ir++)
            {
                ProbEqkRupture rupture = source.getRupture(ir);
                double rupProb = rupture.getProbability();

                /*
                 * First make sure the probability isn't 1.0 (or too close);
                 * otherwise rates are infinite and all IMLs will be exceeded
                 * (because of ergodic assumption). This can happen if the
                 * number of expected events (over the timespan) exceeds ~37,
                 * because at this point 1.0-Math.exp(-num) = 1.0 by numerical
                 * precision (and thus, an infinite number of events). The
                 * number 30 used in the check below provides a safe margin.
                 */
                if (Math.log(1.0 - rupProb) < -30.0)
                    throw new RuntimeException(
                            "The probability for this ProbEqkRupture ("
                                    + rupProb
                                    + ") is too high for a Possion source (~infinite number of events)");
                imr.setEqkRupture(rupture);

                for (double period : periods)
                {
                    DiscretizedFuncAPI hazardCurve = hazCurveMap.get(period);

                    if (period == 0.0)
                    {
                        updateHazCurveForPGA(hazardCurve, imr, rupProb);
                    }
                    else if (periodParam.isAllowed(period)) 
                    {
                        updateHazCurveForSupportedSAPeriod(hazardCurve, imr, rupProb, period);
                    }
                    else if (period > 0.0 && period < imrPeriodList.get(0))
                    {
                        // between PGA and the first SA
                        updateHazCurveBetweenPGAandSA(hazardCurve, imr, imrPeriodList, rupProb, period);
                    }
                    else
                    {
                        updateHazCurveForInterpolatedPeriod(hazardCurve, imr, imrPeriodList, rupProb, period);
                    }
                }
            }
        }

        // This is the final step in the equation we're using to compute
        // the hazard curves.
        for (DiscretizedFuncAPI hazCurve : hazCurveMap.values())
        {
            for (int i = 0; i < hazCurve.getNum(); i++)
            {
                hazCurve.set(i, 1 - hazCurve.getY(i));
            }
        }

        for (double poe : poes)
        {
            Double [] uhs = new Double[periods.length];
            for (int i = 0; i < periods.length; i++)
            {
                DiscretizedFuncAPI hazCurve = hazCurveMap.get(periods[i]);
                uhs[i] = Math.exp(getGMV(hazCurve, poe));
            }
            uhsResults.add(uhs);
        }

        return uhsResults;
    }

    public static DiscretizedFuncAPI initHazCurve(
            Double[] imls)
    {
        DiscretizedFuncAPI hazCurve = new ArbitrarilyDiscretizedFunc();
        for (Double iml : imls)
        {
            hazCurve.set(iml, 1.0);
        }
        return hazCurve;
    }

    /**
     * Interpolate a PoE value given a pair of periods and a pair
     * of PoEs.
     * 
     * This is a simple linear interpolation between a pair of x values (periods)
     * and a pair of y values (poes).
     * @param period1
     * @param period2
     * @param poe1
     * @param poe2
     * @param period The value for which we want to interpolate a PoE value
     */
    public static double interpolatePoe(
            double period1,
            double period2,
            double poe1,
            double poe2,
            double period) {
        // interpolate
        // compute interpolation coefficients. Follow
        // equations
        // 3.3.1 and 3.3.2, pag. 107 in "Numerical Recipes
        // in
        // Fortran 77"
        double a, b;

        a = (period2 - period) / (period2 - period1);
        b = 1 - a;
        return a * poe1 + b * poe2;
    }

    private static void updateHazCurve(
            DiscretizedFuncAPI hazCurve,
            double rupProb,
            double iml,
            double poe)
    {
        double hcValue = hazCurve.getY(iml);
        hazCurve.set(iml, hcValue * Math.pow(1 - rupProb, poe));
    }

    private void updateHazCurveForPGA(
            DiscretizedFuncAPI hazCurve,
            ScalarIntensityMeasureRelationshipAPI imr,
            double rupProb)
    {
        imr.setIntensityMeasure(PGA_Param.NAME);

        for (double iml : imls)
        {
            imr.setIntensityMeasureLevel(iml);
            updateHazCurve(hazCurve, rupProb, iml, imr.getExceedProbability());
        }

    }

    private void updateHazCurveForSupportedSAPeriod(
            DiscretizedFuncAPI hazCurve,
            ScalarIntensityMeasureRelationshipAPI imr,
            double rupProb,
            double period)
    {
        imr.setIntensityMeasure(SA_Param.NAME);
        imr.getParameter(PeriodParam.NAME).setValue(period);

        for (double iml : imls)
        {
            imr.setIntensityMeasureLevel(iml);
            updateHazCurve(hazCurve, rupProb, iml, imr.getExceedProbability());
        }
    }

    private void updateHazCurveBetweenPGAandSA(
            DiscretizedFuncAPI hazCurve,
            ScalarIntensityMeasureRelationshipAPI imr,
            List<Double> periodList,
            double rupProb,
            double period)
    {
        double periodPGA = 0.0;  // PGA
        double periodSA = periodList.get(0);  // First SA period
        
        for (double iml : imls)
        {
            double poePGA, poeSA, poe;
            imr.setIntensityMeasureLevel(iml);
            
            imr.setIntensityMeasure(PGA_Param.NAME);
            poePGA = imr.getExceedProbability();
            
            imr.setIntensityMeasure(SA_Param.NAME);
            imr.getParameter(PeriodParam.NAME).setValue(periodSA);
            poeSA = imr.getExceedProbability();

            poe = interpolatePoe(periodPGA, periodSA, poePGA, poeSA, period);
            updateHazCurve(hazCurve, rupProb, iml, poe);
        }
    }

    private void updateHazCurveForInterpolatedPeriod(
            DiscretizedFuncAPI hazCurve,
            ScalarIntensityMeasureRelationshipAPI imr,
            List<Double> periodList,
            double rupProb,
            double period)
    {
        int periodBinIndex = digitize(periodList.toArray(new Double[periodList.size()]), period);

        double period1 = periodList.get(periodBinIndex);
        double period2 = periodList.get(periodBinIndex + 1);

        imr.setIntensityMeasure(SA_Param.NAME);

        for (double iml : imls)
        {
            double poe1, poe2, poe;

            imr.setIntensityMeasureLevel(iml);

            imr.getParameter(PeriodParam.NAME).setValue(period1);
            poe1 = imr.getExceedProbability();

            imr.getParameter(PeriodParam.NAME).setValue(period2);
            poe2 = imr.getExceedProbability();

            poe = interpolatePoe(period1, period2, poe1, poe2, period);
            updateHazCurve(hazCurve, rupProb, iml, poe);
        }
    }
}
