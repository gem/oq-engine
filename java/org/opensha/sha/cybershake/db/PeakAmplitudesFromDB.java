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

package org.opensha.sha.cybershake.db;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;

public class PeakAmplitudesFromDB implements PeakAmplitudesFromDBAPI {

	
	private DBAccess dbaccess;
	private Runs2DB runs2db;
	
	public static final String TABLE_NAME = "PeakAmplitudes";

	
	public PeakAmplitudesFromDB(DBAccess dbaccess){
		this.dbaccess = dbaccess;
		runs2db = new Runs2DB(dbaccess);
	}
	
	public ArrayList<Integer> getPeakAmpSites() {
		ArrayList<Integer> runs = getPeakAmpRunIDs();
		ArrayList<Integer> ids = new ArrayList<Integer>();
		
		for (int id : runs) {
			ids.add(runs2db.getSiteID(id));
		}
		
		return ids;
	}
	
	public ArrayList<Integer> getPeakAmpRunIDs() {
		return getDistinctIntVal("Run_ID", null);
	}
	
	public ArrayList<CybershakeRun> getPeakAmpRuns() {
		ArrayList<Integer> ids = getPeakAmpRunIDs();
		ArrayList<CybershakeRun> runs = new ArrayList<CybershakeRun>();
		
		for (int id : ids) {
			runs.add(runs2db.getRun(id));
		}
		
		return runs;
	}
	
	public ArrayList<CybershakeRun> getPeakAmpRuns(int siteID, int erfID, int sgtVarID, int rupVarScenID) {
		ArrayList<CybershakeRun> runs = runs2db.getRuns(siteID, erfID, sgtVarID, rupVarScenID, null, null, null, null);
		ArrayList<Integer> ids = getPeakAmpRunIDs();
		
		ArrayList<CybershakeRun> ampsRuns = new ArrayList<CybershakeRun>();
		
		for (CybershakeRun run : runs) {
			for (int id : ids) {
				if (id == run.getRunID()) {
					ampsRuns.add(run);
					break;
				}
			}
		}
		
		return ampsRuns;
	}
	
	public ArrayList<Integer> getDistinctIntVal(String selectCol, String whereClause) {
		ArrayList<Integer> vals = new ArrayList<Integer>();
		
		String sql = "SELECT distinct " + selectCol + " FROM " + TABLE_NAME;
		
		if (whereClause != null && whereClause.length() > 0) {
			sql += " WHERE " + whereClause;
		}
		
//		System.out.println(sql);
		
		ResultSet rs = null;
		try {
			rs = dbaccess.selectData(sql);
		} catch (SQLException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		}
		try {
			rs.first();
			while(!rs.isAfterLast()){
				int id = rs.getInt(selectCol);
				vals.add(id);
				rs.next();
			}
			rs.close();
		} catch (SQLException e) {
			e.printStackTrace();
		}
		
		return vals;
	}
	
	public boolean hasAmps(int siteID, int erfID) {
		return hasAmps(siteID, erfID, -1, -1);
	}
	
	public boolean hasAmps(int siteID, int erfID, int rupVarScenID, int sgtVarID) {
		ArrayList<Integer> runs = runs2db.getRunIDs(siteID, erfID, sgtVarID, rupVarScenID, null, null, null, null);
		if (runs.size() == 0)
			return false;
		
		ArrayList<Integer> ampsRuns = getPeakAmpRunIDs();
		
		for (int id : runs) {
			for (int ampsRun : ampsRuns) {
				if (id == ampsRun)
					return true;
			}
		}
		
		return false;
	}
	
	public boolean hasAmps(int runID) {
		String sql = "SELECT * FROM " + TABLE_NAME + " WHERE Run_ID=" + runID + " LIMIT 1";
		
		try {
			ResultSet rs = dbaccess.selectData(sql);
			
			boolean good = rs.first();
			
			rs.close();
			
			return good;
		} catch (SQLException e) {
			e.printStackTrace();
			return false;
		}
	}
	
