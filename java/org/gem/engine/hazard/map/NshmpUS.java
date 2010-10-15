package org.gem.engine.hazard.map;

import java.io.IOException;

import org.gem.engine.hazard.models.nshmp.us.NshmpUsData;
import org.opensha.gem.GEM1.calc.gemHazardCalculator.GemComputeModel;
import org.opensha.gem.GEM1.calc.gemLogicTree.gemLogicTreeImpl.gmpe.GemGmpe2;
import org.opensha.gem.GEM1.commons.CalculationSettings;
import org.opensha.gem.GEM1.util.CpuParams;

public class NshmpUS {

    /**
     * @param args
     * @throws ClassNotFoundException
     * @throws IOException
     */
    public static void main(String[] args) throws IOException,
            ClassNotFoundException {

        // model name
        String modelName = "UsModel";

        // region where to compute hazard
        double latmin = 35.0;// 24.6;
        double latmax = 35.0;// 50.0;
        double lonmin = -120;// -125.0;
        double lonmax = -120.0;// -65.5;
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

        // outDir = "/home/damiano/results/";

        boolean outputHazCurve = true;

        // logic tree for gmpes
        // BA2008andMcVerry2000 gmpeLogicTree = new BA2008andMcVerry2000();

        GemGmpe2 gmpeLogicTree = new GemGmpe2();

        // US model
        NshmpUsData model = new NshmpUsData(latmin, latmax, lonmin, lonmax);

        // Ceus grid model
        // NshmpCeusGridData model = new
        // NshmpCeusGridData(latmin,latmax,lonmin,lonmax);

        // WUS fault model
        // NshmpWusFaultData model = new
        // NshmpWusFaultData(latmin,latmax,lonmin,lonmax);

        // WUS grid model
        // NshmpWusGridData model = new
        // NshmpWusGridData(latmin,latmax,lonmin,lonmax);

        // calculation settings
        CalculationSettings calcSet = new CalculationSettings();

        // set point to line source
        // calcSet.getErf().get(SourceType.GRID_SOURCE).put(GEM1ERF.BACK_SEIS_RUP_NAME,GEM1ERF.BACK_SEIS_RUP_LINE);

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
