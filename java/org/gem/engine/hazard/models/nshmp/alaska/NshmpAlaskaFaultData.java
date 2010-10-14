package org.gem.engine.hazard.models.nshmp.alaska;

import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Set;

import org.gem.engine.hazard.parsers.GemFileParser;
import org.gem.engine.hazard.parsers.nshmp.NshmpAlaskaFault2GemSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.util.TectonicRegionType;

public class NshmpAlaskaFaultData extends GemFileParser {

    private String inDir = "nshmp/alaska/fault/";

    public NshmpAlaskaFaultData(double latmin, double latmax, double lonmin,
            double lonmax) throws FileNotFoundException {

        srcDataList = new ArrayList<GEMSourceData>();

        // hash map containing fault file with corresponding weight
        HashMap<String, Double> faultFile = new HashMap<String, Double>();

        // Queen Charlotte and Fairweather Flt - GR
        faultFile.put(inDir + "AKF0.out_revF.in", 0.5);

        // Queen Charlotte and Fairweather Flt - Char
        faultFile.put(inDir + "AKF1.out_revF.in", 0.5);

        // Central and Eastern Denali + plus others
        faultFile.put(inDir + "AKF2.out_revF.in", 0.5);

        // Central and Eastern Denali + plus others
        faultFile.put(inDir + "AKF3.out_revF.in", 0.5);

        // Kodiac Island fault and Narrow Cape fault
        faultFile.put(inDir + "AKF4.out_revF.in", 0.5);

        // Kodiac Island fault and Narrow Cape fault
        faultFile.put(inDir + "AKF5.out_revF.in", 0.5);

        // iterator over files
        Set<String> fileName = faultFile.keySet();
        Iterator<String> iterFileName = fileName.iterator();
        while (iterFileName.hasNext()) {
            String key = iterFileName.next();
            System.out.println("Processing file: " + key + ", weight: "
                    + faultFile.get(key));
            NshmpAlaskaFault2GemSourceData fm =
                    new NshmpAlaskaFault2GemSourceData(key,
                            TectonicRegionType.ACTIVE_SHALLOW,
                            faultFile.get(key), latmin, latmax, lonmin, lonmax);
            for (int i = 0; i < fm.getList().size(); i++)
                srcDataList.add(fm.getList().get(i));
        }

    }

    // for testing
    public static void main(String[] args) throws IOException {

        NshmpAlaskaFaultData model =
                new NshmpAlaskaFaultData(-90.0, 90.0, -180.0, 180.0);

        model.writeSources2KMLfile(new FileWriter(
                "/Users/damianomonelli/Desktop/AlaskaFaultSources.kml"));

    }

}
