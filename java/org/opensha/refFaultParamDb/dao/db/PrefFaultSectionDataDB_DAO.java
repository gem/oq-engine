/**
 * 
 */
package org.opensha.refFaultParamDb.dao.db;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.HashMap;

import oracle.spatial.geometry.JGeometry;

import org.opensha.refFaultParamDb.dao.exception.InsertException;
import org.opensha.refFaultParamDb.dao.exception.QueryException;
import org.opensha.refFaultParamDb.dao.exception.UpdateException;
import org.opensha.refFaultParamDb.gui.infotools.SessionInfo;
import org.opensha.refFaultParamDb.vo.FaultSectionData;
import org.opensha.refFaultParamDb.vo.FaultSectionPrefData;
import org.opensha.sha.faultSurface.FaultTrace;

/**
 * <p>Title: PrefFaultSectionDataDB_DAO.java </p>
 * <p>Description: This class creates the Preferred Fault Section Data from Fault Section table.
 * This is needed for faster access to preferred data for scec-vdo and other purposes. </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 *
 */
public class PrefFaultSectionDataDB_DAO  implements java.io.Serializable {
	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;

	private final static String TABLE_NAME = "Pref_Fault_Section_Data";
	public final static String SECTION_ID = "Section_Id";
	public final static String PREF_SLIP_RATE = "Pref_Slip_Rate";
	public final static String PREF_DIP = "Pref_Dip";
	public final static String PREF_RAKE = "Pref_Rake";
	public final static String PREF_UPPER_DEPTH = "Pref_Upper_Depth";
	public final static String PREF_LOWER_DEPTH = "Pref_Lower_Depth";
	public final static String SECTION_NAME = "Name";
	public final static String SHORT_NAME = "Short_Name";
	public final static String FAULT_TRACE = "Fault_Section_Trace";
	public final static String PREF_ASEISMIC_SLIP= "Pref_Aseismic_Slip";
	public final static String DIP_DIRECTION = "Dip_Direction";
	private DB_AccessAPI dbAccess;
	private static HashMap<Integer, FaultSectionPrefData> cachedSections =
		new HashMap<Integer, FaultSectionPrefData>();
	private static ArrayList<FaultSectionPrefData> faultSectionsList;

	public PrefFaultSectionDataDB_DAO(DB_AccessAPI dbAccess) {
		setDB_Connection(dbAccess);
	}

	/**
	 * Set the database connection
	 * @param dbAccess
	 */
	public void setDB_Connection(DB_AccessAPI dbAccess) {
		this.dbAccess = dbAccess;
	}

	/**
	 * Remove the exisiting data from preferred data table and re-populate it.
	 *
	 */
	public void rePopulatePrefDataTable() {
		FaultSectionVer2_DB_DAO faultSectionVer2DAO = new FaultSectionVer2_DB_DAO(dbAccess);
		ArrayList<FaultSectionData> faultSectionsDataList = faultSectionVer2DAO.getAllFaultSections();
		removeAll(); // remove all the pref data
		for(int i=0; i<faultSectionsDataList.size(); ++i) {
			FaultSectionData faultSection = (FaultSectionData)faultSectionsDataList.get(i);
			addFaultSectionPrefData(faultSection.getFaultSectionPrefData());
		}

	}

	/**
	 * Refresh the preferred data for a particular fault section
	 * @param faultSectionId
	 */
	public void rePopulatePrefDataTable(int faultSectionId) {
		FaultSectionVer2_DB_DAO faultSectionVer2DAO = new FaultSectionVer2_DB_DAO(dbAccess);
		FaultSectionData faultSectionData = faultSectionVer2DAO.getFaultSection(faultSectionId);
		removeFaultSection(faultSectionId); // remove all the pref data
		addFaultSectionPrefData(faultSectionData.getFaultSectionPrefData());
	}
	/**
	 * Add a new fault section pref data to the database
	 * @param faultSection
	 * @return
	 */
	private void addFaultSectionPrefData(FaultSectionPrefData faultSectionPrefData) {

		// get JGeomtery object from fault trace
		JGeometry faultSectionTraceGeom =  FaultSectionVer2_DB_DAO.getGeomtery(faultSectionPrefData.getFaultTrace()); 
		String columnNames="";
		String columnVals = "";

		// check if slip rate is present for this fault section
		double slipRate = faultSectionPrefData.getAveLongTermSlipRate();
		if(!Double.isNaN(slipRate)) { // if slip rate estimate is present
			columnNames+=PREF_SLIP_RATE+",";
			columnVals+=slipRate+",";
		}

		// check if rake is present for this section
		double rake = faultSectionPrefData.getAveRake();
		if(!Double.isNaN(rake)) {
			columnNames+=PREF_RAKE+",";
			columnVals+=rake+",";
		}

		// check if dip direction is present for this section. Dip direction is not available wherever dip=90 degrees
		float dipDirection  = faultSectionPrefData.getDipDirection();
		if(!Float.isNaN(dipDirection)) {
			columnNames+=DIP_DIRECTION+",";
			columnVals+=dipDirection+",";
		}
		// check if short name is available
		String shortName = faultSectionPrefData.getShortName();
		if(shortName!=null) {
			columnNames+=SHORT_NAME+",";
			columnVals+="'"+shortName+"',";
		}
		// insert the fault section into the database
		ArrayList<JGeometry> geomteryObjectList = new ArrayList<JGeometry>();
		geomteryObjectList.add(faultSectionTraceGeom);
		String sql = "insert into "+TABLE_NAME+"("+ SECTION_ID+","+
		columnNames+PREF_DIP+","+PREF_UPPER_DEPTH+","+PREF_LOWER_DEPTH+","+SECTION_NAME+","+
		FAULT_TRACE+","+PREF_ASEISMIC_SLIP+") values ("+
		faultSectionPrefData.getSectionId()+","+columnVals+
		faultSectionPrefData.getAveDip()+","+faultSectionPrefData.getAveUpperDepth()+","+
		faultSectionPrefData.getAveLowerDepth()+",'"+faultSectionPrefData.getSectionName()+"',?,"+
		faultSectionPrefData.getAseismicSlipFactor()+")";
		try {
			dbAccess.insertUpdateOrDeleteData(sql, geomteryObjectList);
		}
		catch(SQLException e) {
			throw new InsertException(e.getMessage());
		}
	}

