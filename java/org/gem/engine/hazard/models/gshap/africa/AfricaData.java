package org.gem.engine.hazard.models.gshap.africa;

import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;

import org.gem.engine.hazard.parsers.GemFileParser;
import org.gem.engine.hazard.parsers.africa.GshapIsrael2GemSourceData;
import org.gem.engine.hazard.parsers.africa.IberoMagreb2GemSourceData;
import org.gem.engine.hazard.parsers.africa.gshapAfrica2GemSourceData;
import org.gem.engine.hazard.parsers.ssAfrica.SsAfricaSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;

/**
 * This class builds an array list of GEMAreatSourceData objects representing
 * the area sources for calculation the seismic hazard in Africa The input
 * models are: - IberoMagreb - EastMagreb: Libya and Egypt - Western Africa -
 * SubSahara Region - Africa * @author l.danciu
 */
public class AfricaData extends GemFileParser {

    public AfricaData() throws IOException {

        srcDataList = new ArrayList<GEMSourceData>();

        // IberoMagreb model
        IberoMagreb2GemSourceData model1 =
                new IberoMagreb2GemSourceData(
                        "gshap/africa/iberoMagreb/IberoMagrebInput.dat");
        // Israel Model
        GshapIsrael2GemSourceData model2 =
                new GshapIsrael2GemSourceData("gshap/africa/israel/israel.zon");
        // EastIberoMagreb
        gshapAfrica2GemSourceData model3 =
                new gshapAfrica2GemSourceData(
                        "gshap/africa/eastMagreb/EastIberoMagreb.dat");
        // Western Africa
        gshapAfrica2GemSourceData model4 =
                new gshapAfrica2GemSourceData(
                        "gshap/africa/westAfrica/WestAfricaInput.dat");
        // SubSahara Region
        SsAfricaSourceData model5 = new SsAfricaSourceData();

        srcDataList.addAll(model1.getList());
        srcDataList.addAll(model2.getList());
        srcDataList.addAll(model3.getList());
        srcDataList.addAll(model4.getList());
        srcDataList.addAll(model5.getList());
    }

    // main method for testing
    public static void main(String[] args) throws IOException {

        // read input file and create array list of GEMSourceData
        AfricaData model = new AfricaData();

        model.writeAreaSources2KMLfile(new FileWriter(
                "/Users/damianomonelli/Desktop/AfricaAreaSources.kml"));

    }

}
