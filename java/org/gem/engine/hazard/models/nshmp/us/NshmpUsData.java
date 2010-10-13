package org.gem.engine.hazard.models.nshmp.us;

import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;

import org.gem.engine.hazard.parsers.GemFileParser;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;

public class NshmpUsData extends GemFileParser {
    private static boolean USEGRIDS = true;

    public NshmpUsData(double latmin, double latmax, double lonmin,
            double lonmax) throws FileNotFoundException {

        srcDataList = new ArrayList<GEMSourceData>();

        // Western United States fault model (active shallow tectonics)
        NshmpWusFaultData wusFault =
                new NshmpWusFaultData(latmin, latmax, lonmin, lonmax);
        NshmpCaliforniaFaultData caliFault =
                new NshmpCaliforniaFaultData(latmin, latmax, lonmin, lonmax);

        // Western United States Cascadia subduction model (subduction
        // interface)
        NshmpCascadiaSubductionData cascadiaSub =
                new NshmpCascadiaSubductionData(latmin, latmax, lonmin, lonmax);

        // Central and Eastern United States fault model (stable shallow
        // tectonics)
        NshmpCeusFaultData ceusFault =
                new NshmpCeusFaultData(latmin, latmax, lonmin, lonmax);

        srcDataList.addAll(wusFault.getList());
        srcDataList.addAll(caliFault.getList());
        srcDataList.addAll(cascadiaSub.getList());
        srcDataList.addAll(ceusFault.getList());

        if (USEGRIDS) {
            // Western United States grid model (active shallow and subduction
            // intraslab)
            NewNshmpWusGridData wusGrid =
                    new NewNshmpWusGridData(latmin, latmax, lonmin, lonmax);
            // Central and Eastern United States grid model (stable shallow
            // tectonics)
            NewNshmpCeusGridData ceusGrid =
                    new NewNshmpCeusGridData(latmin, latmax, lonmin, lonmax);
            srcDataList.addAll(wusGrid.getList());
            srcDataList.addAll(ceusGrid.getList());
        }

    }

    public static void main(String[] args) throws IOException {

        NshmpUsData model = new NshmpUsData(24.6, 50, -125, -100);

        for (int i = 0; i < model.getNumSources(); i++) {
            System.out.println(model.getList().get(i).getName());
        }

        // System.out.println(model.getNumSources());
        // System.exit(0);
        // TODO(JMC): Fix this path!
        model.writeSources2KMLfile(new FileWriter(
                "/Users/damianomonelli/Desktop/NshmpUsSources.kml"));
    }

}
