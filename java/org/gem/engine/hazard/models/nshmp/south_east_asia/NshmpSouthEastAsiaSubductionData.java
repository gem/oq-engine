package org.gem.engine.hazard.models.nshmp.south_east_asia;

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Set;

import org.gem.engine.hazard.parsers.GemFileParser;
import org.gem.engine.hazard.parsers.nshmp.NshmpSubduction2GemSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.util.TectonicRegionType;

public class NshmpSouthEastAsiaSubductionData extends GemFileParser {

    private static String inDir =
            "../../data/nshmp/south_east_asia/subduction/";

    public NshmpSouthEastAsiaSubductionData(double latmin, double latmax,
            double lonmin, double lonmax) throws IOException {

        srcDataList = new ArrayList<GEMSourceData>();

        // hash map containing fault file with corresponding weight
        HashMap<String, Double> faultFile = new HashMap<String, Double>();

        // slab-pga.indoN.1000yr -> indoN.1000yr.subd.in
        // 0.667
        faultFile.put(inDir + "indoN.1000yr.subd.in", 0.667);

        // slab-pga.java-sumbaN.M71p -> java.subd.in
        // 0.667
        faultFile.put(inDir + "java.subd.in", 0.667);

        // slab-pga.indoC.333yr -> sumatraC.subd.in
        // 0.667
        faultFile.put(inDir + "sumatraC.subd.in", 0.667);

        // slab-pga.sumaN_gr.new -> sumaN_gr.subd.in
        // 0.333
        faultFile.put(inDir + "sumaN_gr.subd.in", 0.333);

        // iterator over files
        Set<String> fileName = faultFile.keySet();
        Iterator<String> iterFileName = fileName.iterator();
        while (iterFileName.hasNext()) {
            String key = iterFileName.next();
            System.out.println("Processing file: " + key + ", weight: "
                    + faultFile.get(key));
            NshmpSubduction2GemSourceData fm = null;
            fm =
                    new NshmpSubduction2GemSourceData(key,
                            TectonicRegionType.SUBDUCTION_INTERFACE,
                            faultFile.get(key), latmin, latmax, lonmin, lonmax);
            for (int i = 0; i < fm.getList().size(); i++)
                srcDataList.add(fm.getList().get(i));
        }

    }

}
