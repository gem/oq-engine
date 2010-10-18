package org.opensha.sha.calc;

import java.rmi.RemoteException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.gem.GEM1.scratch.HazardCurveCalculator;
import org.opensha.sha.calc.groundMotionField.GroundMotionFieldCalculator;
import org.opensha.sha.calc.stochasticEventSet.StochasticEventSetGenerator;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.util.TectonicRegionType;

/**
 * This class provides methods for hazard calculations.
 * 
 * @author damianomonelli
 * 
 */

public class HazardCalculator {

    /**
     * Calculate hazard curves for a set of sites from an earthquake rupture
     * forecast using the classical PSHA approach
     * 
     * @param siteList
     *            : list of sites ({@link Site}) where to compute hazard curves
     * @param erf
     *            : earthquake rupture forecast {@link EqkRupForecastAPI}
     * @param gmpeMap
     *            : map associating tectonic region types (
     *            {@link TectonicRegionType}) with attenuation relationships (
     *            {@link ScalarIntensityMeasureRelationshipAPI})
     * @param imlVals
     *            : intensity measure levels (double[]) for which calculating
     *            probabilities of exceedence
     * @param integrationDistance
     *            : maximum distance used for integration
     * @return
     */
    public static
            Map<Site, DiscretizedFuncAPI>
            getHazardCurves(
                    List<Site> siteList,
                    EqkRupForecastAPI erf,
                    Map<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> gmpeMap,
                    List<Double> imlVals, double integrationDistance) {
        if (siteList == null) {
            throw new IllegalArgumentException("List of sites cannot be null");
        }
        if (siteList.isEmpty()) {
            throw new IllegalArgumentException(
                    "List of sites must contain at least one site");
        }
        if (erf == null) {
            throw new IllegalArgumentException(
                    "Earthquake rupture forecast cannot be null");
        }
        if (gmpeMap == null) {
            throw new IllegalArgumentException("Gmpe map cannot be null");
        }
        if (gmpeMap.isEmpty()) {
            throw new IllegalArgumentException(
                    "Gmpe map must contain at least one gmpe");
        }
        if (imlVals == null) {
            throw new IllegalArgumentException(
                    "Array of intensity measure levels cannot be null");
        }
        if (imlVals.isEmpty()) {
            throw new IllegalArgumentException(
                    "Array of intensity measure levels must"
                            + " contain at least one value");
        }
        Map<Site, DiscretizedFuncAPI> results =
                new HashMap<Site, DiscretizedFuncAPI>();
        DiscretizedFuncAPI hazardCurve = new ArbitrarilyDiscretizedFunc();
        for (double val : imlVals)
            hazardCurve.set(val, 1.0);
        HazardCurveCalculator curveCalculator = null;
        try {
            curveCalculator = new HazardCurveCalculator();
            curveCalculator.setMaxSourceDistance(integrationDistance);
        } catch (RemoteException e) {
            e.printStackTrace();
        }
        for (Site site : siteList) {
            try {
                curveCalculator.getHazardCurve(hazardCurve, site, gmpeMap, erf);
                results.put(site, hazardCurve);
            } catch (RemoteException e) {
                e.printStackTrace();
            }
        }
        return results;
    }

    /**
     * Calculate uncorrelated ground motion fields from a stochastic event set
     * generated through random sampling of an earthquake rupture forecast
     * 
     * @param siteList
     *            : list of sites ({@link Site}) where to compute ground motion
     *            values
     * @param erf
     *            : earthquake rupture forecast {@link EqkRupForecastAPI}
     * @param gmpeMap
     *            : map associating tectonic region types (
     *            {@link TectonicRegionType}) with attenuation relationships (
     *            {@link ScalarIntensityMeasureRelationshipAPI})
     * @param rn
     *            : random ({@link Random}) number generator
     * @return
     */
    public static
            Map<EqkRupture, Map<Site, Double>>
            getGroundMotionFields(
                    List<Site> siteList,
                    EqkRupForecastAPI erf,
                    Map<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> gmpeMap,
                    Random rn) {
        if (siteList == null) {
            throw new IllegalArgumentException("List of sites cannot be null");
        }
        if (siteList.isEmpty()) {
            throw new IllegalArgumentException(
                    "List of sites must contain at least one site");
        }
        if (erf == null) {
            throw new IllegalArgumentException(
                    "Earthquake rupture forecast cannot be null");
        }
        if (gmpeMap == null) {
            throw new IllegalArgumentException("Gmpe map cannot be null");
        }
        if (gmpeMap.isEmpty()) {
            throw new IllegalArgumentException(
                    "Gmpe map must contain at least one gmpe");
        }
        if (rn == null) {
            throw new IllegalArgumentException(
                    "Random number generator cannot be null");
        }
        Map<EqkRupture, Map<Site, Double>> groundMotionFields =
                new HashMap<EqkRupture, Map<Site, Double>>();
        List<EqkRupture> eqkRupList =
                StochasticEventSetGenerator
                        .getStochasticEventSetFromPoissonianERF(erf, rn);
        for (EqkRupture rup : eqkRupList)
            groundMotionFields.put(rup, GroundMotionFieldCalculator
                    .getStochasticGroundMotionField(
                            gmpeMap.get(rup.getTectRegType()), rup, siteList,
                            rn));
        return groundMotionFields;
    }
}
