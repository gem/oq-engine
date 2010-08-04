package org.opensha.sha.calc.hazus.parallel;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.util.ClassUtils;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.calc.hazardMap.HazardDataSetLoader;

public class HazusDataSetAssmbler {
	
	public static final String METADATA_RP_REPLACE_STR = "$RETURN_PERIOD";
	public static final String METADATA_RP_REGEX_REPLACE_STR = "\\"+METADATA_RP_REPLACE_STR;
	
	public static DecimalFormat df = new DecimalFormat("0.000000");
	
	HashMap<Location, ArbitrarilyDiscretizedFunc> pgaCurves;
	HashMap<Location, ArbitrarilyDiscretizedFunc> pgvCurves;
	HashMap<Location, ArbitrarilyDiscretizedFunc> sa03Curves;
	HashMap<Location, ArbitrarilyDiscretizedFunc> sa10Curves;
	
	ArrayList<String> metadata = null;
	
	public HazusDataSetAssmbler(String hazardMapDir) throws IOException {
		this(hazardMapDir + File.separator + "imrs1", hazardMapDir + File.separator + "imrs2",
				hazardMapDir + File.separator + "imrs3", hazardMapDir + File.separator + "imrs4");
	}
	
	public HazusDataSetAssmbler(String pgaDir, String pgvDir, String sa03Dir, String sa10Dir) throws IOException {
		System.out.println("Loading PGA curves");
		pgaCurves = HazardDataSetLoader.loadDataSet(new File(pgaDir));
		System.out.println("Loading PGV curves");
		pgvCurves = HazardDataSetLoader.loadDataSet(new File(pgvDir));
		System.out.println("Loading SA 0.3s curves");
		sa03Curves = HazardDataSetLoader.loadDataSet(new File(sa03Dir));
		System.out.println("Loading SA 1.0s curves");
		sa10Curves = HazardDataSetLoader.loadDataSet(new File(sa10Dir));
	}
	
	public void loadMetadataFile(String fileName) throws IOException {
		metadata = FileUtils.loadFile(fileName, false);
	}
	
	private boolean hasMetadata() {
		return metadata != null && !metadata.isEmpty();
	}
	
	private void writeMetadata(String fileName) throws IOException {
		FileWriter fw = new FileWriter(fileName);
		
		for (String line : metadata) {
			line = line.trim();
			// skip the RP line
			if (line.contains(METADATA_RP_REPLACE_STR))
				line = "";
			fw.write(line + "\n");
		}
		
		fw.close();
	}
	
	public HashMap<Location, double[]> assemble(double returnPeriod, int years) {
		HashMap<Location, double[]> results = new HashMap<Location, double[]>();
		for (Location loc : pgaCurves.keySet()) {
			double pgaVal = getValFromCurve(pgaCurves.get(loc), returnPeriod, years);
			double pgvVal = getValFromCurve(pgvCurves.get(loc), returnPeriod, years);
			double sa03Val = getValFromCurve(sa03Curves.get(loc), returnPeriod, years);
			double sa10Val = getValFromCurve(sa10Curves.get(loc), returnPeriod, years);
			
			double[] result = { pgaVal, pgvVal, sa03Val, sa10Val };
			results.put(loc, result);
		}
		return results;
	}
	
	public void writeFile(String fileName, HashMap<Location, double[]> results, double returnPeriod)
	throws IOException {
		FileWriter fw = new FileWriter(fileName);
		if (metadata != null) {
			for (String line : metadata) {
				line = line.replaceAll(METADATA_RP_REGEX_REPLACE_STR, returnPeriod+"").trim();
				if (!line.startsWith("#"))
					line = "#" + line;
				fw.write(line + "\n");
			}
		}
		fw.write("#Column Info: Lat,Lon,PGA,PGV,SA-0.3,SA-1" + "\n");
		for (Location loc : results.keySet()) {
			double[] result = results.get(loc);
			
			String line = df.format(loc.getLatitude()) + "," + df.format(loc.getLongitude());
			
			for (int i=0; i<4; i++) {
				double val = result[i];
				if (Double.isNaN(val))
					line += ",NaN";
				else
					line += "," + df.format(val);
			}
			
//			String line = df.format(loc.getLatitude()) + "," + df.format(loc.getLongitude())
//					+ "," + df.format(result[0]) + "," + df.format(result[1])
//					+ "," + df.format(result[2]) + "," + df.format(result[3]);
			fw.write(line + "\n");
		}
		fw.close();
	}
	
