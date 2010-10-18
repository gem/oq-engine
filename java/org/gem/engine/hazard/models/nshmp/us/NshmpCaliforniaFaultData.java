package org.gem.engine.hazard.models.nshmp.us;

import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Set;

import org.gem.engine.hazard.parsers.GemFileParser;
import org.gem.engine.hazard.parsers.nshmp.NshmpFault2GemSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMFaultSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.util.TectonicRegionType;

/**
 * This class builds an array list of GEMFaultSourceData objects representing
 * faults in California according to the NSHMP model The fault models
 * implemented so far are: - California B Faults - California A Faults -
 * California Creeping Fault
 * 
 * @author damianomonelli
 * 
 */

public class NshmpCaliforniaFaultData extends GemFileParser {

    public static String inDir = "nshmp/CA/";

    // constructor
    public NshmpCaliforniaFaultData(double latmin, double latmax,
            double lonmin, double lonmax) throws FileNotFoundException {

        srcDataList = new ArrayList<GEMSourceData>();

        // hash map containing fault file with corresponding weight
        HashMap<String, Double> faultFile = new HashMap<String, Double>();

        // California B Fault model
        // Deformation model D2.1 -> 0.5
        // Deformation model D2.4 -> 0.5
        // Stiched -> 0.5
        // Unstiched -> 0.5
        // CHAR -> 0.6667
        // GR -> 0.3334
        faultFile.put(inDir + "bFault_stitched_D2.1_Char.in", 0.166675); // 0.5*0.5*0.6667
                                                                         // =
                                                                         // 0.166675
        faultFile.put(inDir + "bFault_stitched_D2.1_GR0.in", 0.08335); // 0.5*0.5*0.3334
                                                                       // =
                                                                       // 0.08335
        faultFile.put(inDir + "bFault_unstitched_D2.1_Char.in", 0.166675);
        faultFile.put(inDir + "bFault_unstitched_D2.1_GR0.in", 0.08335);
        faultFile.put(inDir + "bFault_stitched_D2.4_Char.in", 0.166675);
        faultFile.put(inDir + "bFault_stitched_D2.4_GR0.in", 0.08335);
        faultFile.put(inDir + "bFault_unstitched_D2.4_Char.in", 0.166675);
        faultFile.put(inDir + "bFault_unstitched_D2.4_GR0.in", 0.08335);

        // California A Fault model
        // aPriori_D2.1 -> 0.45
        // MoBal_EllB -> 0.225
        // MoBal.HB -> 0.225
        // unseg_HB -> 0.05
        // unseg_Ell -> 0.05
        faultFile.put(inDir + "aFault_aPriori_D2.1.in", 0.45);
        faultFile.put(inDir + "aFault_MoBal_EllB.in", 0.225);
        faultFile.put(inDir + "aFault_MoBal.HB.in", 0.225);
        faultFile.put(inDir + "aFault_unseg_HB.in", 0.05);
        faultFile.put(inDir + "aFault_unsegEll.in", 0.05);

        // California Creeping Fault model
        faultFile.put(inDir + "creepflt.new.in", 1.0);

        // iterator over files
        Set<String> fileName = faultFile.keySet();
        Iterator<String> iterFileName = fileName.iterator();
        while (iterFileName.hasNext()) {
            String key = iterFileName.next();
            System.out.println("Processing file: " + key + ", weight: "
                    + faultFile.get(key));
            // read NSHMP input file
            NshmpFault2GemSourceData fm =
                    new NshmpFault2GemSourceData(key,
                            TectonicRegionType.ACTIVE_SHALLOW,
                            faultFile.get(key), latmin, latmax, lonmin, lonmax);
            for (int i = 0; i < fm.getList().size(); i++)
                srcDataList.add(fm.getList().get(i));
        }
    }
}
