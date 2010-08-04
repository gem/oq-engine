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

package org.opensha.refFaultParamDb.dao.db;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;

import oracle.spatial.geometry.JGeometry;

import org.opensha.commons.geo.Location;
import org.opensha.refFaultParamDb.dao.exception.InsertException;
import org.opensha.refFaultParamDb.dao.exception.QueryException;
import org.opensha.refFaultParamDb.dao.exception.UpdateException;
import org.opensha.refFaultParamDb.vo.EstimateInstances;
import org.opensha.refFaultParamDb.vo.PaleoSite;
import org.opensha.refFaultParamDb.vo.PaleoSitePublication;
import org.opensha.refFaultParamDb.vo.PaleoSiteSummary;

/**
 * <p>Title: PaleoSiteDB_DAO.java </p>
 * <p>Description: Performs insert/delete/update on PaleoSite table on oracle database</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */


public class PaleoSiteDB_DAO  {
	private final static String SEQUENCE_NAME = "Paleo_Site_Sequence";
	private final static String TABLE_NAME="Paleo_Site";
	private final static String SITE_ID="Site_Id";
	//private final static String FAULT_SECTION_ID="Fault_Section_Id";
	private final static String ENTRY_DATE="Entry_Date";
	private final static String SITE_NAME="Site_Name";
	private final static String SITE_LOCATION1="Site_Location1";
	private final static String SITE_LOCATION2="Site_Location2";
	private final static String GENERAL_COMMENTS="General_Comments";
	private final static String OLD_SITE_ID="Old_Site_Id";
	private final static String DIP_EST_ID = "Dip_Est_Id";

	private final static int SRID=8307;

	private DB_AccessAPI dbAccess;
	// estimate instance DAO
	private EstimateInstancesDB_DAO estimateInstancesDAO;
	// paleo site publication DAO
	private PaleoSitePublicationsDB_DAO paleoSitePublicationDAO;

	public PaleoSiteDB_DAO(DB_AccessAPI dbAccess) {
		setDB_Connection(dbAccess);
	}

	public void setDB_Connection(DB_AccessAPI dbAccess) {
		this.dbAccess = dbAccess;
		estimateInstancesDAO = new EstimateInstancesDB_DAO(dbAccess);
		paleoSitePublicationDAO = new PaleoSitePublicationsDB_DAO(dbAccess);
	}

