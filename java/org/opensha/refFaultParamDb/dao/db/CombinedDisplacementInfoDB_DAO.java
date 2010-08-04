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
import org.opensha.refFaultParamDb.vo.CombinedDisplacementInfo;
import org.opensha.refFaultParamDb.vo.EstimateInstances;

/**
 * <p>Title: CombinedDisplacementInfoDB_DAO.java </p>
 * <p>Description: </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class CombinedDisplacementInfoDB_DAO {
	private final static String TABLE_NAME = "Combined_Displacement_Info";
	private final static String INFO_ID = "Info_Id";
	private final static String ENTRY_DATE="Entry_Date";
	private final static String TOTAL_SLIP_EST_ID = "Total_Slip_Est_Id";
	private final static String DISP_ASEISMIC_SLIP_FACTOR_EST_ID="Disp_Aseismic_Est_Id";
	private final static String TOTAL_SLIP_COMMENTS="Total_Slip_Comments";
	private final static String SENSE_OF_MOTION_RAKE = "Sense_of_Motion_Rake";
	private final static String SENSE_OF_MOTION_QUAL = "Sense_of_Motion_Qual";
	private final static String MEASURED_SLIP_COMP_QUAL = "Measured_Slip_Comp_Qual";

	private DB_AccessAPI dbAccess;
	private EstimateInstancesDB_DAO estimateInstancesDAO;

	public CombinedDisplacementInfoDB_DAO(DB_AccessAPI dbAccess) {
		setDB_Connection(dbAccess);
	}

	public void setDB_Connection(DB_AccessAPI dbAccess) {
		this.dbAccess = dbAccess;
		estimateInstancesDAO = new EstimateInstancesDB_DAO(dbAccess);
	}

	/**
	 * Add displacement info into the database
	 *
	 * @param infoId
	 * @param entryDate
	 * @param combinedDispInfo
	 */
	public void addDisplacementInfo(int infoId, String entryDate,
			CombinedDisplacementInfo combinedDispInfo) {
		int displacementId =  estimateInstancesDAO.addEstimateInstance(combinedDispInfo.getDisplacementEstimate());
		String comments = combinedDispInfo.getDisplacementComments();
		if(comments==null) comments="";
		String somQual = combinedDispInfo.getSenseOfMotionQual();
		String measuredCompQual = combinedDispInfo.getMeasuredComponentQual();
		String colNames="", colVals="";
		EstimateInstances somRake = combinedDispInfo.getSenseOfMotionRake();
		if(somRake!=null) { // check whether user entered Sense of motion rake
			colNames += SENSE_OF_MOTION_RAKE+",";
			int rakeEstId = estimateInstancesDAO.addEstimateInstance(somRake);
			colVals += rakeEstId+",";
		}
		// check whether sense of motion qualitative has been entered
		if(somQual!=null) {
			colNames+=SENSE_OF_MOTION_QUAL+",";
			colVals += "'"+somQual+"',";
		}
		// check whether measured component qualitative has been entered
		if(measuredCompQual!=null) {
			colNames += MEASURED_SLIP_COMP_QUAL+",";
			colVals +="'"+measuredCompQual+"',";
		}
		// check whether aseismic slip factor has been provided
		EstimateInstances aseismicSlipEst = combinedDispInfo.getASeismicSlipFactorEstimateForDisp();
		if(aseismicSlipEst!=null) {
			int aSeisId = estimateInstancesDAO.addEstimateInstance(aseismicSlipEst);
			colNames+=DISP_ASEISMIC_SLIP_FACTOR_EST_ID+",";
			colVals +=""+aSeisId+",";
		}


		String sql = "insert into "+TABLE_NAME+"("+TOTAL_SLIP_EST_ID+","+
		colNames+TOTAL_SLIP_COMMENTS+","+
		INFO_ID+","+ENTRY_DATE+") values ("+displacementId+","+colVals+"'"+
		comments+"',"+infoId+",'"+entryDate+"')";
		try {
			dbAccess.insertUpdateOrDeleteData(sql);
		}catch(SQLException e) {
			throw new InsertException(e.getMessage());
		}
	}

	/**
	 * Get the displacement based on combined events info Id
	 * @param infoId
	 * @param entryDate
	 * @return
	 */
	public CombinedDisplacementInfo getDisplacementInfo(int infoId, String entryDate) {
		CombinedDisplacementInfo combinedDisplacementInfo =null;
		String sql = "select "+DISP_ASEISMIC_SLIP_FACTOR_EST_ID+","+SENSE_OF_MOTION_RAKE+","+
		SENSE_OF_MOTION_QUAL+","+MEASURED_SLIP_COMP_QUAL+
		","+TOTAL_SLIP_EST_ID+","+TOTAL_SLIP_COMMENTS+
		" from "+TABLE_NAME+
		" where "+INFO_ID+"="+infoId+" and "+ENTRY_DATE+"='"+entryDate+"'";
		try {
			ResultSet rs = dbAccess.queryData(sql);
			while(rs.next()) {
				combinedDisplacementInfo = new CombinedDisplacementInfo();
				combinedDisplacementInfo.setDisplacementComments(rs.getString(TOTAL_SLIP_COMMENTS));
				combinedDisplacementInfo.setDisplacementEstimate(estimateInstancesDAO.getEstimateInstance(rs.getInt(TOTAL_SLIP_EST_ID)));
				// aseismic slip factor
				EstimateInstances aseismicSlipFactorEst = null;
				int aseismicSlipFactorEstId = rs.getInt(DISP_ASEISMIC_SLIP_FACTOR_EST_ID);
				if(!rs.wasNull()) aseismicSlipFactorEst = estimateInstancesDAO.getEstimateInstance(aseismicSlipFactorEstId);
				// sense of motion rake
				int senseOfMotionRakeId = rs.getInt(SENSE_OF_MOTION_RAKE);
				EstimateInstances senseOfMotionRake =null;
				if(!rs.wasNull()) senseOfMotionRake=this.estimateInstancesDAO.getEstimateInstance(senseOfMotionRakeId);
				// sense of motion qualitative
				String senseOfMotionQual = rs.getString(SENSE_OF_MOTION_QUAL);
				if(rs.wasNull()) senseOfMotionQual=null;
				//measured component of slip
				String measuedCompQual = rs.getString(MEASURED_SLIP_COMP_QUAL);
				if(rs.wasNull()) measuedCompQual=null;

				combinedDisplacementInfo.setASeismicSlipFactorEstimateForDisp(aseismicSlipFactorEst);
				combinedDisplacementInfo.setSenseOfMotionRake(senseOfMotionRake);
				combinedDisplacementInfo.setSenseOfMotionQual(senseOfMotionQual);
				combinedDisplacementInfo.setMeasuredComponentQual(measuedCompQual);
			}
		}
		catch (SQLException ex) {
			throw new QueryException(ex.getMessage());
		}
		return combinedDisplacementInfo;
	}


}
