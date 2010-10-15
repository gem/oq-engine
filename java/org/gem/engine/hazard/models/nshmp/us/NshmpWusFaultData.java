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
 * faults in the Western United States according to the NSHMP model The fault
 * models implemented so far are: - Nevada, Utah, Basin and Range States Long
 * Faults - Nevada, Utah, Basin and Range States Short Faults - Pacific North
 * West Normal Faults - Pacific North West Faults - Pacific North West Short
 * Faults - Seattle Fault Zone - California B Faults - California A Faults -
 * California Creeping Fault - Wasatch Fault
 * 
 * @author damianomonelli
 * 
 */

public class NshmpWusFaultData extends GemFileParser {

    public static String inDir = "tests/data/nshmp/WUS/WUSfaults/";

    // constructor
    public NshmpWusFaultData(double latmin, double latmax, double lonmin,
            double lonmax) throws FileNotFoundException {

        srcDataList = new ArrayList<GEMSourceData>();

        // hash map containing fault file with corresponding weight
        HashMap<String, Double> faultFile = new HashMap<String, Double>();

        // Nevada, Utah, Basin and Range States Long Faults, and
        // Pacific North West Normal Faults models
        // GR -> 0.333
        // CHAR -> 0.667
        // DIP 40 -> 0.2
        // DIP 50 -> 0.6
        // DIP 60 -> 0.2
        faultFile.put(inDir + "nv.d40.gr", 0.0667);
        faultFile.put(inDir + "nv.gr", 0.2);
        faultFile.put(inDir + "nv.d60.gr", 0.0667);
        faultFile.put(inDir + "nv.d40.char", 0.1333);
        faultFile.put(inDir + "nv.char", 0.4);
        faultFile.put(inDir + "nv.d60.char", 0.1333);

        // Utah Long Faults model
        faultFile.put(inDir + "ut.d40.gr", 0.0667);
        faultFile.put(inDir + "ut.gr", 0.2);
        faultFile.put(inDir + "ut.d60.gr", 0.0667);
        faultFile.put(inDir + "ut.d40.char", 0.1333);
        faultFile.put(inDir + "ut.char", 0.4);
        faultFile.put(inDir + "ut.d60.char", 0.1333);

        // Basin&Range States Long Faults model
        faultFile.put(inDir + "brange.d40.gr", 0.0667);
        faultFile.put(inDir + "brange.gr", 0.2);
        faultFile.put(inDir + "brange.d60.gr", 0.0667);
        faultFile.put(inDir + "brange.d40.char", 0.1333);
        faultFile.put(inDir + "brange.char", 0.4);
        faultFile.put(inDir + "brange.d60.char", 0.1333);

        // Pacific North West Normal Faults models
        faultFile.put(inDir + "orwa_n.d40.gr", 0.0667);
        faultFile.put(inDir + "orwa_n.gr", 0.2);
        faultFile.put(inDir + "orwa_n.d60.gr", 0.0667);
        faultFile.put(inDir + "orwa_n.d40.char", 0.1333);
        faultFile.put(inDir + "orwa_n.char", 0.4);
        faultFile.put(inDir + "orwa_n.d60.char", 0.1333);

        // Nevada, Utah, Basin and Range States Short Faults models
        // DIP 40 -> 0.2
        // DIP 50 -> 0.6
        // DIP 60 -> 0.2

        // Nevada Short Faults
        faultFile.put(inDir + "nv.d40.65", 0.2);
        faultFile.put(inDir + "nv.65", 0.6);
        faultFile.put(inDir + "nv.d60.65", 0.2);

        // Utah Short Faults
        faultFile.put(inDir + "ut.d40.65", 0.2);
        faultFile.put(inDir + "ut.65", 0.6);
        faultFile.put(inDir + "ut.d60.65", 0.2);

        // Basin and Range States Short Faults
        faultFile.put(inDir + "brange.d40.65", 0.2);
        faultFile.put(inDir + "brange.65", 0.6);
        faultFile.put(inDir + "brange.d60.65", 0.2);

        // Wasatch Fault model
        // CHAR -> 0.72
        // FLOATING7.4 -> 0.1
        // GR -> 0.18
        // DIP 40 -> 0.2
        // DIP 50 -> 0.6
        // DIP 60 -> 0.2
        faultFile.put(inDir + "wasatch.d40.char", 0.144); // 0.72*0.2
        faultFile.put(inDir + "wasatch.char", 0.432); // 0.72*0.6
        faultFile.put(inDir + "wasatch.d60.char", 0.144); // 0.72*0.2
        faultFile.put(inDir + "wasatch74.d40.gr", 0.02); // 0.1*0.2
        faultFile.put(inDir + "wasatch74.gr", 0.06); // 0.1*0.6
        faultFile.put(inDir + "wasatch74.d60.gr", 0.02); // 0.1*0.2
        faultFile.put(inDir + "wasatch.d40.gr", 0.036); // 0.18*0.2
        faultFile.put(inDir + "wasatch.gr", 0.108); // 0.18*0.6
        faultFile.put(inDir + "wasatch.d60.gr", 0.036); // 0.18*0.2

        // Pacific North West Fault model
        // CHAR -> 0.5
        // GR -> 0.5
        faultFile.put(inDir + "orwa_c.char", 0.5);
        faultFile.put(inDir + "orwa_c.gr", 0.5);

        // Pacific North West Short Faults model
        faultFile.put(inDir + "orwa.65", 1.0);

        // Seattle Fault Zone model
        faultFile.put(inDir + "seattleFZ.in", 1.0);

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
            for (int i = 0; i < fm.getList().size(); i++) {
                srcDataList.add(fm.getList().get(i));
            }
        }
    }

    // for testing
    public static void main(String[] args) throws FileNotFoundException {

        NshmpWusFaultData model = new NshmpWusFaultData(-90, 90, -180, 180);

        System.out.println(model.getNumSources());

        for (int i = 0; i < model.getNumSources(); i++) {

            System.out.println(model.getList().get(i).getName());
            System.out.println(((GEMFaultSourceData) model.getList().get(i))
                    .getMfd());

        }
    }

}
