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
import java.util.ListIterator;

import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.commons.geo.Region;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.sha.cybershake.openshaAPIs.CyberShakeEqkRupture;
import org.opensha.sha.cybershake.openshaAPIs.CyberShakeEvenlyGriddedSurface;
import org.opensha.sha.cybershake.openshaAPIs.CyberShakeProbEqkSource;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.faultSurface.EvenlyGridCenteredSurface;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.faultSurface.PointSurface;

public  class ERF2DB implements ERF2DBAPI{

	protected EqkRupForecast eqkRupForecast;
	private DBAccess dbaccess;

	public ERF2DB(DBAccess dbaccess){
		this.dbaccess = dbaccess;
	}

	/**
	 * Get a list of all ERFs in the database
	 * @return
	 */
	public ArrayList<CybershakeERF> getAllERFs() {
		ArrayList<CybershakeERF> erfs = new ArrayList<CybershakeERF>();

		String sql = "SELECT ERF_ID,ERF_Name,ERF_Description from ERF_IDs order by ERF_ID desc";
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
				int id = rs.getInt("ERF_ID");
				String name = rs.getString("ERF_Name");
				String desc = rs.getString("ERF_Description");
				erfs.add(new CybershakeERF(id, name, desc));
				rs.next();
			}
			rs.close();
		} catch (SQLException e) {
			//			e.printStackTrace();
		}

		return erfs;
	}

	public ArrayList<CyberShakeProbEqkSource> getSources(int erfID) {
		ArrayList<CyberShakeProbEqkSource> sources = new ArrayList<CyberShakeProbEqkSource>();

		ArrayList<Integer> ids = new ArrayList<Integer>();
		ArrayList<String> names = new ArrayList<String>();

		this.loadSourceList(erfID, ids, names);

		if (ids.size() != names.size()) {
			throw new RuntimeException("Source ID list and Names list are different sizes!");
		}

		int maxID = 0;
		for (int id : ids) {
			if (id > maxID)
				maxID = id;
		}

		for (int i=0; i< ids.size(); i++) {
			int sourceID = ids.get(i);
			String name = names.get(i);

			System.out.println("Loading source " + sourceID + "/" + maxID + " (" + name + ")");

			CyberShakeProbEqkSource source = new CyberShakeProbEqkSource(name);

			ArrayList<Integer> rupIDs = this.getRuptureIDs(erfID, sourceID);
			for (int rupID : rupIDs) {
				CyberShakeEqkRupture rup = this.getRupture(erfID, sourceID, rupID);
				source.addRupture(rup);
			}

			sources.add(source);
		}

		return sources;
	}

	public CyberShakeEqkRupture getRupture(int erfID, int sourceID, int rupID) {
		double mag = this.getRuptureDouble("Mag", erfID, sourceID, rupID);
		double prob = this.getRuptureDouble("Prob", erfID, sourceID, rupID);
		//		CyberShakeEvenlyGriddedSurface surface = getRuptureSurface(erfID, sourceID, rupID);
		//		return new CyberShakeEqkRupture(mag, prob, surface, null, sourceID, rupID, erfID);
		return new CyberShakeEqkRupture(mag, prob, null, sourceID, rupID, erfID, this);
	}

	public CyberShakeEvenlyGriddedSurface getRuptureSurface(int erfID, int sourceID, int rupID) {
		System.out.print("Loading surface for " + sourceID + " " + rupID + "...");

		int numRows = getRuptureInt("Num_Rows", erfID, sourceID, rupID);
		int numCols = getRuptureInt("Num_Columns", erfID, sourceID, rupID);
		double spacing = getRuptureDouble("Grid_Spacing", erfID, sourceID, rupID);
		ArrayList<Location> locs = this.getRuptureSurfacePoints(erfID, sourceID, rupID);

		CyberShakeEvenlyGriddedSurface surface = new CyberShakeEvenlyGriddedSurface(numRows, numCols, spacing);
		surface.setAllLocations(locs);

		System.out.println("DONE");

		return surface;
	}

	public ArrayList<Location> getRuptureSurfacePoints(int erfID, int sourceID, int rupID) {
		ArrayList<Location> locs = new ArrayList<Location>();

		String sql = "SELECT Lat,Lon,Depth from Points WHERE ERF_ID = "+"'"+erfID+"' and "+
		"Source_ID = '"+sourceID+"' and Rupture_ID = '"+rupID+"' ORDER BY Point_ID";
		ResultSet rs = null;
		try {
			rs = dbaccess.selectData(sql);
		} catch (SQLException e1) {
			//			TODO Auto-generated catch block
			e1.printStackTrace();
		}
		try{
			rs.first();
			while (!rs.isAfterLast()) {
				double lat = rs.getDouble("Lat");
				double lon = rs.getDouble("Lon");
				double depth = rs.getDouble("Depth");
				locs.add(new Location(lat, lon, depth));
				rs.next();
			}
			rs.close();

		}catch (SQLException e) {
			e.printStackTrace();
		}

		return locs;
	}

	public int getRuptureInt(String column, int erfId,int sourceId,int rupId) {

		String sql = "SELECT " + column + " from Ruptures WHERE ERF_ID = "+"'"+erfId+"' and "+
		"Source_ID = '"+sourceId+"' and Rupture_ID = '"+rupId+"'";
		ResultSet rs = null;
		try {
			rs = dbaccess.selectData(sql);
		} catch (SQLException e1) {
			//			TODO Auto-generated catch block
			e1.printStackTrace();
		}
		int data = 0;
		try{
			rs.first();
			data = Integer.parseInt(rs.getString(column));
			rs.close();

		}catch (SQLException e) {
			e.printStackTrace();
		}
		return data;
	}

	public double getRuptureDouble(String column, int erfId, int sourceId, int rupId) {

		String sql = "SELECT " + column + " from Ruptures WHERE ERF_ID = "+"'"+erfId+"' and "+
		"Source_ID = '"+sourceId+"' and Rupture_ID = '"+rupId+"'";
		ResultSet rs = null;
		try {
			rs = dbaccess.selectData(sql);
		} catch (SQLException e1) {
			//			TODO Auto-generated catch block
			e1.printStackTrace();
		}
		double data = Double.NaN;
		try{
			rs.first();
			data = Double.parseDouble(rs.getString(column));
			rs.close();

		}catch (SQLException e) {
			e.printStackTrace();
		}
		return data;
	}

	/**
	 * Get a list of all ERFs in the database
	 * @return
	 */
	public CybershakeERF getERF(int erfID) {
		String sql = "SELECT ERF_ID,ERF_Name,ERF_Description from ERF_IDs WHERE ERF_ID=" + erfID;
		ResultSet rs = null;
		try {
			rs = dbaccess.selectData(sql);
		} catch (SQLException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		}
		CybershakeERF erf = null;
		try {
			rs.first();
			int id = rs.getInt("ERF_ID");
			String name = rs.getString("ERF_Name");
			String desc = rs.getString("ERF_Description");
			erf = new CybershakeERF(id, name, desc);
			rs.close();
		} catch (SQLException e) {
			//			e.printStackTrace();
		}

		return erf;
	}

	/**
	 * Inserts ERF Parameters info in the "ERF_Metadata"
	 * @param erfId
	 * @param attrName
	 * @param attrVal
	 */
	public void insertERFParams(int erfId, String attrName, String attrVal, String attrType,String attrUnits) {

		//generate the SQL to be inserted in the ERF_Metadata table
		String sql = "INSERT into ERF_Metadata" +
		"(ERF_ID,ERF_Attr_Name,ERF_Attr_Value,ERF_Attr_Type,ERF_Attr_Units)"+
		"VALUES('"+erfId+"','"+attrName+"','"+
		attrVal+"','"+attrType+"','"+attrUnits+"')";
		try {
			dbaccess.insertUpdateOrDeleteData(sql);
		} catch (SQLException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}

	}


	/**
	 * Inserts source rupture information for the ERF in table "Ruptures"
	 * @param erfName
	 * @param sourceId
	 * @param ruptureId
	 * @param sourceName
	 * @param sourcetype
	 * @param magnitude
	 * @param probability
	 * @param gridSpacing
	 * @param numRows
	 * @param numCols
	 * @param numPoints
	 */
	public void insertERFRuptureInfo(int erfId, int sourceId, int ruptureId, 
			String sourceName, String sourceType, double magnitude, 
			double probability, double gridSpacing, double surfaceStartLat, 
			double surfaceStartLon, double surfaceStartDepth,
			double surfaceEndLat, double surfaceEndLon,double surfaceEndDepth, 
			int numRows, int numCols, int numPoints) {
		//		generate the SQL to be inserted in the ERF_Metadata table
		String sql = "INSERT into Ruptures" +
		"(ERF_ID,Source_ID,Rupture_ID,Source_Name,Source_Type,Mag,Prob,"+
		"Grid_Spacing,Num_Rows,Num_Columns,Num_Points,Start_Lat,Start_Lon,"+
		"Start_Depth,End_Lat,End_Lon,End_Depth)"+
		"VALUES('"+erfId+"','"+sourceId+"','"+
		ruptureId+"','"+sourceName+"','"+sourceType+"','"+(float)magnitude+"','"+
		(float)probability+"','"+(float)gridSpacing+"','"+numRows+"','"+numCols+
		"','"+numPoints+"','"+(float)surfaceStartLat+"','"+(float)surfaceStartLon+"','"+(float)surfaceStartDepth+
		"','"+(float)surfaceEndLat+"','"+(float)surfaceEndLon+"','"+(float)surfaceEndDepth+"')";
		try {
			dbaccess.insertUpdateOrDeleteData(sql);
		} catch (SQLException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}

	}

	/**
	 * Inserts surface locations information for each rupture in table "Points"
	 * @param erfName
	 * @param sourceId
	 * @param ruptureId
	 * @param lat
	 * @param lon
	 * @param depth
	 * @param rake
	 * @param dip
	 * @param strike
	 */
	public void insertRuptureSurface(int erfId, int sourceId, int ruptureId, 
			double lat, double lon, double depth, double rake, 
			double dip, double strike) {
		//		generate the SQL to be inserted in the ERF_Metadata table
		String sql = "INSERT into Points"+ 
		"(ERF_ID,Source_ID,Rupture_ID,Lat,Lon,Depth,Rake,Dip,Strike)"+
		"VALUES('"+erfId+"','"+sourceId+"','"+
		ruptureId+"','"+(float)lat+"','"+(float)lon+"','"+(float)depth+"','"+
		(float)rake+"','"+(float)dip+"','"+(float)strike+"')";
		try {
			dbaccess.insertUpdateOrDeleteData(sql);
		} catch (SQLException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}

	}

	public ArrayList<Integer> getRuptureIDs(int erfID, int sourceID) {
		ArrayList<Integer> ids = new ArrayList<Integer>();

		String sql = "SELECT Rupture_ID from Ruptures WHERE ERF_ID=" + erfID + " AND Source_ID=" + sourceID + " order by Rupture_ID";

		ResultSet rs = null;
		try {
			rs = dbaccess.selectData(sql);
		} catch (SQLException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		}
		try {
			rs.first();
			while (!rs.isAfterLast()) {
				int id = rs.getInt("Rupture_ID");
				ids.add(id);

				rs.next();
			}
			rs.close();
		} catch (SQLException e) {
			//			e.printStackTrace();
		}

		return ids;
	}
	
	public ArrayList<CybershakeRuptureRecord> getRuptures(int erfID, int sourceID) {
		String sql = "SELECT Rupture_ID, Mag, Prob FROM Ruptures WHERE ERF_ID="+erfID+" AND Source_ID="+sourceID;
		
		ArrayList<CybershakeRuptureRecord> records = new ArrayList<CybershakeRuptureRecord>();
		
		ResultSet rs = null;
		try {
			rs = dbaccess.selectData(sql);
		} catch (SQLException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
			return null;
		}
		try {
			rs.first();
			while(!rs.isAfterLast()){
				int rupID = rs.getInt("Rupture_ID");
				double mag = rs.getDouble("Mag");
				double prob = rs.getDouble("Prob");
				records.add(new CybershakeRuptureRecord(sourceID, rupID, mag, prob));
				rs.next();
			}
			rs.close();
		} catch (SQLException e) {
			//			e.printStackTrace();
		}
		
		return records;
	}
	
	public void loadRVs(int erfID, int rupVarScenID, int sourceID, int rupID,
			ArrayList<String> lfns, ArrayList<Location> hypocenterLocs) {
		String sql = "SELECT Rup_Var_LFN, Hypocenter_Lat, Hypocenter_Lon, Hypocenter_Depth" +
				" FROM Rupture_Variations WHERE Rup_Var_Scenario_ID="+rupVarScenID+" and ERF_ID="+erfID+
				" and Source_ID="+sourceID+" and Rupture_ID="+rupID;
		//		System.out.println(sql);
		ResultSet rs = null;
		try {
			rs = dbaccess.selectData(sql);
		} catch (SQLException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
			return;
		}
		try {
			rs.first();
			while(!rs.isAfterLast()){
				String lfn = rs.getString("Rup_Var_LFN");
				double lat = rs.getDouble("Hypocenter_Lat");
				double lon = rs.getDouble("Hypocenter_Lon");
				double depth = rs.getDouble("Hypocenter_Depth");
				//				System.out.println("Loaded source " + id);
				Location hypo = null;
				if (lat != 0 && lon != 0 && depth != 0) {
					hypo = new Location(lat, lon, depth);
				}
				lfns.add(lfn);
				hypocenterLocs.add(hypo);
				rs.next();
			}
			rs.close();
		} catch (SQLException e) {
			//			e.printStackTrace();
		}

		return;
	}

	public void loadSourceList(int erfID, ArrayList<Integer> ids, ArrayList<String> names) {
		String sql = "SELECT distinct Source_ID,Source_Name from Ruptures WHERE ERF_ID=" + erfID + " order by Source_ID";
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
				int id = rs.getInt("Source_ID");
				//				System.out.println("Loaded source " + id);
				ids.add(id);
				if (names != null) {
					String name = rs.getString("Source_Name");
					names.add(name);
				}
				rs.next();
			}
			rs.close();
		} catch (SQLException e) {
			//			e.printStackTrace();
		}

		return;
	}

	public int calcNumPoints(int erfID, int sourceID, int ruptureID) {
		String sql = "SELECT count(*) from Points WHERE ERF_ID=" + erfID + " AND Source_ID=" + sourceID + " AND Rupture_ID=" + ruptureID;
		//		sql = "SELECT * FROM (" + sql + ") A"; 
		ResultSet rs = null;
		try {
			rs = dbaccess.selectData(sql);
		} catch (SQLException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		}
		int num = -1;
		try {
			rs.first();
			num = rs.getInt("count(*)");
			rs.close();
		} catch (SQLException e) {
			e.printStackTrace();
		}
		return num;
	}

	public int getListedNumPoints(int erfID, int sourceID, int ruptureID) {
		String sql = "SELECT Num_Points from Ruptures WHERE ERF_ID=" + erfID + " AND Source_ID=" + sourceID + " AND Rupture_ID=" + ruptureID;
		ResultSet rs = null;
		try {
			rs = dbaccess.selectData(sql);
		} catch (SQLException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		}
		int num = -1;
		try {
			rs.first();
			num = rs.getInt("Num_Points");
			rs.close();
		} catch (SQLException e) {
			//			e.printStackTrace();
		}
		return num;
	}

	public ArrayList<int[]> checkNumPoints(int erfID) {
		ArrayList<Integer> ids = new ArrayList<Integer>();

		this.loadSourceList(erfID, ids, null);

		ArrayList<int[]> bad = new ArrayList<int[]>();

		for (int sourceID : ids) {
			System.out.println("Processing source " + sourceID);
			ArrayList<Integer> rupIDs = this.getRuptureIDs(erfID, sourceID);
			for (int ruptureID : rupIDs) {
				int listNum = this.getListedNumPoints(erfID, sourceID, ruptureID);
				int calcNum = this.calcNumPoints(erfID, sourceID, ruptureID);

				if (listNum != calcNum || listNum < 0) {
					System.out.println(sourceID + " " + ruptureID + " " + listNum + "-->" + calcNum);
					int asdf[] = {sourceID, ruptureID};
					bad.add(asdf);
				}
			}
		}
		return bad;
	}

	/**
	 * Inserts surface locations information for each rupture in table "Points"
	 * @param erfName
	 * @param sourceId
	 * @param ruptureId
	 * @param lat
	 * @param lon
	 * @param depth
	 * @param rake
	 * @param dip
	 * @param strike
	 */
	public void insertRuptureSurface(int erfId, ArrayList<Integer> sourceId, ArrayList<Integer> ruptureId, 
			ArrayList<Double> lat, ArrayList<Double> lon, ArrayList<Double> depth, ArrayList<Double> rake, 
			ArrayList<Double> dip, ArrayList<Double> strike) {
		//		generate the SQL to be inserted in the ERF_Metadata table
		String sql = null;
		int size = sourceId.size();
		int maxInsertPoints = 1000;
		try {
			for (int i=0; i<size; i++) {

				if (i % maxInsertPoints == 0) {
					if (i > 0) {
						dbaccess.insertUpdateOrDeleteData(sql);
					}

					sql = "INSERT into Points"+ 
					"(ERF_ID,Source_ID,Rupture_ID,Lat,Lon,Depth,Rake,Dip,Strike) VALUES";
				}
				sql += "('"+erfId+"','"+sourceId.get(i)+"','"+
				ruptureId.get(i)+"','"+lat.get(i).floatValue()+"','"+lon.get(i).floatValue()+"','"+depth.get(i).floatValue()+"','"+
				rake.get(i).floatValue()+"','"+dip.get(i).floatValue()+"','"+strike.get(i).floatValue()+"') ";
				if ((i + 1) == size || (i + 1) % maxInsertPoints == 0) { // this is the last one, no comma at end

				} else {
					sql += ",";
				}
			}
			dbaccess.insertUpdateOrDeleteData(sql);
		} catch (SQLException e) {
			// TODO Auto-generated catch block
			int num = sql.length() - 1;
			if (num > 100)
				System.out.println(sql.substring(0, 100) + " ... " + sql.substring(num - 30));
			else
				System.out.println(sql);
			e.printStackTrace();
		}
	}

	/**
	 * Inserts surface locations information for each rupture in table "Points"
	 * @param erfName
	 * @param sourceId
	 * @param ruptureId
	 * @param lat
	 * @param lon
	 * @param depth
	 * @param rake
	 * @param dip
	 * @param strike
	 */
	public void insertBatchRuptureSurface(int erfId, ArrayList<Integer> sourceId, ArrayList<Integer> ruptureId, 
			ArrayList<Double> lat, ArrayList<Double> lon, ArrayList<Double> depth, ArrayList<Double> rake, 
			ArrayList<Double> dip, ArrayList<Double> strike) {

		ArrayList<Integer> sourceIds = new ArrayList<Integer>();
		ArrayList<Integer> ruptureIds = new ArrayList<Integer>(); 
		ArrayList<Double> lats = new ArrayList<Double>();
		ArrayList<Double> lons = new ArrayList<Double>();
		ArrayList<Double> depths = new ArrayList<Double>();
		ArrayList<Double> rakes = new ArrayList<Double>(); 
		ArrayList<Double> dips = new ArrayList<Double>();
		ArrayList<Double> strikes = new ArrayList<Double>();

		for (int i=0; i<sourceIds.size(); i++) {
			if (i % 1000 == 0) {
				sourceIds.clear();
				sourceIds.clear();
				sourceIds.clear();
				sourceIds.clear();
				sourceIds.clear();
				sourceIds.clear();
				sourceIds.clear();
				sourceIds.clear();
				sourceIds.clear();
			}
		}
	}

	/**
	 * 
	 * Inserts ERF name and description in table ERF_IDs
	 * @param erfName
	 * @param erfDesc
	 * @return Autoincremented Id from the table for the last inserted ERF
	 */
	public int insertERFId(String erfName, String erfDesc) {
		//		generate the SQL to be inserted in the ERF_Metadata table
		String sql = "INSERT into ERF_IDs"+ 
		"(ERF_Name,ERF_Description)"+
		"VALUES('"+erfName+"','"+erfDesc+"')";
		try {
			dbaccess.insertUpdateOrDeleteData(sql);
		} catch (SQLException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}		
		return getInserted_ERF_ID(erfName);

	}

	/**
	 * Retrives the id of the ERF from the table ERF_IDs  for the corresponding ERF_Name.
	 * @param erfName
	 * @return
	 */
	public int getInserted_ERF_ID(String erfName){
		String sql = "SELECT ERF_ID from ERF_IDs WHERE ERF_Name = "+"'"+erfName+"'";
		ResultSet rs = null;
		try {
			rs = dbaccess.selectData(sql);
		} catch (SQLException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		}		 
		try {
			rs.first();
			String erfId = rs.getString("ERF_ID");
			rs.close();
			return Integer.parseInt(erfId);
		} catch (SQLException e) {
			e.printStackTrace();
		}
		return -1;
	}

	/**
	 * Retrives the rupture probability
	 * @param erfId
	 * @param sourceId
	 * @param rupId
	 * @return
	 * @throws SQLException 
	 */
	public double getRuptureProb(int erfId,int sourceId,int rupId) {
		String sql = "SELECT Prob from Ruptures WHERE ERF_ID = "+"'"+erfId+"' and "+
		"Source_ID = '"+sourceId+"' and Rupture_ID = '"+rupId+"'";
		ResultSet rs = null;
		try {
			rs = dbaccess.selectData(sql);
		} catch (SQLException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		}
		double rupProb = Double.NaN;
		try{
			rs.first();
			rupProb = Double.parseDouble(rs.getString("Prob"));
			rs.close();

		}catch (SQLException e) {
			e.printStackTrace();
		}
		return rupProb;
	}

	public void insertSrcRupInDB(){
		this.insertSrcRupInDB(null, 0, 0);
	}

	private boolean isInsideCutoffForRegion(GriddedRegion region, ProbEqkRupture rupture) {

		long startTime = System.currentTimeMillis();

		Region circular;

		EvenlyGriddedSurfaceAPI rupSurface = new EvenlyGridCenteredSurface(rupture.getRuptureSurface());

		ListIterator it = rupSurface.getAllByRowsIterator();

		int numLocs = region.getNodeCount();

		while (it.hasNext()) {
			Location ptLoc = (Location) it.next();

			for (int i=0; i<numLocs; i++) {
				Location loc = region.locationForIndex(i);
				circular = new Region(loc, CybershakeSiteInfo2DB.CUT_OFF_DISTANCE);

				if (circular.contains(ptLoc)) {
					System.out.println("Took " + ((System.currentTimeMillis() - startTime) / 1000d) + " secs to FIND...inserting rupture...");
					return true;
				}
			}
		}
		System.out.println("Took " + ((System.currentTimeMillis() - startTime) / 1000d) + " secs to NOT FIND");
		return false;
	}

	public void insertSrcRupInDB(GriddedRegion region, int startSource, int startRup){
		int numSources = eqkRupForecast.getNumSources();
		int erfId = this.getInserted_ERF_ID(eqkRupForecast.getName());

		boolean forRegion = (region != null);
		for(int sourceId = 0;sourceId<numSources;++sourceId){
			if (sourceId < startSource)
				continue;
			//			 get the ith source
			ProbEqkSource source  = (ProbEqkSource)eqkRupForecast.getSource(sourceId);
			int numRuptures = source.getNumRuptures();
			System.out.println("Insert source "+(sourceId+1)+" of "+numSources + " (" + numRuptures + " rups)");
			for(int ruptureId=0;ruptureId<numRuptures;++ruptureId){
				if (ruptureId < startRup)
					continue;
				else
					startRup = 0;
				System.out.println("Inserting rupture " + (ruptureId+1) + " of " + numRuptures);
				//getting the rupture on the source and its gridCentered Surface
				ProbEqkRupture rupture = source.getRupture(ruptureId);

				if (forRegion) {
					if (!this.isInsideCutoffForRegion(region, rupture))
						continue;
				}

				this.insertSrcRupInDB(eqkRupForecast, erfId, sourceId, ruptureId);
			}
		}
	}

	public void insertAllRupsForSourceRegionInDB(GriddedRegion region, EqkRupForecastAPI forecast, int erfID, int sourceID, boolean skipDuplicates) {
		ProbEqkSource source  = (ProbEqkSource)forecast.getSource(sourceID);
		int numRuptures = source.getNumRuptures();
		SiteInfo2DB siteInfo = null;
		if (skipDuplicates)
			siteInfo = new SiteInfo2DB(this.dbaccess);
		for(int ruptureId=0;ruptureId<numRuptures;++ruptureId){
			if (skipDuplicates) {
				if (siteInfo.isRupInDB(erfID, sourceID, ruptureId)) {
					//					  System.out.println("It's already there!");
					continue;
				}
			}
			if (this.isInsideCutoffForRegion(region, source.getRupture(ruptureId))) {
				System.out.println("Found one that's not in there!");
				this.insertSrcRupInDB(forecast, erfID, sourceID, ruptureId);
			}
		}
		System.out.println("Done with source " + sourceID);
	}

	/**
	 * Insert the specified rupture from the given forecast
	 * @param forecast
	 * @param erfID
	 * @param sourceID
	 * @param rupID
	 */
	public void insertSrcRupInDB(EqkRupForecastAPI forecast, int erfID, int sourceID, int rupID) {
		ProbEqkSource source  = (ProbEqkSource)forecast.getSource(sourceID);
		String sourceName = source.getName();
		// getting the rupture on the source and its gridCentered Surface
		ProbEqkRupture rupture = source.getRupture(rupID);
		double mag = rupture.getMag();
		double prob = rupture.getProbability();
		double aveRake = rupture.getAveRake();
		EvenlyGriddedSurfaceAPI rupSurface = new EvenlyGridCenteredSurface(
				rupture.getRuptureSurface());
		// Local Strike for each grid centered location on the rupture
		double[] localStrikeList = this.getLocalStrikeList(rupture
				.getRuptureSurface());
		double dip = rupSurface.getAveDip();
		int numRows = rupSurface.getNumRows();
		int numCols = rupSurface.getNumCols();
		int numPoints = numRows * numCols;
		double gridSpacing = rupSurface.getGridSpacingAlongStrike();
		if(!rupSurface.isGridSpacingSame()) throw new RuntimeException("this may not work now that grid spacing can differ along strike and down dip");
		Location surfaceStartLocation = (Location) rupSurface.get(0, 0);
		Location surfaceEndLocation = (Location) rupSurface.get(0, numCols - 1);
		double surfaceStartLat = surfaceStartLocation.getLatitude();
		double surfaceStartLon = surfaceStartLocation.getLongitude();
		double surfaceStartDepth = surfaceStartLocation.getDepth();
		double surfaceEndLat = surfaceEndLocation.getLatitude();
		double surfaceEndLon = surfaceEndLocation.getLongitude();
		double surfaceEndDepth = surfaceEndLocation.getDepth();
		System.out.println("Inserting rupture into database...");
		insertERFRuptureInfo(erfID, sourceID, rupID, sourceName, null, mag,
				prob, gridSpacing, surfaceStartLat, surfaceStartLon,
				surfaceStartDepth, surfaceEndLat, surfaceEndLon,
				surfaceEndDepth, numRows, numCols, numPoints);
		System.out.println("Inserting rupture surface points into database...");
		//		for (int k = 0; k < numRows; ++k) {
		//			for (int j = 0; j < numCols; ++j) {
		//				Location loc = rupSurface.getLocation(k, j);
		//				insertRuptureSurface(erfID, sourceID, rupID, loc
		//						.getLatitude(), loc.getLongitude(), loc.getDepth(),
		//						aveRake, dip, localStrikeList[j]);
		//			}
		//		}

		ArrayList<Integer> sourceIds = new ArrayList<Integer>();
		ArrayList<Integer> ruptureIds = new ArrayList<Integer>(); 
		ArrayList<Double> lats = new ArrayList<Double>();
		ArrayList<Double> lons = new ArrayList<Double>();
		ArrayList<Double> depths = new ArrayList<Double>();
		ArrayList<Double> rakes = new ArrayList<Double>(); 
		ArrayList<Double> dips = new ArrayList<Double>();
		ArrayList<Double> strikes = new ArrayList<Double>();
		for(int k=0;k<numRows;++k){
			for (int j = 0; j < numCols; ++j) {
				Location loc = rupSurface.getLocation(k,j);
				sourceIds.add(sourceID);
				ruptureIds.add(rupID);
				lats.add(loc.getLatitude());
				lons.add(loc.getLongitude());
				depths.add(loc.getDepth());
				rakes.add(aveRake);
				dips.add(dip);
				strikes.add(localStrikeList[j]);
			}
		}
		this.insertRuptureSurface(erfID, sourceIds, ruptureIds, lats, lons, depths, rakes, dips, strikes);
	}


	/**
	 * Returns the local strike list for a given rupture
	 * @param surface GriddedSurfaceAPI
	 * @return double[]
	 */
	private double[] getLocalStrikeList(EvenlyGriddedSurfaceAPI surface){
		int numCols = surface.getNumCols();
		double[] localStrike = null;
		//if it not a point surface, then get the Azimuth(strike) for 2 neighbouring
		//horizontal locations on the rupture surface.
		//if it is a point surface then it will be just having one location so
		//in that we take the Ave. Strike for the Surface.
		if(! (surface instanceof PointSurface)){
			localStrike = new double[numCols - 1];
			for (int i = 0; i < numCols - 1; ++i) {
				Location loc1 = surface.getLocation(0, i);
				Location loc2 = surface.getLocation(0, i + 1);
				double strike = LocationUtils.azimuth(loc1, loc2);
				localStrike[i] = strike;
			}
		}
		else if(surface instanceof PointSurface) {
			localStrike = new double[1];
			localStrike[0]= surface.getAveStrike();
		}

		return localStrike;
	}	  

	public void insertForecaseInDB(String erfDescription, GriddedRegion region){
		int erfId = insertERFId(eqkRupForecast.getName(), erfDescription);

		ListIterator it = eqkRupForecast.getAdjustableParamsIterator();
		//adding the forecast parameters
		while(it.hasNext()){
			ParameterAPI param = (ParameterAPI)it.next();
			Object paramValue = param.getValue();
			if(paramValue instanceof String)
				paramValue = ((String)paramValue).replaceAll("'", "");
			String paramType = param.getType();
			paramType = paramType.replaceAll("Parameter", "");
			insertERFParams(erfId, param.getName(), paramValue.toString(), paramType,param.getUnits());
		}
		it = eqkRupForecast.getTimeSpan().getAdjustableParamsIterator();
		//adding the timespan parameters
		while(it.hasNext()){
			ParameterAPI param = (ParameterAPI)it.next();
			String paramType = param.getType();
			paramType = paramType.replaceAll("Parameter", "");
			insertERFParams(erfId, param.getName(), param.getValue().toString(), paramType,param.getUnits());
		}
		//inserts the rupture information in the database
		insertSrcRupInDB(region, 0, 0);
	}

	public void deleteRupture(int erfID, int srcID, int rupID) {
		//generate the SQL to be inserted in the ERF_Metadata table
		String sql = "DELETE FROM Ruptures WHERE ERF_ID=" + erfID + " AND Source_ID=" + srcID + " AND Rupture_ID=" + rupID;
		try {
			dbaccess.insertUpdateOrDeleteData(sql);
		} catch (SQLException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}

	public void deleteRupturePoints(int erfID, int srcID, int rupID) {
		//generate the SQL to be inserted in the ERF_Metadata table
		String sql = "DELETE FROM Points WHERE ERF_ID=" + erfID + " AND Source_ID=" + srcID + " AND Rupture_ID=" + rupID;
		try {
			dbaccess.insertUpdateOrDeleteData(sql);
		} catch (SQLException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}

	public void insertForecaseInDB(String erfDescription){
		this.insertForecaseInDB(erfDescription, null);
	}

	/**
	 * returns the instance of the last inserted ERF
	 * @return
	 */
	public EqkRupForecastAPI getERF_Instance(){
		return this.eqkRupForecast;
	}

	public int getSourceIDFromName(int erfID, String name) {
		String sql = "SELECT distinct Source_ID from Ruptures WHERE ERF_ID=" + erfID + " AND Source_Name='" + name + "'";
		ResultSet rs = null;
		try {
			rs = dbaccess.selectData(sql);
		} catch (SQLException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		}		 
		try {
			rs.first();
			int id = rs.getInt("Source_ID");
			rs.close();
			return id;
		} catch (SQLException e) {
			System.err.println("Couldn't get an ID for name: '" + name + "'");
			//			  e.printStackTrace();
		}
		return -1;
	}
	
	private String getHypoInsertStr(int erfID, int rupVarScenID, String rupVarLFN, Location hypocenter) {
		String sql = "UPDATE Rupture_Variations ";
		sql += "SET Hypocenter_Lat=" + hypocenter.getLatitude() + ",";
		sql += "Hypocenter_Lon=" + hypocenter.getLongitude() + ",";
		sql += "Hypocenter_Depth=" + hypocenter.getDepth() + " ";
		sql += "WHERE ERF_ID=" + erfID + " AND Rup_Var_Scenario_ID=" + rupVarScenID + " ";
		sql += "AND Rup_Var_LFN='" + rupVarLFN + "'";
		
		return sql;
	}
	
	public int updateHypocenterForRupVar(int erfID, int rupVarScenID,
					ArrayList<String> rupVarLFNs, ArrayList<Location> hypocenters) {
		
		String sqlPref = "UPDATE Rupture_Variations SET ";
		String latPart = "Hypocenter_Lat = CASE\n";
		String lonPart = "Hypocenter_Lon = CASE\n";
		String depPart = "Hypocenter_Depth = CASE\n";
		
		for (int i=0; i< hypocenters.size(); i++) {
			String rupVarLFN = rupVarLFNs.get(i);
			Location hypocenter = hypocenters.get(i);
			
			String prefix = "WHEN (Rup_Var_LFN='" + rupVarLFN + "') THEN ";
			latPart += prefix + hypocenter.getLatitude() + "\n";
			lonPart += prefix + hypocenter.getLongitude() + "\n";
			depPart += prefix + hypocenter.getDepth() + "\n";
		}
		latPart += "ELSE Hypocenter_Lat\nEND";
		lonPart += "ELSE Hypocenter_Lon\nEND";
		depPart += "ELSE Hypocenter_Depth\nEND";
		
		String where = "WHERE ERF_ID=" + erfID + " AND Rup_Var_Scenario_ID=" + rupVarScenID;
		
		String sql = sqlPref + latPart + "\n" + where;
//		System.out.println(sql);
//		System.exit(0);
		
		try {
			int latNum = dbaccess.insertUpdateOrDeleteData(sql);
			sql = sqlPref + lonPart + "\n" + where;
			int lonNum = dbaccess.insertUpdateOrDeleteData(sql);
			sql = sqlPref + depPart + "\n" + where;
			int depNum = dbaccess.insertUpdateOrDeleteData(sql);
			if (latNum == lonNum && lonNum == depNum)
				return latNum;
			System.err.println("WARNING...weird insert. Affected rows (lat, lon, dep): "
						+ latNum + " " + lonNum + " " + depNum);
			return -1;
		} catch (SQLException e) {
			System.out.println(sql);
			e.printStackTrace();
			return -1;
		}
	}

	public int updateHypocenterForRupVar(int erfID, int rupVarScenID,
			String rupVarLFN, Location hypocenter) {
		String sql = getHypoInsertStr(erfID, rupVarScenID, rupVarLFN, hypocenter);
		
		System.out.println(sql);
		
		try {
			return dbaccess.insertUpdateOrDeleteData(sql);
		} catch (SQLException e) {
			e.printStackTrace();
			return -1;
		}
	}

	public static void main(String args[]) {
		DBAccess db = Cybershake_OpenSHA_DBApplication.db;
		ERF2DB erf2db = new ERF2DB(db);
		String name = "Ventura-Pitas Point";
		//		  System.out.println(name + ": " + erf2db.getSourceIDFromName(34, name));
		ArrayList<int[]> bad = erf2db.checkNumPoints(35);

		if (bad.size() > 0) {
			for (int[] it : bad) {
				System.out.println("BAD: " + it[0] + " " + it[1]);
			}
		} else {
			System.out.println("All checks out!");
		}

		db.destroy();
	}

}
