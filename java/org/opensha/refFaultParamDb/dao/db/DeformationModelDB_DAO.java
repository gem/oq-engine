/**
 * 
 */
package org.opensha.refFaultParamDb.dao.db;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;

import org.opensha.refFaultParamDb.dao.exception.QueryException;
import org.opensha.refFaultParamDb.dao.exception.UpdateException;
import org.opensha.refFaultParamDb.vo.DeformationModel;
import org.opensha.refFaultParamDb.vo.EstimateInstances;

/**
 *  Allows the user to set the fault sections within this deformation model and also allows to set 
 *  slip rate and aseismic slip factor for each of these sections
 * 
 * @author vipingupta
 *
 */
public class DeformationModelDB_DAO {
	private final static String TABLE_NAME="Deformation_Model";
	private final static String DEF_MODEL_ID = "Deformation_Model_Id";
	private final static String SECTION_ID = "Section_Id";
	private final static String AVE_LONG_TERM_SLIP_RATE="Ave_Long_Term_Slip_Rate_Est";
	private final static String AVE_ASEISMIC_SLIP_EST="Average_Aseismic_Slip_Est";
	private EstimateInstancesDB_DAO estimateInstancesDAO;
	private DB_AccessAPI dbAccessAPI;

	public DeformationModelDB_DAO(DB_AccessAPI dbAccessAPI) {
		setDB_Connection(dbAccessAPI);
	}

	public void setDB_Connection(DB_AccessAPI dbAccessAPI) {
		this.dbAccessAPI = dbAccessAPI;
		estimateInstancesDAO = new EstimateInstancesDB_DAO(dbAccessAPI);
	}




	/**
	 * Update the slip rate for fault section in a deformation model
	 * 
	 * @param deformationModelId
	 * @param faultSectionId
	 * @param slipRateEstimate
	 */
	public void updateSlipRate(int deformationModelId, int faultSectionId, EstimateInstances slipRateEstimate) {
		String  colVals="";

		if(slipRateEstimate!=null) { // check whether slip rate is available
			int slipRateEstId = this.estimateInstancesDAO.addEstimateInstance(slipRateEstimate);
			colVals+=slipRateEstId;
		} else colVals+="NULL";

		// update the fault section in the deforamtion table
		String sql = "update "+TABLE_NAME+" set "+AVE_LONG_TERM_SLIP_RATE+"="+colVals+" where "+
		DEF_MODEL_ID+"="+deformationModelId+" and "+SECTION_ID+"="+faultSectionId;
		try {
			dbAccessAPI.insertUpdateOrDeleteData(sql);
		}catch(SQLException e) {
			throw new UpdateException(e.getMessage());
		}
	}

	/**
	 * Update the aseimsic slip factor for fault section in he deformation model
	 * @param deformationModelId
	 * @param faultSectionId
	 * @param slipRateEstimate
	 */
	public void updateAseimsicSlipFactor(int deformationModelId, int faultSectionId, EstimateInstances aseismicSlipFactorEstimate) {
		String  colVals="";

		if(aseismicSlipFactorEstimate!=null) { // check whether slip rate is available
			int slipRateEstId = this.estimateInstancesDAO.addEstimateInstance(aseismicSlipFactorEstimate);
			colVals+=slipRateEstId;
		} else colVals+="NULL";

		// update the fault section into the deformation table
		String sql = "update "+TABLE_NAME+" set "+AVE_ASEISMIC_SLIP_EST+"="+colVals+" where "+
		DEF_MODEL_ID+"="+deformationModelId+" and "+SECTION_ID+"="+faultSectionId;
		try {
			dbAccessAPI.insertUpdateOrDeleteData(sql);
		}catch(SQLException e) {
			throw new UpdateException(e.getMessage());
		}
	}

	/**
	 * Get slip Rate for particular fault section and deformation model
	 * 
	 * @param deformationModelId
	 * @param faultSectionId
	 * @return
	 */
	public EstimateInstances getSlipRateEstimate(int deformationModelId, int faultSectionId) {
		String sql = "select "+AVE_LONG_TERM_SLIP_RATE+
		" from "+TABLE_NAME+" where "+DEF_MODEL_ID+"="+deformationModelId+" and "+SECTION_ID+"="+faultSectionId;
		EstimateInstances slipRateEst = null;
		try {
			ResultSet rs  = dbAccessAPI.queryData(sql);
			// iterate over all fault section to get their slip rates and aseismic slip factor estimates
			while(rs.next()) {
				int slipRateEstId = rs.getInt(AVE_LONG_TERM_SLIP_RATE);
				if(!rs.wasNull()) slipRateEst =  this.estimateInstancesDAO.getEstimateInstance(slipRateEstId);
			}
			rs.close();
		} catch(SQLException e) { throw new QueryException(e.getMessage()); }
		return slipRateEst;
	}

