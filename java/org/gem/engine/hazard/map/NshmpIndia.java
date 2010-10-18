package org.gem.engine.hazard.map;

import java.io.IOException;

import org.gem.engine.hazard.models.nshmp.india.NshmpIndiaGridData;
import org.opensha.gem.GEM1.calc.gemHazardCalculator.GemComputeModel;
import org.opensha.gem.GEM1.calc.gemLogicTree.gemLogicTreeImpl.gmpe.GemGmpe2;
import org.opensha.gem.GEM1.commons.CalculationSettings;
import org.opensha.gem.GEM1.util.CpuParams;
import org.opensha.gem.GEM1.util.SourceType;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.GEM1ERF;

public class NshmpIndia {

    /**
     * @param args
     * @throws IOException
     */
    public static void main(String[] args) throws IOException {

        // model name
        String modelName = "NshmpIndia";

        // region where to compute hazard
        double latmin = 10.0;
        double latmax = 26.0;
        double lonmin = 68.0;
        double lonmax = 90.0;
        double delta = 0.1;

        // probability level for computing hazard map
        double[] probLevel = new double[3];
        probLevel[0] = 0.02;
        probLevel[1] = 0.05;
        probLevel[2] = 0.1;

        // number of threads (cpus) to be used for calculation
        int nproc = 30;

        // local storage
        String outDir = "/home/laurentiu/results/";
        outDir = "/Users/laurentiudanciu/Documents/workspace/results/";

        boolean outputHazCurve = true;

        // logic tree for gmpes

        GemGmpe2 gmpeLogicTree = new GemGmpe2();

        NshmpIndiaGridData model =
                new NshmpIndiaGridData(latmin, latmax, lonmin, lonmax);

        // calculation settings
        CalculationSettings calcSet = new CalculationSettings();

        // set point to line source
        calcSet.getErf()
                .get(SourceType.GRID_SOURCE)
                .put(GEM1ERF.GRIDDED_SEIS_RUP_TYPE_NAME,
                        GEM1ERF.GRIDDED_SEIS_RUP_TYPE_LINE);

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
