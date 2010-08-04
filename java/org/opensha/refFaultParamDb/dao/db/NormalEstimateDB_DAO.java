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

import org.opensha.commons.data.estimate.Estimate;
import org.opensha.commons.data.estimate.NormalEstimate;
import org.opensha.refFaultParamDb.dao.EstimateDAO_API;
import org.opensha.refFaultParamDb.dao.exception.InsertException;
import org.opensha.refFaultParamDb.dao.exception.QueryException;
import org.opensha.refFaultParamDb.dao.exception.UpdateException;
/**
 * <p>Title: NormalEstimateDB_DAO.java </p>
 * <p>Description: </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class NormalEstimateDB_DAO implements EstimateDAO_API {

	private final static String TABLE_NAME="Normal_Est";
	private final static String EST_ID="Est_Id";
	private final static String MEAN="MEAN";
	private final static String STD_DEV="STD_DEV";
	private final static String MIN_X = "Min_X";
	private final static String MAX_X = "Max_X";
	private DB_AccessAPI dbAccessAPI;
	public final static String EST_TYPE_NAME="NormalEstimate";
	private final static String ERR_MSG = "This class just deals with Normal Estimates";

	/**
	 * Constructor.
	 * @param dbConnection
	 */
	public NormalEstimateDB_DAO(DB_AccessAPI dbAccessAPI) {
		setDB_Connection(dbAccessAPI);
	}

	public NormalEstimateDB_DAO() { }


	public void setDB_Connection(DB_AccessAPI dbAccessAPI) {
		this.dbAccessAPI = dbAccessAPI;
	}

	/**
	 * Add the normal estimate into the database table
	 * @param estimateInstanceId
	 * @param estimate
	 * @throws InsertException
	 */
	public void addEstimate(int estimateInstanceId, Estimate estimate) throws InsertException {
		if(!(estimate instanceof NormalEstimate)) throw new InsertException(ERR_MSG);
		String colNames="", colVals="";
		NormalEstimate normalEstimate = (NormalEstimate)estimate;
		double minX = normalEstimate.getMin();
		if(!Double.isInfinite(minX)) {
			colNames +=MIN_X+",";
			colVals +=minX+",";
		}
		double maxX = normalEstimate.getMax();
		if(!Double.isInfinite(maxX)) {
			colNames +=MAX_X+",";
			colVals +=maxX+",";
		}
		String sql = "insert into "+TABLE_NAME+"("+ EST_ID+","+colNames+MEAN+","+
		STD_DEV+")"+
		" values ("+estimateInstanceId+","+colVals+estimate.getMean()+","+
		estimate.getStdDev()+")";
		try { dbAccessAPI.insertUpdateOrDeleteData(sql); }
		catch(SQLException e) {
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
	public Estimate getEstimate(int estimateInstanceId) throws QueryException {
		NormalEstimate estimate=null;
		String condition  =  " where "+EST_ID+"="+estimateInstanceId;
		ArrayList<Estimate> estimateList = query(condition);
		if(estimateList.size()>0) estimate = (NormalEstimate)estimateList.get(0);
		return estimate;
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
			if(numRows==1) return true;
		}
		catch(SQLException e) { throw new UpdateException(e.getMessage()); }
		return false;
	}

	public String getEstimateTypeName() {
		return EST_TYPE_NAME;
	}


	private ArrayList<Estimate> query(String condition) throws QueryException {
		ArrayList<Estimate> estimateList = new ArrayList<Estimate>();
		// this awkward sql is needed else we get "Invalid scale exception"
		String sql = "select "+EST_ID+",("+MEAN+"+0) "+MEAN+",("+STD_DEV+"+0) "+STD_DEV+", ("+MIN_X+"+0) " +MIN_X+",("+MAX_X+"+0) "+MAX_X+" from "+TABLE_NAME+" "+condition;
		try {
			ResultSet rs  = dbAccessAPI.queryData(sql);
			while(rs.next()) {
				NormalEstimate normalEstimate = new NormalEstimate(rs.getFloat(MEAN),
						rs.getFloat(STD_DEV));
				double minX = rs.getFloat(MIN_X);
				if(rs.wasNull()) minX = Double.NEGATIVE_INFINITY;
				double maxX = rs.getFloat(MAX_X);
				if(rs.wasNull()) maxX = Double.POSITIVE_INFINITY;
				normalEstimate.setMinMax(minX, maxX);
				estimateList.add(normalEstimate);

			}
			rs.close();
		} catch(SQLException e) { throw new QueryException(e.getMessage()); }
		return estimateList;
	}

}