	/**
	 * Add a new paleo site
	 *
	 * @param paleoSite
	 * @throws InsertException
	 */
	public void addPaleoSite(PaleoSite paleoSite) throws InsertException {
		int paleoSiteId = paleoSite.getSiteId();
		String systemDate;
		try {
			if(paleoSiteId<=0)
				paleoSiteId = dbAccess.getNextSequenceNumber(SEQUENCE_NAME);
			systemDate = dbAccess.getSystemDate();
			paleoSite.setSiteId(paleoSiteId);
			paleoSite.setEntryDate(systemDate);
		}catch(SQLException e) {
			throw new InsertException(e.getMessage());
		}

		JGeometry location1;
		// if elevation is available
		if(!Float.isNaN(paleoSite.getSiteElevation1()))
			location1 = new JGeometry(paleoSite.getSiteLon1(),
					paleoSite.getSiteLat1(),
					paleoSite.getSiteElevation1(),
					SRID);
		// if elevation not available
		else location1 = new JGeometry(paleoSite.getSiteLon1(),
				paleoSite.getSiteLat1(),
				SRID);



		ArrayList<JGeometry> geomteryObjectList = new ArrayList<JGeometry>();
		geomteryObjectList.add(location1);

		String colNames="", colVals="";

		// check whether dip estimate exists
		EstimateInstances dipEst = paleoSite.getDipEstimate();
		if(dipEst!=null) {
			colNames = DIP_EST_ID+",";
			int id = this.estimateInstancesDAO.addEstimateInstance(dipEst);
			colVals=""+id+",";
		}

		//check whether second location exists or not
		JGeometry location2;
		if(!Float.isNaN(paleoSite.getSiteLat1())) {
			// if elevation is available
			if(!Float.isNaN(paleoSite.getSiteElevation2()))
				location2 = new JGeometry(paleoSite.getSiteLon2(),
						paleoSite.getSiteLat2(),
						paleoSite.getSiteElevation2(),
						SRID);
			// if elevation is not available
			else location2 = new JGeometry(paleoSite.getSiteLon2(),
					paleoSite.getSiteLat2(),
					SRID);
			geomteryObjectList.add(location2);
			colNames+=SITE_LOCATION2+",";
			colVals+="?,";
		}

		String sql = "insert into "+TABLE_NAME+"("+ SITE_ID+","+
		ENTRY_DATE+","+SITE_NAME+","+SITE_LOCATION1+","+colNames+
		GENERAL_COMMENTS+","+OLD_SITE_ID+") "+
		" values ("+paleoSiteId+",'"+systemDate+
		"','"+paleoSite.getSiteName()+"',?,"+colVals+"'"+paleoSite.getGeneralComments()+"','"+
		paleoSite.getOldSiteId()+"')";
		try {	
			//System.out.println(sql);
			dbAccess.insertUpdateOrDeleteData(sql, geomteryObjectList);
			// put the reference, site type and representative strand index
			ArrayList<PaleoSitePublication> paleoSitePubList = paleoSite.getPaleoSitePubList();
			for(int i=0; i<paleoSitePubList.size(); ++i ) {
				// set the site entry date and site id
				PaleoSitePublication paleoSitePub = (PaleoSitePublication)paleoSitePubList.get(i);
				paleoSitePub.setSiteId(paleoSiteId);
				paleoSitePub.setSiteEntryDate(systemDate);
				this.paleoSitePublicationDAO.addPaleoSitePublicationInfo(paleoSitePub);
			}
		}
		catch(SQLException e) {
			throw new InsertException(e.getMessage());
		}
	}


	/**
	 * Get paleo site data based on paleoSiteId
	 * @param paleoSiteId
	 * @return
	 * @throws QueryException
	 */
	public PaleoSite getPaleoSite(int paleoSiteId) throws QueryException {
		String condition = " where "+SITE_ID+"="+paleoSiteId;
		ArrayList<PaleoSite> paleoSiteList = query(condition);
		PaleoSite paleoSite = null;
		if(paleoSiteList.size()>0) paleoSite = (PaleoSite)paleoSiteList.get(0);
		return paleoSite;
	}

	/**
	 * Get paleo site data based on qfaultSiteId
	 * @param qFaultSiteId
	 * @return
	 * @throws QueryException
	 */
	public PaleoSite getPaleoSiteByQfaultId(String qFaultSiteId) throws QueryException {
		String condition = " where "+OLD_SITE_ID+"='"+qFaultSiteId+"'";
		ArrayList<PaleoSite> paleoSiteList = query(condition);
		PaleoSite paleoSite = null;
		if(paleoSiteList.size()>0) paleoSite = (PaleoSite)paleoSiteList.get(0);
		return paleoSite;
	}

	/**
	 * Get paleo site data based on paleoSiteName
	 * @param paleoSiteName
	 * @return
	 * @throws QueryException
	 */
	public PaleoSite getPaleoSite(String paleoSiteName) throws QueryException {
		String condition = " where "+SITE_NAME+"='"+paleoSiteName+"'";
		ArrayList<PaleoSite> paleoSiteList = query(condition);
		PaleoSite paleoSite = null;
		if(paleoSiteList.size()>0) paleoSite = (PaleoSite)paleoSiteList.get(0);
		return paleoSite;
	}


