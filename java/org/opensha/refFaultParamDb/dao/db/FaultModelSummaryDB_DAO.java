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
import org.opensha.refFaultParamDb.gui.infotools.SessionInfo;
import org.opensha.refFaultParamDb.vo.FaultModelSummary;

/**
 * <p>Title: FaultModelDB_DAO.java </p>
 * <p>Description: Performs insert/delete/update on fault model on oracle database</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */


public class FaultModelSummaryDB_DAO   implements java.io.Serializable {
  /**
	 * 
	 */
	private static final long serialVersionUID = 1L;
	
private final static String SEQUENCE_NAME="Fault_Model_Summary_Sequence";
  private final static String TABLE_NAME="Fault_Model_Summary";
  private final static String FAULT_MODEL_ID="Fault_Model_Id";
  private final static String CONTRIBUTOR_ID="Contributor_Id";
  private final static String FAULT_MODEL_NAME="Fault_Model_Name";
  private DB_AccessAPI dbAccessAPI;


  public FaultModelSummaryDB_DAO(DB_AccessAPI dbAccessAPI) {
   setDB_Connection(dbAccessAPI);
  }

  public void setDB_Connection(DB_AccessAPI dbAccessAPI) {
   this.dbAccessAPI = dbAccessAPI;
 }

 /**
  * Add a new fault model
  *
  * @param faultModel
  * @throws InsertException
  */
  public int addFaultModel(FaultModelSummary faultModel) throws InsertException {
    int faultModelId = -1;
    try {
      faultModelId = dbAccessAPI.getNextSequenceNumber(SEQUENCE_NAME);
    }catch(SQLException e) {
      throw new InsertException(e.getMessage());
    }
    String sql = "insert into "+TABLE_NAME+"("+ FAULT_MODEL_ID+","+CONTRIBUTOR_ID+
        ","+FAULT_MODEL_NAME+") "+
        " values ("+faultModelId+","+SessionInfo.getContributor().getId()+
        ",'"+faultModel.getFaultModelName()+"')";
    try { 
    	dbAccessAPI.insertUpdateOrDeleteData(sql); 
    	faultModel.setFaultModelId(faultModelId);
    }
    catch(SQLException e) {
      //e.printStackTrace();
      throw new InsertException(e.getMessage());
    }
    return faultModelId;
  }


  /**
   * Update a fault Model
   *
   * @param faultModelId
   * @param faultModel
   * @return
   * @throws UpdateException
   */
  public boolean updateFaultModel(int faultModelId, FaultModelSummary faultModel) throws UpdateException {
    String sql = "update "+TABLE_NAME+" set "+FAULT_MODEL_NAME+"= '"+
        faultModel.getFaultModelName()+"',"+CONTRIBUTOR_ID+"="+SessionInfo.getContributor().getId()+
       " where "+FAULT_MODEL_ID+"="+faultModelId;
    try {
      int numRows = dbAccessAPI.insertUpdateOrDeleteData(sql);
      if(numRows==1) return true;
    }
    catch(SQLException e) { throw new UpdateException(e.getMessage()); }
    return false;

  }

  /**
   * Get a fault model based on fault model ID
   * @param faultModelId
   * @return
   * @throws QueryException
   */
  public FaultModelSummary getFaultModel(int faultModelId) throws QueryException {
    FaultModelSummary faultModel=null;
    String condition = " where "+FAULT_MODEL_ID+"="+faultModelId;
    ArrayList<FaultModelSummary> faultModelList=query(condition);
    if(faultModelList.size()>0) faultModel = (FaultModelSummary)faultModelList.get(0);
    return faultModel;

  }

  /**
   * remove a fault model from the database
   * @param faultModelId
   * @return
   * @throws UpdateException
   */
  public boolean removeFaultModel(int faultModelId) throws UpdateException {
    String sql = "delete from "+TABLE_NAME+"  where "+FAULT_MODEL_ID+"="+faultModelId;
    try {
      int numRows = dbAccessAPI.insertUpdateOrDeleteData(sql);
      if(numRows==1) return true;
    }
    catch(SQLException e) { throw new UpdateException(e.getMessage()); }
    return false;
  }


  /**
   * Get all the fault Models from the database
   * @return
   * @throws QueryException
   */
  public ArrayList<FaultModelSummary> getAllFaultModels() throws QueryException {
   return query(" ");
  }

  private ArrayList<FaultModelSummary> query(String condition) throws QueryException {
    ArrayList<FaultModelSummary> faultModelList = new ArrayList<FaultModelSummary>();
    String sql =  "select "+FAULT_MODEL_ID+","+FAULT_MODEL_NAME+","+CONTRIBUTOR_ID+" from "+TABLE_NAME+condition;
    try {
      ResultSet rs  = dbAccessAPI.queryData(sql);
      ContributorDB_DAO contributorDAO = new ContributorDB_DAO(dbAccessAPI);
      while(rs.next()) faultModelList.add(new FaultModelSummary(rs.getInt(FAULT_MODEL_ID),
            rs.getString(FAULT_MODEL_NAME),
            contributorDAO.getContributor(rs.getInt(CONTRIBUTOR_ID))));
      rs.close();
    } catch(SQLException e) { throw new QueryException(e.getMessage()); }
    return faultModelList;
  }

}
