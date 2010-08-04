package org.opensha.gem.GEM1.calc.gemHazardMaps;

import java.io.IOException;

import org.opensha.gem.GEM1.calc.gemHazardCalculator.GemComputeModel;
import org.opensha.gem.GEM1.calc.gemLogicTree.gemLogicTreeImpl.gmpe.GemGmpe;
import org.opensha.gem.GEM1.calc.gemModelParsers.forecastML.ForecastML2GemSourceData;
import org.opensha.gem.GEM1.commons.CalculationSettings;
import org.opensha.gem.GEM1.util.CpuParams;


public class TripleS {

	/**
	 * @param args
	 * @throws IOException 
	 */
	public static void main(String[] args) throws IOException {
		
		// model name
		String modelName = "TripleSGlobalModel";
		
		
		// region where to compute hazard
	    double latmin = 34.5;//-90.0;
	    double latmax = 34.5;//90.0;
	    double lonmin = -118.0;//-180.0;
	    double lonmax = -118.0;//180.0;
	    double delta = 0.5;
	    
		// probability level for computing hazard map
		double[] probLevel = new double[3];
		probLevel[0] = 0.02;
		probLevel[1] = 0.05;
		probLevel[2] = 0.1;
		
	    // number of threads (cpus) to be used for calculation
	    int nproc = 1;
	    
		// output directory (on damiano's mac)
		String outDir = "/Users/damianomonelli/Documents" +
		"/GEM/USA_USGS/NSHM_2008/";
		
		//outDir = "/home/damiano/results/";
		
		boolean outputHazCurve = true;
		
		GemGmpe gmpeLogicTree = new GemGmpe();
		
		ForecastML2GemSourceData model = new ForecastML2GemSourceData("../../data/global_smooth_seismicity/zechar.triple_s.global.rate_forecast.xml");
		
		// calculation settings
		CalculationSettings calcSet = new CalculationSettings();
		
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
