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
            new TypeToken<List<Map<String, String>>>() {
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
    private static final String CURVE = "curve";

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
        Type listType = new TypeToken<List<GEMSourceData>>() {
        }.getType();
        return gson.create().fromJson((String) cache.get(key), listType);
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
        List<String> json = new ArrayList<String>();
        Gson gson = new Gson();
        for (Site site : siteList) {
            Double lon = site.getLocation().getLongitude();
            Double lat = site.getLocation().getLatitude();
            Map<String, String> siteMap = new HashMap<String, String>();
            siteMap.put(SITE_LON, lon.toString());
            siteMap.put(SITE_LAT, lat.toString());

            JsonObject hazardCurve =
                    gson.toJsonTree(siteMap, SITE_TYPE).getAsJsonObject();
            JsonElement curveElement =
                    curveToJsonElement(hazCurves.get(site), gson);
            hazardCurve.add(CURVE, curveElement);
            json.add(hazardCurve.toString());
        }
        return json;
    }

    /**
     * Convert a hazard curve to a JSON list of x,y pairs (as dicts). Example:
     * [{"x": "-5.2983174", "y": "0.0"}, ... , {"x": "0.756122", "y": "0.0"}]
     * 
     * @param func
     * @return
     */
    public static JsonElement curveToJsonElement(DiscretizedFuncAPI func,
            Gson gson) {
        List<Map<String, String>> curve = new ArrayList<Map<String, String>>();
        Iterator<DataPoint2D> ptIter = func.getPointsIterator();
        while (ptIter.hasNext()) {
            DataPoint2D point = ptIter.next();
            Map<String, String> xy = new HashMap<String, String>();
            xy.put(X, Double.toString(point.getX()));
            xy.put(Y, Double.toString(point.getY()));
            curve.add(xy);
        }
        return gson.toJsonTree(curve, CURVE_TYPE);
    }
}
