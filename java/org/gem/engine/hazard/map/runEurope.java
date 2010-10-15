package org.gem.engine.hazard.map;

import java.io.FileWriter;
import java.io.IOException;

import org.gem.engine.hazard.parsers.europe.newEurope2GemSourceData;
import org.opensha.gem.GEM1.calc.gemHazardCalculator.GemComputeModel;
import org.opensha.gem.GEM1.calc.gemLogicTree.gemLogicTreeImpl.gmpe.GemGmpe;
import org.opensha.gem.GEM1.commons.CalculationSettings;
import org.opensha.gem.GEM1.util.CpuParams;

public class runEurope {

    public static void main(String[] args) throws IOException {

        // european model
        newEurope2GemSourceData europeModel = new newEurope2GemSourceData();

        europeModel.writeAreaSources2KMLfile(new FileWriter(
                "/Users/damianomonelli/Desktop/EuropaSources.kml"));

        System.exit(0);

        // model name
        String modelName = "Europe";

        // ************** output directory ***************//
        // local storage
        String outDir = "/home/laurentiu/results/";
        outDir = "/Users/laurentiudanciu/Documents/workspace/results/";
        // ********************* calculation settings **********************//
        // this class defines default calculation settings
        // if you want to change settings then you have to set the parameter
        // here
        CalculationSettings calcSet = new CalculationSettings();

        // e.g set new value for discretization of area source
        // calcSet.getErf().get(SourceType.AREA_SOURCE).put(GEM1ERF.AREA_DISCR_PARAM_NAME,
        // 0.2);

        // **************** region where to compute hazard ***************//
        double latmin = 36.00;
        double latmax = 38.00;
        double lonmin = 34.00;
        double lonmax = 36.00;
        double delta = 0.1;

        // *********** probability level for computing hazard map *********//
        double[] probLevel = { 0.02, 0.05, 0.1 };

        // **************** logic tree for gmpes************
        GemGmpe gmpeLogicTree = new GemGmpe();

        // ******** number of cpus to be used in the calculations ********//
        int nproc = 2;
        // set number of cpu to be used (default is 1)
        calcSet.getOut().put(CpuParams.CPU_NUMBER.toString(), nproc);

        boolean outputHazCurve = true;

        new GemComputeModel(europeModel.getList(), modelName,
                gmpeLogicTree.getGemLogicTree(), latmin, latmax, lonmin,
                lonmax, delta, probLevel, outDir, outputHazCurve, calcSet);

        System.exit(0);

    }
}