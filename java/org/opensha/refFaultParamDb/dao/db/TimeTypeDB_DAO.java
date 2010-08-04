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

import org.opensha.refFaultParamDb.dao.exception.QueryException;

/**
 * <p>Title: TimeTypeDB_DAO.java </p>
 * <p>Description: Find time type id corresponding to a particular time type(exact time
 * or time estimate)</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class TimeTypeDB_DAO  {

	private final static String TABLE_NAME="Time_Type";
	private final static String TIME_TYPE_ID="Time_Type_Id";
	private final static String TIME_DESCRIPTION="Time_Type_Description";
	private DB_AccessAPI dbAccessAPI;
	public final static String EXACT_TIME = "Exact Time";
	public final static String TIME_ESTIMATE = "Time Estimate";
	/**
	 * Constructor.
	 * @param dbConnection
	 */
	public TimeTypeDB_DAO(DB_AccessAPI dbAccessAPI) {
		setDB_Connection(dbAccessAPI);
	}


	public void setDB_Connection(DB_AccessAPI dbAccessAPI) {
		this.dbAccessAPI = dbAccessAPI;
	}

	/**
	 * Get time type id for a particular time type(estimate/excat time) from the table
	 *
	 * @param timeType
	 * @return
	 * @throws QueryException
	 */
	public int getTimeTypeId(String timeType)  throws QueryException {
		int timeTypeId = -1;
		String sql =  "select "+TIME_TYPE_ID+","+TIME_DESCRIPTION+" from "+TABLE_NAME+
		" where "+TIME_DESCRIPTION+"='"+timeType+"'";
		try {
			ResultSet rs  = dbAccessAPI.queryData(sql);
			if(rs.next()) timeTypeId = rs.getInt(TIME_TYPE_ID);
			rs.close();
		} catch(SQLException e) { throw new QueryException(e.getMessage()); }
		return timeTypeId;
	}


	public String getTimeType(int timeTypeId) throws QueryException {
		String timeType = "";
		String sql =  "select "+TIME_TYPE_ID+","+TIME_DESCRIPTION+" from "+TABLE_NAME+
		" where "+TIME_TYPE_ID+"="+timeTypeId+"";
		try {
			ResultSet rs  = dbAccessAPI.queryData(sql);
			if(rs.next()) timeType = rs.getString(TIME_DESCRIPTION);
			rs.close();
		} catch(SQLException e) { throw new QueryException(e.getMessage()); }
		return timeType;
	}


}
