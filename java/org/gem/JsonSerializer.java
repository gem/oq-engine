package org.gem;

import java.lang.reflect.Type;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Properties;

import org.gem.engine.hazard.memcached.Cache;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.util.TectonicRegionType;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.reflect.TypeToken;

public class JsonSerializer {

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
            ArrayList<GEMSourceData> sourceList) {
        cache.set(key, getJsonSourceList(sourceList));
    }

    public static ArrayList<GEMSourceData> getSourceListFromCache(Cache cache,
            String key) {
        Type listType = new TypeToken<ArrayList<GEMSourceData>>() {
        }.getType();
        return new Gson().fromJson((String) cache.get(key), listType);
    }

    public static
            HashMap<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI>
            getGmpeMapFromCache(Cache cache, String key) {

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
}