	/**
	 * It returns a list of PaleoSiteSummary objects. Each such object has a name
	 * and id. If there is no name corresponding to paleo site in the database,
	 * then this function gets the references for the paleo site and sets it as the name
	 * which can then be used subsequently.
	 *
	 * @return
	 * @throws QueryException
	 */
	public ArrayList<PaleoSiteSummary> getAllPaleoSiteNames() throws QueryException {
		ArrayList<PaleoSiteSummary> paleoSiteSummaryList = new ArrayList<PaleoSiteSummary>();
		String sql =  "select "+SITE_ID+","+SITE_NAME+" from "+TABLE_NAME+" order by "+SITE_NAME;
		try {
			ResultSet rs  = dbAccess.queryData(sql);
			while(rs.next())  {
				PaleoSiteSummary paleoSiteSummary = new PaleoSiteSummary();
				paleoSiteSummary.setSiteId(rs.getInt(SITE_ID));
				paleoSiteSummary.setSiteName(rs.getString(SITE_NAME));
				paleoSiteSummaryList.add(paleoSiteSummary);
			}
			rs.close();
		} catch(SQLException e) { throw new QueryException(e.getMessage()); }
		return paleoSiteSummaryList;
	}

	/**
	 * Get a list of PaleoSites which just have Id, Name and Locations
	 * @return
	 * @throws QueryException
	 */
	public ArrayList<PaleoSite> getPaleoSiteNameIdAndLocations() throws QueryException {
		ArrayList<PaleoSite> paleoSiteList = new ArrayList<PaleoSite>();
		String sqlWithSpatialColumnNames =  "select "+SITE_ID+","+SITE_NAME+","+SITE_LOCATION1+","+
		SITE_LOCATION2+" from "+TABLE_NAME;
		String sqlWithNoSpatialColumnNames =  "select "+SITE_ID+","+SITE_NAME+" from "+TABLE_NAME;

		ArrayList<String> spatialColumnNames = new ArrayList<String>();
		spatialColumnNames.add(SITE_LOCATION1);
		spatialColumnNames.add(SITE_LOCATION2);
		try {
			SpatialQueryResult spatialQueryResult  = dbAccess.queryData(sqlWithSpatialColumnNames, sqlWithNoSpatialColumnNames, spatialColumnNames);
			ResultSet rs = spatialQueryResult.getCachedRowSet();
			int i=0;
			while(rs.next())  {
				PaleoSite paleoSite = new PaleoSite();
				paleoSite.setSiteId(rs.getInt(SITE_ID));
				paleoSite.setSiteName(rs.getString(SITE_NAME));
				// location 1
				ArrayList<JGeometry> geometries = spatialQueryResult.getGeometryObjectsList(i++);
				setPaleoSiteLocations(paleoSite, geometries);
				paleoSiteList.add(paleoSite);
			}
			rs.close();
		} catch(SQLException e) { throw new QueryException(e.getMessage()); }
		return paleoSiteList;
	}

	/**
	 * remove a paleo site from the database
	 * @param paleoSiteId
	 * @return
	 * @throws UpdateException
	 */
	public boolean removePaleoSite(int paleoSiteId) throws UpdateException {
		String sql = "delete from "+TABLE_NAME+"  where "+SITE_ID+"="+paleoSiteId;
		try {
			int numRows = dbAccess.insertUpdateOrDeleteData(sql);
			if(numRows==1) return true;
		}
		catch(SQLException e) { throw new UpdateException(e.getMessage()); }
		return false;
	}


	/**
	 * Get all the paleo sites from the database
	 * @return
	 * @throws QueryException
	 */
	public ArrayList<PaleoSite> getAllPaleoSites() throws QueryException {
		return query(" ");
	}



