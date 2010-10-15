package org.gem.engine.hazard.parsers.japan;

import java.io.BufferedReader;
import java.io.IOException;
import java.util.ArrayList;

import org.gem.engine.hazard.parsers.GemFileParser;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;

public class JapanSourceData extends GemFileParser {

    private static boolean USERECTANGULAR = true;
    private static boolean USECOMPLEX = false;

    public JapanSourceData(BufferedReader inputRectangularFaults,
            BufferedReader inputComplexFault) throws IOException {

        ArrayList<GEMSourceData> srcList = new ArrayList<GEMSourceData>();

        // Reading rectangular faults
        if (USERECTANGULAR) {
            String line = inputRectangularFaults.readLine();
            int cnt = 0;
            boolean go = true;
            while ((line = inputRectangularFaults.readLine()) != null && go) {
                srcList.add(new RectangularFaultData(line).getFaultSourceData());
                int id =
                        Integer.valueOf(srcList.get(srcList.size() - 1).getID())
                                .intValue();
            }
            this.srcDataList = srcList;
        }

        // Reading complex faults
        if (USECOMPLEX) {
            String line = inputComplexFault.readLine();
            int cnt = 0;
            boolean go = true;
            while ((line = inputComplexFault.readLine()) != null && go) {
                srcList.add(new RectangularFaultData(line).getFaultSourceData());
                int id =
                        Integer.valueOf(srcList.get(srcList.size() - 1).getID())
                                .intValue();
            }
            this.srcDataList = srcList;
        }

        System.out.println("done");

    }

}
