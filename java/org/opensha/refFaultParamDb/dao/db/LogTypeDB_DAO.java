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
 * <p>Title: LogTypeDB_DAO.java </p>
 * <p>Description: Find log type id corresponding to a particular log base</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class LogTypeDB_DAO  {

	private final static String TABLE_NAME="Log_Type";
	private final static String LOG_TYPE_ID="Log_Type_Id";
	private final static String LOG_BASE="Log_Base";
	public final static String LOG_BASE_E = "E";
	public final static String LOG_BASE_10="10";
	private DB_AccessAPI dbAccessAPI;

	/**
	 * Constructor.
	 * @param dbConnection
	 */
	public LogTypeDB_DAO(DB_AccessAPI dbAccessAPI) {
		setDB_Connection(dbAccessAPI);
	}


	public void setDB_Connection(DB_AccessAPI dbAccessAPI) {
		this.dbAccessAPI = dbAccessAPI;
	}

	/**
	 * Get log type id for a particular log base from the table
	 *
	 * @param logBase
	 * @return
	 * @throws QueryException
	 */
	public int getLogTypeId(String logBase)  throws QueryException {
		int logTypeId = -1;
		String sql =  "select "+LOG_TYPE_ID+","+LOG_BASE+" from "+TABLE_NAME+
		" where "+LOG_BASE+"='"+logBase+"'";
		try {
			ResultSet rs  = dbAccessAPI.queryData(sql);
			if(rs.next()) logTypeId = rs.getInt(LOG_TYPE_ID);
			rs.close();
		} catch(SQLException e) { throw new QueryException(e.getMessage()); }
		return logTypeId;
	}


	public String getLogBase(int logTypeId) throws QueryException {
		String logBase = "";
		String sql =  "select "+LOG_TYPE_ID+","+LOG_BASE+" from "+TABLE_NAME+
		" where "+LOG_TYPE_ID+"="+logTypeId+"";
		try {
			ResultSet rs  = dbAccessAPI.queryData(sql);
			if(rs.next()) logBase = rs.getString(LOG_BASE);
			rs.close();
		} catch(SQLException e) { throw new QueryException(e.getMessage()); }
		return logBase;
	}


}
