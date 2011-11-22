package org.gem.calc;

import java.util.ArrayList;
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
     *            curves and y-axis of UHS).
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

        hazCurveMap = new HashMap<Double, DiscretizedFuncAPI>();
        for (double period : this.periods)
        {
            hazCurveMap.put(period, initHazCurve(this.imls));
        }
    }
    /**
     * Compute a list of UHS results (1 per PoE). Each result is 1D array
     * representing the y-axis values of the UHS curve; x-axis values of UHS
     * curves are the specified SA period values.
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
                        updateHazCurveBetweenPGAandSA(hazardCurve, imr, rupProb, period);
                    }
                    else
                    {
                        updateHazCurveForInterpolatedPeriod(hazardCurve, imr, rupProb, period);
                    }
                }
            }
        }
        

        // TODO: finalize hazard curve calculations
        // TODO: for each period, extract UHS from hazard curves

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
            double rupProb,
            double period)
    {
        double period1 = 0.0;
        double period2 = -1;
        
        for (double iml : imls)
        {
            imr.setIntensityMeasureLevel(iml);
            
            imr.setIntensityMeasure(PGA_Param.NAME);
            double poePGA = imr.getExceedProbability();
            
            imr.setIntensityMeasure(SA_Param.NAME);
            imr.getParameter(PeriodParam.NAME).setValue(period2);
            double poeSA = imr.getExceedProbability();
        }
    }

    private void updateHazCurveForInterpolatedPeriod(
            DiscretizedFuncAPI hazCurve,
            ScalarIntensityMeasureRelationshipAPI imr,
            double rupProb,
            double period)
    {
        
    }
}
