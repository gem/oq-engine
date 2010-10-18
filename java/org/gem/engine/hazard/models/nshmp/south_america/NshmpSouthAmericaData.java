package org.gem.engine.hazard.models.nshmp.south_america;

import java.io.IOException;
import java.util.ArrayList;

import org.gem.engine.hazard.parsers.GemFileParser;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;

public class NshmpSouthAmericaData extends GemFileParser {
    private static boolean USEGRIDS = false;

    public NshmpSouthAmericaData(double latmin, double latmax, double lonmin,
            double lonmax) throws IOException {

        srcDataList = new ArrayList<GEMSourceData>();

        // South America fault model (both shallow active and stable crust
        // sources)
        NshmpSouthAmericaFaultData fault =
                new NshmpSouthAmericaFaultData(latmin, latmax, lonmin, lonmax);

        // South America subduction model (interface sources)
        NshmpSouthAmericaSubductionData sub =
                new NshmpSouthAmericaSubductionData(latmin, latmax, lonmin,
                        lonmax);

        srcDataList.addAll(fault.getList());
        srcDataList.addAll(sub.getList());

        if (USEGRIDS) {

            // South America grid model (both shallow active and stable crust
            // sources plus intraslab sources)
            NshmpSouthAmericaGridData grid =
                    new NshmpSouthAmericaGridData(latmin, latmax, lonmin,
                            lonmax);
            srcDataList.addAll(grid.getList());
        }

    }

}