	/**
	 * Remove all preferred data
	 */
	private void removeAll() {
		String sql = "delete from "+TABLE_NAME;
		try {
			dbAccess.insertUpdateOrDeleteData(sql);
		} catch(SQLException e) { throw new UpdateException(e.getMessage()); }
	}

	/**
	 * Remove data for a specific fault section
	 *
	 */
	private void removeFaultSection(int faultSectionId) {
		String sql = "delete from "+TABLE_NAME+" where "+SECTION_ID+"="+faultSectionId;
		try {
			dbAccess.insertUpdateOrDeleteData(sql);
		} catch(SQLException e) { throw new UpdateException(e.getMessage()); }
	}

	/**
	 * Get a list of all Fault Section Pref Data from the database
	 * @return
	 */
	public ArrayList<FaultSectionPrefData> getAllFaultSectionPrefData() {
		if(faultSectionsList==null) 
			faultSectionsList = query("");
		return faultSectionsList;
	}

	/**
	 * Get Preferred fault section data for a Fault Section Id
	 * @param faultSectionId
	 * @return
	 */
	public FaultSectionPrefData getFaultSectionPrefData(int faultSectionId) {
		String condition = " where "+SECTION_ID+"="+faultSectionId;
		if(cachedSections.containsKey(new Integer(faultSectionId))) {
			return (FaultSectionPrefData)cachedSections.get(new Integer(faultSectionId));
		}
		ArrayList<FaultSectionPrefData> faultSectionsList = query(condition);	
		FaultSectionPrefData faultSectionPrefData = null;		
		if(faultSectionsList.size()>0) faultSectionPrefData = (FaultSectionPrefData)faultSectionsList.get(0);
		return faultSectionPrefData;  
	}

