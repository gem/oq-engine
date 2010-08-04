/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.data.NearCA_NSHMP;

import java.io.FileWriter;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.opensha.commons.data.region.CaliforniaRegions;
import org.opensha.commons.geo.Location;
import org.opensha.commons.util.FileUtils;

/**
 * Make Non CA faults file from the combined files given by NSHMP. 
 * The files were received on Aug 29, 2007 at 12:49 PM from Steve Harmsen
 * 
 *  
 * @author vipingupta
 *
 */
public class MakeNonCA_File {
	private final static String PATH = "org/opensha/sha/earthquake/rupForecastImpl/WGCEP_UCERF_2_3/data/NearCA_NSHMP/";
	private CaliforniaRegions.RELM_GRIDDED relmRegion = new CaliforniaRegions.RELM_GRIDDED();
	private final static String OUT_FILE = "NonCA_Faults.txt";

	public MakeNonCA_File() {
		try {
			FileWriter fw = new FileWriter(PATH+OUT_FILE); // Non-CA Char file
			processFile("azz.65", fw);
			processFile("nv.65.aug", fw);
			processFile("orwa.65.aug", fw);
			processFile("azc", fw);
			processFile("azgr", fw);
			processFile("nv.char", fw);
			processFile("nv.gr", fw);
			processFile("orwa.new.char", fw);
			processFile("orwa.new.gr", fw);
			fw.close();
		}catch(Exception e) {
			e.printStackTrace();
		}
	}

	/**
	 * Process Non CA  File from NSMP
	 * 
	 * @param fileName
	 * @param fw
	 */
	private void processFile(String fileName, FileWriter fw) {
		int i=0;
		try {
			// read the NSHMP format file
			ArrayList<String> fileLines = FileUtils.loadFile(PATH+fileName);
			int numLines = fileLines.size();
			double latitude, longitude;
			while(i<numLines) {
				ArrayList<String> faultLines = new ArrayList<String>();
				faultLines.add(fileLines.get(i++));
				faultLines.add(fileLines.get(i++));
				faultLines.add(fileLines.get(i++));
				faultLines.add(fileLines.get(i++));
				int numTracePoints = Integer.parseInt(faultLines.get(3).trim());
				boolean isFaultInsideRELM = false;
				for(int locIndex = 0; locIndex<numTracePoints; ++locIndex) {
					String locLine = fileLines.get(i++);
					faultLines.add(locLine);
					StringTokenizer tokenizer = new StringTokenizer(locLine);
					latitude = Double.parseDouble(tokenizer.nextToken().trim());
					longitude = Double.parseDouble(tokenizer.nextToken().trim());
					if(relmRegion.contains(new Location(latitude, longitude)))  isFaultInsideRELM = true;
				}

				if(!isFaultInsideRELM) continue; // if this fault does not lie in RELM region, then move to next fault

				System.out.println(faultLines.get(0));
				// if it lies in RELM region, write to a file
				for(int lineIndex=0; lineIndex<faultLines.size(); ++lineIndex)
					fw.write(faultLines.get(lineIndex)+"\n");

			} 
		}catch(Exception e) {
			e.printStackTrace();
		}
	}

	public static void main(String args[]) {
		new MakeNonCA_File();
	}

}
