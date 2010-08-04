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

import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;

public class SiteInfo2DB implements SiteInfo2DBAPI {

	private DBAccess dbaccess;

	
	public SiteInfo2DB(DBAccess dbaccess){
		this.dbaccess = dbaccess;
	}
	
	/**
	 * Inserts the new site in the database table CyberShake_Sites
	 * @param siteName
	 * @param siteShortName
	 * @param lat
	 * @param lon
	 * @returns the Site Id for the last inserted Site
	 */
	public int insertSite(String siteName, String siteShortName, double lat,
			double lon) {
//		generate the SQL to be inserted in the Sites table
		String sql = "INSERT into CyberShake_Sites"+ 
		             "(CS_Site_Name,CS_Short_Name,CS_Site_Lat,CS_Site_Lon)"+
		             "VALUES('"+siteName+"','"+siteShortName+"','"+
		(float)lat+"','"+(float)lon+"')";
		try {
			dbaccess.insertUpdateOrDeleteData(sql);
		} catch (SQLException e) {
			if (e.getMessage().contains("Duplicate")) {
				System.out.println("Duplicate");
			} else {
				e.printStackTrace();
			}
		}		
		return getSiteId(siteShortName);
		
	}
	
	public void setSiteType(int siteID, int typeID) {
		String sql = "UPDATE CyberShake_Sites SET CS_Site_Type_ID=" + typeID + " WHERE CS_Site_ID=" + siteID;
		
		try {
			dbaccess.insertUpdateOrDeleteData(sql);
		} catch (SQLException e) {
			e.printStackTrace();
		}		
	}
	
	public void setSiteLongName(int siteID, String longName) {
		String sql = "UPDATE CyberShake_Sites SET CS_Site_Name='" + longName + "' WHERE CS_Site_ID=" + siteID;
		
		try {
			dbaccess.insertUpdateOrDeleteData(sql);
		} catch (SQLException e) {
			e.printStackTrace();
		}		
	}

	/**
	 * Returns the site id of the cybershake site for the corresponding cybershake_short_site_name
	 * @param cybershakeShortSiteName
	 * @return
	 */
	public int getSiteId(String cybershakeShortSiteName){
//		 gets the last auto increment id from Sites table
		 String sql = "SELECT CS_Site_ID from CyberShake_Sites where CS_Short_Name = "+"'"+cybershakeShortSiteName+"'";
		 ResultSet rs = null;
		try {
			rs = dbaccess.selectData(sql);
		} catch (SQLException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		}
			try {
				rs.first();
				String siteID = rs.getString("CS_Site_ID");
				rs.close();;
				return Integer.parseInt(siteID);
				
			} catch (SQLException e) {
				e.printStackTrace();
			}
		 return -1;
	}
	
	/**
	 * Returns the site id of the cybershake site for the corresponding cybershake_short_site_name
	 * @param cybershakeShortSiteName
	 * @return
	 */
	public double getSiteCutoffDistance(String cybershakeShortSiteName){
		int id = this.getSiteId(cybershakeShortSiteName);
		return this.getSiteCutoffDistance(id);
	}
	
	/**
	 * Returns the site id of the cybershake site for the corresponding cybershake_short_site_name
	 * @param cybershakeShortSiteName
	 * @return
	 */
	public double getSiteCutoffDistance(int siteID){
//		 gets the last auto increment id from Sites table
		 String sql = "SELECT Cutoff_Dist from CyberShake_Site_Regions where CS_Site_ID=" + siteID;
		 ResultSet rs = null;
		try {
			rs = dbaccess.selectData(sql);
		} catch (SQLException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		}
			try {
				rs.first();
				double dist = rs.getDouble("Cutoff_Dist");
				rs.close();
				return dist;
				
			} catch (SQLException e) {
				e.printStackTrace();
			}
		 return CybershakeSiteInfo2DB.CUT_OFF_DISTANCE;
	}
	
	/**
	 * Returns the site id the cybershake site with given lat and lon
	 * @param lat
	 * @param lon
	 * @return
	 */
	public int getSiteId(double lat,double lon){
//		 gets the last auto increment id from Sites table
		 String sql = "SELECT CS_Site_ID from CyberShake_Sites where CS_Site_Lat = "+"'"+(float)lat+"' and "+
		              "CS_Site_Lon = "+"'"+(float)lon+"'";
		 ResultSet rs = null;
		try {
			rs = dbaccess.selectData(sql);
		} catch (SQLException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		}
			try {
				rs.first();
				String siteID = rs.getString("CS_Site_ID");
				rs.close();
				return Integer.parseInt(siteID);
			} catch (SQLException e) {
				e.printStackTrace();
			}
		 return -1;
	}
	
