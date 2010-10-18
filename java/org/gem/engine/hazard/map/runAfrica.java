package org.gem.engine.hazard.map;

import java.io.FileWriter;
import java.io.IOException;

import org.gem.engine.hazard.models.gshap.africa.AfricaData;
import org.opensha.gem.GEM1.calc.gemHazardCalculator.GemComputeModel;
import org.opensha.gem.GEM1.calc.gemLogicTree.gemLogicTreeImpl.gmpe.GemGmpe;
import org.opensha.gem.GEM1.commons.CalculationSettings;
import org.opensha.gem.GEM1.util.CpuParams;

/**
 * This class combines the information obtained for three parsers (to read the
 * input models IberoMagreb, Eastern and Western Africa) and returns a list of
 * GEMAreaSourceData. This info is used to compute the hazard for Africa
 * 
 * @author l.danciu
 */

public class runAfrica {

    /**
     * @param args
     * @throws IOException
     */
    public static void main(String[] args) throws IOException {

        AfricaData africaModel = new AfricaData();

        africaModel.writeAreaSources2KMLfile(new FileWriter(
                "/Users/damianomonelli/Desktop/AfricaSources.kml"));

        System.exit(0);

        // concatenate the models in one Array model
        String modelName = "Africa";

        // region where to compute hazard
        double latmin = 10.00;// 39.0;
        double latmax = 10.00;// 38.0;//39.0;
        double lonmin = 20.00;// -20.0;//-119.8;
        double lonmax = 20.00;// 60.0;//-119.8;
        double delta = 0.1;

        // probability level for computing hazard map
        // first run 10%50years
        double[] probLevel = { 0.02, 0.05, 0.1 };

        // number of threads (cpus) to be used for calculation
        int nproc = 2;

        // output directory (local machine)
        String outDir = "/Users/laurentiudanciu/Documents/workspace/results/";

        // flag for hazard curves output
        boolean outputHazCurve = true;

        // logic tree for gmpes valid for active shallow regions
        GemGmpe gmpeLogicTree = new GemGmpe();

        // calculation settings
        CalculationSettings calcSet = new CalculationSettings();

        // set number of threads
        calcSet.getOut().put(CpuParams.CPU_NUMBER.toString(), nproc);

        // to compute PSA(0.02sec, 1.0sec)
        // calcSet.getOut().put(IntensityMeasureParams.INTENSITY_MEAS_TYPE.toString(),PSA_Params)

        System.out.println("Number of sources considered: "
                + africaModel.getList().size());

        new GemComputeModel(africaModel.getList(), modelName,
                gmpeLogicTree.getGemLogicTree(), latmin, latmax, lonmin,
                lonmax, delta, probLevel, outDir, outputHazCurve, calcSet);

        System.exit(0);

    }
}
