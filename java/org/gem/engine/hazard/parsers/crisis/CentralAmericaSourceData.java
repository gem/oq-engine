package org.gem.engine.hazard.parsers.crisis;

import java.io.BufferedReader;
import java.util.ArrayList;

import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMAreaSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMFaultSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSubductionFaultSourceData;
import org.opensha.sha.util.TectonicRegionType;

public class CentralAmericaSourceData extends CrisisSourceData {

    public CentralAmericaSourceData(BufferedReader input) {
        super(input);

        ArrayList<GEMSourceData> srcList = this.srcDataList;

        int counter = 0;
        int idx = 0;
        for (GEMSourceData srcDat : srcList) {

            if (srcDat.getName().matches("\\wsi.*")) {
                System.out.println("Interface....:" + srcDat.getName());
                srcList.get(idx).setTectReg(
                        TectonicRegionType.SUBDUCTION_INTERFACE);
            }
            if (srcDat.getName().matches("\\wsp.*")) {
                System.out.println("Intraplate...:" + srcDat.getName());
                srcList.get(idx).setTectReg(TectonicRegionType.SUBDUCTION_SLAB);
            }

            if (srcDat instanceof GEMAreaSourceData) {
                counter += 1;
            } else if (srcDat instanceof GEMFaultSourceData) {
                counter += 1;
            } else if (srcDat instanceof GEMSubductionFaultSourceData) {
                counter += 1;
            }
            idx++;
        }
        System.out.println("# assigned sources : " + counter
                + " tot. number of sources " + srcList.size());
        System.out.println("done");
        this.srcDataList = srcList;

    }

}