	/**
	 * @returns the supported SA Period as list of strings.
	 */
	public ArrayList<CybershakeIM>  getSupportedIMs(){
		String sql = "SELECT I.IM_Type_ID,I.IM_Type_Measure,I.IM_Type_Value,I.Units from IM_Types I JOIN (";
		sql += "SELECT distinct IM_Type_ID from " + TABLE_NAME;
		sql += ") A ON A.IM_Type_ID=I.IM_Type_ID";
		
//		System.out.println(sql);

		ArrayList<CybershakeIM> ims = new ArrayList<CybershakeIM>();
		ResultSet rs = null;
		try {
			rs = dbaccess.selectData(sql);
		} catch (SQLException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		}
		try {
			rs.first();
			while(!rs.isAfterLast()){
				int id = rs.getInt("IM_Type_ID");
				String measure = rs.getString("IM_Type_Measure");
				Double value = rs.getDouble("IM_Type_Value");
				String units = rs.getString("Units");
				ims.add(new CybershakeIM(id, measure, value, units));
				rs.next();
			}
			rs.close();
		} catch (SQLException e) {
			e.printStackTrace();
		}
		return ims;
	}
	
	public int countAmps(int runID, CybershakeIM im) {
		String sql = "SELECT count(*) from " + TABLE_NAME + " where Run_ID=" + runID;
		if (im != null)
			sql += " and IM_Type_ID="+im.getID();
//		System.out.println(sql);
		ResultSet rs = null;
		try {
			rs = dbaccess.selectData(sql);
		} catch (SQLException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
			return -1;
		}
		try {
			rs.first();
			int count = rs.getInt(1);
			rs.close();
			return count;
		} catch (SQLException e) {
			e.printStackTrace();
		}
		return -1;
	}
	
	/**
	 * @returns the supported SA Period as list of strings.
	 */
	public ArrayList<CybershakeIM>  getSupportedIMs(int runID) {
		String whereClause = "Run_ID="+runID;
		long startTime = System.currentTimeMillis();
		String sql = "SELECT I.IM_Type_ID,I.IM_Type_Measure,I.IM_Type_Value,I.Units from IM_Types I JOIN (";
		sql += "SELECT distinct IM_Type_ID from " + TABLE_NAME + " WHERE " + whereClause;
		sql += ") A ON A.IM_Type_ID=I.IM_Type_ID";
		
		System.out.println(sql);
		
//		System.out.println(sql);
		ArrayList<CybershakeIM> ims = new ArrayList<CybershakeIM>();
		ResultSet rs = null;
		try {
			rs = dbaccess.selectData(sql);
		} catch (SQLException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		}
		try {
			rs.first();
			while(!rs.isAfterLast()){
				int id = rs.getInt("IM_Type_ID");
				String measure = rs.getString("IM_Type_Measure");
				Double value = rs.getDouble("IM_Type_Value");
				String units = rs.getString("Units");
				ims.add(new CybershakeIM(id, measure, value, units));
				rs.next();
			}
			rs.close();
		} catch (SQLException e) {
//			e.printStackTrace();
		}
		long duration = System.currentTimeMillis() - startTime;
		System.out.println("Total SA Period Select Time: " + ((double)duration / 1000) + " sec");
		return ims;
	}
	