	private ArrayList<PaleoSite> query(String condition) throws QueryException {
		ArrayList<PaleoSite> paleoSiteList = new ArrayList<PaleoSite>();
		String sqlWithSpatialColumnNames =  "select "+SITE_ID+",to_char("+ENTRY_DATE+") as "+ENTRY_DATE+
		","+SITE_NAME+","+SITE_LOCATION1+","+
		SITE_LOCATION2+","+
		DIP_EST_ID+","+GENERAL_COMMENTS+","+OLD_SITE_ID+
		" from "+TABLE_NAME+condition;
		String sqlWithNoSpatialColumnNames =  "select "+SITE_ID+",to_char("+ENTRY_DATE+") as "+ENTRY_DATE+
		","+SITE_NAME+","+
		DIP_EST_ID+","+GENERAL_COMMENTS+","+OLD_SITE_ID+
		" from "+TABLE_NAME+condition;

		ArrayList<String> spatialColumnNames = new ArrayList<String>();
		spatialColumnNames.add(SITE_LOCATION1);
		spatialColumnNames.add(SITE_LOCATION2);
		try {
			SpatialQueryResult spatialQueryResult  = dbAccess.queryData(sqlWithSpatialColumnNames, sqlWithNoSpatialColumnNames, spatialColumnNames);
			ResultSet rs = spatialQueryResult.getCachedRowSet();
			int i=0;
			while(rs.next())  {
				PaleoSite paleoSite = new PaleoSite();
				paleoSite.setSiteId(rs.getInt(SITE_ID));
				paleoSite.setEntryDate(rs.getString(ENTRY_DATE));


				paleoSite.setSiteName(rs.getString(SITE_NAME));

				int dipEstId = rs.getInt(DIP_EST_ID);
				if(!rs.wasNull()) paleoSite.setDipEstimate(this.estimateInstancesDAO.getEstimateInstance(dipEstId));

				paleoSite.setGeneralComments(rs.getString(GENERAL_COMMENTS));
				paleoSite.setOldSiteId(rs.getString(OLD_SITE_ID));
				paleoSite.setPaleoSitePubList(this.paleoSitePublicationDAO.getPaleoSitePublicationInfo(rs.getInt(SITE_ID)));

				ArrayList<JGeometry> geometries = spatialQueryResult.getGeometryObjectsList(i++);
				setPaleoSiteLocations(paleoSite, geometries);

				paleoSiteList.add(paleoSite);
			}
			rs.close();
		} catch(SQLException e) { throw new QueryException(e.getMessage()); }
		return paleoSiteList;
	}

	/**
	 * Get closest fault section
	 * 
	 * @param loc
	 * @return
	 */
	/*public static FaultSectionPrefData getClosestFaultSection(Location loc) {
	  double minDist = Double.MAX_VALUE, dist;
	  FaultSectionPrefData closestFaultSection=null;
	  for(int i=0; i<prefFaultSectionDataList.size(); ++i) {
		  FaultSectionPrefData  prefFaultSectionData = (FaultSectionPrefData)prefFaultSectionDataList.get(i);
		  dist  = prefFaultSectionData.getFaultTrace().getMinHorzDistToLine(loc);
		  //System.out.println(prefFaultSectionData.getSectionId()+":"+dist);
		  if(dist<minDist) {
			  minDist = dist;
			  closestFaultSection = prefFaultSectionData;
		  }
	  }
	  return closestFaultSection;
  }*/

	/**
	 * set the locations in paleo site
	 * @param paleoSite
	 * @param geometries
	 */
	private void setPaleoSiteLocations(PaleoSite paleoSite, ArrayList<JGeometry> geometries) {
		JGeometry location1 =(JGeometry) geometries.get(0);
		double []point1 = location1.getPoint();
		//location 2
		JGeometry location2 = (JGeometry) geometries.get(1);


		paleoSite.setSiteLat1((float)point1[1]);
		paleoSite.setSiteLon1((float)point1[0]);
		// if elevation available, set it else set it as NaN
		if(point1.length>2)
			paleoSite.setSiteElevation1((float)point1[2]);
		else paleoSite.setSiteElevation1(Float.NaN);
		//FaultSectionPrefData faultSectionPrefData = getClosestFaultSection(new Location(paleoSite.getSiteLat1(), paleoSite.getSiteLon1()));
		//paleoSite.setFaultSectionNameId(faultSectionPrefData.getSectionName(), faultSectionPrefData.getSectionId());
		// check whether second locations exists or not
		if(location2!=null) {
			double []point2 = location2.getPoint();
			paleoSite.setSiteLat2((float)point2[1]);
			paleoSite.setSiteLon2((float)point2[0]);
			// if elevation available, set it else set it as NaN
			if(point2.length>2)
				paleoSite.setSiteElevation2((float)point2[2]);
			else paleoSite.setSiteElevation2(Float.NaN);
			//faultSectionPrefData = getClosestFaultSection(new Location(paleoSite.getSiteLat2(), paleoSite.getSiteLon2()));
			//paleoSite.setGeneralComments(paleoSite.getGeneralComments()+"; Other associated fault section Id="+faultSectionPrefData.getSectionId());
		}
	}