	/**
	 * Get asesimic slip for a specific fault section and deformation model
	 * @param deformationModelId
	 * @param faultSectionId
	 * @return
	 */
	public EstimateInstances getAseismicSlipEstimate(int deformationModelId, int faultSectionId) {
		String sql = "select "+AVE_ASEISMIC_SLIP_EST+
		" from "+TABLE_NAME+" where "+DEF_MODEL_ID+"="+deformationModelId+" and "+SECTION_ID+"="+faultSectionId;
		EstimateInstances aseismicSlipEst = null;
		try {
			ResultSet rs  = dbAccessAPI.queryData(sql);
			// iterate over all fault section to get their slip rates and aseismic slip factor estimates
			while(rs.next()) {
				int aseimicFactorEstId = rs.getInt(AVE_ASEISMIC_SLIP_EST);
				if(!rs.wasNull()) aseismicSlipEst =  this.estimateInstancesDAO.getEstimateInstance(aseimicFactorEstId);
			}
			rs.close();
		} catch(SQLException e) { throw new QueryException(e.getMessage()); }
		return aseismicSlipEst;
	}

	/**
	 * Get a list of all fault sections within this deformation model
	 * @param deformationModelId
	 * @return
	 */
	public ArrayList<Integer> getFaultSectionIdsForDeformationModel(int deformationModelId) {
		ArrayList<Integer> faultSectionIdList = new ArrayList<Integer>();
		String sql = "select "+SECTION_ID+ " from "+TABLE_NAME+" where "+DEF_MODEL_ID+"="+deformationModelId;

		try {
			ResultSet rs  = dbAccessAPI.queryData(sql);
			// iterate over all fault section to get their slip rates and aseismic slip factor estimates
			while(rs.next()) {
				faultSectionIdList.add(new Integer( rs.getInt(SECTION_ID)));
			}
			rs.close();
		} catch(SQLException e) { throw new QueryException(e.getMessage()); }
		return faultSectionIdList;

	}

	/**
	 * Get a List of Ids of all fault sections, their slip rates and aseismic slip estimates in a deformation model
	 * @param deformationModelIddelId
	 * @return
	 */
	public DeformationModel getDeformationModel(int deformationModelId) {
		String sql = "select "+DEF_MODEL_ID+","+SECTION_ID+ ","+AVE_LONG_TERM_SLIP_RATE+","+AVE_ASEISMIC_SLIP_EST+
		" from "+TABLE_NAME+" where "+DEF_MODEL_ID+"="+deformationModelId;
		DeformationModel deformationModel = new DeformationModel();
		deformationModel.setDeformationModelId(deformationModelId);
		try {
			ResultSet rs  = dbAccessAPI.queryData(sql);
			// iterate over all fault section to get their slip rates and aseismic slip factor estimates
			while(rs.next()) {
				int faultSectionId = rs.getInt(SECTION_ID);
				deformationModel.addFaultSection(faultSectionId);
				int slipRateEstId = rs.getInt(AVE_LONG_TERM_SLIP_RATE);
				if(!rs.wasNull()) deformationModel.setSlipRateEstimate(faultSectionId, this.estimateInstancesDAO.getEstimateInstance(slipRateEstId));
				deformationModel.setAseismicSlipFactorEstimate(faultSectionId, estimateInstancesDAO.getEstimateInstance(rs.getInt(AVE_ASEISMIC_SLIP_EST)));
			}
			rs.close();
		} catch(SQLException e) { throw new QueryException(e.getMessage()); }
		return deformationModel;
	}

	/**
	 * This removes all the rows from the table which associates faultsection names with a particular deformation model
	 * 
	 * @param deformationModelId
	 */
	protected void removeModel(int deformationModelId) {
		String sql = "delete from "+TABLE_NAME+" where "+DEF_MODEL_ID+"="+deformationModelId;
		try {
			dbAccessAPI.insertUpdateOrDeleteData(sql);
		} catch(SQLException e) { throw new UpdateException(e.getMessage()); }
	}
}
