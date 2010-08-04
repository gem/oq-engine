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

import org.opensha.refFaultParamDb.dao.exception.QueryException;
import org.opensha.refFaultParamDb.vo.SectionSource;

/**
 * <p>Title: SectionSourceDB_DAO.java </p>
 * <p>Description: Gets the section source based on source name. Example of sources
 * are CFM or 2002</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */


public class SectionSourceDB_DAO  {
	private final static String TABLE_NAME="Section_Source";
	private final static String SECTION_SOURCE_ID="Section_Source_Id";
	private final static String SECTION_SOURCE_NAME="Section_Source_Name";
	private DB_AccessAPI dbAccessAPI;


	public SectionSourceDB_DAO(DB_AccessAPI dbAccessAPI) {
		setDB_Connection(dbAccessAPI);
	}

	public void setDB_Connection(DB_AccessAPI dbAccessAPI) {
		this.dbAccessAPI = dbAccessAPI;
	}


	/**
	 * Get a section source based on section source ID
	 * @param sectionSourceId
	 * @return
	 * @throws QueryException
	 */
	public SectionSource getSectionSource(int sectionSourceId) throws QueryException {
		String condition = " where "+SECTION_SOURCE_ID+"="+sectionSourceId;
		ArrayList<SectionSource> sectionSourceList=query(condition);
		SectionSource sectionSource=null;
		if(sectionSourceList.size()>0) sectionSource = (SectionSource)sectionSourceList.get(0);
		return sectionSource;

	}

	/**
	 * Get a section source based on section source name
	 * @param sectionSourceName
	 * @return
	 * @throws QueryException
	 */
	public SectionSource getSectionSource(String sectionSourceName) throws QueryException {
		String condition = " where "+SECTION_SOURCE_NAME+"='"+sectionSourceName+"'";
		ArrayList<SectionSource> sectionSourceList=query(condition);
		SectionSource sectionSource=null;
		if(sectionSourceList.size()>0) sectionSource = (SectionSource)sectionSourceList.get(0);
		return sectionSource;
	}

	public ArrayList<SectionSource> getAllSectionSource() {
		return query(" ");
	}


	private ArrayList<SectionSource> query(String condition) throws QueryException {
		ArrayList<SectionSource> sectionSourceList = new ArrayList<SectionSource>();
		String sql =  "select "+SECTION_SOURCE_ID+","+SECTION_SOURCE_NAME+
		" from "+TABLE_NAME+condition;
		try {
			ResultSet rs  = dbAccessAPI.queryData(sql);
			while(rs.next()) sectionSourceList.add(new SectionSource(rs.getInt(SECTION_SOURCE_ID),
					rs.getString(SECTION_SOURCE_NAME)));
			rs.close();
		} catch(SQLException e) { throw new QueryException(e.getMessage()); }
		return sectionSourceList;
	}

}
