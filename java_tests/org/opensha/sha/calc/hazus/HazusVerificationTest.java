package org.opensha.sha.calc.hazus;


import java.io.FileNotFoundException;
import java.io.IOException;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.StringTokenizer;

import org.junit.Before;
import org.junit.Test;
import org.opensha.commons.geo.Location;
import org.opensha.commons.util.DataUtils;
import org.opensha.commons.util.FileUtils;


public class HazusVerificationTest {
	
	DecimalFormat df = new DecimalFormat("0.0000");

	@Before
	public void setUp() throws Exception {
	}
	
	private HashMap<Location, double[]> loadFile(String fileName) throws FileNotFoundException, IOException {
		HashMap<Location, double[]> file = new HashMap<Location, double[]>();
		
		ArrayList<String> lines = FileUtils.loadFile(fileName);
		
		for (String line : lines) {
			// skip all of the comment/blank lines
			if (line.length() < 5)
				continue;
			if (line.startsWith("#"))
				continue;
			try {
				Integer.parseInt(line.substring(0, 2));
			} catch (NumberFormatException e) {
				continue;
			}
			
			StringTokenizer tok = new StringTokenizer(line, ",");
			
			double lat = Double.parseDouble(tok.nextToken());
			double lon = Double.parseDouble(tok.nextToken());
			double pga = Double.parseDouble(tok.nextToken());
			double pgv = Double.parseDouble(tok.nextToken());
			double sa03 = Double.parseDouble(tok.nextToken());
			double sa10 = Double.parseDouble(tok.nextToken());
			
			double[] result = { pga, pgv, sa03, sa10 };
			Location loc = new Location(lat, lon);
			
			file.put(loc, result);
		}
		
		return file;
	}
	
	private void compareResults(String refFile, String newFile) throws FileNotFoundException, IOException {
		HashMap<Location, double[]> refResults = loadFile(refFile);
		HashMap<Location, double[]> newResults = loadFile(newFile);
		
		double[] maxDiffs = new double[4];
		double[] avgDiffs = new double[4];
		for (int i=0; i<4; i++) {
			maxDiffs[i] = 0;
			avgDiffs[i] = 0;
		}
		
		for (Location loc : refResults.keySet()) {
			double[] refvals = refResults.get(loc);
			double[] newvals = newResults.get(loc);
			
			for (int i=0; i<4; i++) {
				double pdiff = DataUtils.getPercentDiff(newvals[i], refvals[i]);
				avgDiffs[i] += pdiff;
				if (pdiff > maxDiffs[i])
					maxDiffs[i] = pdiff;
			}
		}
		for (int i=0; i<4; i++) {
			avgDiffs[i] /= (double)refResults.keySet().size();
		}
		
		System.out.println("Comparing reference file '" + refFile + "'");
		System.out.println("To new file '" + newFile + "'");
		
		System.out.println("All values are percent differences.");
		System.out.println("PGA:\tavg: " + df.format(avgDiffs[0]) + "% max: " + df.format(maxDiffs[0]) + "%");
		System.out.println("PGV:\tavg: " + df.format(avgDiffs[1]) + "% max: " + df.format(maxDiffs[1]) + "%");
		System.out.println("SA 0.3:\tavg: " + df.format(avgDiffs[2]) + "% max: " + df.format(maxDiffs[2]) + "%");
		System.out.println("SA 1.0:\tavg: " + df.format(avgDiffs[3]) + "% max: " + df.format(maxDiffs[3]) + "%");
	}
	
	@Test
	public void testResults() throws FileNotFoundException, IOException {
		String refDir = "/home/kevin/OpenSHA/hazus/Run1_Grid01_NoSoil/";
		String newDir = "/home/kevin/workspace/OpenSHA_head_refactor/HazusMapDataSets/verify3/";
		
//		String refDir = "/home/kevin/OpenSHA/hazus/Run3b_05grid_soil_withbackgroundseism/";
//		String newDir = "/home/kevin/workspace/OpenSHA_head_refactor/HazusMapDataSets/verify1/";
		
		compareResults(refDir + "final_100.dat", newDir + "final_100.0.dat");
		System.out.println();
		compareResults(refDir + "final_250.dat", newDir + "final_250.0.dat");
		System.out.println();
		compareResults(refDir + "final_500.dat", newDir + "final_500.0.dat");
		System.out.println();
		compareResults(refDir + "final_750.dat", newDir + "final_750.0.dat");
		System.out.println();
		compareResults(refDir + "final_1000.dat", newDir + "final_1000.0.dat");
		System.out.println();
		compareResults(refDir + "final_1500.dat", newDir + "final_1500.0.dat");
		System.out.println();
		compareResults(refDir + "final_2000.dat", newDir + "final_2000.0.dat");
		System.out.println();
		compareResults(refDir + "final_2500.dat", newDir + "final_2500.0.dat");
		System.out.println();
	}

}