	/**
	 * Inserts the regional bounds (min/max lat/lon) for all cybershake sites in table CyberShake_Site_Regions
	 * @param siteId
	 * @param erfId
	 * @param cutOffDistance
	 * @param maxLat
	 * @param maxLatSrcId
	 * @param maxLatRupId
	 * @param minLat
	 * @param minLatSrcId
	 * @param minLatRupId
	 * @param maxLon
	 * @param maxLonSrcId
	 * @param maxLonRupId
	 * @param minLon
	 * @param minLonSrcId
	 * @param minLonRupId
	 */
	public void insertSiteRegionalBounds(int siteId, int erfId,
			double cutOffDistance, double maxLat, int maxLatSrcId,
			int maxLatRupId, double minLat, int minLatSrcId, int minLatRupId,
			double maxLon, int maxLonSrcId, int maxLonRupId, double minLon,
			int minLonSrcId, int minLonRupId) {
		
//		generate the SQL to be inserted in the Site_Region table
		String sql = "INSERT into CyberShake_Site_Regions VALUES('"+siteId+"','"+erfId+"','"+
		(float)cutOffDistance+"','"+(float)maxLat+"','"+maxLatSrcId+"','"+maxLatRupId+"','"+(float)maxLon+"','"+
		maxLatSrcId+"','"+maxLonRupId+"','"+(float)minLat+"','"+minLatSrcId+"','"+minLatRupId+"','"+
		(float)minLon+"','"+minLonSrcId+"','"+minLonRupId+"')";
		System.out.println(sql);
		try {
			dbaccess.insertUpdateOrDeleteData(sql);
		} catch (SQLException e) {
			if (e.getMessage().contains("Duplicate")) {
				System.out.println("Duplicate");
			} else {
				e.printStackTrace();
			}
		}
	}
	
	/**
	 * Inserts the regional bounds (min/max lat/lon) for all cybershake sites in table CyberShake_Site_Regions
	 * @param siteId
	 * @param erfId
	 * @param cutOffDistance
	 * @param maxLat
	 * @param maxLatSrcId
	 * @param maxLatRupId
	 * @param minLat
	 * @param minLatSrcId
	 * @param minLatRupId
	 * @param maxLon
	 * @param maxLonSrcId
	 * @param maxLonRupId
	 * @param minLon
	 * @param minLonSrcId
	 * @param minLonRupId
	 */
	public void updateSiteRegionalBounds(int siteId, int erfId,
			double cutOffDistance, double maxLat, int maxLatSrcId,
			int maxLatRupId, double minLat, int minLatSrcId, int minLatRupId,
			double maxLon, int maxLonSrcId, int maxLonRupId, double minLon,
			int minLonSrcId, int minLonRupId) {
		
//		generate the SQL to be inserted in the Site_Region table
//		String sql = "INSERT into CyberShake_Site_Regions VALUES('"+siteId+"','"+erfId+"','"+
//		(float)cutOffDistance+"','"+(float)maxLat+"','"+maxLatSrcId+"','"+maxLatRupId+"','"+(float)maxLon+"','"+
//		maxLatSrcId+"','"+maxLonRupId+"','"+(float)minLat+"','"+minLatSrcId+"','"+minLatRupId+"','"+
//		(float)minLon+"','"+minLonSrcId+"','"+minLonRupId+"')";
		String sql = "UPDATE CyberShake_Site_Regions ";
		sql += "SET Max_Lat="+(float)maxLat+", ";
		sql += "Max_Lat_Source_ID="+maxLatSrcId+", ";
		sql += "Max_Lat_Rupture_ID="+maxLatRupId+", ";
		sql += "Min_Lat="+(float)minLat+", ";
		sql += "Min_Lat_Source_ID="+minLatSrcId+", ";
		sql += "Min_Lat_Rupture_ID="+minLatRupId+", ";
		sql += "Max_Lon="+(float)maxLon+", ";
		sql += "Max_Lon_Source_ID="+maxLonSrcId+", ";
		sql += "Max_Lon_Rupture_ID="+maxLonRupId+", ";
		sql += "Min_Lon="+(float)minLon+", ";
		sql += "Min_Lon_Source_ID="+minLonSrcId+", ";
		sql += "Min_Lon_Rupture_ID="+minLonRupId+" ";
		
		sql += "WHERE CS_Site_ID=" + siteId + " AND ERF_ID=" + erfId + " AND Cutoff_Dist=" + cutOffDistance;
		System.out.println(sql);
		try {
			dbaccess.insertUpdateOrDeleteData(sql);
		} catch (SQLException e) {
			if (e.getMessage().contains("Duplicate")) {
				System.out.println("Duplicate");
			} else {
				e.printStackTrace();
			}
		}
	}

