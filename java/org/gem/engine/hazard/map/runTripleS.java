package org.gem.engine.hazard.map;

import java.io.IOException;

import org.gem.engine.hazard.parsers.forecastML.ForecastML2GemSourceData;
import org.opensha.gem.GEM1.calc.gemHazardCalculator.GemComputeModel;
import org.opensha.gem.GEM1.calc.gemLogicTree.gemLogicTreeImpl.gmpe.GemGmpe;
import org.opensha.gem.GEM1.commons.CalculationSettings;
import org.opensha.gem.GEM1.util.CpuParams;

public class runTripleS {

    /**
     * @param args
     * @throws IOException
     */
    public static void main(String[] args) throws IOException {

        // model name
        String modelName = "TripleSGlobalModel";

        // region where to compute hazard
        double latmin = -90.0;
        double latmax = 90.0;
        double lonmin = -180.0;
        double lonmax = 180.0;
        double delta = 10.0;

        // probability level for computing hazard map
        double[] probLevel = new double[3];
        probLevel[0] = 0.02;
        probLevel[1] = 0.05;
        probLevel[2] = 0.1;

        // number of threads (cpus) to be used for calculation
        int nproc = 30;

        // output directory (on damiano's mac)
        String outDir =
                "/Users/damianomonelli/Documents" + "/GEM/USA_USGS/NSHM_2008/";

        // outDir = "/home/damiano/results/";

        boolean outputHazCurve = true;

        GemGmpe gmpeLogicTree = new GemGmpe();

        ForecastML2GemSourceData model =
                new ForecastML2GemSourceData(
                        "global_smooth_seismicity/zechar.triple_s.global.rate_forecast.xml");

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
