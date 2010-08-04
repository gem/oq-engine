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
import org.opensha.commons.data.estimate.MinMaxPrefEstimate;
import org.opensha.refFaultParamDb.dao.EstimateDAO_API;
import org.opensha.refFaultParamDb.dao.exception.InsertException;
import org.opensha.refFaultParamDb.dao.exception.QueryException;
import org.opensha.refFaultParamDb.dao.exception.UpdateException;
/**
 * <p>Title: MinMaxPrefEstimateDB_DAO.java </p>
 * <p>Description: It saves the min/max/preferred estimate into the database</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class MinMaxPrefEstimateDB_DAO implements EstimateDAO_API {
	private final static String TABLE_NAME="Min_Max_Pref_Est";
	private final static String MIN_X = "Min_X";
	private final static String MAX_X = "Max_X";
	private final static String PREF_X = "Pref_X";
	private final static String MIN_PROB = "Min_Prob";
	private final static String MAX_PROB = "Max_Prob";
	private final static String PREF_PROB = "Pref_Prob";
	private final static String EST_ID = "Est_Id ";
	private DB_AccessAPI dbAccessAPI;
	public final static String EST_TYPE_NAME="MinMaxPrefEstimate";
	private final static String ERR_MSG = "This class just deals with Min/Max/Pref Estimates";

	/**
	 * Constructor.
	 * @param dbConnection
	 */
	public MinMaxPrefEstimateDB_DAO(DB_AccessAPI dbAccessAPI) {
		setDB_Connection(dbAccessAPI);
	}

	public MinMaxPrefEstimateDB_DAO() { }


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
		if(!(estimate instanceof MinMaxPrefEstimate)) throw new InsertException(ERR_MSG);
		MinMaxPrefEstimate minMaxPrefEstimate = (MinMaxPrefEstimate)estimate;
		String colNames="", colVals="";
		// min X
		double minX = minMaxPrefEstimate.getMinimum();
		if(!Double.isNaN(minX)) {
			colNames +=MIN_X+",";
			colVals +=minX+",";
		}
		// max X
		double maxX = minMaxPrefEstimate.getMaximum();
		if(!Double.isNaN(maxX)) {
			colNames +=MAX_X+",";
			colVals +=maxX+",";
		}
		// pref X
		double prefX = minMaxPrefEstimate.getPreferred();
		if(!Double.isNaN(prefX)) {
			colNames +=PREF_X+",";
			colVals +=prefX+",";
		}
		// min Prob
		double minProb = minMaxPrefEstimate.getMinimumProb();
		if(!Double.isNaN(minProb)) {
			colNames +=MIN_PROB+",";
			colVals +=minProb+",";
		}
		// max Prob
		double maxProb = minMaxPrefEstimate.getMaximumProb();
		if(!Double.isNaN(maxProb)) {
			colNames +=MAX_PROB+",";
			colVals +=maxProb+",";
		}
		// pref prob
		double prefProb = minMaxPrefEstimate.getPreferredProb();
		if(!Double.isNaN(prefProb)) {
			colNames +=PREF_PROB+",";
			colVals +=prefProb+",";
		}


		// insert into min/max/pref table
		String sql = "insert into "+TABLE_NAME+"("+ colNames+EST_ID+")"+
		" values ("+colVals+estimateInstanceId+")";
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
		MinMaxPrefEstimate estimate=null;
		String condition  =  " where "+EST_ID+"="+estimateInstanceId;
		ArrayList<Estimate> estimateList = query(condition);
		if(estimateList.size()>0) estimate = (MinMaxPrefEstimate)estimateList.get(0);
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
		String sql = "select "+EST_ID+",("+MIN_X+"+0) "+MIN_X+",("+MAX_X+"+0) "+ MAX_X+
		",("+PREF_X+"+0) "+PREF_X+",("+ MIN_PROB+"+0) "+MIN_PROB+",("+MAX_PROB+"+0) "+MAX_PROB+
		", ("+PREF_PROB+"+0) "+PREF_PROB+" from "+TABLE_NAME+" "+condition;
		try {
			ResultSet rs  = dbAccessAPI.queryData(sql);
			while(rs.next()) {
				// get min/max and preferred
				double minX = rs.getFloat(MIN_X);
				if(rs.wasNull()) minX = Double.NaN;
				double maxX = rs.getFloat(MAX_X);
				if(rs.wasNull()) maxX = Double.NaN;
				double prefX = rs.getFloat(PREF_X);
				if(rs.wasNull()) prefX = Double.NaN;
				double minProb = rs.getFloat(MIN_PROB);
				if(rs.wasNull()) minProb = Double.NaN;
				double maxProb = rs.getFloat(MAX_PROB);
				if(rs.wasNull()) maxProb = Double.NaN;
				double prefProb = rs.getFloat(PREF_PROB);
				if(rs.wasNull()) prefProb = Double.NaN;
				// min/max/pref estimate
				MinMaxPrefEstimate estimate = new MinMaxPrefEstimate(minX, maxX, prefX,
						minProb, maxProb, prefProb);
				estimateList.add(estimate);
			}
			rs.close();
		} catch(SQLException e) { throw new QueryException(e.getMessage()); }
		return estimateList;
	}

}
