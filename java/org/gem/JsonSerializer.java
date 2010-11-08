package org.gem;

import java.lang.reflect.Type;
import java.util.ArrayList;

import org.gem.engine.hazard.memcached.Cache;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;

import com.google.gson.Gson;
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
}