	/**
	 * Get the fault sections based on some filter parameter
	 * @param condition
	 * @return
	 */
	private ArrayList<FaultSectionPrefData> query(String condition) {
		ArrayList<FaultSectionPrefData> faultSectionsList = new ArrayList<FaultSectionPrefData>();
		// this awkward sql is needed else we get "Invalid scale exception"
		String sqlWithSpatialColumnNames =  "select "+SECTION_ID+
		", ("+PREF_SLIP_RATE+"+0) "+PREF_SLIP_RATE+
		", ("+PREF_DIP+"+0) "+ PREF_DIP+
		", ("+PREF_RAKE+"+0) "+ PREF_RAKE+
		", ("+PREF_UPPER_DEPTH+"+0) "+ PREF_UPPER_DEPTH+
		", ("+PREF_LOWER_DEPTH+"+0) "+PREF_LOWER_DEPTH+
		","+SECTION_NAME+","+FAULT_TRACE+","+SHORT_NAME+
		",("+PREF_ASEISMIC_SLIP+"+0) "+PREF_ASEISMIC_SLIP+
		",("+DIP_DIRECTION+"+0) "+DIP_DIRECTION+
		" from "+TABLE_NAME+condition+ " order by "+SECTION_NAME;

		String sqlWithNoSpatialColumnNames =  "select "+SECTION_ID+
		", ("+PREF_SLIP_RATE+"+0) "+PREF_SLIP_RATE+
		", ("+PREF_DIP+"+0) "+ PREF_DIP+
		", ("+PREF_RAKE+"+0) "+ PREF_RAKE+
		", ("+PREF_UPPER_DEPTH+"+0) "+ PREF_UPPER_DEPTH+
		", ("+PREF_LOWER_DEPTH+"+0) "+PREF_LOWER_DEPTH+
		","+SECTION_NAME+","+SHORT_NAME+
		",("+PREF_ASEISMIC_SLIP+"+0) "+PREF_ASEISMIC_SLIP+
		",("+DIP_DIRECTION+"+0) "+DIP_DIRECTION+" from "+TABLE_NAME+condition+" order by "+SECTION_NAME;

		//System.out.println(sqlWithSpatialColumnNames+"\n\n"+sqlWithNoSpatialColumnNames);

		ArrayList<String> spatialColumnNames = new ArrayList<String>();
		spatialColumnNames.add(FAULT_TRACE);
		try {
			SpatialQueryResult spatialQueryResult  = dbAccess.queryData(sqlWithSpatialColumnNames, sqlWithNoSpatialColumnNames, spatialColumnNames);
			ResultSet rs = spatialQueryResult.getCachedRowSet();
			int i=0;
			while(rs.next())  {
				FaultSectionPrefData faultSectionPrefData = new FaultSectionPrefData();
				faultSectionPrefData.setSectionId(rs.getInt(SECTION_ID));
				faultSectionPrefData.setSectionName(rs.getString(SECTION_NAME));
				faultSectionPrefData.setAseismicSlipFactor(rs.getFloat(PREF_ASEISMIC_SLIP));
				faultSectionPrefData.setAveDip(rs.getFloat(PREF_DIP));

				// get slip rate estimate if slip rate is provided for this fault section
				double slipRate= rs.getFloat(PREF_SLIP_RATE);
				if(rs.wasNull()) slipRate = Double.NaN;
				faultSectionPrefData.setAveLongTermSlipRate(slipRate);

				// get rake estimate if rake is provided for this fault section
				double rake= rs.getFloat(PREF_RAKE);
				if(rs.wasNull()) rake = Double.NaN;
				faultSectionPrefData.setAveRake(rake);

				float dipDirection = rs.getFloat(FaultSectionVer2_DB_DAO.DIP_DIRECTION);
				if(rs.wasNull()) dipDirection = Float.NaN;
				faultSectionPrefData.setDipDirection(dipDirection);

				faultSectionPrefData.setAveLowerDepth(rs.getFloat(PREF_LOWER_DEPTH));
				faultSectionPrefData.setAveUpperDepth(rs.getFloat(PREF_UPPER_DEPTH));

				// fault trace
				String sectionName = faultSectionPrefData.getSectionName();

				//				 short name
				String shortName = rs.getString(SHORT_NAME);
				if(!rs.wasNull()) faultSectionPrefData.setShortName(shortName);

				ArrayList<JGeometry> geometries = spatialQueryResult.getGeometryObjectsList(i++);
				FaultTrace faultTrace = FaultSectionVer2_DB_DAO.getFaultTrace(sectionName, faultSectionPrefData.getAveUpperDepth(), geometries);	
				faultSectionPrefData.setFaultTrace(faultTrace);
				faultSectionsList.add(faultSectionPrefData);
				cachedSections.put(new Integer(faultSectionPrefData.getSectionId()), faultSectionPrefData);
			}
			rs.close();
		} catch(SQLException e) { throw new QueryException(e.getMessage()); }
		return faultSectionsList;
	}

	/**
	 * Recalculate the fault section pref data
	 * @param args
	 */
	public static void main(String []args) {
		try {
			DB_AccessAPI dbAccessAPI = new ServerDB_Access(ServerDB_Access.SERVLET_URL_DB3);
			SessionInfo.setUserName(args[0]);
			SessionInfo.setPassword(args[1]);
			SessionInfo.setContributorInfo();
			PrefFaultSectionDataDB_DAO prefFaultSectionDAO = new  PrefFaultSectionDataDB_DAO(dbAccessAPI);
			prefFaultSectionDAO.rePopulatePrefDataTable();
			System.exit(0);
		} catch (Throwable t) {
			// TODO Auto-generated catch block
			t.printStackTrace();
			System.exit(1);
		}
	}

	/**
	 * Get Max slip rate from preferred fault data
	 *
	 */
	public double getMaxSlipRate() {
		String sql = "select max("+PREF_SLIP_RATE+") from "+TABLE_NAME;
		ResultSet rs;
		double maxSlipRate=0;
		try {
			rs = dbAccess.queryData(sql);
			rs.next();
			maxSlipRate = rs.getFloat(0);
			rs.close();
		} catch (SQLException e) {
			throw new QueryException(e.getMessage()); 
		}
		return maxSlipRate;
	}



	/**
	 * Get Min slip rate from preferred fault data
	 *
	 */
	public double getMinSlipRate() {
		String sql = "select min("+PREF_SLIP_RATE+") from "+TABLE_NAME;
		ResultSet rs;
		double minSlipRate=0;
		try {
			rs = dbAccess.queryData(sql);
			rs.next();
			minSlipRate = rs.getFloat(0);
			rs.close();
		} catch (SQLException e) {
			throw new QueryException(e.getMessage()); 
		}
		return minSlipRate;
	}



}