	public static void main(String args[]) {
		ArrayList<Location> locList = new ArrayList<Location>();
		locList.add(new Location(37.5104,	-121.8346));
		locList.add(new Location(33.7701,	-117.4909));
		locList.add(new Location(33.2071,	-116.7273));
		locList.add(new Location(33.4100,	-117.0400));
		locList.add(new Location(33.9303,	-117.8437));
		locList.add(new Location(35.4441,	-117.6815));
		locList.add(new Location(34.9868,	-118.5080));
		locList.add(new Location(37.9306,	-122.2977));
		locList.add(new Location(37.5563,	-121.9739));
		locList.add(new Location(38.0320,	-122.7891));
		locList.add(new Location(36.9415,	-121.6729));
		locList.add(new Location(38.5200,	-123.2400));
		locList.add(new Location(37.5207,	-122.5135));
		locList.add(new Location(33.6153,	-116.7091));
		locList.add(new Location(32.9975,	-115.9436));
		locList.add(new Location(33.9730,	-116.8170));
		locList.add(new Location(35.1540,	-119.7000));
		locList.add(new Location(33.7414,	-116.1870));
		locList.add(new Location(34.4556,	-117.8870));
		locList.add(new Location(34.2544,	-117.4340));
		locList.add(new Location(34.1158,	-117.1370));
		locList.add(new Location(33.8200,	-116.3010));
		locList.add(new Location(34.3697,	-117.6680));
		for(int i=0; i<locList.size(); ++i) {
			//System.out.println(PaleoSiteDB_DAO.getClosestFaultSection(locList.get(i)).getSectionName());
		}

		/*
 		// FOR OBTAINING QFAULT ID for Peter Bird's DATA 
 		ArrayList lines=null;
		try {
			lines = FileUtils.loadFile("WG_QFault.txt");
		} catch (FileNotFoundException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
 		PaleoSiteDB_DAO dao = new PaleoSiteDB_DAO(DB_AccessAPI.dbConnection);
 		for(int i=0;i<lines.size(); ++i) {
 			int id = Integer.parseInt((String)lines.get(i))+260;
 			//System.out.println(id);
 			PaleoSite site= dao.getPaleoSite(id);
 			String qFaultId;
 			if(site==null) qFaultId="null";
 			else qFaultId = site.getOldSiteId();
 			//if(qFaultId==null || qFaultId.equalsIgnoreCase("null")) qFaultId="";
 			System.out.println(qFaultId);
 		}*/

		// FOR OBTAINING REF CATEGORY FOR PETER BIRD DATA
		/*ArrayList lines2=null, lines1=null;
 		try {
 			lines1 = FileUtils.loadFile("RefCat1.txt"); // file with ref categories
 			lines2 = FileUtils.loadFile("RefCat2.txt"); 
 			boolean found = false;
 			for(int i=0; i<lines2.size(); ++i) {
 				String line2 = (String)lines2.get(i);
 				StringTokenizer tokenizer2 = new StringTokenizer(line2,"|");
 				String faultId2 = tokenizer2.nextToken().trim();
 				String citation2 = tokenizer2.nextToken().trim();
 				//System.out.println(faultId2+"\t"+citation2);
 				found = false;
 				for(int j=0; j<lines1.size(); ++j) {
 					String line1 = (String)lines1.get(j);
 	 				StringTokenizer tokenizer1 = new StringTokenizer(line1,"|");
 	 				String faultId1 = tokenizer1.nextToken().trim();
 	 				String citation1 = tokenizer1.nextToken().trim();
 	 				String refType = tokenizer1.nextToken().trim();
 	 				if(faultId1.equalsIgnoreCase(faultId2) &&
 	 					citation1.equalsIgnoreCase(citation2)) {
 	 					System.out.println(refType);
 	 					found=true;
 	 					break;
 	 				}

 				}
 				if(!found) System.out.println("****Not found****"+faultId2+","+citation2);

 			}



 		}catch(Exception e) {
 			e.printStackTrace();
 		}*/
	}

}
