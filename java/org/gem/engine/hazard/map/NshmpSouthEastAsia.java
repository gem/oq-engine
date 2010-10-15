package org.gem.engine.hazard.map;

import java.io.IOException;

import org.gem.engine.hazard.models.nshmp.south_east_asia.NshmpSouthEastAsiaData;
import org.opensha.gem.GEM1.calc.gemHazardCalculator.GemComputeModel;
import org.opensha.gem.GEM1.calc.gemLogicTree.gemLogicTreeImpl.gmpe.GemGmpe;
import org.opensha.gem.GEM1.commons.CalculationSettings;
import org.opensha.gem.GEM1.util.CpuParams;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.GEM1ERF;

public class NshmpSouthEastAsia {

    /**
     * @param args
     * @throws IOException
     */
    public static void main(String[] args) throws IOException {

        // model name
        String modelName = "NshmpSouthEastAsia";

        // region where to compute hazard
        double latmin = -3.0;
        double latmax = -3.0;
        double lonmin = 102.0;// -125.0;//-119.8;
        double lonmax = 102.0;// -100.0;//-119.8;
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
        String outDir =
                "/Users/damianomonelli/Documents" + "/GEM/USA_USGS/NSHM_2008/";

        boolean outputHazCurve = true;

        // logic tree for gmpes
        // BA2008andMcVerry2000 gmpeLogicTree = new BA2008andMcVerry2000();

        GemGmpe gmpeLogicTree = new GemGmpe();

        NshmpSouthEastAsiaData model =
                new NshmpSouthEastAsiaData(latmin, latmax, lonmin, lonmax);

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
