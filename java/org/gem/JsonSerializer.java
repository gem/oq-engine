package org.gem;

import java.lang.reflect.Type;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Properties;

import org.gem.engine.hazard.redis.Cache;
import org.opensha.commons.data.DataPoint2D;
import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.util.TectonicRegionType;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.reflect.TypeToken;

public class JsonSerializer {

    /* Hazard Curve to JSON stuff */

    /**
     * Type definition for converting a hazard curve to JSON.
     */
    private static final Type CURVE_TYPE =
            new TypeToken<List<Double>>() {
            }.getType();

    /**
     * Type definition for converting a site to JSON.
     */
    private static final Type SITE_TYPE = new TypeToken<Map<String, String>>() {
    }.getType();

    private static final String SITE_LON = "site_lon";
    private static final String SITE_LAT = "site_lat";
    private static final String X = "x";
    private static final String Y = "y";
    private static final String POES = "poes";

    /* End Hazard Curve to JSON stuff */

    /**
     * Serializes and array list of GEMSourceData
     *
     * @param sourceList
     * @return
     */
    public static String getJsonSourceList(ArrayList<GEMSourceData> sourceList) {
        String json = new Gson().toJson(sourceList);
        return json;
    }

    public static void serializeSourceList(Cache cache, String key,
            ArrayList<GEMSourceData> sources) {
        cache.set(key, getJsonSourceList(sources));
    }

    public static List<GEMSourceData> getSourceListFromCache(Cache cache,
            String key) {
        GsonBuilder gson = new GsonBuilder();
        gson.registerTypeAdapter(GEMSourceData.class,
                new SourceDataDeserializer());
        Type listType = new TypeToken<ArrayList<GEMSourceData>>() {
        }.getType();
        // At least up to gson 1.6 what we get is a LinkedList<GEMSourceData>
        // while GEM1ERF.GEM1ERF is expecting ArrayList<GEMSourceData>.
        List<GEMSourceData> result =
            gson.create().fromJson((String) cache.get(key), listType);
        return new ArrayList<GEMSourceData>(result);
    }

    public static HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> getGmpeMapFromCache(
            Cache cache, String key) {

        GsonBuilder gson = new GsonBuilder();
        gson.registerTypeAdapter(ScalarIntensityMeasureRelationshipAPI.class,
                new ScalarIntensityMeasureRelationshipApiDeserializer());
        gson.registerTypeAdapter(TectonicRegionType.class,
                new TectonicRegionTypeDeserializer());

        Type hashType =
                new TypeToken<HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>>() {
                }.getType();

        return gson.create().fromJson((String) cache.get(key), hashType);
    }

    public static void serializeConfigurationFile(Cache cache, String key,
            Properties configProperties) {
        String json = new Gson().toJson(configProperties, Properties.class);
        cache.set(key, json);
    }

    public static Properties getConfigurationPropertiesFromCache(Cache cache,
            String key) {
        return new Gson().fromJson((String) cache.get(key), Properties.class);
    }

    /**
     * Convert the input Map into a List of JSON Strings.
     *
     * <p>
     * <b>The order in which the results are returned is based on the order of
     * the site list.</b>
     * </p>
     *
     * @param hazCurves
     * @return List of JSON Strings
     */
    public static List<String> hazardCurvesToJson(
            Map<Site, DiscretizedFuncAPI> hazCurves, List<Site> siteList) {
        List<String> result = new ArrayList<String>();
        Gson gson = new Gson();
        for (Site site : siteList) {
            result.add(ordinatesToJsonElement(hazCurves.get(site), gson).toString());
        }
        return result;
    }

    /**
     * Convert a hazard curve to a JSON list of ordinates.
     *
     * @param func
     * @return
     */
    public static JsonElement ordinatesToJsonElement(DiscretizedFuncAPI func,
            Gson gson) {
        List<Double> curve = new ArrayList<Double>();
        Iterator<DataPoint2D> ptIter = func.getPointsIterator();
        while (ptIter.hasNext()) {
            DataPoint2D point = ptIter.next();
            curve.add(point.getY());
        }
        return gson.toJsonTree(curve, CURVE_TYPE);
    }
}
