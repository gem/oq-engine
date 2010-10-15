package org.gem.engine.hazard.models.nshmp.india;

import java.io.FileNotFoundException;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.Hashtable;
import java.util.Iterator;
import java.util.Set;

import org.gem.engine.hazard.parsers.GemFileParser;
import org.gem.engine.hazard.parsers.nshmp.NshmpGrid2GemSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.util.TectonicRegionType;

public class NshmpIndiaGridData extends GemFileParser implements Serializable {

    // directory for grid seismicity files
    private String inDir = "../../data/nshmp/india/";

    // the following files should be in the india input folder together with the
    // agrid files;
    // ec.hazgridXnga.in
    // epm.hazgridXnga.in
    // gg.hazgridXnga.in
    // mg.hazgridXnga.in
    // nc.hazgridXnga.in
    // nl.hazgridXnga.in
    // rok.hazgridXnga.in
    // sc.hazgridXnga.in
    // wpm.hazgridXnga.in
    // ec.a
    // epm.a
    // gg.a
    // mg.a
    // nc.a
    // nl.a
    // rok.a
    // sc.a
    // wpm.a

    public NshmpIndiaGridData(double latmin, double latmax, double lonmin,
            double lonmax) throws FileNotFoundException {

        srcDataList = new ArrayList<GEMSourceData>();

        // ArrayList<String> file = new ArrayList<String>();
        // ArrayList<Double> weight = new ArrayList<Double>();

        // hash map containing grid file with corresponding weight
        Hashtable<String, Double> gridFile = new Hashtable<String, Double>();

        // ec.pga.out
        // weight = 1.000
        gridFile.put(inDir + "ec.hazgridXnga.in", 1.000);

        // epm.pga.out
        // weight = 1.000
        gridFile.put(inDir + "epm.hazgridXnga.in", 1.000);

        // gg.pga.out
        // weight = 1.000
        gridFile.put(inDir + "gg.hazgridXnga.in", 1.000);

        // mg.pga.out
        // weight = 1.000
        gridFile.put(inDir + "mg.hazgridXnga.in", 1.000);

        // nc.pga.out
        // weight = 1.000
        gridFile.put(inDir + "nc.hazgridXnga.in", 1.000);

        // nl.pga.out
        // weight = 1.000
        gridFile.put(inDir + "nl.hazgridXnga.in", 1.000);

        // rok.pga.out
        // weight = 1.000
        gridFile.put(inDir + "rok.hazgridXnga.in", 1.000);

        // sc.pga.out
        // weight = 1.000
        gridFile.put(inDir + "sc.hazgridXnga.in", 1.000);

        // wpm.pga.nmc
        // weight = 1.000
        gridFile.put(inDir + "wpm.hazgridXnga.in", 1.000);

        // iterator over files
        Set<String> fileName = gridFile.keySet();
        Iterator<String> iterFileName = fileName.iterator();
        while (iterFileName.hasNext()) {
            String key = iterFileName.next();
            System.out.println("Processing file: " + key + ", weight: "
                    + gridFile.get(key));
            NshmpGrid2GemSourceData gm = null;
            gm =
                    new NshmpGrid2GemSourceData(key,
                            TectonicRegionType.STABLE_SHALLOW,
                            gridFile.get(key), latmin, latmax, lonmin, lonmax,
                            true);
            for (int i = 0; i < gm.getList().size(); i++)
                srcDataList.add(gm.getList().get(i));
        }

    }
}
