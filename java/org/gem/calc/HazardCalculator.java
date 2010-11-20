package org.gem.calc;

import java.rmi.RemoteException;
import java.util.HashMap;
import java.util.List;
import java.util.ListIterator;
import java.util.Map;
import java.util.Random;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.gem.engine.CommandLineCalculator;
import org.gem.engine.hazard.memcached.Cache;
import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.sha.calc.HazardCurveCalculator;
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

    private static Log logger = LogFactory.getLog(HazardCalculator.class);

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
        validateInput(siteList, erf, gmpeMap);
        if (imlVals == null) {
            String msg = "Array of intensity measure levels cannot be null";
            logger.error(msg);
            throw new IllegalArgumentException(msg);
        }
        if (imlVals.isEmpty()) {
            String msg =
                    "Array of intensity measure levels must"
                            + " contain at least one value";
            logger.error(msg);
            throw new IllegalArgumentException(msg);
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
            for (Site site : siteList) {
                curveCalculator.getHazardCurve(hazardCurve, site, gmpeMap, erf);
                results.put(site, hazardCurve);
            }
        } catch (RemoteException e) {
            e.printStackTrace();
        }
        return results;
    }

    /**
     * Calculate ground motion fields (correlated or uncorrelated) from a
     * stochastic event set generated through random sampling of an earthquake
     * rupture forecast
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
     * @param : correlation flag, if true compute correlated ground motion
     *        fields using Jayaram and Baker (2009) correlation model
     *        considering no Vs30 clustering; if false compute uncorrelated
     *        ground motion fields
     * @return
     */
    public static
            Map<EqkRupture, Map<Site, Double>>
            getGroundMotionFields(
                    List<Site> siteList,
                    EqkRupForecastAPI erf,
                    Map<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> gmpeMap,
                    Random rn, boolean correlation) {
        validateInput(siteList, erf, gmpeMap);
        if (rn == null) {
            String msg = "Random number generator cannot be null";
            logger.error(msg);
            throw new IllegalArgumentException(msg);
        }
        Map<EqkRupture, Map<Site, Double>> groundMotionFields =
                new HashMap<EqkRupture, Map<Site, Double>>();
        List<EqkRupture> eqkRupList =
                StochasticEventSetGenerator
                        .getStochasticEventSetFromPoissonianERF(erf, rn);
        if (correlation == true) {
            Boolean inter_event = true;
            Boolean Vs30Cluster = false;
            for (EqkRupture rup : eqkRupList)
                groundMotionFields.put(rup, GroundMotionFieldCalculator
                        .getStochasticGroundMotionField_JB2009(
                                gmpeMap.get(rup.getTectRegType()), rup,
                                siteList, rn, inter_event, Vs30Cluster));
        } else {
            for (EqkRupture rup : eqkRupList)
                groundMotionFields.put(rup, GroundMotionFieldCalculator
                        .getStochasticGroundMotionField(
                                gmpeMap.get(rup.getTectRegType()), rup,
                                siteList, rn));
        }
        return groundMotionFields;
    }

    public static
            void
            generateAndSaveGMFs(
                    Cache cache,
                    String key,
                    String gmf_id,
                    List<Site> siteList,
                    EqkRupForecastAPI erf,
                    Map<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> gmpeMap,
                    Random rn, boolean correlation) {
        Map<EqkRupture, Map<Site, Double>> gmfs =
                getGroundMotionFields(siteList, erf, gmpeMap, rn, correlation);

        String[] site_ids = new String[siteList.size()];
        ListIterator<Site> sites = siteList.listIterator();
        while (sites.hasNext()) {
            Site this_site = sites.next();
            site_ids[sites.nextIndex() - 1] =
                    Integer.toString(sites.nextIndex() - 1);
        }
        String[] rupture_ids = new String[gmfs.keySet().size()];
        for (int x = 0; x < gmfs.keySet().size(); x++) {
            rupture_ids[x] = Integer.toString(x);
        }
        CommandLineCalculator.gmfToMemcache(cache, key, gmf_id, rupture_ids,
                site_ids, gmfs);
    }

    public static
            Boolean
            validateInput(
                    List<Site> siteList,
                    EqkRupForecastAPI erf,
                    Map<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> gmpeMap) {
        if (siteList == null) {
            String msg = "List of sites cannot be null";
            logger.error(msg);
            throw new IllegalArgumentException(msg);
        }
        if (siteList.isEmpty()) {
            String msg = "List of sites must contain at least one site";
            logger.error(msg);
            throw new IllegalArgumentException(msg);
        }
        if (erf == null) {
            String msg = "Earthquake rupture forecast cannot be null";
            logger.error(msg);
            throw new IllegalArgumentException(msg);
        }
        if (gmpeMap == null) {
            String msg = "Gmpe map cannot be null";
            logger.error(msg);
            throw new IllegalArgumentException(msg);
        }
        if (gmpeMap.isEmpty()) {
            String msg = "Gmpe map must contain at least one gmpe";
            logger.error(msg);
            throw new IllegalArgumentException(msg);
        }
        return true;
    }
}
