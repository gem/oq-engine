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
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.util.TectonicRegionType;


public class UHSCalculator {

/**
 * Compute a list of UHS results (1 per PoE). Each result is 1D array representing
 * the y-axis values of the UHS curve; x-axis values of UHS curves are the specified
 * SA period values.
 * 
 * @param periods SA (Spectral Acceleration) periods which represent the x-axis
 * values of a UHS.
 * @param poes Probability of Exceedance levels. One UHS will be computed per PoE
 * value.
 * @param imlVals List of Intensity Measure Level values (x-axis of hazard
 * curves and y-axis of UHS).
 * @param site The site of interest for this computation.
 * @param erf Earthquake Rupture Forecast
 * @param imrMap Map of GMPEs, keyed by TectonicRegionType
 * @param maxDistance Maximum distance (in km) from the site of interest 
 * for a source to be considered in the calculation. (This corresponds to the
 * MAXIMUM_DISTANCE job config param.)
 * @return list of UHS results (1 per PoE)
 */
    public static List<Double[]> computeUHS(
            Double[] periods,
            Double[] poes,
            Double[] imlVals,
            Site site,
            EqkRupForecastAPI erf,
            Map<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> imrMap,
            double maxDistance) {

        // Final results of the calculation
        List<Double[]> uhsResults = new ArrayList<Double[]>();

        // initialize the Hazard Curve map, 1 per 'period'
        Map<Double, DiscretizedFuncAPI> hazCurveMap = initHazCurves(periods, imlVals);

        for (int is = 0; is < erf.getNumSources(); is++) {
            ProbEqkSource source = erf.getSource(is);

            // Ignore sources located > maxDistance
            // from the site of the interest:
            if (source.getMinDistance(site) > maxDistance) {
                continue;
            }

            TectonicRegionType trt = source.getTectonicRegionType();
            ScalarIntensityMeasureRelationshipAPI imr = imrMap.get(trt);
            if (imr == null) {
                // TODO: throw a runtime error
            }
            imr.setUserMaxDistance(maxDistance);
            imr.setSite(site);
            
            PeriodParam periodParam = ((SA_Param)imr.getParameter(SA_Param.NAME)).getPeriodParam();
            List<Double> periodList = periodParam.getAllowedDoubles();

            for (int ir = 0; ir < source.getNumRuptures(); ir++) {
                ProbEqkRupture rupture = source.getRupture(ir);
                double rupProb = rupture.getProbability();
                
                // TODO: check if the rupProb is in a reasonable range
                imr.setEqkRupture(rupture);
                
                for (double period : periods) {
                    // TODO:
                }
            }
        }
        
        // TODO: finalize hazard curve calculations
        // TODO: for each period, extract UHS from hazard curves
        
        return null;
    }

    /**
     * Initialize a map of hazard curve objects, 1 for each period.
     */
    public static  Map<Double, DiscretizedFuncAPI> initHazCurves(Double[] periods, Double[] imls) {
        Map<Double, DiscretizedFuncAPI> hazCurveMap = new HashMap<Double, DiscretizedFuncAPI>();
        
        for (Double p : periods) {
            DiscretizedFuncAPI hazCurve = new ArbitrarilyDiscretizedFunc();
            // initialize the curve with number of points == the number of IMLs
            for (Double iml : imls) {
                hazCurve.set(iml, 1.0);
            }
            hazCurveMap.put(p, hazCurve);
        }
        return hazCurveMap;
    }
}