	/**
	 * 
	 * @param erfId
	 * @param srcId
	 * @param rupId
	 * @returns the rupture variation ids for the rupture
	 */
	public ArrayList<Integer> getRupVarationsForRupture(int erfId,int srcId, int rupId){
		String sql = "SELECT Rup_Var_ID from Rupture_Variations where Source_ID = '"+srcId+"' "+
		             "and ERF_ID =  '"+erfId +"' and Rup_Var_Scenario_ID='3' and Rupture_ID = '"+rupId+"'";
		
		ArrayList<Integer> rupVariationList = new ArrayList<Integer>();
		ResultSet rs = null;
		try {
			rs = dbaccess.selectData(sql);
		} catch (SQLException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		}
		try {
			rs.first();
			while(!rs.isAfterLast()){
			  String rupVariation = rs.getString("Rup_Var_ID");	
			  rupVariationList.add(Integer.parseInt(rupVariation));
			  rs.next();
			}
			rs.close();
		} catch (SQLException e) {
			e.printStackTrace();
		}
		return rupVariationList;
	}
	
	/**
	 * 
	 * @param siteId
	 * @param erfId
	 * @param srcId
	 * @param rupId
	 * @param rupVarId
	 * @returns the IM Value for the particular IM type
	 */
	public double getIM_Value(int runID, int srcId, int rupId, int rupVarId, CybershakeIM im){
		String sql = "SELECT distinct IM_Value from " + TABLE_NAME + " where Source_ID = '"+srcId+"' "+
        "and Run_ID =  '"+runID +"' and Rupture_ID = '"+rupId+"' " +
        "and IM_Type_ID = '"+im.getID()+"' and Rup_Var_ID = '"+rupVarId+"'";
//		System.out.println(sql);
		double imVal = Double.NaN;
		ResultSet rs = null;
		try {
			rs = dbaccess.selectData(sql);
		} catch (SQLException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		}
		try {
			rs.first();
			imVal = Double.parseDouble(rs.getString("IM_Value"));	
			rs.close();
		} catch (SQLException e) {
			e.printStackTrace();
		}
		return imVal;
	}
	
	/**
	 * 
	 * @param siteId
	 * @param erfId
	 * @param srcId
	 * @param rupId
	 * @throws SQLException 
	 * @returns the a list of IM Values for the particular IM type
	 */
	public ArrayList<Double> getIM_Values(int runID, int srcId, int rupId, CybershakeIM im) throws SQLException{
		String sql = "SELECT IM_Value from " + TABLE_NAME + " where Run_ID=" + runID + " and Source_ID = '"+srcId+"' "+
        "and Rupture_ID = '"+rupId+"' and IM_Type_ID = '"+im.getID()+"'";
//		System.out.println(sql);
		ResultSet rs = null;
		ArrayList<Double> vals = new ArrayList<Double>();
		try {
			rs = dbaccess.selectData(sql);
			
		} catch (SQLException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		}
		rs.first();
		vals.add(rs.getDouble("IM_Value"));
//		vals.add(Double.parseDouble(rs.getString("IM_Value")));
		while (rs.next()) {
			vals.add(rs.getDouble("IM_Value"));
//			vals.add(Double.parseDouble(rs.getString("IM_Value")));
		}
		rs.close();
		return vals;
	}
	
	 /**
	  * @return all possible SGT Variation IDs
	  */
	public ArrayList<Integer> getSGTVarIDs() {
		ArrayList<Integer> vars = new ArrayList<Integer>();
		
		String sql = "SELECT SGT_Variation_ID from SGT_Variation_IDs order by SGT_Variation_ID desc";
		
		ResultSet rs = null;
		try {
			rs = dbaccess.selectData(sql);
		} catch (SQLException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		}
		try {
			rs.first();
			while(!rs.isAfterLast()){
			  int id = rs.getInt("SGT_Variation_ID");
			  vars.add(id);
			  rs.next();
			}
			rs.close();
		} catch (SQLException e) {
			e.printStackTrace();
		}
		
		return vars;
	}
	
