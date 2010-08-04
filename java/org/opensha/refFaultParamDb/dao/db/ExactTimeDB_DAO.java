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

import org.opensha.refFaultParamDb.dao.exception.InsertException;
import org.opensha.refFaultParamDb.dao.exception.QueryException;
import org.opensha.refFaultParamDb.dao.exception.UpdateException;
import org.opensha.refFaultParamDb.data.ExactTime;
/**
 * <p>Title: ExactTimeDB_DAO.java </p>
 * <p>Description: This class allows to put/get exact time from database </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class ExactTimeDB_DAO {

	private final static String TABLE_NAME="Exact_Time_Info";
	private final static String TIME_INSTANCE_ID="Time_Instance_Id";
	private final static String YEAR="Year";
	private final static String MONTH="Month";
	private final static String DAY = "Day";
	private final static String HOUR = "Hour";
	private final static String MINUTE = "Minute";
	private final static String SECOND = "Second";
	private final static String ERA = "Era";
	private final static String IS_NOW = "Is_Now";
	private final static String YES_IS_NOW = "Y";
	private final static String NOT_IS_NOW = "N";
	private DB_AccessAPI dbAccessAPI;
//	private final static String ERR_MSG = "This class just deals with Exact Times";

	/**
	 * Constructor.
	 * @param dbConnection
	 */
	public ExactTimeDB_DAO(DB_AccessAPI dbAccessAPI) {
		setDB_Connection(dbAccessAPI);
	}

	public ExactTimeDB_DAO() { }


	public void setDB_Connection(DB_AccessAPI dbAccessAPI) {
		this.dbAccessAPI = dbAccessAPI;
	}

	/**
	 *
	 * @param timeInstanceId
	 * @param exactTime
	 * @throws InsertException
	 */
	public void addExactTime(int timeInstanceId, ExactTime exactTime) throws InsertException {
		String isNow = NOT_IS_NOW;
		if(exactTime.getIsNow()) isNow=YES_IS_NOW;
		// insert into exact time info table
		String sql = "insert into "+TABLE_NAME+"("+ TIME_INSTANCE_ID+","+YEAR+","+
		MONTH+","+DAY+","+HOUR+","+MINUTE+","+SECOND+","+ERA+","+IS_NOW+")"+
		" values ("+timeInstanceId+","+exactTime.getYear()+","+
		exactTime.getMonth()+","+exactTime.getDay()+","+exactTime.getHour()+","+
		exactTime.getMinute()+","+exactTime.getSecond()+",'"+exactTime.getEra()+"',"+
		"'"+isNow+"')";
		try { dbAccessAPI.insertUpdateOrDeleteData(sql); }
		catch(SQLException e) {
			//e.printStackTrace();
			throw new InsertException(e.getMessage());
		}
	}

	/**
	 * Get the exact time based on time instance id
	 * @param timeInstanceId
	 * @return
	 * @throws QueryException
	 */
	public ExactTime getExactTime(int timeInstanceId) throws QueryException {
		ExactTime exactTime=null;
		String condition  =  " where "+TIME_INSTANCE_ID+"="+timeInstanceId;
		ArrayList<ExactTime> exactTimeList = query(condition);
		if(exactTimeList.size()>0) exactTime = (ExactTime)exactTimeList.get(0);
		return exactTime;
	}

	/**
	 * Remove the time instance based on id
	 * @param estimateInstanceId
	 * @return
	 * @throws UpdateException
	 */
	public boolean removeTime(int timeInstanceId) throws UpdateException {
		String sql = "delete from "+TABLE_NAME+"  where "+TIME_INSTANCE_ID+"="+timeInstanceId;
		try {
			int numRows = dbAccessAPI.insertUpdateOrDeleteData(sql);
			if(numRows==1) return true;
		}
		catch(SQLException e) { throw new UpdateException(e.getMessage()); }
		return false;
	}

	/**
	 * Query the table to get the exact time instances
	 * @param condition
	 * @return
	 * @throws QueryException
	 */
	private ArrayList<ExactTime> query(String condition) throws QueryException {
		ArrayList<ExactTime> exactTimeList = new ArrayList<ExactTime>();
		String sql = "select "+TIME_INSTANCE_ID+","+YEAR+","+
		MONTH+","+DAY+","+HOUR+","+MINUTE+","+SECOND+","+ERA+","+IS_NOW+
		" from "+TABLE_NAME+" "+condition;
		try {
			ResultSet rs  = dbAccessAPI.queryData(sql);
			while(rs.next()) {
				boolean isNow = false;
				if(rs.getString(IS_NOW).equalsIgnoreCase(YES_IS_NOW)) isNow=true;
				ExactTime exactTime = new ExactTime(rs.getInt(YEAR),
						rs.getInt(MONTH),
						rs.getInt(DAY),
						rs.getInt(HOUR),
						rs.getInt(MINUTE),
						rs.getInt(SECOND),
						rs.getString(ERA),
						isNow);
				exactTimeList.add(exactTime);
			}
			rs.close();
		} catch(SQLException e) { throw new QueryException(e.getMessage()); }
		return exactTimeList;
	}

}
