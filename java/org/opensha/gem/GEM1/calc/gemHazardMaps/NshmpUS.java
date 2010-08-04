package org.opensha.gem.GEM1.calc.gemHazardMaps;

import java.io.IOException;

import org.opensha.gem.GEM1.calc.gemHazardCalculator.GemComputeModel;
import org.opensha.gem.GEM1.calc.gemLogicTree.gemLogicTreeImpl.gmpe.GemGmpe;
import org.opensha.gem.GEM1.calc.gemModelData.nshmp.us.NshmpUsData;
import org.opensha.gem.GEM1.commons.CalculationSettings;
import org.opensha.gem.GEM1.util.CpuParams;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.GEM1ERF;
import org.opensha.sha.util.TectonicRegionType;

public class NshmpUS {

	/**
	 * @param args
	 * @throws ClassNotFoundException 
	 * @throws IOException 
	 */
	public static void main(String[] args) throws IOException, ClassNotFoundException {
		
		// model name
		String modelName = "USModel";
		
		// region where to compute hazard
	    double latmin = 34.5;//24.6;
	    double latmax = 34.5;//50.0;
	    double lonmin = -118.0;//-125.0;
	    double lonmax = -118.0;//-65.0;
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
		String outDir = "/Users/damianomonelli/Documents" +
		"/GEM/USA_USGS/NSHM_2008/";
		
		//outDir = "/home/damiano/results/";
		
		boolean outputHazCurve = true;
		
		GemGmpe gmpeLogicTree = new GemGmpe();
		
		// US model
		NshmpUsData model = new NshmpUsData(latmin,latmax,lonmin,lonmax);
		
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