	/**
	 * Inserts the rupture ids that correspond to a given site within given cutoff distance
	 * inside the table CyberShake_Site_Ruptures
	 * @param siteId
	 * @param erfId
	 * @param sourceId
	 * @param ruptureId
	 * @param cutoffDistance
	 */
	public void insertSite_RuptureInfo(int siteId, int erfId, int sourceId,
			int ruptureId, double cutOffDistance) {
//		generate the SQL to be inserted in the Sites table
		String sql = "INSERT into CyberShake_Site_Ruptures VALUES('"+siteId+"','"+erfId+"','"+
		sourceId+"','"+ruptureId+"','"+cutOffDistance+"')";
		//System.out.println(sql);
		try {
			dbaccess.insertUpdateOrDeleteData(sql);
		} catch (SQLException e) {
			// TODO Auto-generated catch block
			if (e.getMessage().contains("Duplicate")) {
				System.out.println("Duplicate");
			} else {
				e.printStackTrace();
				System.exit(1);
			}
		}
	}
	
	public void insertSite_RuptureInfoList(int siteId, int erfId, int sourceId, ArrayList<Integer> ruptureId, double cutOffDistance) {
//		generate the SQL to be inserted in the Sites table
		String sql = "INSERT into CyberShake_Site_Ruptures VALUES";
		
		int size = ruptureId.size();
		for (int i=0; i<size; i++) {
			sql += "('"+siteId+"','"+erfId+"','"+sourceId+"','"+ruptureId.get(i)+"','"+cutOffDistance+"')";
			
			if ((i + 1) == size) { // this is the last one, no comma at end
				
			} else {
				sql += ",";
			}
		}
		System.out.println(sql);
		try {
			dbaccess.insertUpdateOrDeleteData(sql);
		} catch (SQLException e) {
			// TODO Auto-generated catch block
			if (e.getMessage().contains("Duplicate")) {
				System.out.println("Duplicate");
			} else {
				e.printStackTrace();
				System.exit(1);
			}
		}
		
	}
	
	/**
	 * Find out if the given rupture is already in the database
	 * @param erfID
	 * @param sourceID
	 * @param rupID
	 * @return
	 */
	public boolean isRupInDB(int erfID, int sourceID, int rupID) {
		long start = 0;
		if (Cybershake_OpenSHA_DBApplication.timer) {
			start = System.currentTimeMillis();
		}
//		System.out.println("Is " + erfID + " " + sourceID + " " + rupID + " in there?");
		String sql = "SELECT * FROM Ruptures WHERE ERF_ID="+erfID+" and Source_ID="+sourceID+" and Rupture_ID="+rupID;
		try {
			ResultSet rs = dbaccess.selectData(sql);
			if (Cybershake_OpenSHA_DBApplication.timer) {
				System.out.println("Got the select result at " + (System.currentTimeMillis() - start) + " milliseconds");
			}
			boolean result = rs.next();
			if (Cybershake_OpenSHA_DBApplication.timer) {
				long total = (System.currentTimeMillis() - start);
				System.out.println("Took " + total + " miliseconds to check if the rupture exists!!");
			}
//			if (result)
//				System.out.println("Yes it is!");
//			else
//				System.out.println("NOPE!");
		    return result;
		} catch (SQLException e) {
			e.printStackTrace();
		}
		if (Cybershake_OpenSHA_DBApplication.timer) {
			long total = (System.currentTimeMillis() - start);
			System.out.println("Took " + total + " miliseconds to check if the rupture exists!!");
		}
		return false;
	}
	
