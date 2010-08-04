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

import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.refFaultParamDb.dao.exception.InsertException;
import org.opensha.refFaultParamDb.dao.exception.QueryException;
import org.opensha.refFaultParamDb.dao.exception.UpdateException;
/**
 * <p>Title: XY_EstimateDB_DAO.java </p>
 * <p>Description: </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class XY_EstimateDB_DAO  {

	private final static String TABLE_NAME="XY_Est";
	private final static String EST_ID="Est_Id";
	private final static String X="X";
	private final static String Y="Y";
	private DB_AccessAPI dbAccessAPI;

	/**
	 * Constructor.
	 * @param dbConnection
	 */
	public XY_EstimateDB_DAO(DB_AccessAPI dbAccessAPI) {
		setDB_Connection(dbAccessAPI);
	}

	public XY_EstimateDB_DAO() { }


	public void setDB_Connection(DB_AccessAPI dbAccessAPI) {
		this.dbAccessAPI = dbAccessAPI;
	}

	/**
	 * Add the normal estimate into the database table
	 * @param estimateInstanceId
	 * @param estimate
	 * @throws InsertException
	 */
	public void addEstimate(int estimateInstanceId, DiscretizedFuncAPI func) throws InsertException {
		int numPoints = func.getNum();
		try {
			for (int i = 0; i < numPoints; ++i) {
				// insert into log normal table
				String sql = "insert into " + TABLE_NAME + "(" + EST_ID + "," + X + "," +
				Y + ")" +
				" values (" + estimateInstanceId + "," + func.getX(i) + "," +
				func.getY(i) + ")";
				dbAccessAPI.insertUpdateOrDeleteData(sql);
			}
		}
		catch (SQLException e) {
			//e.printStackTrace();
			throw new InsertException(e.getMessage());
		}
	}

	/**
	 *
	 * @param estimateInstanceId
	 * @return
	 * @throws QueryException
	 */
	public void getEstimate(int estimateInstanceId, DiscretizedFuncAPI func) throws QueryException {
		String condition = " where " + EST_ID + "=" + estimateInstanceId;
		// this awkward sql is needed else we get "Invalid scale exception"
		String sql = "select "+EST_ID+",("+X+"+0) "+X+",("+Y+"+0) "+Y+" from "+TABLE_NAME+" "+condition;
		try {
			ResultSet rs  = dbAccessAPI.queryData(sql);
			while(rs.next()) {
				func.set(rs.getFloat("X"),rs.getFloat("Y"));
			}
			rs.close();
		} catch(SQLException e) { throw new QueryException(e.getMessage()); }
	}

	/**
	 *
	 * @param estimateInstanceId
	 * @return
	 * @throws UpdateException
	 */
	public boolean removeEstimate(int estimateInstanceId) throws UpdateException {
		String sql = "delete from "+TABLE_NAME+"  where "+EST_ID+"="+estimateInstanceId;
		try {
			int numRows = dbAccessAPI.insertUpdateOrDeleteData(sql);
			if(numRows>=1) return true;
		}
		catch(SQLException e) { throw new UpdateException(e.getMessage()); }
		return false;
	}

}
