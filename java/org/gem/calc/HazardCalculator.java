package org.gem.calc;

import java.rmi.RemoteException;
import java.text.DecimalFormat;
import java.text.DecimalFormatSymbols;
import java.util.HashMap;
import java.util.List;
import java.util.ListIterator;
import java.util.Locale;
import java.util.Map;
import java.util.Random;
import java.util.Set;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.gem.JsonSerializer;
import org.gem.engine.hazard.redis.Cache;
import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.sha.calc.HazardCurveCalculator;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.util.TectonicRegionType;

import com.google.gson.Gson;

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
        HazardCurveCalculator curveCalculator = null;
        try {
            curveCalculator = new HazardCurveCalculator();
            curveCalculator.setMaxSourceDistance(integrationDistance);
            int site_num = 0;
            for (Site site : siteList) {
                site_num += 1;
                DiscretizedFuncAPI hazardCurve =
                        new ArbitrarilyDiscretizedFunc();
                for (double val : imlVals)
                    hazardCurve.set(val, 1.0);
                curveCalculator.getHazardCurve(hazardCurve, site, gmpeMap, erf);
                if ((site_num % 100) == 0) {
                    logger.info("Computed hazard curve for site #" + site_num + " of " + siteList.size());
                }
                results.put(site, hazardCurve);
            }
            if ((site_num % 100) != 0) {
                logger.info("Computed hazard curve for site #" + site_num + " of " + siteList.size());
            }
        } catch (RemoteException e) {
            logger.error(e);
            throw new RuntimeException(e);
        }
        return results;
    }

    /**
     * Get the site/hazard curve pairs as a list of JSON Strings.
     *
     * @param siteList
     * @param erf
     * @param gmpeMap
     * @param imlVals
     * @param integrationDistance
     * @return
     */
    public static
            String[]
            getHazardCurvesAsJson(
                    List<Site> siteList,
                    EqkRupForecastAPI erf,
                    Map<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> gmpeMap,
                    List<Double> imlVals, double integrationDistance) {
        Map<Site, DiscretizedFuncAPI> curves =
                getHazardCurves(siteList, erf, gmpeMap, imlVals,
                        integrationDistance);
        List<String> returnCurves =
                JsonSerializer.hazardCurvesToJson(curves, siteList);
        return returnCurves.toArray(new String[returnCurves.size()]);
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
        for (EqkRupture rup : eqkRupList) {
            logger.debug("rupture mag is " + rup.getMag());
            GroundMotionFieldCalculator gmfCalc =
                new GroundMotionFieldCalculator(
                        gmpeMap.get(rup.getTectRegType()),rup,siteList);
            if (correlation == true) {
                groundMotionFields.put(rup, gmfCalc
                        .getCorrelatedGroundMotionField_JB2009(
                        		rn));
            } else {
                groundMotionFields.put(rup, gmfCalc
                        .getUncorrelatedGroundMotionField(rn));
            }
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
            sites.next();
            site_ids[sites.nextIndex() - 1] =
                    Integer.toString(sites.nextIndex() - 1);
        }
        String[] rupture_ids = new String[gmfs.keySet().size()];
        for (int x = 0; x < gmfs.keySet().size(); x++) {
            rupture_ids[x] = Integer.toString(x);
        }
        gmfToMemcache(cache, key, gmf_id, rupture_ids, site_ids, gmfs);
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

    /**
     * From a ground motion field this method serializes only the data that is
     * needed to a json string.<br>
     * The suggested format for a jsonized GMF is<br>
     * {'gmf_id' : { 'eqkrupture_id' : { 'site_id' : {'lat' : lat_val, 'lon' :
     * lon_val, 'mag' : double_val}}, { 'site_id' : { ...}} , {...} }}
     *
     * From identifiers.py, these are what the expected keys look like (this
     * makes no expectation of the values), the keys are after the colon.
     *
     * sites: job_id!block_id!!sites gmf: job_id!block_id!!gmf gmf:
     * job_id!block_id!site!gmf
     *
     * @return
     */
    protected static String gmfToJson(String gmfId, String[] eqkRuptureIds,
            String[] siteIds,
            Map<EqkRupture, Map<Site, Double>> groundMotionFields) {
        StringBuilder result = new StringBuilder();
        Gson gson = new Gson();
        result.append("{");
        result.append(gson.toJson(gmfId));
        result.append(":{");
        // TODO:
        // The EqkRupture memcache keys must be known here.
        // For now behave, as if the map object is ordered.
        //
        Set<EqkRupture> groundMotionFieldsKeys = groundMotionFields.keySet();
        int indexEqkRupture = 0;
        for (EqkRupture eqkRupture : groundMotionFieldsKeys) {
            if (indexEqkRupture > 0) {
                result.append(",");
            }
            result.append(gson.toJson(eqkRuptureIds[indexEqkRupture++]));
            // start the eqk json object
            result.append(":");
            Map<Site, Double> groundMotionField =
                    groundMotionFields.get(eqkRupture);
            // TODO:
            // The sites' memcache keys must be known here.
            // For now behave, as if the map object is ordered.
            Set<Site> groundMotionFieldKeys = groundMotionField.keySet();
            int indexSite = 0;
            StringBuilder siteListString = new StringBuilder();
            siteListString.append("{");
            // must instantiate the DecimalFormat object with a locale
            // that uses the dot as decimal separator (such as the US locale)
            DecimalFormatSymbols dfs = new DecimalFormatSymbols(Locale.US);
            DecimalFormat df = new DecimalFormat("0.########E0", dfs);
            for (Site s : groundMotionFieldKeys) {
                if (indexSite > 0) {
                    siteListString.append(",");
                }
                StringBuilder siteString = new StringBuilder();
                siteString.append(gson.toJson(siteIds[indexSite++]));
                // start the json site's value object
                siteString.append(":{");
                siteString.append(gson.toJson("lat") + ":"
                        + df.format(s.getLocation().getLatitude()));
                siteString.append(",");
                siteString.append(gson.toJson("lon") + ":"
                        + df.format(s.getLocation().getLongitude()));
                siteString.append(",");
                siteString.append(gson.toJson("mag") + ":"
                        + df.format(groundMotionField.get(s)));
                // close the the json site's value object and the site json
                // object
                siteString.append("}");
                siteListString.append(siteString);
            } // for
            siteListString.append("}");
            // close the eqk json object
            result.append(siteListString);
        } // for
        result.append("}}");
        return result.toString();
    }

    /**
     * Saves a ground motion map to a Cache object.<br>
     * <br>
     * 1) Converts the <code>groundMotionFields</code> into json format.<br>
     * E.g.<br>
     * {"gmf_id":<br>
     * {"eqkRupture_id_0":<br>
     * {"site_id_0":{"lat":35.0,"lon":37.6,"mag":-4.7}},
     * {"site_id_1":{"lat":37.5,"lon":35.6,"mag":-2.8}},...
     *
     * 2) Saves the json string to memCache.
     *
     * @param memCacheKey
     * @param gmfId
     *            The "json key" for the GMF (ground motion field)
     * @param eqkRuptureIds
     *            The "json key" for the the ruptures contained in
     *            groundMotionFields
     * @param siteIds
     *            The "json key" for all the sites contained in
     *            groundMotionFields
     * @param groundMotionFields
     *            The GMF to be saved to memcache
     * @param cache
     *            The memcache
     */
    protected static void gmfToMemcache(Cache cache, String memCacheKey,
            String gmfId, String[] eqkRuptureIds, String[] siteIds,
            Map<EqkRupture, Map<Site, Double>> groundMotionFields) {
        String json =
                gmfToJson(gmfId, eqkRuptureIds, siteIds, groundMotionFields);
        logger.debug("Saving GMF to " + memCacheKey);
        cache.set(memCacheKey, json);
    }
}