	/**
	 * Find out if the given rupture is already in the database
	 * @param erfID
	 * @param sourceID
	 * @param rupID
	 * @param siteID
	 * @return
	 */
	public boolean isSiteRupInDB(int erfID, int sourceID, int rupID, int siteID) {
		long start = 0;
		if (Cybershake_OpenSHA_DBApplication.timer) {
			start = System.currentTimeMillis();
		}
		String sql = "SELECT * FROM CyberShake_Site_Ruptures WHERE ERF_ID="+erfID+" and Source_ID="+sourceID+" and Rupture_ID="+rupID+" and CS_Site_ID="+siteID;
		try {
			ResultSet rs = dbaccess.selectData(sql);
			if (Cybershake_OpenSHA_DBApplication.timer) {
				System.out.println("Got the select result at " + (System.currentTimeMillis() - start) + " milliseconds");
			}
			boolean result = rs.next();
			if (Cybershake_OpenSHA_DBApplication.timer) {
				long total = (System.currentTimeMillis() - start);
				System.out.println("Took " + total + " miliseconds to check if the rupture exists!!");
			}
		    return result;
		} catch (SQLException e) {
			e.printStackTrace();
		}
		if (Cybershake_OpenSHA_DBApplication.timer) {
			long total = (System.currentTimeMillis() - start);
			System.out.println("Took " + total + " miliseconds to check if the rupture exists!!");
		}
		return false;
	}

