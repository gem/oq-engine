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

package org.opensha.sha.cybershake.plot.interpMap;

import java.io.IOException;
import java.util.ArrayList;

import org.opensha.commons.util.XYZClosestPointFinder;
import org.opensha.sha.cybershake.HazardCurveFetcher;
import org.opensha.sha.cybershake.db.CybershakeSite;
import org.opensha.sha.cybershake.db.Cybershake_OpenSHA_DBApplication;
import org.opensha.sha.cybershake.db.DBAccess;
import org.opensha.sha.cybershake.plot.HazardCurvePlotter;
import org.opensha.sha.cybershake.plot.HazardCurves2XYZ;

/**
 * This class takes the CyberShake hazard curves, and computes the difference with a base map
 * at each point. The closest point in the base map is taken.
 * 
 * @author kevin
 *
 */
public class HazardCurvePointDifferences {
	
	private XYZClosestPointFinder xyz;
	private ArrayList<CybershakeSite> sites;
	private HazardCurveFetcher fetcher;
	private ArrayList<Integer> types;
	
	public HazardCurvePointDifferences(HazardCurveFetcher fetcher, String comparisonFile,
			ArrayList<Integer> types) throws IOException {
		this.fetcher = fetcher;
		this.types = types;
		xyz = new XYZClosestPointFinder(comparisonFile);
		
		sites = fetcher.getCurveSites();
	}
	
	public ArrayList<Double> getSiteDifferenceValues(boolean isProbAt_IML, double level) {
		ArrayList<Double> csVals = fetcher.getSiteValues(isProbAt_IML, level);
		
		ArrayList<Double> diff = new ArrayList<Double>();
		
		ArrayList<CybershakeSite> newSites = new ArrayList<CybershakeSite>();
		
		for (int i=0; i<sites.size(); i++) {
			CybershakeSite site = sites.get(i);
			
			if (types != null && !types.contains(site.type_id))
				continue;
			
			newSites.add(site);
			
			double csVal = csVals.get(i);
			double compVal = xyz.getClosestVal(site.lat, site.lon);
			
			diff.add(csVal - compVal);
		}
		
		this.sites = newSites;
		
		return diff;
	}
	
	public void writeXYZ(String fileName, boolean isProbAt_IML, double level) throws IOException {
		ArrayList<Double> vals = getSiteDifferenceValues(isProbAt_IML, level);
		HazardCurves2XYZ.writeXYZ(fileName, sites, vals, null);
	}
	
	public void writeLabelsFile(String labelsFile) throws IOException {
		HazardCurves2XYZ.writeLabelsFile(labelsFile, sites);
	}
	
	public static void main(String args[]) throws IOException {
		String compFile = null;
		String outFile = null;
		String labelsFile = null;
		String types = "";
		
		int imTypeID = 21;
		
		boolean isProbAt_IML = false;
		double level = 0.0004;
		
		if (args.length == 0) {
			System.err.println("WARNING: Running from debug mode!");
			compFile = "/home/kevin/CyberShake/baseMaps/cb2008/cb2008_base_map_2percent_hiRes_0.005.txt";
			outFile = "/home/kevin/CyberShake/interpolatedDiffMap/diffs.txt";
			labelsFile = "/home/kevin/CyberShake/interpolatedDiffMap/markers.txt";
		} else if (args.length >= 3 && args.length <= 7) {
			compFile = args[0];
			outFile = args[1];
			labelsFile = args[2];
			imTypeID = Integer.parseInt(args[3]);
			if (args.length == 5) {
				types = args[4];
			} else if (args.length == 6) {
				isProbAt_IML = Boolean.parseBoolean(args[4]);
				level = Double.parseDouble(args[5]);
			} else if (args.length == 7) {
				types = args[4];
				isProbAt_IML = Boolean.parseBoolean(args[5]);
				level = Double.parseDouble(args[6]);
			}
		} else {
			System.err.println("USAGE: HazardCurvePointDifferences base_map_file outFile labelsFile imTypeID [types] " +
					"[isProbAt_IML level]");
			System.exit(1);
		}
		
		System.out.println("*****************************");
		System.out.println("Basemap: " + compFile);
		System.out.println("Diff output: " + outFile);
		System.out.println("Labels: " + labelsFile);
		System.out.println("IM Type ID: " + imTypeID);
		System.out.println("Types: " + types);
		if (isProbAt_IML) {
			System.out.println("Prob of exceeding IML of:  " + level);
		} else {
			System.out.println("IML at Prob of: " + level);
		}
		System.out.println("*****************************\n");
		
		ArrayList<Integer> typeIDs = null;
		
		if (types.length() > 0) {
			ArrayList<String> idSplit = HazardCurvePlotter.commaSplit(types);
			typeIDs = new ArrayList<Integer>();
			for (String idStr : idSplit) {
				int id = Integer.parseInt(idStr);
				typeIDs.add(id);
				System.out.println("Added site type: " + id);
			}
		}
		
		DBAccess db = Cybershake_OpenSHA_DBApplication.db;
		HazardCurveFetcher fetcher = new HazardCurveFetcher(db, null, 3, 5, imTypeID);
		
		HazardCurvePointDifferences diff = new HazardCurvePointDifferences(fetcher, compFile, typeIDs);
		
		diff.writeXYZ(outFile, isProbAt_IML, level);
		diff.writeLabelsFile(labelsFile);
		
		System.exit(0);
	}

}