	/**
	 * @return all possible Rup Var Scenario IDs
	 */
	public ArrayList<Integer> getRupVarScenarioIDs() {
		ArrayList<Integer> vars = new ArrayList<Integer>();
		
		String sql = "SELECT Rup_Var_Scenario_ID from Rupture_Variation_Scenario_IDs order by Rup_Var_Scenario_ID desc";
		
		ResultSet rs = null;
		try {
			rs = dbaccess.selectData(sql);
		} catch (SQLException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		}
		try {
			rs.first();
			while(!rs.isAfterLast()){
			  int id = rs.getInt("Rup_Var_Scenario_ID");
			  vars.add(id);
			  rs.next();
			}
			rs.close();
		} catch (SQLException e) {
			e.printStackTrace();
		}
		
		return vars;
	}
	
	public CybershakeIM getIMForPeriod(double period, int runID) {
		return this.getIMForPeriod(period, runID, null);
	}
	
	public CybershakeIM getIMForPeriod(double period, int runID, HazardCurve2DB curve2db) {
		ArrayList<Double> periods = new ArrayList<Double>();
		periods.add(period);
		
		return getIMForPeriods(periods, runID, curve2db).get(0);
	}
	
	public ArrayList<CybershakeIM> getIMForPeriods(ArrayList<Double> periods, int runID) {
		return this.getIMForPeriods(periods, runID, null);
	}
	
	public ArrayList<CybershakeIM> getIMForPeriods(ArrayList<Double> periods, int runID, HazardCurve2DB curve2db) {
		ArrayList<CybershakeIM> supported = this.getSupportedIMs(runID);
		if (curve2db != null) {
			supported.addAll(curve2db.getSupportedIMs(runID));
		}
		
		ArrayList<CybershakeIM> matched = new ArrayList<CybershakeIM>();
		
		if (supported.size() == 0)
			return null;
		
		double maxDist = 0.5;
		
		for (double period : periods) {
			CybershakeIM closest = null;
			double dist = Double.POSITIVE_INFINITY;
			
			for (CybershakeIM im : supported) {
				double val = Math.abs(period - im.getVal());
//				System.out.println("Comparing " + val + " to " + im.getVal());
				if (val < dist && val <= maxDist) {
					closest = im;
					dist = val;
				}
			}
			if (dist != Double.POSITIVE_INFINITY)
				System.out.println("Matched " + period + " with " + closest.getVal());
			else
				System.out.println("NO MATCH FOR " + period + "!!!");
			matched.add(closest);
		}
		
		return matched;
	}
	
	public int deleteAllAmpsForSite(int siteID) {
		ArrayList<Integer> runs = runs2db.getRunIDs(siteID);
		int rows = 0;
		for (int runID : runs) {
			int num = deleteAmpsForRun(runID);
			if (num < 0)
				return -1;
			
		}
		return rows;
	}
	
	public int deleteAmpsForRun(int runID) {
		String sql = "DELETE FROM " + TABLE_NAME + " WHERE Run_ID="+runID;
		System.out.println(sql);
		try {
			return dbaccess.insertUpdateOrDeleteData(sql);
		} catch (SQLException e) {
//			TODO Auto-generated catch block
			e.printStackTrace();
			return -1;
		}
	}
	
	public static void main(String args[]) {
		DBAccess db = Cybershake_OpenSHA_DBApplication.db;
		PeakAmplitudesFromDB amps = new PeakAmplitudesFromDB(db);
		
		System.out.println(amps.getPeakAmpSites().size() + " sites");
		System.out.println(amps.getPeakAmpRuns().size() + " runs");
		
		System.out.println("Amps for 90, 36? " + amps.hasAmps(90, 36) + " (false!)");
		System.out.println("Amps for 90, 35? " + amps.hasAmps(90, 35) + " (true!)");
		System.out.println("Amps for run 1? " + amps.hasAmps(1) + " (false!)");
		System.out.println("Amps for run 216? " + amps.hasAmps(216) + " (true!)");
		
		for (CybershakeIM im : amps.getSupportedIMs()) {
			System.out.println("IM: " + im);
		}
		
		System.out.println("Count for 216: " + amps.countAmps(216, null));
		
		db.destroy();
		
		System.exit(0);
	}
	
}
