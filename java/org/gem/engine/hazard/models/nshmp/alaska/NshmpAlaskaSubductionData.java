package org.gem.engine.hazard.models.nshmp.alaska;

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Set;

import org.gem.engine.hazard.parsers.GemFileParser;
import org.gem.engine.hazard.parsers.nshmp.NshmpSubduction2GemSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.util.TectonicRegionType;

public class NshmpAlaskaSubductionData extends GemFileParser {

    private String inDir = "nshmp/alaska/subduction/";

    public NshmpAlaskaSubductionData(double latmin, double latmax,
            double lonmin, double lonmax) {

        srcDataList = new ArrayList<GEMSourceData>();

        // hash map containing fault file with corresponding weight
        HashMap<String, Double> faultFile = new HashMap<String, Double>();

        // Aleutian Megathrust
        faultFile.put(inDir + "megaA.out_revF.in", 1.0);

        // Aleutian Megathrust
        faultFile.put(inDir + "megaAll.out_revF.in", 1.0);

        // Semidi region
        faultFile.put(inDir + "megaB.out_revF.in", 1.0);

        // Aleutian Megathrust Kodiak Segment
        faultFile.put(inDir + "megaD.out_revF.in", 1.0);

        // Aleutian Megathrust
        faultFile.put(inDir + "megaeast.out_revF.in", 1.0);

        // Aleutian Megathrust Far West
        faultFile.put(inDir + "megaF.out_revF.in", 1.0);

        // Transition fault
        faultFile.put(inDir + "trans.out_revF.in", 1.0);

        // Yakatag-Icy Bay Megathrust
        faultFile.put(inDir + "yak.out_revF.in", 1.0);

        // iterator over files
        Set<String> fileName = faultFile.keySet();
        Iterator<String> iterFileName = fileName.iterator();
        while (iterFileName.hasNext()) {
            String key = iterFileName.next();
            System.out.println("Processing file: " + key + ", weight: "
                    + faultFile.get(key));
            NshmpSubduction2GemSourceData fm = null;
            try {
                fm =
                        new NshmpSubduction2GemSourceData(key,
                                TectonicRegionType.SUBDUCTION_INTERFACE,
                                faultFile.get(key), latmin, latmax, lonmin,
                                lonmax);
            } catch (IOException e) {
                // TODO Auto-generated catch block
                e.printStackTrace();
            }
            for (int i = 0; i < fm.getList().size(); i++)
                srcDataList.add(fm.getList().get(i));
        }

    }

    // for testing
    public static void main(String[] args) throws Exception {

        NshmpAlaskaSubductionData m =
                new NshmpAlaskaSubductionData(-90.0, 90.0, -180.0, 180.0);

    }

}
