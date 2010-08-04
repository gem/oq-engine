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
import org.opensha.refFaultParamDb.vo.Fault;

/**
 * <p>Title: FaultDB_DAO.java </p>
 * <p>Description: this class interacts with the database to get the fault information </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class FaultDB_DAO  {
	private DB_AccessAPI dbAccessAPI;
	private final static String TABLE_NAME = "Fault_Names";
	private final static String FAULT_ID = "Fault_Id";
	private final static String FAULT_NAME = "Fault_Name";


	public FaultDB_DAO(DB_AccessAPI dbAccessAPI) {
		setDB_Connection(dbAccessAPI);
	}

	/**
	 *
	 * @param dbAccessAPI
	 */
	public void setDB_Connection(DB_AccessAPI dbAccessAPI) {
		this.dbAccessAPI = dbAccessAPI;
	}

	/**
	 * Add a fault name to the database
	 * @param fault
	 * @return
	 * @throws InsertException
	 */
	public void addFault(Fault fault) throws InsertException {

		// insert into the table
		String sql = "insert into "+TABLE_NAME+"("+ FAULT_ID+","+FAULT_NAME+")"+
		" values ("+fault.getFaultId()+",'"+fault.getFaultName()+"')";
		try { dbAccessAPI.insertUpdateOrDeleteData(sql); }
		catch(SQLException e) {
			//e.printStackTrace();
			throw new InsertException(e.getMessage());
		}
	}


	/**
	 * Get the information about a fault based on fault Id
	 * @param faultId
	 * @return
	 */
	public Fault getFault(int faultId) throws QueryException {
		Fault fault=null;
		String condition  =  " where "+FAULT_ID+"="+faultId+"";
		ArrayList<Fault> faultList = query(condition);
		if(faultList.size()>0) fault = (Fault)faultList.get(0);
		return fault;
	}

	/**
	 * Get information about a fault based on fault name
	 * @param faultName
	 * @return
	 */
	public Fault getFault(String faultName) throws QueryException {
		Fault fault=null;
		String condition  =  " where "+FAULT_NAME+"='"+faultName+"'";
		ArrayList<Fault> faultList = query(condition);
		if(faultList.size()>0) fault = (Fault)faultList.get(0);
		return fault;
	}

	/**
	 * Get a list of all the faults existing itn database
	 * @return
	 */
	public ArrayList<Fault> getAllFaults() throws QueryException {
		return query(" ");
	}

	// query based on the condition
	private ArrayList<Fault> query(String condition) throws QueryException  {
		ArrayList<Fault> faultNamesList = new ArrayList<Fault>();
		String sql = "select "+FAULT_ID+","+FAULT_NAME+" from "+
		TABLE_NAME+" "+condition;
		try {
			ResultSet rs  = dbAccessAPI.queryData(sql);
			while(rs.next()) faultNamesList.add(new Fault(rs.getInt(FAULT_ID), rs.getString(FAULT_NAME)));
			rs.close();
		} catch(SQLException e) { throw new QueryException(e.getMessage()); }
		return faultNamesList;
	}
}
