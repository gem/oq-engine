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

package org.opensha.sha.calc.IM_EventSet.v03.outputImpl;

import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.opensha.commons.util.FileUtils;
import org.opensha.sha.calc.IM_EventSet.v03.IM_EventSetOutputWriter;

/**
 * This class represents a segment (constant ERF, site, imr, and imt) of a HAZ01A file
 * 
 * @author kevin
 *
 */
public class HAZ01ASegment {
	private String erf;
	private int siteID;
	private String imr;
	private String imt;
	private ArrayList<Integer> sourceIDs = null;
	private ArrayList<Integer> rupIDs = null;
	private ArrayList<Double> vs30Vals = null;
	private ArrayList<Double> distVals = null;
	private ArrayList<Double> meanVals = null;
	private ArrayList<Double> stdDevVals = null;
	private ArrayList<Double> interStdDevVals = null;
	
	private boolean listsInitialized = false;
	
	public HAZ01ASegment(String erf, int siteID, String imr, String imt) {
		this.erf = erf;
		this.siteID = siteID;
		this.imr = imr;
		this.imt = imt;
	}
	
	public String getErf() {
		return erf;
	}
	public int getSiteID() {
		return siteID;
	}
	public String getIMR() {
		return imr;
	}
	public String getIMT() {
		return imt;
	}
	public Double getVs30Val(int i) {
		return vs30Vals.get(i);
	}
	public Double getDistVal(int i) {
		return distVals.get(i);
	}
	public Double getMeanVal(int i) {
		return meanVals.get(i);
	}
	public Double getStdDevVal(int i) {
		return stdDevVals.get(i);
	}
	public Double getInterStdDevVal(int i) {
		return interStdDevVals.get(i);
	}
	public Integer getSourceID(int i) {
		return sourceIDs.get(i);
	}
	public Integer getRupID(int i) {
		return rupIDs.get(i);
	}
	public int size() {
		return sourceIDs.size();
	}
	
	public void addRecord(int sourceID, int rupID, double vs30, double dist, double mean,
			double stdDev, double interStdDev) {
		if (!listsInitialized) {
			sourceIDs = new ArrayList<Integer>();
			rupIDs = new ArrayList<Integer>();
			vs30Vals = new ArrayList<Double>();
			distVals = new ArrayList<Double>();
			meanVals = new ArrayList<Double>();
			stdDevVals = new ArrayList<Double>();
			interStdDevVals = new ArrayList<Double>();
			listsInitialized = true;
		}
		this.sourceIDs.add(sourceID);
		this.rupIDs.add(rupID);
		this.vs30Vals.add(vs30);
		this.distVals.add(dist);
		this.meanVals.add(mean);
		this.stdDevVals.add(stdDev);
		this.interStdDevVals.add(interStdDev);
	}

	public String getLine(int lineID, int i) {
		return getLine(lineID, sourceIDs.get(i), rupIDs.get(i), vs30Vals.get(i), distVals.get(i), meanVals.get(i),
					stdDevVals.get(i), interStdDevVals.get(i));
	}
	
	public String getLine(int lineID, int sourceID, int rupID, double vs30, double dist, double mean,
					double stdDev, double interStdDev) {
		String line = lineID + "," + erf + "," + sourceID + "," + rupID + "," + imr;
		line += "," + siteID + "," + vs30 + "," + IM_EventSetOutputWriter.distFormat.format(dist) + "," + imt;
		line += "," + IM_EventSetOutputWriter.meanSigmaFormat.format(mean)
					+ "," + IM_EventSetOutputWriter.meanSigmaFormat.format(stdDev)
					+ "," + IM_EventSetOutputWriter.meanSigmaFormat.format(interStdDev);
		return line;
	}
	
	public static ArrayList<HAZ01ASegment> loadHAZ01A(String file) throws FileNotFoundException, IOException {
		ArrayList<String> lines = FileUtils.loadFile(file);
		
		String curERF = "";
		String curIMR = "";
		int curSite = -1;
		String curIMT = "";
		
		HAZ01ASegment curSeg = null;
		ArrayList<HAZ01ASegment> segs = new ArrayList<HAZ01ASegment>();
		
		// skip the header, and column names
		for (int i=2; i<lines.size(); i++) {
			String line = lines.get(i);
			StringTokenizer tok = new StringTokenizer(line, ",");
			tok.nextToken(); // line id
			String erf = tok.nextToken();
			int sourceID = Integer.parseInt(tok.nextToken());
			int rupID = Integer.parseInt(tok.nextToken());
			String imr = tok.nextToken();
			int site = Integer.parseInt(tok.nextToken());
			double vs30 = Double.parseDouble(tok.nextToken());
			double dist = Double.parseDouble(tok.nextToken());
			String imt = tok.nextToken();
			double mean = Double.parseDouble(tok.nextToken());
			double stdDev = Double.parseDouble(tok.nextToken());
			double interStdDev = Double.parseDouble(tok.nextToken());
			
			boolean newSec = false;
			if (!erf.equals(curERF)) {
				newSec = true;
				curERF = erf;
			}
			if (!imr.equals(curIMR)) {
				newSec = true;
				curIMR = imr;
			}
			if (!imt.equals(curIMT)) {
				newSec = true;
				curIMT = imt;
			}
			if (curSite != site) {
				newSec = true;
				curSite = site;
			}
			
			if (newSec) {
				if (curSeg != null)
					segs.add(curSeg);
				curSeg = new HAZ01ASegment(erf, site, imr, imt);
			}
			curSeg.addRecord(sourceID, rupID, vs30, dist, mean, stdDev, interStdDev);
		}
		
		if (curSeg != null)
			segs.add(curSeg);
		
		return segs;
	}
}
