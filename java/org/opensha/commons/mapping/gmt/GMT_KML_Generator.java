/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with
 * the Southern California Earthquake Center (SCEC, http://www.scec.org)
 * at the University of Southern California and the UnitedStates Geological
 * Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ******************************************************************************/

package org.opensha.commons.mapping.gmt;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.opensha.commons.mapping.gmt.raster.RasterExtractor;
import org.opensha.commons.util.FileUtils;

public class GMT_KML_Generator {
	
	String psFile;
	double minLat;
	double minLon;
	double maxLat;
	double maxLon;
	
	public GMT_KML_Generator(String psFile, double minLat, double maxLat,
			double minLon, double maxLon) {
		this.psFile = psFile;
		this.minLat = minLat;
		this.minLon = minLon;
		this.maxLat = maxLat;
		this.maxLon = maxLon;
	}
	
	private void extract(String pngFile) throws FileNotFoundException, IOException {
		RasterExtractor raster = new RasterExtractor(psFile, pngFile);
		raster.writePNG();
	}
	
	private void writeKML(String kmlFileName, String imgFile) throws IOException {
		FileWriter fw = new FileWriter(kmlFileName);
		fw.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>"+"\n");
		fw.write("<kml xmlns=\"http://earth.google.com/kml/2.2\">"+"\n");
		fw.write("  <Folder>"+"\n");
		fw.write("    <name>OpenSHA Hazard Maps</name>"+"\n");
		fw.write("    <description>Open Seismic Hazard Analysis</description>"+"\n");
		fw.write("    <GroundOverlay>"+"\n");
		fw.write("      <name>Hazard Map</name>"+"\n");
		fw.write("      <description></description>"+"\n");
		fw.write("      <Icon>"+"\n");
		fw.write("        <href>" + imgFile + "</href>"+"\n");
		fw.write("      </Icon>"+"\n");
		fw.write("      <LatLonBox>"+"\n");
		fw.write("        <north>" + maxLat + "</north>"+"\n");
		fw.write("        <south>" + minLat + "</south>"+"\n");
		fw.write("        <east>" + maxLon + "</east>"+"\n");
		fw.write("        <west>" + minLon + "</west>"+"\n");
		fw.write("        <rotation>0</rotation>"+"\n");
		fw.write("      </LatLonBox>"+"\n");
		fw.write("    </GroundOverlay>"+"\n");
		fw.write("  </Folder>"+"\n");
		fw.write("</kml>"+"\n");
		fw.write(""+"\n");
		
		fw.flush();
		fw.close();
	}
	
	public void makeKMZ(String kmzFileName) throws FileNotFoundException, IOException {
		File kmzFile = new File(kmzFileName);
		
		String parent = kmzFile.getParent();
		if (parent == null)
			throw new IllegalArgumentException("KMZ file doesn't have a parent!");
		if (!parent.endsWith(File.separator))
			parent += File.separator;
		
		ArrayList<String> zipFiles = new ArrayList<String>();
		
		String pngFileName = "map.png";
		String absPNGFileName = parent + pngFileName;
		extract(absPNGFileName);
		zipFiles.add(pngFileName);
		
		String kmlFileName = "map.kml";
		String absKMLFileName = parent + kmlFileName;
		writeKML(absKMLFileName, pngFileName);
		zipFiles.add(kmlFileName);
		
		FileUtils.createZipFile(kmzFileName, parent, zipFiles);
		
		for (String fileName : zipFiles) {
			new File(parent + fileName).delete();
		}
	}
	
	public static double[] decodeGMTRegion(String reg) {
		String newReg = reg.substring(2);
		StringTokenizer tok = new StringTokenizer(newReg, "/");
		if (tok.countTokens() != 4)
			throw new RuntimeException("Invalid region string: " + reg);
		double bounds[] = new double[4];
		bounds[0] = Double.parseDouble(tok.nextToken());
		bounds[1] = Double.parseDouble(tok.nextToken());
		bounds[2] = Double.parseDouble(tok.nextToken());
		bounds[3] = Double.parseDouble(tok.nextToken());
		
		return bounds;
	}

	/**
	 * @param args
	 * @throws IOException 
	 * @throws FileNotFoundException 
	 */
	public static void main(String[] args) throws FileNotFoundException, IOException {
		String psFile = null;
		String kmzFile = null;
		double minLat = 0;
		double maxLat = 0;
		double minLon = 0;
		double maxLon = 0;
		
		if (args.length == 6) {
			psFile = args[0];
			kmzFile = args[1];
			minLat = Double.parseDouble(args[2]);
			maxLat = Double.parseDouble(args[3]);
			minLon = Double.parseDouble(args[4]);
			maxLon = Double.parseDouble(args[5]);
		} else if (args.length == 3 && args[2].startsWith("-R")) {
			psFile = args[0];
			kmzFile = args[1];
			double bounds[] = decodeGMTRegion(args[2]);
			minLon = bounds[0];
			maxLon = bounds[1];
			minLat = bounds[2];
			maxLat = bounds[3];
		} else {
			System.err.println("USAGE: GMT_KML_Generator ps_file kmz_file minLat maxLat minLon maxLon");
			System.err.println("\t-- OR --");
			System.err.println("USAGE: GMT_KML_Generator ps_file kmz_file -R<minLon>/<maxLon>/<minLat>/<maxLat>");
			System.exit(2);
		}
		
		GMT_KML_Generator gen = new GMT_KML_Generator(psFile, minLat, maxLat, minLon, maxLon);
		
		gen.makeKMZ(kmzFile);
	}

}
