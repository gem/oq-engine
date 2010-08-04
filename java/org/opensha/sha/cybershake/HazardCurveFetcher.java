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

package org.opensha.sha.cybershake;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;

import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.data.siteData.SiteDataAPI;
import org.opensha.commons.data.siteData.impl.CVM4BasinDepth;
import org.opensha.commons.data.siteData.impl.WillsMap2006;
import org.opensha.sha.calc.hazardMap.HazardDataSetLoader;
import org.opensha.sha.cybershake.db.CybershakeSite;
import org.opensha.sha.cybershake.db.CybershakeSiteInfo2DB;
import org.opensha.sha.cybershake.db.Cybershake_OpenSHA_DBApplication;
import org.opensha.sha.cybershake.db.DBAccess;
import org.opensha.sha.cybershake.db.HazardCurve2DB;

public class HazardCurveFetcher {
	
	HazardCurve2DB curve2db;
	CybershakeSiteInfo2DB site2db;
	
	ArrayList<Integer> ids;
	ArrayList<CybershakeSite> sites;
	ArrayList<DiscretizedFuncAPI> funcs;
	
	ArrayList<CybershakeSite> allSites = null;
	
	public HazardCurveFetcher(DBAccess db, ArrayList<Integer> erfIDs, int rupVarScenarioID, int sgtVarID, int imTypeID) {
		this.initDBConnections(db);
		System.out.println("rupV: " + rupVarScenarioID + " sgtV: " + sgtVarID);
		ids = curve2db.getAllHazardCurveIDs(erfIDs, rupVarScenarioID, sgtVarID, imTypeID);
//		System.out.println("Got " + ids.size() + " IDs");
		sites = new ArrayList<CybershakeSite>();
		funcs = new ArrayList<DiscretizedFuncAPI>();
		ArrayList<Integer> siteIDs = new ArrayList<Integer>();
		System.out.println("Start loop...");
		for (int i=ids.size()-1; i>=0; i--) {
			int id = ids.get(i);
			if (siteIDs.contains(id)) {
				ids.remove(i);
				continue;
			}
			sites.add(site2db.getSiteFromDB(curve2db.getSiteIDFromCurveID(id)));
			DiscretizedFuncAPI curve = curve2db.getHazardCurve(id);
			funcs.add(curve);
		}
//		System.out.println("Out of constructor!");
	}
	
	private void initDBConnections(DBAccess db) {
		curve2db = new HazardCurve2DB(db);
		site2db = new CybershakeSiteInfo2DB(db);
	}
	
	public ArrayList<Double> getSiteValues(boolean isProbAt_IML, double val) {
		ArrayList<Double> vals = new ArrayList<Double>();
		for (DiscretizedFuncAPI func : funcs) {
			vals.add(HazardDataSetLoader.getCurveVal(func, isProbAt_IML, val));
		}
		return vals;
	}

	public ArrayList<Integer> getCurveIDs() {
		return ids;
	}

	public ArrayList<CybershakeSite> getCurveSites() {
		return sites;
	}

	public ArrayList<DiscretizedFuncAPI> getFuncs() {
		return funcs;
	}
	
	public ArrayList<CybershakeSite> getAllSites() {
		if (allSites == null) {
			allSites = site2db.getAllSitesFromDB();
		}
		return allSites;
	}
	
	public void writeCurveToFile(DiscretizedFuncAPI curve, String fileName) throws IOException {
		FileWriter fw = new FileWriter(fileName);
		
		for (int i = 0; i < curve.getNum(); ++i)
			fw.write(curve.getX(i) + " " + curve.getY(i) + "\n");
		
		fw.close();
	}
	
	public void saveAllCurvesToDir(String outDir) {
		File outDirFile = new File(outDir);
		
		if (!outDirFile.exists())
			outDirFile.mkdir();
		
		if (!outDir.endsWith(File.separator))
			outDir += File.separator;
		
		ArrayList<DiscretizedFuncAPI> curves = this.getFuncs();
		ArrayList<CybershakeSite> curveSites = this.getCurveSites();
		
		for (int i=0; i<curves.size(); i++) {
			DiscretizedFuncAPI curve = curves.get(i);
			CybershakeSite site = curveSites.get(i);
			
			String fileName = outDir + site.short_name + "_" + site.lat + "_" + site.lon + ".txt";
			
			System.out.println("Writing " + fileName);
			
			try {
				this.writeCurveToFile(curve, fileName);
			} catch (IOException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			}
		}
	}
	
	public static void main(String args[]) throws IOException {
		String outDir = "/home/kevin/CyberShake/curve_data";
		
		DBAccess db = Cybershake_OpenSHA_DBApplication.db;
		
		System.out.println("1");
		
		ArrayList<Integer> erfIDs = new ArrayList<Integer>();
		erfIDs.add(34);
		erfIDs.add(35);
		HazardCurveFetcher fetcher = new HazardCurveFetcher(db, erfIDs, 3, 5, 21);
		
		System.out.println("2");
		
//		fetcher.saveAllCurvesToDir(outDir);
		
		WillsMap2006 wills = new WillsMap2006();
		CVM4BasinDepth cvm = new CVM4BasinDepth(SiteDataAPI.TYPE_DEPTH_TO_2_5);
		
		ArrayList<CybershakeSite> sites = fetcher.getCurveSites();
		String tot = "";
		for (CybershakeSite site : sites) {
			String str = site.lon + ", " + site.lat + ", " + site.short_name + ", ";
			if (site.type_id == CybershakeSite.TYPE_POI)
				str += "Point of Interest";
			else if (site.type_id == CybershakeSite.TYPE_BROADBAND_STATION)
				str += "Seismic Station";
			else if (site.type_id == CybershakeSite.TYPE_PRECARIOUS_ROCK)
				str += "Precarious Rock";
			else if (site.type_id == CybershakeSite.TYPE_TEST_SITE)
				continue;
			else
				str += "Unknown";
			double vs30 = wills.getValue(site.createLocation());
			double basin = cvm.getValue(site.createLocation());
			str += ", " + vs30 + ", " + basin;
			System.out.println(str);
			tot += str + "\n";
		}
		System.out.print(tot);
		
		System.exit(0);
	}
}
