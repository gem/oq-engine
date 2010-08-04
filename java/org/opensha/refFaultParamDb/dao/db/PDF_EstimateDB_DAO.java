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

import org.opensha.commons.data.estimate.Estimate;
import org.opensha.commons.data.estimate.PDF_Estimate;
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;
import org.opensha.refFaultParamDb.dao.EstimateDAO_API;
import org.opensha.refFaultParamDb.dao.exception.InsertException;
import org.opensha.refFaultParamDb.dao.exception.QueryException;
import org.opensha.refFaultParamDb.dao.exception.UpdateException;

/**
 * <p>Title: PDF_EstimateDB_DAO.java </p>
 * <p>Description: This class interacts with the database to put/get the PDF estimate</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class PDF_EstimateDB_DAO implements EstimateDAO_API {
	private final static String  TABLE_NAME = "PDF_Est";
	private final static String EST_ID = "Est_Id";
	private final static String MIN_X = "Min_X";
	private final static String DELTA_X = "Delta_X";
	private final static String NUM = "Num";

	public final static String EST_TYPE_NAME="PDF_Estimate";
	private final static String ERR_MSG = "This class just deals with PDF Estimates";
	private XY_EstimateDB_DAO xyEstimateDB_DAO  = new XY_EstimateDB_DAO();
	private DB_AccessAPI dbAccessAPI;

	/**
	 * Constructor.
	 * @param dbConnection
	 */
	public PDF_EstimateDB_DAO(DB_AccessAPI dbAccessAPI) {
		setDB_Connection(dbAccessAPI);
	}

	public PDF_EstimateDB_DAO() { }


	public void setDB_Connection(DB_AccessAPI dbAccessAPI) {
		this.dbAccessAPI = dbAccessAPI;
		xyEstimateDB_DAO.setDB_Connection(dbAccessAPI);
	}

	/**
	 * Add the normal estimate into the database table
	 * @param estimateInstanceId
	 * @param estimate
	 * @throws InsertException
	 */
	public void addEstimate(int estimateInstanceId, Estimate estimate) throws InsertException {
		if(!(estimate instanceof PDF_Estimate)) throw new InsertException(ERR_MSG);
		PDF_Estimate pdfEstimate = (PDF_Estimate)estimate;
		EvenlyDiscretizedFunc evenlyDiscFunc = (EvenlyDiscretizedFunc)pdfEstimate.getFunc();
		String sql = "insert into "+TABLE_NAME+"("+EST_ID+","+MIN_X+","+DELTA_X+","+
		NUM+") values ("+estimateInstanceId+","+evenlyDiscFunc.getMinX()+","+
		evenlyDiscFunc.getDelta()+","+evenlyDiscFunc.getNum()+")";
		try {
			dbAccessAPI.insertUpdateOrDeleteData(sql);
		}catch(SQLException sqlException) {
			throw new InsertException(sqlException.getMessage());
		}
		xyEstimateDB_DAO.addEstimate(estimateInstanceId, pdfEstimate.getValues());
	}

	/**
	 *
	 * @param estimateInstanceId
	 * @return
	 * @throws QueryException
	 */
	public Estimate getEstimate(int estimateInstanceId) throws QueryException {
		// this awkward sql is needed else we get "Invalid scale exception"
		String sql = "select "+EST_ID+",("+MIN_X+"+0) "+MIN_X+",("+DELTA_X+"+0) "+DELTA_X+","+NUM+" from "+
		TABLE_NAME+" where "+EST_ID+"="+estimateInstanceId;
		EvenlyDiscretizedFunc evenlyDiscFunc=null;
		try {
			ResultSet rs = dbAccessAPI.queryData(sql);
			while(rs.next())
				evenlyDiscFunc = new EvenlyDiscretizedFunc(rs.getFloat(MIN_X),
						rs.getInt(NUM), rs.getFloat(DELTA_X));
		}
		catch (SQLException ex) {
			throw new QueryException(ex.getMessage());
		}
		xyEstimateDB_DAO.getEstimate(estimateInstanceId,evenlyDiscFunc);
		PDF_Estimate estimate=new PDF_Estimate(evenlyDiscFunc,false);
		return estimate;
	}

	/**
	 * Remobe the estimate from the database
	 *
	 * @param estimateInstanceId
	 * @return
	 * @throws UpdateException
	 */
	public boolean removeEstimate(int estimateInstanceId) throws UpdateException {
		boolean isRemovedFromXY_Est= xyEstimateDB_DAO.removeEstimate(estimateInstanceId);
		String sql = "delete from "+TABLE_NAME+" where "+EST_ID+"="+estimateInstanceId;

		try {
			int numRows = dbAccessAPI.insertUpdateOrDeleteData(sql);
			if(numRows==1 && isRemovedFromXY_Est) return true;
		}
		catch(SQLException e) { throw new UpdateException(e.getMessage()); }
		return false;
	}

	public String getEstimateTypeName() {
		return EST_TYPE_NAME;
	}

}
