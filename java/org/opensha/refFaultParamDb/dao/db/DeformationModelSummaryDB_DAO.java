/**
 * 
 */
package org.opensha.refFaultParamDb.dao.db;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;

import org.opensha.refFaultParamDb.dao.exception.InsertException;
import org.opensha.refFaultParamDb.dao.exception.QueryException;
import org.opensha.refFaultParamDb.dao.exception.UpdateException;
import org.opensha.refFaultParamDb.gui.infotools.SessionInfo;
import org.opensha.refFaultParamDb.vo.DeformationModelSummary;

/**
 * This class puts Deformation model summary (name, associated fault model) into the database.
 * 
 * @author vipingupta
 *
 */
public class DeformationModelSummaryDB_DAO  implements java.io.Serializable {
	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;

	private final static String SEQUENCE_NAME="Def_Model_Summary_Sequence";
	private final static String TABLE_NAME="Deformation_Model_Summary";
	private final static String DEF_MODEL_ID="Deformation_Model_Id";
	private final static String FAULT_MODEL_ID="Fault_Model_Id";
	private final static String CONTRIBUTOR_ID="Contributor_Id";
	private final static String DEF_MODEL_NAME="Deformation_Model_Name";
	private FaultModelSummaryDB_DAO faultModelSummaryDAO;
	private DB_AccessAPI dbAccessAPI;


	public DeformationModelSummaryDB_DAO(DB_AccessAPI dbAccessAPI) {
		setDB_Connection(dbAccessAPI);
	}

	public void setDB_Connection(DB_AccessAPI dbAccessAPI) {
		this.dbAccessAPI = dbAccessAPI;
		faultModelSummaryDAO= new FaultModelSummaryDB_DAO(dbAccessAPI);
	}

	/**
	 * Add a new deformation model
	 *
	 * @param deformationModel
	 * @throws InsertException
	 */
	public int addDeformationModel(DeformationModelSummary deformationModel) throws InsertException {
		int deformationModelId = -1;
		try {
			deformationModelId = dbAccessAPI.getNextSequenceNumber(SEQUENCE_NAME);
		}catch(SQLException e) {
			throw new InsertException(e.getMessage());
		}
		String sql = "insert into "+TABLE_NAME+"("+ DEF_MODEL_ID+","+FAULT_MODEL_ID+","+CONTRIBUTOR_ID+
		","+DEF_MODEL_NAME+") "+
		" values ("+deformationModelId+","+deformationModel.getFaultModel().getFaultModelId()+","+
		SessionInfo.getContributor().getId()+
		",'"+deformationModel.getDeformationModelName()+"')";
		try { 
			dbAccessAPI.insertUpdateOrDeleteData(sql); 
			deformationModel.setDeformationModelId(deformationModelId);
		}
		catch(SQLException e) {
			//e.printStackTrace();
			throw new InsertException(e.getMessage());
		}
		return deformationModelId;
	}


	/**
	 * Update a deformation Model
	 *
	 * @param deformationModelId
	 * @param deformationModel
	 * @return
	 * @throws UpdateException
	 */
	public boolean updateDeformationModel(int deformationModelId, DeformationModelSummary deformationModel) throws UpdateException {
		String sql = "update "+TABLE_NAME+" set "+DEF_MODEL_NAME+"= '"+
		deformationModel.getDeformationModelName()+"',"+CONTRIBUTOR_ID+"="+SessionInfo.getContributor().getId()+
		","+FAULT_MODEL_ID+"="+deformationModel.getFaultModel().getFaultModelId()+
		" where "+DEF_MODEL_ID+"="+deformationModelId;
		try {
			int numRows = dbAccessAPI.insertUpdateOrDeleteData(sql);
			if(numRows==1) return true;
		}
		catch(SQLException e) { throw new UpdateException(e.getMessage()); }
		return false;

	}

	/**
	 * Get a deformation model based on deformation model ID
	 * 
	 * @param faultModelId
	 * @return
	 * @throws QueryException
	 */
	public DeformationModelSummary getDeformationModel(int deformationModelId) throws QueryException {
		DeformationModelSummary deformationModel=null;
		String condition = " where "+DEF_MODEL_ID+"="+deformationModelId;
		ArrayList<DeformationModelSummary> deformationModelList=query(condition);
		if(deformationModelList.size()>0) deformationModel = (DeformationModelSummary)deformationModelList.get(0);
		return deformationModel;

	}

	/**
	 * Get a deformation model based on deformation model Name
	 * 
	 * @param deformationModelName
	 * @return
	 * @throws QueryException
	 */
	public DeformationModelSummary getDeformationModel(String deformationModelName) throws QueryException {
		DeformationModelSummary deformationModel=null;
		String condition = " where "+DEF_MODEL_NAME+"='"+deformationModelName+"'";
		ArrayList<DeformationModelSummary> deformationModelList=query(condition);
		if(deformationModelList.size()>0) deformationModel = (DeformationModelSummary)deformationModelList.get(0);
		return deformationModel;

	}

	/**
	 * remove a deformation model from the database
	 * @param deformationModelId
	 * @return
	 * @throws UpdateException
	 */
	public boolean removeDeformationModel(int deformationModelId) throws UpdateException {
		String sql = "delete from "+TABLE_NAME+"  where "+DEF_MODEL_ID+"="+deformationModelId;
		try {
			int numRows = dbAccessAPI.insertUpdateOrDeleteData(sql);
			if(numRows==1) return true;
		}
		catch(SQLException e) { throw new UpdateException(e.getMessage()); }
		return false;
	}


	/**
	 * Get all the deformation Models from the database
	 * @return
	 * @throws QueryException
	 */
	public ArrayList<DeformationModelSummary> getAllDeformationModels() throws QueryException {
		return query(" ");
	}

	private ArrayList<DeformationModelSummary> query(String condition) throws QueryException {
		ArrayList<DeformationModelSummary> deformationModelList = new ArrayList<DeformationModelSummary>();
		String sql =  "select "+DEF_MODEL_ID+","+FAULT_MODEL_ID+","+DEF_MODEL_NAME+","+CONTRIBUTOR_ID+" from "+
		TABLE_NAME+condition+ " order by "+DEF_MODEL_ID;
		try {
			ResultSet rs  = dbAccessAPI.queryData(sql);
			ContributorDB_DAO contributorDAO = new ContributorDB_DAO(dbAccessAPI);
			while(rs.next()) {
				DeformationModelSummary defModelSummary = new DeformationModelSummary();
				defModelSummary.setContributor(contributorDAO.getContributor(rs.getInt(CONTRIBUTOR_ID)));
				defModelSummary.setDeformationModelId(rs.getInt(DEF_MODEL_ID));
				defModelSummary.setDeformationModelName(rs.getString(DEF_MODEL_NAME));
				defModelSummary.setFaultModel(this.faultModelSummaryDAO.getFaultModel(rs.getInt(FAULT_MODEL_ID)));
				deformationModelList.add(defModelSummary);
			}

			rs.close();
		} catch(SQLException e) { throw new QueryException(e.getMessage()); }
		return deformationModelList;
	}

}
