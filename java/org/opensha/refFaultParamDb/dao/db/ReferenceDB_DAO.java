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
import org.opensha.refFaultParamDb.vo.Reference;

/**
 * <p>Title:ReferenceDB_DAO.java</p>
 * <p>Description: This class connects with database to access the Reference table </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class ReferenceDB_DAO {
	private final static String SEQUENCE_NAME="Reference_Sequence";
	private final static String TABLE_NAME="Reference";
	private final static String REFERENCE_ID="Reference_Id";
	private final static String REF_YEAR="Ref_Year";
	private final static String REF_AUTH = "Ref_Auth";
	private final static String FULL_BIBLIOGRAPHIC_REFERENCE="Full_Bibliographic_Reference";
	private final static String QFAULT_REFERENCE_ID= "QFault_Reference_Id";
	private DB_AccessAPI dbAccessAPI;
	private static ArrayList<Reference> referenceList;

	/**
	 * Constructor.
	 * @param dbConnection
	 */
	public ReferenceDB_DAO(DB_AccessAPI dbAccessAPI) {
		setDB_Connection(dbAccessAPI);
	}


	public void setDB_Connection(DB_AccessAPI dbAccessAPI) {
		this.dbAccessAPI = dbAccessAPI;
	}

	/**
	 * Add a reference to the reference table
	 * @param reference
	 * @return
	 * @throws InsertException
	 */
	public int addReference(Reference reference) throws InsertException {
		int referenceId = -1;
		try {
			referenceId = dbAccessAPI.getNextSequenceNumber(SEQUENCE_NAME);
		}catch(SQLException e) {
			throw new InsertException(e.getMessage());
		}

		String sql = "insert into "+TABLE_NAME+"("+ REFERENCE_ID+","+REF_AUTH+","+
		REF_YEAR+","+FULL_BIBLIOGRAPHIC_REFERENCE+")"+
		" values ("+referenceId+",'"+reference.getRefAuth()+"','"+
		reference.getRefYear()+"','"+reference.getFullBiblioReference()+"')";
		try {
			dbAccessAPI.insertUpdateOrDeleteData(sql);
			if(referenceList!=null)
				referenceList.add(reference); // add to cached list of references
		}
		catch(SQLException e) {
			//e.printStackTrace();
			throw new InsertException(e.getMessage());
		}
		return referenceId;
	}

	/**
	 * Update a reference in the table
	 * @param referenceId
	 * @param reference
	 * @throws UpdateException
	 */
	public boolean updateReference(int referenceId, Reference reference) throws UpdateException {
		String sql = "update "+TABLE_NAME+" set "+REF_AUTH+"= '"+
		reference.getRefAuth()+"',"+ REF_YEAR+"="+reference.getRefYear()+","+
		FULL_BIBLIOGRAPHIC_REFERENCE+"='"+
		reference.getFullBiblioReference()+"' where "+REFERENCE_ID+"="+referenceId;
		try {
			int numRows = dbAccessAPI.insertUpdateOrDeleteData(sql);
			if(numRows==1) return true;
		}
		catch(SQLException e) { throw new UpdateException(e.getMessage()); }
		return false;
	}


	/**
	 * Get reference corresponding to an Id
	 * @param referenceId
	 * @return
	 * @throws QueryException
	 */
	public Reference getReference(int referenceId) throws QueryException {
		Reference reference=null;
		String condition  =  " where "+REFERENCE_ID+"="+referenceId;
		ArrayList<Reference> referenceList = query(condition);
		if(referenceList.size()>0) reference = (Reference)referenceList.get(0);
		return reference;
	}

	/**
	 * Get reference corresponding to an Id
	 * @param referenceId
	 * @return
	 * @throws QueryException
	 */
	public Reference getReference(String author, String year) throws QueryException {
		Reference reference=null;
		String condition  =  " where "+REF_AUTH+"='"+author+"' and "+REF_YEAR+"='"+year+"'";
		ArrayList<Reference> referenceList = query(condition);
		if(referenceList.size()>0) reference = (Reference)referenceList.get(0);
		return reference;
	}


	/**
	 * Get reference corresponding to Qfault_Reference_Id
	 * @param qfaultReferenceId
	 * @return
	 * @throws QueryException
	 */
	public Reference getReferenceByQfaultId(int qfaultReferenceId) throws QueryException {
		Reference reference=null;
		String condition  =  " where "+QFAULT_REFERENCE_ID+"="+qfaultReferenceId;
		ArrayList<Reference> referenceList = query(condition);
		if(referenceList.size()>0) reference = (Reference)referenceList.get(0);
		return reference;
	}


	/**
	 * Remove a reference from the table
	 *
	 * @param referenceId
	 * @throws UpdateException
	 */
	public boolean removeReference(int referenceId) throws UpdateException {
		String sql = "delete from "+TABLE_NAME+"  where "+REFERENCE_ID+"="+referenceId;
		try {
			int numRows = dbAccessAPI.insertUpdateOrDeleteData(sql);
			if(numRows==1) return true;
		}
		catch(SQLException e) { throw new UpdateException(e.getMessage()); }
		return false;
	}

	/**
	 * Get a list of all the references ordered by short citation
	 *
	 * @return
	 * @throws QueryException
	 */
	public ArrayList<Reference> getAllReferences() throws QueryException {
		return query(" ");
	}

	/**
	 * Get a list of summary for all references
	 * @return
	 * @throws QueryException
	 */
	public ArrayList<Reference> getAllReferencesSummary() throws QueryException {
		if(referenceList!=null) return referenceList;
		referenceList = new ArrayList<Reference>();
		String sql = "select "+REFERENCE_ID+","+REF_YEAR+","+
		REF_AUTH+" from "+TABLE_NAME+" order by "+REF_AUTH;
		try {
			ResultSet rs  = dbAccessAPI.queryData(sql);
			while(rs.next())  {
				Reference referenceSummary = new Reference();
				referenceSummary.setRefAuth(rs.getString(REF_AUTH));
				referenceSummary.setReferenceId(rs.getInt(REFERENCE_ID));
				referenceSummary.setRefYear(rs.getString(REF_YEAR));
				referenceList.add(referenceSummary);
			}
			rs.close();
		} catch(SQLException e) { throw new QueryException(e.getMessage()); }
		return referenceList;
	}


	private ArrayList<Reference> query(String condition) throws QueryException {
		ArrayList<Reference> referenceList = new ArrayList<Reference>();
		String sql = "select "+REFERENCE_ID+","+REF_YEAR+","+
		REF_AUTH+","+ QFAULT_REFERENCE_ID+","+FULL_BIBLIOGRAPHIC_REFERENCE+" from "+TABLE_NAME+
		" "+condition+" order by "+REF_AUTH;
		try {
			ResultSet rs  = dbAccessAPI.queryData(sql);
			while(rs.next())  {
				Reference reference = new Reference(rs.getInt(REFERENCE_ID),
						rs.getString(REF_AUTH),
						rs.getString(REF_YEAR),
						rs.getString(FULL_BIBLIOGRAPHIC_REFERENCE));
				int qFaultRefId = rs.getInt(QFAULT_REFERENCE_ID);
				if(!rs.wasNull()) reference.setQfaultReferenceId(qFaultRefId);
				referenceList.add(reference);
			}
			rs.close();
		} catch(SQLException e) { throw new QueryException(e.getMessage()); }
		return referenceList;
	}
}
