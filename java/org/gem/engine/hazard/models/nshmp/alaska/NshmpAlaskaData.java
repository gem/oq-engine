package org.gem.engine.hazard.models.nshmp.alaska;

import java.io.FileNotFoundException;
import java.util.ArrayList;

import org.gem.engine.hazard.parsers.GemFileParser;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;

public class NshmpAlaskaData extends GemFileParser {

    public NshmpAlaskaData(double latmin, double latmax, double lonmin,
            double lonmax) throws FileNotFoundException {

        srcDataList = new ArrayList<GEMSourceData>();

        NshmpAlaskaFaultData fault =
                new NshmpAlaskaFaultData(latmin, latmax, lonmin, lonmax);

        NshmpAlaskaSubductionData subFault =
                new NshmpAlaskaSubductionData(latmin, latmax, lonmin, lonmax);

        srcDataList.addAll(fault.getList());
        srcDataList.addAll(subFault.getList());

    }

}
