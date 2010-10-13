package org.gem.engine.hazard.models.nshmp.us;

import java.io.FileNotFoundException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Set;

import org.gem.engine.hazard.parsers.GemFileParser;
import org.gem.engine.hazard.parsers.nshmp.NshmpGrid2GemSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.util.TectonicRegionType;

public class NewNshmpWusGridData extends GemFileParser {

    // directory for grid seismicity files
    public static String inDir = "nshmp/wus_grids/";

    public NewNshmpWusGridData(double latmin, double latmax, double lonmin,
            double lonmax) throws FileNotFoundException {

        srcDataList = new ArrayList<GEMSourceData>();

        NshmpGrid2GemSourceData gm = null;

        ArrayList<String> inputGridFile = null;

        ArrayList<Double> inputGridFileWeight = new ArrayList<Double>();

        // Extensional WUS
        // gridFile.put(inDir+"EXTmapC.in",0.6667);
        // gridFile.put(inDir+"EXTmapG.in",0.3333);
        inputGridFile = new ArrayList<String>();
        inputGridFileWeight = new ArrayList<Double>();
        inputGridFile.add(inDir + "EXTmapC.in");
        inputGridFileWeight.add(0.6667);
        inputGridFile.add(inDir + "EXTmapG.in");
        inputGridFileWeight.add(0.3333);
        gm =
                new NshmpGrid2GemSourceData(inputGridFile,
                        TectonicRegionType.ACTIVE_SHALLOW, inputGridFileWeight,
                        latmin, latmax, lonmin, lonmax, true);
        srcDataList.addAll(gm.getList());

        // Western United States model
        // gridFile.put(inDir+"WUSmapC.in",0.25);
        // gridFile.put(inDir+"WUSmapG.in",0.25);
        inputGridFile = new ArrayList<String>();
        inputGridFileWeight = new ArrayList<Double>();
        inputGridFile.add(inDir + "WUSmapC.in");
        inputGridFileWeight.add(0.25);
        inputGridFile.add(inDir + "WUSmapG.in");
        inputGridFileWeight.add(0.25);
        gm =
                new NshmpGrid2GemSourceData(inputGridFile,
                        TectonicRegionType.ACTIVE_SHALLOW, inputGridFileWeight,
                        latmin, latmax, lonmin, lonmax, true);
        srcDataList.addAll(gm.getList());

        // nopuget model
        // gridFile.put(inDir+"nopugetC.in",0.25);
        // gridFile.put(inDir+"nopugetG.in",0.25);
        inputGridFile = new ArrayList<String>();
        inputGridFileWeight = new ArrayList<Double>();
        inputGridFile.add(inDir + "nopugetC.in");
        inputGridFileWeight.add(0.25);
        inputGridFile.add(inDir + "nopugetG.in");
        inputGridFileWeight.add(0.25);
        gm =
                new NshmpGrid2GemSourceData(inputGridFile,
                        TectonicRegionType.ACTIVE_SHALLOW, inputGridFileWeight,
                        latmin, latmax, lonmin, lonmax, true);
        srcDataList.addAll(gm.getList());

        // puget model
        // gridFile.put(inDir+"pugetmapC.in",0.25);
        // gridFile.put(inDir+"pugetmapG.in",0.25);
        inputGridFile = new ArrayList<String>();
        inputGridFileWeight = new ArrayList<Double>();
        inputGridFile.add(inDir + "pugetmapC.in");
        inputGridFileWeight.add(0.25);
        inputGridFile.add(inDir + "pugetmapG.in");
        inputGridFileWeight.add(0.25);
        gm =
                new NshmpGrid2GemSourceData(inputGridFile,
                        TectonicRegionType.ACTIVE_SHALLOW, inputGridFileWeight,
                        latmin, latmax, lonmin, lonmax, true);
        srcDataList.addAll(gm.getList());

        // pacific north west deep events
        // gridFile.put(inDir+"pacnwdeep.in",1.0);
        gm =
                new NshmpGrid2GemSourceData(inDir + "pacnwdeep.in",
                        TectonicRegionType.SUBDUCTION_SLAB, 1.0, latmin,
                        latmax, lonmin, lonmax, true);
        srcDataList.addAll(gm.getList());

        // portdeep model
        // gridFile.put(inDir+"portdeep.in",1.0);
        gm =
                new NshmpGrid2GemSourceData(inDir + "portdeep.in",
                        TectonicRegionType.SUBDUCTION_SLAB, 1.0, latmin,
                        latmax, lonmin, lonmax, true);
        srcDataList.addAll(gm.getList());

    }

}
