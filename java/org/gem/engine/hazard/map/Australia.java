package org.gem.engine.hazard.map;

import java.io.FileWriter;
import java.io.IOException;

import org.gem.CalculationSettings;
import org.gem.engine.hazard.GemComputeModel;
import org.gem.engine.hazard.GemGmpe2;
import org.gem.engine.hazard.parsers.australia.australia2GemSourceData;
import org.gem.params.CpuParams;

public class Australia {

    /**
     * @param args
     * @throws IOException
     */
    public static void main(String[] args) throws IOException {

        // model name
        String modelName = "Australia";

        // region where to compute hazard
        double latmin = -21.00;
        double latmax = -19.00;
        double lonmin = 132.5;
        double lonmax = 134.5;
        double delta = 0.1;

        // probability level for computing hazard map
        double[] probLevel = new double[3];
        probLevel[0] = 0.02;
        probLevel[1] = 0.05;
        probLevel[2] = 0.1;

        // number of threads (cpus) to be used for calculation
        int nproc = 1;

        // output directory (on damiano's mac)
        // for US model
        String outDir = "/Users/damianomonelli/Documents/GEM/";

        // outDir = "/home/damiano/results/";

        boolean outputHazCurve = true;

        GemGmpe2 gmpeLogicTree = new GemGmpe2();

        // australia model
        australia2GemSourceData model = new australia2GemSourceData();

        model.writeAreaSources2KMLfile(new FileWriter(
                "/Users/damianomonelli/Desktop/AustraliaSource.kml"));

        // calculation settings
        CalculationSettings calcSet = new CalculationSettings();

        // set number of threads
        calcSet.getOut().put(CpuParams.CPU_NUMBER.toString(), nproc);

        System.out.println("Number of sources considered: "
                + model.getList().size());

        new GemComputeModel(model.getList(), modelName,
                gmpeLogicTree.getGemLogicTree(), latmin, latmax, lonmin,
                lonmax, delta, probLevel, outDir, outputHazCurve, calcSet);

        System.exit(0);

    }

}
