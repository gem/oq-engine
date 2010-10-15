package org.gem.engine.hazard.models.nshmp.alaska;

import java.io.FileNotFoundException;
import java.util.HashMap;

import org.gem.engine.hazard.parsers.GemFileParser;

public class NshmpAlaskaGridData extends GemFileParser {

    private String inDir = "data/nshmp/alaska/grid/";

    public NshmpAlaskaGridData(double latmin, double latmax, double lonmin,
            double lonmax) throws FileNotFoundException {

        // hash map containing grid file with corresponding weight
        HashMap<String, Double> gridFile = new HashMap<String, Double>();

        gridFile.put(inDir + "AKDEEP.out_revF.in", 1.0);

        gridFile.put(inDir + "AKDEEPER.out_revF.in", 1.0);

        gridFile.put(inDir + "AKML75.out_revF.in", 1.0);

        gridFile.put(inDir + "AKMT.out_revF.in", 1.0);

    }

}