	/**
	 * 
	 * @returns the list of all cybershake site locations
	 */
	public LocationList getAllSitesLocation() {
//		 gets the last auto increment id from Sites table
		 String sql = "SELECT CS_Site_Lat,CS_Site_Lon from CyberShake_Sites";
		 LocationList siteLocationList = new LocationList();
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
				  double lat = Double.parseDouble(rs.getString("CS_Site_Lat"));	
				  double lon = Double.parseDouble(rs.getString("CS_Site_Lon"));
				  Location loc = new Location(lat,lon);
				  siteLocationList.add(loc);
				  rs.next();
				}
				rs.close();
			} catch (SQLException e) {
				e.printStackTrace();
			}
		 return siteLocationList;
   }


	/**
	 * 
	 * @returns the ArrayList of short site names for all Cybershake
	 */
	public ArrayList<String> getAllSites() {	
//		 gets the last auto increment id from Sites table
		 String sql = "SELECT CS_Short_Name from CyberShake_Sites ORDER BY CS_Site_ID";
		 ArrayList<String> siteList = new ArrayList<String>();
		 ResultSet rs =null;
		try {
			rs = dbaccess.selectData(sql);
		} catch (SQLException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		}
			try {
				rs.first();
				while(!rs.isAfterLast()){
				  siteList.add(rs.getString("CS_Short_Name"));
				  rs.next();
				}
				rs.close();
			} catch (SQLException e) {
				e.printStackTrace();
			}
		 return siteList;	
     }

	/**
	 * 
	 * @param siteShortName
	 * @param srcId
	 * @returns the list of rupture ids 
	 */
	public ArrayList<Integer> getRupIdsForSite(String siteShortName, int erf_id, int srcId) {
		int siteId = this.getSiteId(siteShortName);
		return getRupIdsForSite(siteId, erf_id, srcId);
	}
	
	/**
	 * 
	 * @param siteShortName
	 * @param srcId
	 * @returns the list of rupture ids 
	 */
	public ArrayList<Integer> getRupIdsForSite(int siteID, int erf_id, int srcId) {
		String sql = "Select Rupture_ID from CyberShake_Site_Ruptures where CS_Site_ID = "+"'"+siteID+"' and ERF_ID = '" + erf_id + "' " + 
		             " and Source_ID ='"+srcId+"' order by Rupture_ID asc";
		ArrayList<Integer> rupList = new ArrayList<Integer>();
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
			  int rupId = Integer.parseInt(rs.getString("Rupture_ID"));	
			  rupList.add(rupId);
			  rs.next();
			}
			rs.close();
		} catch (SQLException e) {
			e.printStackTrace();
		}
		return rupList;
	}
	
	/**
	 * 
	 * @param siteShortName short site name as in database for Cybershake site
	 * @returns the Earthquake rupture forecast source id's for a given cybershake site.
	 */
	public void getSrcIfoForSite(String siteShortName, int erf_id, ArrayList<Integer> ids) {
		int siteId = this.getSiteId(siteShortName);
		getSrcIfoForSite(siteId, erf_id, ids);
	}
	
	/**
	 * 
	 * @param siteShortName short site name as in database for Cybershake site
	 * @returns the Earthquake rupture forecast source id's for a given cybershake site.
	 */
	public void getSrcIfoForSite(int siteID, int erf_id, ArrayList<Integer> ids) {
		String sql = "Select Source_ID from CyberShake_Site_Ruptures where CS_Site_ID = "+"'"+siteID+"' and ERF_ID = '" + erf_id + "' " +
		             " group by Source_ID order by Source_ID asc";
		System.out.println(sql);
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
			  ids.add(id);
			  rs.next();
			}
			rs.close();
		} catch (SQLException e) {
			e.printStackTrace();
		}
	}
	
	/**
	 * 
	 * @param siteShortName short site name as in database for Cybershake site
	 * @returns the Earthquake rupture forecast source id's for a given cybershake site.
	 */
	public ArrayList<Integer> getSrcIdsForSite(String siteShortName, int erf_id) {
		int siteId = this.getSiteId(siteShortName);
		return getSrcIdsForSite(siteId, erf_id);
	}

	/**
	 * 
	 * @param siteShortName short site name as in database for Cybershake site
	 * @returns the Earthquake rupture forecast source id's for a given cybershake site.
	 */
	public ArrayList<Integer> getSrcIdsForSite(int  siteID, int erf_id) {
		String sql = "Select Source_ID from CyberShake_Site_Ruptures where CS_Site_ID = "+"'"+siteID+"' and ERF_ID = '" + erf_id + "' " +
		             " group by Source_ID order by Source_ID asc";
		System.out.println(sql);
		ArrayList<Integer> srcIdList = new ArrayList<Integer>();
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
			  int srcId = Integer.parseInt(rs.getString("Source_ID"));	
			  srcIdList.add(srcId);
			  rs.next();
			}
			rs.close();
		} catch (SQLException e) {
			e.printStackTrace();
		}
		return srcIdList;
	}

	/**
	 * 
	 * @param site
	 * @returns the Location for the given cybershake site location
	 */
	public Location getLocationForSite(String site){
		 String sql = "SELECT CS_Site_Lat,CS_Site_Lon from CyberShake_Sites WHERE CS_Short_Name = '"+site+"'";
		 Location loc = null;
		 ResultSet rs = null;
		try {
			rs = dbaccess.selectData(sql);
		} catch (SQLException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		}
			try {
				rs.first();
				double lat = Double.parseDouble(rs.getString("CS_Site_Lat"));	
				double lon = Double.parseDouble(rs.getString("CS_Site_Lon"));
				loc = new Location(lat,lon);
				rs.close();
			} catch (SQLException e) {
				e.printStackTrace();
			}
		 return loc;
	}
	
	/**
	 * Gets a CybershakeSite from the Database
	 * @param shortName
	 * @return
	 */
	public CybershakeSite getSiteFromDB(String shortName) {
		String sql = "SELECT CS_Site_ID,CS_Site_Name,CS_Site_Lat,CS_Site_Lon,CS_Site_Type_ID from CyberShake_Sites WHERE CS_Short_Name = '"+shortName+"'";
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
			double lat = rs.getDouble("CS_Site_Lat");	
			double lon = rs.getDouble("CS_Site_Lon");
			int id = rs.getInt("CS_Site_ID");
			String longName = rs.getString("CS_Site_Name");
			int typeID = rs.getInt("CS_Site_Type_ID");
			rs.close();

			CybershakeSite site = new CybershakeSite(id, lat, lon, longName, shortName, typeID);
			return site;
		} catch (SQLException e) {
			e.printStackTrace();
			return null;
		}
	}
	
	/**
	 * Gets a CybershakeSite from the Database
	 * @param shortName
	 * @return
	 */
	public CybershakeSite getSiteFromDB(int siteID) {
		String sql = "SELECT CS_Site_Name,CS_Short_Name,CS_Site_Lat,CS_Site_Lon,CS_Site_Type_ID from CyberShake_Sites WHERE CS_Site_ID = "+siteID+"";
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
			double lat = rs.getDouble("CS_Site_Lat");	
			double lon = rs.getDouble("CS_Site_Lon");
			String longName = rs.getString("CS_Site_Name");
			String shortName = rs.getString("CS_Short_Name");
			int typeID = rs.getInt("CS_Site_Type_ID");
			rs.close();

			CybershakeSite site = new CybershakeSite(siteID, lat, lon, longName, shortName, typeID);
			return site;
		} catch (SQLException e) {
			e.printStackTrace();
			return null;
		}
	}
	
	/**
	 * Gets all CybershakeSite's from the Database
	 * @return
	 */
	public ArrayList<CybershakeSite> getAllSitesFromDB() {
		String sql = "SELECT CS_Site_ID,CS_Site_Name,CS_Short_Name,CS_Site_Lat,CS_Site_Lon,CS_Site_Type_ID from CyberShake_Sites";
		ResultSet rs = null;
		ArrayList<CybershakeSite> sites = new ArrayList<CybershakeSite>();
		try {
			rs = dbaccess.selectData(sql);
		} catch (SQLException e1) {
			// TODO Auto-generated catch block
			e1.printStackTrace();
		}
		
		try {
			rs.first();
			
			while (!rs.isAfterLast()) {
				double lat = rs.getDouble("CS_Site_Lat");	
				double lon = rs.getDouble("CS_Site_Lon");
				int id = rs.getInt("CS_Site_ID");
				String longName = rs.getString("CS_Site_Name");
				String shortName = rs.getString("CS_Short_Name");
				int typeID = rs.getInt("CS_Site_Type_ID");
				
				sites.add(new CybershakeSite(id, lat, lon, longName, shortName, typeID));
				rs.next();
			}
			rs.close();
		} catch (SQLException e) {
			e.printStackTrace();
		}
		
		return sites;
	}
	
	public ArrayList<CybershakeSiteType> getSiteTypes() {
		ArrayList<CybershakeSiteType> types = new ArrayList<CybershakeSiteType>();
		
		String sql = "SELECT * from CyberShake_Site_Types";
		
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
				int id = rs.getInt("CS_Site_Type_ID");
				String longName = rs.getString("CS_Site_Type_Name");
				String shortName = rs.getString("CS_Site_Type_Short_Name");
				
				types.add(new CybershakeSiteType(id, shortName, longName));
				rs.next();
			}
			rs.close();
		} catch (SQLException e) {
			e.printStackTrace();
		}
		
		return types;
	}
	
	public ArrayList<Integer> getERFsForSite(int siteID) {
		ArrayList<Integer> erfs = new ArrayList<Integer>();
		
		String sql = "select distinct ERF_ID from CyberShake_Site_Ruptures where CS_Site_ID=" + siteID;
		
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
				int id = rs.getInt("ERF_ID");
				
				erfs.add(id);
				rs.next();
			}
			rs.close();
		} catch (SQLException e) {
			e.printStackTrace();
		}
		
		return erfs;
	}
	
	public int deleteRupturesForSite(int siteId) {
		String sql = "DELETE FROM CyberShake_Site_Ruptures WHERE CS_Site_ID="+siteId;
		System.out.println(sql);
		try {
			return dbaccess.insertUpdateOrDeleteData(sql);
		} catch (SQLException e) {
//			TODO Auto-generated catch block
			e.printStackTrace();
			return -1;
		}
	}
	
	public int deleteRegionsForSite(int siteId) {
		String sql = "DELETE FROM CyberShake_Site_Regions WHERE CS_Site_ID="+siteId;
		System.out.println(sql);
		try {
			return dbaccess.insertUpdateOrDeleteData(sql);
		} catch (SQLException e) {
//			TODO Auto-generated catch block
			e.printStackTrace();
			return -1;
		}
	}
	
	public int deleteSiteRecord(int siteId) {
		String sql = "DELETE FROM CyberShake_Sites WHERE CS_Site_ID="+siteId;
		System.out.println(sql);
		try {
			return dbaccess.insertUpdateOrDeleteData(sql);
		} catch (SQLException e) {
//			TODO Auto-generated catch block
			e.printStackTrace();
			return -1;
		}
	}
	
	/**
	 * tester main function
	 * @param args
	 */
	public static void main(String args[]) {
		DBAccess db = Cybershake_OpenSHA_DBApplication.db;
		SiteInfo2DB siteDB = new SiteInfo2DB(db);
//		siteDB.isRupInDB(33, 0, 9);
		ArrayList<CybershakeSiteType> types = siteDB.getSiteTypes();
		for (CybershakeSiteType type : types) {
			System.out.println(type);
		}
		System.out.println("DONE!");
		db.destroy();
	}
}
