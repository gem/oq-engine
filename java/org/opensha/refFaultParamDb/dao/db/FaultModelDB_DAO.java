/**
 * 
 */
package org.opensha.refFaultParamDb.dao.db;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;

import org.opensha.refFaultParamDb.dao.exception.InsertException;
import org.opensha.refFaultParamDb.dao.exception.QueryException;
import org.opensha.refFaultParamDb.dao.exception.UpdateException;

/**
 * This class accesses the database to get/put/update the fault sections within a Fault Model
 * 
 * @author vipingupta
 *
 */
public class FaultModelDB_DAO {
	private final static String TABLE_NAME="Fault_Model";
	private final static String FAULT_MODEL_ID="Fault_Model_Id";
	private final static String SECTION_ID="Section_Id";
	private DB_AccessAPI dbAccessAPI;

	public FaultModelDB_DAO(DB_AccessAPI dbAccessAPI) {
		setDB_Connection(dbAccessAPI);
	}


	public void setDB_Connection(DB_AccessAPI dbAccessAPI) {
		this.dbAccessAPI = dbAccessAPI;
	}


	/**
	 * Add fault model and list of fault sections in that fault model into the database
	 * @param faultModelId
	 * @param faultSectionsIdList
	 */
	public void addFaultModelSections(int faultModelId, ArrayList<Integer> faultSectionsIdList) {
		// REMOVE all the sections from this model
		removeModel(faultModelId); // remove all fault sections associated with this fault model
		try {
			for(int i=0; i<faultSectionsIdList.size(); ++i) {
				String sql = "insert into "+TABLE_NAME+" ("+FAULT_MODEL_ID+","+SECTION_ID+") values ("+
				faultModelId+","+faultSectionsIdList.get(i)+")";
				dbAccessAPI.insertUpdateOrDeleteData(sql);
			}
		} catch(SQLException e) { throw new InsertException(e.getMessage()); }
	}

	/**
	 * Get a List of Ids of all fault sections in a fault model
	 * @param faultModelId
	 * @return
	 */
	public ArrayList<Integer> getFaultSectionIdList(int faultModelId) {
		String sql = "select "+SECTION_ID+ " from "+TABLE_NAME+" where "+FAULT_MODEL_ID+"="+faultModelId;
		ArrayList<Integer> faultSectionIdList = new ArrayList<Integer>();
		try {
			ResultSet rs  = dbAccessAPI.queryData(sql);
			while(rs.next()) faultSectionIdList.add(new Integer(rs.getInt(SECTION_ID)));
			rs.close();
		} catch(SQLException e) { throw new QueryException(e.getMessage()); }
		return faultSectionIdList;
	}

	/**
	 * This removes all the rows from the table which associates faultsection names with a particular model
	 * 
	 * @param faultModelId
	 */
	private void removeModel(int faultModelId) {
		String sql = "delete from "+TABLE_NAME+" where "+FAULT_MODEL_ID+"="+faultModelId;
		try {
			dbAccessAPI.insertUpdateOrDeleteData(sql);
		} catch(SQLException e) { throw new UpdateException(e.getMessage()); }
	}
}
