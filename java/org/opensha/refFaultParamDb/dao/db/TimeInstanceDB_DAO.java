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
import org.opensha.refFaultParamDb.data.TimeAPI;
import org.opensha.refFaultParamDb.data.TimeEstimate;
import org.opensha.refFaultParamDb.vo.Reference;

/**
 * <p>Title: TimeInstanceDB_DAO.java </p>
 * <p>Description: Time Instance DB DAO. It adds the time instance to the database.
 * It checks whether time is exact time or an estimate and handles appropriately </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class TimeInstanceDB_DAO  {
	private final static String TABLE_NAME="Time_Instances";
	private final static String REFERENCES_TABLE_NAME = "Time_Instances_References";
	private final static String SEQUENCE_NAME="Time_Instances_Sequence";
	private final static String TIME_ID="Time_Id";
	private final static String TIME_TYPE_ID="Time_Type_Id";
	private final static String COMMENTS="Comments";
	private final static String REFERENCE_ID="Reference_Id";
	private DB_AccessAPI dbAccessAPI;

	/**
	 * Constructor.
	 * @param dbConnection
	 */
	public TimeInstanceDB_DAO(DB_AccessAPI dbAccessAPI) {
		setDB_Connection(dbAccessAPI);
	}


	public void setDB_Connection(DB_AccessAPI dbAccessAPI) {
		this.dbAccessAPI = dbAccessAPI;
	}

	/**
	 * Add time instance to the database
	 * @param estimateInstance
	 * @throws InsertException
	 */
	public int addTimeInstance(TimeAPI timeInstance) throws InsertException {
		String timeType;
		if(timeInstance instanceof ExactTime)  // exact time
			timeType = TimeTypeDB_DAO.EXACT_TIME;
		else timeType = TimeTypeDB_DAO.TIME_ESTIMATE; // time estimate

		// get id for the time type (time type refers to whether time is estimate or exact time)
		TimeTypeDB_DAO timeTypeDB_DAO = new TimeTypeDB_DAO(dbAccessAPI);
		int timeTypeId = timeTypeDB_DAO.getTimeTypeId(timeType);
		int timeInstanceId = -1;
		try {
			timeInstanceId = dbAccessAPI.getNextSequenceNumber(SEQUENCE_NAME);
		}catch(SQLException e) {
			throw new InsertException(e.getMessage());
		}

		String sql = "insert into "+TABLE_NAME+"("+TIME_ID+","+TIME_TYPE_ID+","+COMMENTS+")"+
		" values("+timeInstanceId+","+timeTypeId+",'"+
		timeInstance.getDatingComments()+"')";
		try {
			dbAccessAPI.insertUpdateOrDeleteData(sql);
			if(timeType.equalsIgnoreCase(TimeTypeDB_DAO.EXACT_TIME)) // add exact time to database
				addExactTimeToDatabase(timeInstanceId, (ExactTime)timeInstance );
			// add time estimate to database
			else addTimeEstimateToDatabase(timeInstanceId,(TimeEstimate)timeInstance);

			// add the time references to the database
			ArrayList<Reference> referenceList = timeInstance.getReferencesList();
			for(int i=0; i<referenceList.size(); ++i) {
				int referenceId = (referenceList.get(i)).getReferenceId();
				sql = "insert into "+REFERENCES_TABLE_NAME+"("+TIME_ID+
				","+REFERENCE_ID+") "+
				"values ("+timeInstanceId+","+referenceId+")";
				dbAccessAPI.insertUpdateOrDeleteData(sql);
			}


		}catch(SQLException e) {
			throw new InsertException(e.getMessage());
		}
		return timeInstanceId;
	}

	/**
	 * Add exact time to the database
	 * @param timeInstanceId
	 * @param timeInstance
	 */
	private void addExactTimeToDatabase(int timeInstanceId, ExactTime timeInstance) {
		ExactTimeDB_DAO exactTimeDAO = new ExactTimeDB_DAO(this.dbAccessAPI);
		exactTimeDAO.addExactTime(timeInstanceId, timeInstance);
	}

	/**
	 * Remove exact time instance from the database
	 * @param timeInstanceId
	 * @return
	 */
	private boolean removeExactTimeFromDatabase(int timeInstanceId) {
		ExactTimeDB_DAO exactTimeDAO = new ExactTimeDB_DAO(this.dbAccessAPI);
		return exactTimeDAO.removeTime(timeInstanceId);
	}

	/**
	 * Get the exact time instance from database
	 * @param timeInstanceId
	 * @return
	 */
	private ExactTime getExactTimeFromDatabase(int timeInstanceId) {
		ExactTimeDB_DAO exactTimeDAO = new ExactTimeDB_DAO(this.dbAccessAPI);
		return exactTimeDAO.getExactTime(timeInstanceId);
	}

	/**
	 * Add  time estimate to the database
	 * @param timeInstanceId
	 * @param timeInstance
	 */
	private void addTimeEstimateToDatabase(int timeInstanceId, TimeEstimate timeInstance) {
		TimeEstimateDB_DAO timeEstimateDAO = new TimeEstimateDB_DAO(this.dbAccessAPI);
		timeEstimateDAO.addTimeEstimate(timeInstanceId, timeInstance);
	}

	/**
	 * Get the time estimate based on id
	 *
	 * @param timeInstanceId
	 * @return
	 */
	private TimeEstimate getTimeEstimateFromDatabase(int timeInstanceId) {
		TimeEstimateDB_DAO timeEstimateDAO = new TimeEstimateDB_DAO(this.dbAccessAPI);
		return timeEstimateDAO.getTimeEstimate(timeInstanceId);
	}

	/**
	 * Remove the time estimate from the database
	 * @param timeInstanceId
	 * @return
	 */
	private boolean removeTimeEstimateFromDatabase(int timeInstanceId) {
		TimeEstimateDB_DAO timeEstimateDAO = new TimeEstimateDB_DAO(this.dbAccessAPI);
		return timeEstimateDAO.removeTimeEstimate(timeInstanceId);
	}

	/**
	 * Get time instance based on time instances id
	 * @param timeInstanceId
	 * @return
	 * @throws QueryException
	 */
	public TimeAPI getTimeInstance(int timeInstanceId) throws QueryException {
		TimeAPI timAPI=null;
		String condition  =  " where "+TIME_ID+"="+timeInstanceId;
		ArrayList<TimeAPI> timeInstancesList = query(condition);
		if(timeInstancesList.size()>0) timAPI = (TimeAPI)timeInstancesList.get(0);
		return timAPI;

	}

	/**
	 * remove the time instance from the table
	 * @param timeInstanceId
	 * @return
	 * @throws UpdateException
	 */
	public boolean removeTimeInstance(int timeInstanceId) throws UpdateException {
		String sql = "select "+TIME_ID+","+TIME_TYPE_ID+","+COMMENTS+" from "+
		TABLE_NAME+" where "+TIME_ID+"="+timeInstanceId;
		try {
			ResultSet rs  = dbAccessAPI.queryData(sql);
			TimeTypeDB_DAO timeTypeDB_DAO = new TimeTypeDB_DAO(dbAccessAPI);
			while(rs.next())  {
				String timeTypeName = timeTypeDB_DAO.getTimeType(rs.getInt(TIME_TYPE_ID));

				// delete from specific table for each time type

				// remove exact time from database
				if(timeTypeName.equalsIgnoreCase(TimeTypeDB_DAO.EXACT_TIME))
					this.removeExactTimeFromDatabase(timeInstanceId);
				// remove time estimate from the database
				else this.removeTimeEstimateFromDatabase(timeInstanceId);

				// remove from the references table
				String referencesDelSql = "delete from "+REFERENCES_TABLE_NAME+ " where "+
				TIME_ID+" ="+timeInstanceId;
				dbAccessAPI.insertUpdateOrDeleteData(referencesDelSql);

				//remove from master table of time instances
				String delSql = "delete from "+TABLE_NAME+" where "+TIME_ID+"="+timeInstanceId;
				int numRows = dbAccessAPI.insertUpdateOrDeleteData(delSql);
				if(numRows==1) return true;
			}
			rs.close();
		} catch(SQLException e) { throw new QueryException(e.getMessage()); }
		return false;
	}

	/**
	 * Query the tables to get the time data based on the query condition
	 *
	 * @param condition
	 * @return
	 * @throws QueryException
	 */
	private ArrayList<TimeAPI> query(String condition) throws QueryException {
		ArrayList<TimeAPI> timeInstancesList = new ArrayList<TimeAPI>();
		String sql = "select "+TIME_ID+","+TIME_TYPE_ID+","+COMMENTS+" from "+
		TABLE_NAME+" "+condition;
		try {
			ResultSet rs  = dbAccessAPI.queryData(sql);
			TimeTypeDB_DAO timeTypeDB_DAO = new TimeTypeDB_DAO(dbAccessAPI);
			ReferenceDB_DAO referenceDAO = new ReferenceDB_DAO(dbAccessAPI);
			while(rs.next())  {
				TimeAPI timeAPI;
				String timeTypeName = timeTypeDB_DAO.getTimeType(rs.getInt(TIME_TYPE_ID));

				if(timeTypeName.equalsIgnoreCase(TimeTypeDB_DAO.EXACT_TIME)) // get exact time from database
					timeAPI = getExactTimeFromDatabase(rs.getInt(TIME_ID));
				// get time estimate from database
				else timeAPI = getTimeEstimateFromDatabase(rs.getInt(TIME_ID));

				timeAPI.setDatingComments(rs.getString(COMMENTS));

				// get the references list for this time
				ArrayList<Reference> referenceList = new ArrayList<Reference>();
				sql = "select "+REFERENCE_ID+","+TIME_ID +" from "+REFERENCES_TABLE_NAME+
				" where "+TIME_ID+"="+rs.getInt(TIME_ID);
				ResultSet referenceResultSet = dbAccessAPI.queryData(sql);
				while(referenceResultSet.next()) {
					referenceList.add(referenceDAO.getReference(referenceResultSet.getInt(REFERENCE_ID)));
				}
				referenceResultSet.close();
				// set the references in the VO
				timeAPI.setReferencesList(referenceList);
				timeInstancesList.add(timeAPI);
			}
			rs.close();
		} catch(SQLException e) { throw new QueryException(e.getMessage()); }
		return timeInstancesList;
	}

}
