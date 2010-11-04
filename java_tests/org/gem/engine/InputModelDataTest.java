package org.gem.engine;

import org.junit.Test;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMAreaSourceData;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

public class InputModelDataTest {

    @Test
    public void serializeToJsonFaultTest() {
        InputModelData model =
                new InputModelData("java_tests/data/src_model_fault.dat", 0.1);
        System.out.println(model.getSourceList().size());
        String json = InputModelData.getJsonSourceList();
        System.out.println(json);
    }

    @Test
    public void serializeToJsonSubductionTest() {
        InputModelData model =
                new InputModelData("java_tests/data/src_model_subduction.dat",
                        0.1);
        System.out.println(model.getSourceList().size());
        String json = InputModelData.getJsonSourceList();
        System.out.println(json);
    }

    @Test
    public void serializeToJsonAreaTest() {
        InputModelData model =
                new InputModelData("java_tests/data/src_model_area.dat", 0.1);
        if (model.getSourceList().get(0) instanceof GEMAreaSourceData) {
            GsonBuilder build = new GsonBuilder().serializeNulls();
            GEMAreaSourceData src =
                    (GEMAreaSourceData) model.getSourceList().get(0);
            System.out.println(new Gson().toJson(src.getRegion()));
            System.out.println(new Gson().toJson(src.getMagfreqDistFocMech()));
            System.out.println(src.getAveRupTopVsMag().toString());
            System.out.println(build.create().toJson(src.getAveRupTopVsMag()));
        }
        // System.out.println(model.getSourceList().size());
        // String json = InputModelData.getJsonSourceList();
        // System.out.println(json);
    }
}
