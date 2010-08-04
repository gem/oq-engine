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
import org.opensha.refFaultParamDb.vo.SiteRepresentation;

/**
 * <p>Title: SiteRepresentationDB_DAO.java </p>
 * <p>Description: </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class SiteRepresentationDB_DAO  {

	private final static String TABLE_NAME="Site_Representations";
	private final static String SITE_REPRESENTATION_ID="Site_Representation_Id";
	public final static String SITE_REPRESENTATION_NAME="Site_Representation_Name";
	private DB_AccessAPI dbAccessAPI;


	public SiteRepresentationDB_DAO(DB_AccessAPI dbAccessAPI) {
		setDB_Connection(dbAccessAPI);
	}

	public void setDB_Connection(DB_AccessAPI dbAccessAPI) {
		this.dbAccessAPI = dbAccessAPI;
	}

	/**
	 * Get all the representations with which a site can be associated
	 * @return
	 */
	public ArrayList<SiteRepresentation> getAllSiteRepresentations() {
		return query(" ");
	}

	/**
	 * Get a representation based on site representation Id
	 * @param siteRepresentationId
	 * @return
	 */
	public SiteRepresentation getSiteRepresentation(int siteRepresentationId) {
		SiteRepresentation siteRepresentation=null;
		String condition = " where "+SITE_REPRESENTATION_ID+"="+siteRepresentationId;
		ArrayList<SiteRepresentation> siteRepresentationList=query(condition);
		if(siteRepresentationList.size()>0) siteRepresentation = (SiteRepresentation)siteRepresentationList.get(0);
		return siteRepresentation;
	}

	/**
	 * Get a  representation based on site representation name
	 *
	 * @param siteRepresentationName
	 * @return
	 */
	public SiteRepresentation getSiteRepresentation(String siteRepresentationName) {
		SiteRepresentation siteRepresentation=null;
		String condition = " where upper("+SITE_REPRESENTATION_NAME+")=upper('"+siteRepresentationName+"')";
		ArrayList<SiteRepresentation> siteRepresentationList=query(condition);
		if(siteRepresentationList.size()>0) siteRepresentation = (SiteRepresentation)siteRepresentationList.get(0);
		return siteRepresentation;
	}

	/**
	 *
	 * @param condition
	 * @return
	 * @throws QueryException
	 */
	private ArrayList<SiteRepresentation> query(String condition) throws QueryException {
		ArrayList<SiteRepresentation> siteRepresentationList = new ArrayList<SiteRepresentation>();
		String sql =  "select "+SITE_REPRESENTATION_ID+","+SITE_REPRESENTATION_NAME+" from "+TABLE_NAME+condition;
		try {
			ResultSet rs  = dbAccessAPI.queryData(sql);
			while(rs.next()) siteRepresentationList.add(new SiteRepresentation(rs.getInt(SITE_REPRESENTATION_ID),
					rs.getString(SITE_REPRESENTATION_NAME)));
			rs.close();
		} catch(SQLException e) { throw new QueryException(e.getMessage()); }
		return siteRepresentationList;
	}


}