	public static void writeSitesFile(String fileName, Collection<Location> locs) throws IOException {
		double minLat = LocationList.calcMinLat(locs);
		double maxLat = LocationList.calcMaxLat(locs);
		double minLon = LocationList.calcMinLon(locs);
		double maxLon = LocationList.calcMaxLon(locs);
		double latSpacing = Double.MAX_VALUE;
		double lonSpacing = Double.MAX_VALUE;
		for (Location loc : locs) {
			double myLatSpacing = loc.getLatitude() - minLat;
			double myLonSpacing = loc.getLongitude() - minLon;
			if (myLatSpacing > 0 && myLatSpacing < latSpacing)
				latSpacing = myLatSpacing;
			if (myLonSpacing > 0 && myLonSpacing < lonSpacing)
				lonSpacing = myLonSpacing;
		}
		FileWriter fw = new FileWriter(fileName);
		fw.write((float)minLat + " " + (float)maxLat + " " + (float)latSpacing + "\n");
		fw.write((float)minLon + " " + (float)maxLon + " " + (float)lonSpacing + "\n");
		fw.close();
	}
	
	private static double getValFromCurve(ArbitrarilyDiscretizedFunc curve, double returnPeriod, int years) {
		double probVal = ((double)years) / returnPeriod;
		try {
			return curve.getFirstInterpolatedX_inLogXLogYDomain(probVal);
		} catch (Exception e) {
			return Double.NaN;
		}
	}
	
	public static void main(String args[]) throws IOException {
		String dataDir = null;
		String metadataFile = null;
		int years = -1;
		if (args.length == 0) {
			System.err.println("WARNING: Running with hardcoded paths!");
			dataDir = "/home/kevin/OpenSHA/hazus/ca_0.1_test/curves";
			years = 30;
		} else if (args.length == 2 || args.length == 3) {
			dataDir = args[0];
			years = Integer.parseInt(args[1]);
			if (args.length == 3) {
				metadataFile = args[2];
			}
		} else {
			String cname = ClassUtils.getClassNameWithoutPackage(HazusDataSetAssmbler.class);
			System.out.println("USAGE: " + cname + " <dataDir> <years> [<metadataFile>]");
			System.exit(2);
		}
		if (!(new File(dataDir).exists()))
			throw new FileNotFoundException("Data dir doesn't exist: " + dataDir);
		if (years < 1)
			throw new IllegalArgumentException("Years must be >= 1");
		
		HazusDataSetAssmbler assem = new HazusDataSetAssmbler(dataDir);
		
		if (metadataFile != null)
			assem.loadMetadataFile(metadataFile);
		
		HashMap<Location, double[]> results = null;
		String fileName;
		
		ArrayList<String> fileNames = new ArrayList<String>();
		
		int[] rps = { 100, 250, 500, 750, 1000, 1500, 2000, 2500 };
		
		for (int rp : rps) {
			results = assem.assemble(rp, years);
			fileName = "final_" + rp + ".dat";
			assem.writeFile(dataDir+"/"+fileName, results, rp);
			fileNames.add(fileName);
		}
		
		fileName = "sites.dat";
		writeSitesFile(dataDir+"/"+fileName, results.keySet());
		fileNames.add(fileName);
		
		if (assem.hasMetadata()) {
			fileName = "metadata.dat";
			assem.writeMetadata(dataDir+"/"+fileName);
			fileNames.add(fileName);
		}
		
		String zipFile = dataDir + "/hazus.zip";
		FileUtils.createZipFile(zipFile, dataDir, fileNames);
	}

}
