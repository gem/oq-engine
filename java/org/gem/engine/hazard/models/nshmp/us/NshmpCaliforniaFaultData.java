package org.gem.engine.hazard.models.nshmp.us;

import java.io.FileNotFoundException;
import java.util.ArrayList;
import java.util.HashMap;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.gem.engine.hazard.parsers.GemFileParser;
import org.gem.engine.hazard.parsers.nshmp.NshmpFault2GemSourceData;
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

    private static final Log logger =
            LogFactory.getLog(NshmpCaliforniaFaultData.class);

    private final String path;

    public NshmpCaliforniaFaultData(String path) {
        this.path = path;
    }

    public void read(double latMin, double latMax, double lonMin, double lonMax) {
        srcDataList = new ArrayList<GEMSourceData>();

        // hash map containing fault file with corresponding weight
        HashMap<String, Double> files = new HashMap<String, Double>();

        // California B Fault model
        // Deformation model D2.1 -> 0.5
        // Deformation model D2.4 -> 0.5
        // Stiched -> 0.5
        // Unstiched -> 0.5
        // CHAR -> 0.6667
        // GR -> 0.3334
        files.put(path + "bFault_stitched_D2.1_Char.in", 0.166675); // 0.5*0.5*0.6667
        // =
        // 0.166675
        files.put(path + "bFault_stitched_D2.1_GR0.in", 0.08335); // 0.5*0.5*0.3334
        // =
        // 0.08335
        files.put(path + "bFault_unstitched_D2.1_Char.in", 0.166675);
        files.put(path + "bFault_unstitched_D2.1_GR0.in", 0.08335);
        files.put(path + "bFault_stitched_D2.4_Char.in", 0.166675);
        files.put(path + "bFault_stitched_D2.4_GR0.in", 0.08335);
        files.put(path + "bFault_unstitched_D2.4_Char.in", 0.166675);
        files.put(path + "bFault_unstitched_D2.4_GR0.in", 0.08335);

        // California A Fault model
        // aPriori_D2.1 -> 0.45
        // MoBal_EllB -> 0.225
        // MoBal.HB -> 0.225
        // unseg_HB -> 0.05
        // unseg_Ell -> 0.05
        files.put(path + "aFault_aPriori_D2.1.in", 0.45);
        files.put(path + "aFault_MoBal_EllB.in", 0.225);
        files.put(path + "aFault_MoBal.HB.in", 0.225);
        files.put(path + "aFault_unseg_HB.in", 0.05);
        files.put(path + "aFault_unsegEll.in", 0.05);

        // California Creeping Fault model
        files.put(path + "creepflt.new.in", 1.0);

        for (String file : files.keySet()) {
            Double weight = files.get(file);
            logger.info("Processing file " + file + ", weight " + weight);

            try {
                TectonicRegionType tectRegion =
                        TectonicRegionType.ACTIVE_SHALLOW;

                NshmpFault2GemSourceData fm =
                        new NshmpFault2GemSourceData(file, tectRegion, weight,
                                latMin, latMax, lonMin, lonMax);

                srcDataList.addAll(fm.getList());
            } catch (FileNotFoundException e) {
                throw new RuntimeException(e);
            }
        }
    }

}
