package org.opensha.gem.GEM1.calc.gemHazardMaps;

import java.io.IOException;

import org.opensha.gem.GEM1.calc.gemHazardCalculator.GemComputeModel;
import org.opensha.gem.GEM1.calc.gemLogicTree.gemLogicTreeImpl.gmpe.GemGmpe;
import org.opensha.gem.GEM1.calc.gemModelData.nshmp.south_america.NshmpSouthAmericaData;
import org.opensha.gem.GEM1.commons.CalculationSettings;
import org.opensha.gem.GEM1.util.CpuParams;
import org.opensha.gem.GEM1.util.DistanceParams;

public class NshmpSouthAmerica {

	public static void main(String[] args) throws IOException, ClassNotFoundException {
		
		// model name
		String modelName = "NshmpSouthAmerica";
		
		
		// region where to compute hazard
//	    double latmin = -18.0;
//	    double latmax = -18.0;
//	    double lonmin = -65.0;
//	    double lonmax = -65.0;
//	    double latmin = -36.2;
//	    double latmax = -32.8;
//	    double lonmin = -77.2;
//	    double lonmax = -76.8;
	    double latmin = -55;
		double latmax = 15;
		double lonmin = -85;
		double lonmax = -30;
//	    double delta = 0.1;
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
//		String outDir = "/Users/damianomonelli/Documents" +
//		"/GEM/USA_USGS/NSHM_2008/";
		String outDir = "/tmp/gem_nshmp/";
		
		//outDir = "/home/damiano/results/";
		
		boolean outputHazCurve = true;
		
		// logic tree for gmpes
		//BA2008andMcVerry2000 gmpeLogicTree = new BA2008andMcVerry2000();
		
		GemGmpe gmpeLogicTree = new GemGmpe();
		
		// US model
		NshmpSouthAmericaData model = new NshmpSouthAmericaData(latmin,latmax,lonmin,lonmax);
		
		// calculation settings
		CalculationSettings calcSet = new CalculationSettings();
		
		// set point to line source
		//calcSet.getErf().get(SourceType.GRID_SOURCE).put(GEM1ERF.BACK_SEIS_RUP_NAME,GEM1ERF.BACK_SEIS_RUP_LINE);
		
		// set number of threads
		calcSet.getOut().put(CpuParams.CPU_NUMBER.toString(),nproc);
		
		System.out.println("Number of sources considered: "+model.getList().size());

		new GemComputeModel(model.getList(), 
				modelName,
				gmpeLogicTree.getGemLogicTree(),
				latmin, latmax, lonmin, lonmax, delta,
				probLevel,
				outDir,
				outputHazCurve,
				calcSet);
		
		System.exit(0);

	}

}
