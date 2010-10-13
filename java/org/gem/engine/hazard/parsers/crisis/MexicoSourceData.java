package org.gem.engine.hazard.parsers.crisis;

import java.io.BufferedReader;
import java.util.ArrayList;
import java.util.HashMap;

import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMAreaSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMFaultSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSubductionFaultSourceData;
import org.opensha.sha.util.TectonicRegionType;

public class MexicoSourceData extends CrisisSourceData {

    public MexicoSourceData(BufferedReader input) {
        super(input);

        HashMap<Integer, TectonicRegionType> tecRegMap =
                new HashMap<Integer, TectonicRegionType>();
        tecRegMap.put(8, TectonicRegionType.SUBDUCTION_INTERFACE);
        tecRegMap.put(12, TectonicRegionType.SUBDUCTION_INTERFACE);
        tecRegMap.put(13, TectonicRegionType.SUBDUCTION_INTERFACE);
        tecRegMap.put(14, TectonicRegionType.SUBDUCTION_INTERFACE);
        tecRegMap.put(15, TectonicRegionType.SUBDUCTION_INTERFACE);
        tecRegMap.put(16, TectonicRegionType.SUBDUCTION_INTERFACE);
        tecRegMap.put(17, TectonicRegionType.SUBDUCTION_INTERFACE);
        tecRegMap.put(18, TectonicRegionType.SUBDUCTION_INTERFACE);
        tecRegMap.put(19, TectonicRegionType.SUBDUCTION_INTERFACE);
        tecRegMap.put(20, TectonicRegionType.SUBDUCTION_INTERFACE);
        tecRegMap.put(21, TectonicRegionType.SUBDUCTION_INTERFACE);
        tecRegMap.put(22, TectonicRegionType.SUBDUCTION_INTERFACE);
        tecRegMap.put(23, TectonicRegionType.SUBDUCTION_INTERFACE);
        tecRegMap.put(24, TectonicRegionType.SUBDUCTION_INTERFACE);
        tecRegMap.put(25, TectonicRegionType.SUBDUCTION_INTERFACE);
        tecRegMap.put(26, TectonicRegionType.SUBDUCTION_INTERFACE);
        tecRegMap.put(27, TectonicRegionType.SUBDUCTION_INTERFACE);
        tecRegMap.put(28, TectonicRegionType.SUBDUCTION_INTERFACE);
        tecRegMap.put(29, TectonicRegionType.SUBDUCTION_INTERFACE);

        tecRegMap.put(30, TectonicRegionType.SUBDUCTION_SLAB);
        tecRegMap.put(31, TectonicRegionType.SUBDUCTION_SLAB);
        tecRegMap.put(32, TectonicRegionType.SUBDUCTION_SLAB);
        tecRegMap.put(36, TectonicRegionType.SUBDUCTION_SLAB);

        ArrayList<GEMSourceData> srcList = this.srcDataList;

        int counter = 0;
        int idx = 0;
        for (GEMSourceData srcDat : srcList) {

            if (tecRegMap.containsKey(idx)) {
                if (tecRegMap.get(idx).equals(
                        TectonicRegionType.SUBDUCTION_INTERFACE)) {
                    System.out.printf("Interface....[%d]:%s\n", idx,
                            srcDat.getName());
                    srcList.get(idx).setTectReg(
                            TectonicRegionType.SUBDUCTION_INTERFACE);
                }
                if (tecRegMap.get(idx).equals(
                        TectonicRegionType.SUBDUCTION_SLAB)) {
                    System.out.printf("Intraplate..[%d]:%s\n", idx,
                            srcDat.getName());
                    srcList.get(idx).setTectReg(
                            TectonicRegionType.SUBDUCTION_SLAB);
                }
            }

            // Verifying the number of sources contained in the model VS the one
            // wih an assigned
            // tectonic region
            if (srcDat instanceof GEMAreaSourceData) {
                counter += 1;
            } else if (srcDat instanceof GEMFaultSourceData) {
                counter += 1;
            } else if (srcDat instanceof GEMSubductionFaultSourceData) {
                counter += 1;
            }
            idx++;
        }
        this.srcDataList = srcList;

    }

}
