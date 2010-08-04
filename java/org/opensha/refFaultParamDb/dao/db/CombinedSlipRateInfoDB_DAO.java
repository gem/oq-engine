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

import org.opensha.refFaultParamDb.dao.exception.InsertException;
import org.opensha.refFaultParamDb.dao.exception.QueryException;
import org.opensha.refFaultParamDb.vo.CombinedSlipRateInfo;
import org.opensha.refFaultParamDb.vo.EstimateInstances;

/**
 * <p>Title: CombinedSlipRateInfoDB_DAO.java </p>
 * <p>Description: this class gets/puts slip rate data for Combined Events Info for
 * a site in the database. </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class CombinedSlipRateInfoDB_DAO {
	private final static String TABLE_NAME = "Combined_Slip_Rate_Info";
	private final static String SLIP_ASEISMIC_SLIP_FACTOR_EST_ID="Slip_Aseismic_Est_Id";
	private final static String SLIP_RATE_EST_ID= "Slip_Rate_Est_Id";
	private final static String SLIP_RATE_COMMENTS="Slip_Rate_Comments";
	private final static String ENTRY_DATE="Entry_Date";
	private final static String INFO_ID = "Info_Id";
	private final static String SENSE_OF_MOTION_RAKE = "Sense_of_Motion_Rake";
	private final static String SENSE_OF_MOTION_QUAL = "Sense_of_Motion_Qual";
	private final static String MEASURED_SLIP_COMP_QUAL = "Measured_Slip_Comp_Qual";

	private DB_AccessAPI dbAccess;
	private EstimateInstancesDB_DAO estimateInstancesDAO;

	public CombinedSlipRateInfoDB_DAO(DB_AccessAPI dbAccess) {
		setDB_Connection(dbAccess);
	}

	public void setDB_Connection(DB_AccessAPI dbAccess) {
		this.dbAccess = dbAccess;
		estimateInstancesDAO = new EstimateInstancesDB_DAO(dbAccess);
	}

	/**
	 * Add slip rate info into the database
	 * @param infoId
	 * @param entryDate
	 * @param combinedSlipRateInfo
	 */
	public void addSlipRateInfo(int infoId, String entryDate,
			CombinedSlipRateInfo combinedSlipRateInfo) {

		int slipRateId =  estimateInstancesDAO.addEstimateInstance(combinedSlipRateInfo.getSlipRateEstimate());
		String comments = combinedSlipRateInfo.getSlipRateComments();
		if(comments==null) comments="";
		String colNames="", colVals="";
		String somQual = combinedSlipRateInfo.getSenseOfMotionQual();
		String measuredCompQual = combinedSlipRateInfo.getMeasuredComponentQual();
		EstimateInstances somRake = combinedSlipRateInfo.getSenseOfMotionRake();
		if(somRake!=null) { // check whether user entered Sense of motion rake
			colNames += SENSE_OF_MOTION_RAKE+",";
			int rakeEstId = estimateInstancesDAO.addEstimateInstance(somRake);
			colVals += rakeEstId+",";
		}
		if(somQual!=null) { // check whether user has entered qualitative sense of motion
			colNames+=SENSE_OF_MOTION_QUAL+",";
			colVals += "'"+somQual+"',";
		}
		if(measuredCompQual!=null) { // check whether has entered measured componenet
			colNames += MEASURED_SLIP_COMP_QUAL+",";
			colVals +="'"+measuredCompQual+"',";
		}
		// check whether aseismic slip factor has been provided
		EstimateInstances aseismicSlipEst = combinedSlipRateInfo.getASeismicSlipFactorEstimateForSlip();
		if(aseismicSlipEst!=null) {
			int aSeisId = estimateInstancesDAO.addEstimateInstance(aseismicSlipEst);
			colNames+=SLIP_ASEISMIC_SLIP_FACTOR_EST_ID+",";
			colVals +=""+aSeisId+",";
		}
		String sql = "insert into "+TABLE_NAME+"("+SLIP_RATE_EST_ID+","+
		colNames+SLIP_RATE_COMMENTS+","+
		INFO_ID+","+ENTRY_DATE+") values ("+slipRateId+","+colVals+"'"+
		comments+"',"+infoId+",'"+entryDate+"')";
		//System.out.println(sql);
		try {
			dbAccess.insertUpdateOrDeleteData(sql);
		}catch(SQLException e) {
			throw new InsertException(e.getMessage());
		}
	}


	/**
	 * Return the slip rate info for a combined info for a site
	 * @param infoId
	 * @param entryDate
	 * @return
	 */
	public CombinedSlipRateInfo getCombinedSlipRateInfo(int infoId, String entryDate) {
		CombinedSlipRateInfo combinedSlipRateInfo = null;
		String sql = "select "+SLIP_ASEISMIC_SLIP_FACTOR_EST_ID+","+SENSE_OF_MOTION_RAKE+","+
		SENSE_OF_MOTION_QUAL+","+MEASURED_SLIP_COMP_QUAL+","+
		SLIP_RATE_EST_ID+","+SLIP_RATE_COMMENTS+" from "
		+TABLE_NAME+
		" where "+INFO_ID+"="+infoId+" and "+ENTRY_DATE+"='"+entryDate+"'";
		try {
			ResultSet rs = dbAccess.queryData(sql);
			while(rs.next()) {
				combinedSlipRateInfo = new CombinedSlipRateInfo();
				combinedSlipRateInfo.setSlipRateComments(rs.getString(SLIP_RATE_COMMENTS));
				combinedSlipRateInfo.setSlipRateEstimate(estimateInstancesDAO.getEstimateInstance(rs.getInt(SLIP_RATE_EST_ID)));
				// aseismic slip factor
				EstimateInstances aseismicSlipFactorEst = null;
				int aseismicSlipFactorEstId = rs.getInt(SLIP_ASEISMIC_SLIP_FACTOR_EST_ID);
				if(!rs.wasNull()) aseismicSlipFactorEst = estimateInstancesDAO.getEstimateInstance(aseismicSlipFactorEstId);
				// sense of motion rake
				int senseOfMotionRakeId = rs.getInt(SENSE_OF_MOTION_RAKE);
				EstimateInstances senseOfMotionRake =null;
				if(!rs.wasNull()) senseOfMotionRake=this.estimateInstancesDAO.getEstimateInstance(senseOfMotionRakeId);
				// sense of motion qual
				String senseOfMotionQual = rs.getString(SENSE_OF_MOTION_QUAL);
				if(rs.wasNull()) senseOfMotionQual=null;
				String measuedCompQual = rs.getString(MEASURED_SLIP_COMP_QUAL);
				// measured component qual
				if(rs.wasNull()) measuedCompQual=null;
				combinedSlipRateInfo.setASeismicSlipFactorEstimateForSlip(aseismicSlipFactorEst);
				combinedSlipRateInfo.setSenseOfMotionRake(senseOfMotionRake);
				combinedSlipRateInfo.setSenseOfMotionQual(senseOfMotionQual);
				combinedSlipRateInfo.setMeasuredComponentQual(measuedCompQual);
			}
		}
		catch (SQLException ex) {
			throw new QueryException(ex.getMessage());
		}
		return combinedSlipRateInfo;
	}

}
