package org.gem.engine.hazard.models.gshap.south_east_asia;

import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;

import org.gem.engine.hazard.parsers.GemFileParser;
import org.gem.engine.hazard.parsers.gshap.sea.GshapSEAsia2GemSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;

/**
 * This class builds an array list of GEMAreatSourceData objects representing
 * the area sources for calculation the seismic hazard in SE ASIA -GSHAP The
 * input models are: area sources background sources
 * 
 * @author l.danciu
 */
public class SeAsiaData extends GemFileParser {

    public SeAsiaData() throws IOException {

        srcDataList = new ArrayList<GEMSourceData>();

        // Area Source Model
        GshapSEAsia2GemSourceData model1 =
                new GshapSEAsia2GemSourceData(
                        "gshap/south_east_asia/seAsiaCorr.dat");
        // Background Area Sources Model
        GshapSEAsia2GemSourceData model2 =
                new GshapSEAsia2GemSourceData(
                        "gshap/south_east_asia/gshapeaBackgrd.dat");

        srcDataList.addAll(model1.getList());
        srcDataList.addAll(model2.getList());
    }

    // for testing
    public static void main(String[] args) throws IOException {

        SeAsiaData model = new SeAsiaData();

        model.writeAreaSources2KMLfile(new FileWriter(
                "/Users/damianomonelli/Desktop/SEAsources.kml"));

    }

}
