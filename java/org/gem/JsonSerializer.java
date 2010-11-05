package org.gem;

import java.util.ArrayList;

import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;

import com.google.gson.Gson;

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

}
