package org.gem.engine.hazard.map;

import java.io.IOException;

import org.gem.engine.hazard.models.gshap.south_east_asia.SeAsiaData;
import org.opensha.gem.GEM1.calc.gemHazardCalculator.GemComputeModel;
import org.opensha.gem.GEM1.calc.gemLogicTree.gemLogicTreeImpl.gmpe.GemGmpe;
import org.opensha.gem.GEM1.commons.CalculationSettings;
import org.opensha.gem.GEM1.util.CpuParams;

public class runSEAsia {

    public static void main(String[] args) throws IOException {

        // model name
        String modelName = "GshapSEA";

        // output directory
        String outDir = "/home/laurentiu/results/";
        outDir = "/Users/laurentiudanciu/Documents/workspace/results/";

        // region where to compute hazard
        double latmin = -5.00;
        double latmax = 65.0;// 60.00;
        double lonmin = 10.0;// 60.00;
        double lonmax = 150.0;// 150.00;
        double delta = 0.1;

        // probability level for computing hazard map
        double[] probLevel = { 0.02, 0.05, 0.1 };

        // number of cpus to be used in the calculations
        int nproc = 30;

        // save hazard curves
        boolean outputHazCurve = true;

        // read model
        SeAsiaData seModel = new SeAsiaData();

        // logic tree for gmpes
        GemGmpe gmpeLogicTree = new GemGmpe();

        // define calculation settings
        CalculationSettings calcSet = new CalculationSettings();

        // set cpu number
        calcSet.getOut().put(CpuParams.CPU_NUMBER.toString(), nproc);

        new GemComputeModel(seModel.getList(), modelName,
                gmpeLogicTree.getGemLogicTree(), latmin, latmax, lonmin,
                lonmax, delta, probLevel, outDir, outputHazCurve, calcSet);

        System.exit(0);

    }
}