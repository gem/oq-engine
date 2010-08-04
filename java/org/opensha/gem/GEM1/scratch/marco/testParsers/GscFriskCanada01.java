package org.opensha.gem.GEM1.scratch.marco.testParsers;

import java.io.BufferedReader;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;


import org.opensha.commons.geo.Location;
import org.opensha.commons.data.Site;
import org.opensha.gem.GEM1.calc.gemHazardCalculator.GemComputeModel;
import org.opensha.gem.GEM1.calc.gemHazardMaps.GemCalcSetup;
import org.opensha.gem.GEM1.calc.gemLogicTree.GemLogicTree;
import org.opensha.gem.GEM1.calc.gemModelParsers.gscFrisk.canada.GscFriskSourceData03;
import org.opensha.gem.GEM1.util.CpuParams;
import org.opensha.gem.GEM1.util.DistanceParams;

public class GscFriskCanada01 extends GemCalcSetup {

	private static boolean TEST = false;
	private static boolean GMT = false;
	
	public GscFriskCanada01(String inputDir, String outputDir) {
		super(inputDir, outputDir);
	}

	/**
	 * @param args
	 * @throws IOException 
	 */
	public static void main(String[] args) throws IOException {
		
		String inputdir;
		String outputdir;
		String inpuFileName;
		boolean skipComm;
		double minLat, minLon, maxLat, maxLon, grdSpc;

		// Relative path from the GemComputeHazardLogicTree
		inputdir  	= "./../../data/canada/";
		outputdir   = "./../../output/";
		
		// Instantiate Calc Setup
		GscFriskCanada01 clcSetup = new GscFriskCanada01(inputdir,outputdir);
		
		// File names
//		inpuFileName = "eh2005_pga.m"; skipComm = false; minLat = 45.00; maxLat = 85.00; minLon = -125.00; maxLon = -42.00; grdSpc = 0.1; // Eastern Canada // With mlg to mo
//		inpuFileName = "er2005_pga.m"; skipComm = false; minLat = 45.00; maxLat = 85.00; minLon = -125.00; maxLon = -42.00; grdSpc = 0.1; // Eastern Canada // With mlg to mo
		inpuFileName = "wh2005_pga.m"; skipComm = true; minLat = 45.00; maxLat = 85.00; minLon = -125.00; maxLon = -42.00; grdSpc = 0.1; // Eastern Canada // With mlg to mo
		inpuFileName = "wr2005_pga.m"; skipComm = true; minLat = 45.00; maxLat = 85.00; minLon = -125.00; maxLon = -42.00; grdSpc = 0.1; // Eastern Canada // With mlg to mo
//		inpuFileName = "eh2005_pga.m"; skipComm = false; minLat = 47.00; maxLat = 49.50; minLon = -71.00; maxLon = -68.00; grdSpc = 0.1; // Test in eastern Canada // With mlg to mo
//		GemLogicTree gemLT = gscFrisk.getGmpeLT().getGemLogicTree();
		
		// Investigaton Areas
		minLat = 52.00; maxLat = 49.50; minLon = -71.00; maxLon = -68.00; grdSpc = 0.1; // Test in eastern Canada 
		minLat = 50.00; maxLat = 55.00; minLon = -130.00; maxLon = -123.00; grdSpc = 0.1; // Test in western Canada 
		minLat = 47.50; maxLat = 85.00; minLon = -150.00;  maxLon = -110.00; grdSpc = 0.1; // Western Canada
		
		// Buffered reader 
		BufferedReader file = clcSetup.getInputBufferedReader(inpuFileName);
		
		// Parsing
		GscFriskSourceData03 parser = new GscFriskSourceData03(file,skipComm);
		
//		System.exit(0);
		
		// -----------------------------------------------------------------------------------------
		//                                                                            Compute Hazard
		System.out.println("Calculation running");
		
		// Define model name
		String[] xx = inpuFileName.split("_");
		String modelName = "canada_"+xx[0];
		System.out.println("ModelName:"+modelName);
		
		// Writing source GMT - File
		if (GMT) {
			String[] aa = inpuFileName.split("\\.");
			System.out.println(clcSetup.getOutputPath(outputdir)+aa[0]+".gmt");
			parser.writeAreaGMTfile(new FileWriter(clcSetup.getOutputPath(outputdir)+aa[0]+".gmt"));
			System.out.println("GMT creation completed");
			
			System.out.println(clcSetup.getOutputPath(outputdir)+aa[0]+"_faults.gmt");
			parser.writeFaultGMTfile(new FileWriter(clcSetup.getOutputPath(outputdir)+aa[0]+"_faults.gmt"));
			System.out.println("GMT creation completed");
		}
		
		// This a test on the automatic creation of the magnitude-distance filter
//		ArrayList<Double[]> lst = gscFrisk.setUpMDFilter();
//		System.exit(0);
	
		// Adjust Calculation Settings
		HashMap<String,Object> outMap = clcSetup.getcalcSett().getOut();  
		outMap.put(CpuParams.CPU_NUMBER.toString(),30);
		outMap.put(DistanceParams.MAX_DIST_SOURCE.toString(),200.0);
		clcSetup.getcalcSett().setOut(outMap);
		
		// Probabilities of exceedance
		double[] prbEx = {0.1,0.02};
		
		if (TEST){
			
			// Creates a random set of sites - For testing purposes
			int numSites = 50;
			ArrayList<Site> siteList = new ArrayList<Site>();
			for (int i = 0; i < numSites; i++){
				double lon = Math.random() * (maxLon-minLon) + minLon;
				double lat = Math.random() * (maxLat-minLat) + minLat;
				siteList.add(new Site(new Location(lat,lon)));
			}		
			
			// This is for testing purposes 
			GemLogicTree gemLT = clcSetup.getGmpeLT111().getGemLogicTree();
			GemComputeModel gcm = new GemComputeModel(
					parser.getList(), 
					modelName, 
//					clcSetup.getGmpeLT().getGemLogicTree(), 
					gemLT,
					siteList, 
					prbEx, 
					clcSetup.getOutputPath(outputdir), 
					true, clcSetup.getcalcSett());
			
		} else {
			
			System.out.println("pippo");
		
			// Compute hazard
			if (skipComm){
	
				GemComputeModel gcm = new GemComputeModel(
					parser.getList(), 
					modelName, 
					clcSetup.getGmpeLT().getGemLogicTree(),
					minLat, maxLat, minLon, maxLon, grdSpc, 
					prbEx, 
					clcSetup.getOutputPath(outputdir), 
					true, 
					clcSetup.getcalcSett());
			} else {
				GemLogicTree gemLT = clcSetup.getGmpeLT111().getGemLogicTree();
				GemComputeModel gcm = new GemComputeModel(
					parser.getList(), 
					modelName, 
					gemLT,
					minLat, maxLat, minLon, maxLon, grdSpc, 
					prbEx, 
					clcSetup.getOutputPath(outputdir), 
					true, 
					clcSetup.getcalcSett());	
			}
		}
		
		System.out.println("Calculation Completed");	
		System.exit(0);
	}

}
