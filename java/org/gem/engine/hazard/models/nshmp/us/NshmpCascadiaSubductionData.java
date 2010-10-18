package org.gem.engine.hazard.models.nshmp.us;

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Set;

import org.gem.engine.hazard.parsers.GemFileParser;
import org.gem.engine.hazard.parsers.nshmp.NshmpSubduction2GemSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.util.TectonicRegionType;

public class NshmpCascadiaSubductionData extends GemFileParser {

    public static String inDir = "nshmp/cascadia/";

    public NshmpCascadiaSubductionData(double latmin, double latmax,
            double lonmin, double lonmax) {

        srcDataList = new ArrayList<GEMSourceData>();

        // hash map containing fault file with corresponding weight
        HashMap<String, Double> faultFile = new HashMap<String, Double>();

        // SUB.top.pga.9N.zhao
        // .04
        faultFile.put(inDir + "cascadia.top.9z.in", 0.04);

        // SUB.bot.pga.88N.z
        // .02667
        faultFile.put(inDir + "cascadia.bot.88z.in", 0.02667);

        // SUB.bot.pga.92N.z
        // .02667
        faultFile.put(inDir + "cascadia.bot.92z.in", 0.02667);

        // SUB.bot.pga.9N.z
        // .08
        faultFile.put(inDir + "cascadia.bot.9z.in", 0.08);

        // SUB.mid.pga.88N.z
        // .02667
        faultFile.put(inDir + "cascadia.mid.88z.in", 0.02667);

        // SUB.mid.pga.92N.z
        // .02667
        faultFile.put(inDir + "cascadia.mid.92z.in", 0.02667);

        // SUB.mid.pga.9N.z
        // .08
        faultFile.put(inDir + "cascadia.mid.9z.in", 0.08);

        // SUB.top.pga.88N.z
        // .013333
        faultFile.put(inDir + "cascadia.top.88z.in", 0.013333);

        // SUB.top.pga.92N.z
        // .01333
        faultFile.put(inDir + "cascadia.top.92z.in", 0.01333);

        // SUB.bot.pga.8387z.out
        // .010267
        faultFile.put(inDir + "cascadia.bot.8387z.in", 0.010267);

        // SUB.bot.pga.8082z.out
        // 0.005133
        faultFile.put(inDir + "cascadia.bot.8082z.in", 0.005133);

        // SUB.mid.pga.8387z.out
        // 0.010267
        faultFile.put(inDir + "cascadia.mid.8387z.in", 0.010267);

        // SUB.mid.pga.8082z.out
        // 0.005133
        faultFile.put(inDir + "cascadia.mid.8082z.in", 0.005133);

        // SUB.older2.pga.8387z.out
        // .025667
        faultFile.put(inDir + "cascadia.older2.8387z.in", 0.025667);

        // SUB.older2.pga.8082z.out
        // 0.012833
        faultFile.put(inDir + "cascadia.older2.8082z.in", 0.012833);

        // SUB.older2.pga.92Nz.out
        // .0667
        faultFile.put(inDir + "cascadia.older2.92z.in", 0.0667);

        // SUB.older2.pga.9Nz.out
        // 0.2
        faultFile.put(inDir + "cascadia.older2.9z.in", 0.2);

        // SUB.older2.pga.88Nz.out
        // .0667
        faultFile.put(inDir + "cascadia.older2.88z.in", 0.0667);

        // SUB.top.pga.8387z.out
        // .00513333
        faultFile.put(inDir + "cascadia.top.8387z.in", 0.00513333);

        // SUB.top.pga.8082z.out
        // 0.0025667
        faultFile.put(inDir + "cascadia.top.8082z.in", 0.0025667);

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

}
