package org.gem.engine.hazard.map;

import java.io.IOException;

import org.gem.engine.hazard.parsers.ecuador.ecuador2GemSourceData;
import org.opensha.gem.GEM1.calc.gemHazardCalculator.GemComputeModel;
import org.opensha.gem.GEM1.calc.gemLogicTree.gemLogicTreeImpl.gmpe.GemGmpe2;
import org.opensha.gem.GEM1.commons.CalculationSettings;
import org.opensha.gem.GEM1.util.CpuParams;
import org.opensha.gem.GEM1.util.SourceType;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.GEM1ERF;

public class Ecuador {

    public static void main(String[] args) throws IOException {

        // model name
        String modelName = "Ecuador";

        // region where to compute hazard
        double latmin = -7.0;
        double latmax = 5.0;
        double lonmin = -83.0;
        double lonmax = -75.0;
        double delta = 0.1;

        // probability level for computing hazard map
        double[] probLevel = new double[1];
        probLevel[0] = 0.1;

        // number of threads (cpus) to be used for calculation
        int nproc = 1;

        // output directory (on damiano's mac)
        // for US model
        String outDir = "/Users/damianomonelli/Desktop/";

        // outDir = "/home/damiano/results/";

        boolean outputHazCurve = true;

        // gmpe
        GemGmpe2 gmpeLogicTree = new GemGmpe2();

        // calculation settings
        CalculationSettings calcSet = new CalculationSettings();

        // read model for ecuador
        ecuador2GemSourceData model = new ecuador2GemSourceData();

        // set number of threads
        calcSet.getOut().put(CpuParams.CPU_NUMBER.toString(), nproc);

        // set area discretization
        calcSet.getErf().get(SourceType.AREA_SOURCE)
                .put(GEM1ERF.AREA_SRC_DISCR_PARAM_NAME, 0.05);

        System.out.println("Number of sources considered: "
                + model.getList().size());

        new GemComputeModel(model.getList(), modelName,
                gmpeLogicTree.getGemLogicTree(), latmin, latmax, lonmin,
                lonmax, delta, probLevel, outDir, outputHazCurve, calcSet);

        System.exit(0);

    }

}
