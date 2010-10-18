package org.gem.engine.hazard.map;

import java.io.IOException;

import org.gem.engine.hazard.models.nshmp.alaska.NshmpAlaskaData;
import org.opensha.gem.GEM1.calc.gemHazardCalculator.GemComputeModel;
import org.opensha.gem.GEM1.calc.gemLogicTree.gemLogicTreeImpl.gmpe.GemGmpe;
import org.opensha.gem.GEM1.commons.CalculationSettings;
import org.opensha.gem.GEM1.util.CpuParams;

public class NshmpAlaska {

    public static void main(String[] args) throws IOException,
            ClassNotFoundException {

        // model name
        String modelName = "NshmpAlaska";

        // region where to compute hazard
        double latmin = 55.0;// 48.0;
        double latmax = 55.0;// 72.0;
        double lonmin = -200.0;
        double lonmax = -200.0;// -125.0;
        double delta = 10.0;

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

        // outDir = "/home/damiano/results/";

        boolean outputHazCurve = true;

        // logic tree for gmpes
        // BA2008andMcVerry2000 gmpeLogicTree = new BA2008andMcVerry2000();

        GemGmpe gmpeLogicTree = new GemGmpe();

        // US model
        NshmpAlaskaData model =
                new NshmpAlaskaData(latmin, latmax, lonmin, lonmax);

        // calculation settings
        CalculationSettings calcSet = new CalculationSettings();

        // set point to line source
        // calcSet.getErf().get(SourceType.GRID_SOURCE).put(GEM1ERF.BACK_SEIS_RUP_NAME,GEM1ERF.BACK_SEIS_RUP_LINE);

        // set number of threads
        calcSet.getOut().put(CpuParams.CPU_NUMBER.toString(), nproc);

        // set maximum distance to source
        // calcSet.getOut().put(DistanceParams.MAX_DIST_SOURCE.toString(),
        // 1000.0);

        System.out.println("Number of sources considered: "
                + model.getList().size());

        new GemComputeModel(model.getList(), modelName,
                gmpeLogicTree.getGemLogicTree(), latmin, latmax, lonmin,
                lonmax, delta, probLevel, outDir, outputHazCurve, calcSet);

        System.exit(0);

    }

}
