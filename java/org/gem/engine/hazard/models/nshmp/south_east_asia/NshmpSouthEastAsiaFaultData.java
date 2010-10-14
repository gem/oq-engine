package org.gem.engine.hazard.models.nshmp.south_east_asia;

import java.io.FileNotFoundException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Set;

import org.gem.engine.hazard.parsers.GemFileParser;
import org.gem.engine.hazard.parsers.nshmp.NshmpFault2GemSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.util.TectonicRegionType;

public class NshmpSouthEastAsiaFaultData extends GemFileParser {

    private static String inDir = "nshmp/south_east_asia/fault/";

    public NshmpSouthEastAsiaFaultData(double latmin, double latmax,
            double lonmin, double lonmax) throws FileNotFoundException {

        srcDataList = new ArrayList<GEMSourceData>();

        // hash map containing fault file with corresponding weight
        HashMap<String, Double> faultFile = new HashMap<String, Double>();

        // sumatra_siehpga.char.lowQ -> sumatra_flt.lowQ.sieh.char
        // 0.25
        faultFile.put(inDir + "sumatra_flt.lowQ.sieh.char", 0.25);

        // sumatra_frenchpga.char.lowQ -> sumatra_flt.lowQ.french.char
        // 0.25
        faultFile.put(inDir + "sumatra_flt.lowQ.french.char", 0.25);

        // sumatra_oldpga.char.lowQ -> sumatra_flt.lowQ.M7p9.char
        // 0.25
        faultFile.put(inDir + "sumatra_flt.lowQ.M7p9.char", 0.25);

        // sumatra_oldpga.gr.lowQ -> sumatra_flt.lowQ.M7p9.gr
        // 0.25
        faultFile.put(inDir + "sumatra_flt.lowQ.M7p9.gr", 0.25);

        // thaipga.char.lowQ -> thai.new.char
        // 0.5
        faultFile.put(inDir + "thai.new.char", 0.5);

        // thaipga.gr.lowQ -> thai.new.gr
        // .50
        faultFile.put(inDir + "thai.new.gr", 0.5);

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
