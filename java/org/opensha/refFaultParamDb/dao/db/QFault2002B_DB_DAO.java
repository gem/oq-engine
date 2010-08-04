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
import org.opensha.refFaultParamDb.vo.QFault2002B;

/**
 * <p>Title: QFault2002B_DB_DAO.java </p>
 * <p>Description: get the fault sections info from Qfault2002B table in pasadena
 * oracle database</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class QFault2002B_DB_DAO  {

	private final static String TABLE_NAME="QFault_2002B";
	private final static String SECTION_ID="Section_Id";
	private final static String SECTION_NAME="Section_Name";
	private final static String EFFECTIVE_DATE="Effective_Date";
	private final static String COMMENTS="comments";
	private final static String AVG_SLIP_RATE="Avg_Slip_Rate";
	private final static String SLIP_COMMENTS="Slip_Comments";
	private final static String SLIP_RATE_STDDEV="Slip_Rate_StdDev";
	private final static String SLIP_DEV_COMMENTS="Slip_Dev_Comment";
	private final static String AVG_DIP="Avg_Dip";
	private final static String DIP_COMMENTS="Dip_Comments";
	private final static String AVG_UPPER_DEPTH="Avg_Upper_Depth";
	private final static String UPPER_D_COMMENT="Upper_D_Comment";
	private final static String AVG_LOWER_DEPTH="Avg_Lower_Depth";
	private final static String LOWER_D_COMMENT="Lower_D_Comment";
	private final static String AVG_RAKE="Avg_Rake";
	private final static String RAKE_COMMENTS="Rake_Comments";

	private DB_AccessAPI dbAccessAPI;

	/**
	 * Constructor.
	 * @param dbConnection
	 */
	public QFault2002B_DB_DAO(DB_AccessAPI dbAccessAPI) {
		setDB_Connection(dbAccessAPI);
	}


	public void setDB_Connection(DB_AccessAPI dbAccessAPI) {
		this.dbAccessAPI = dbAccessAPI;
	}

	public QFault2002B getFaultSection(String sectionId) throws QueryException {
		QFault2002B faultSection=null;
		String condition = " where "+SECTION_ID+"='"+sectionId+"'";
		ArrayList<QFault2002B> faultSectionList = query(condition);
		if(faultSectionList.size()>0) faultSection = (QFault2002B)faultSectionList.get(0);
		return faultSection;
	}

	public ArrayList<QFault2002B> getAllFaultSections() throws QueryException {
		return query(" ");
	}

	private ArrayList<QFault2002B> query(String condition) throws QueryException {
		ArrayList<QFault2002B> faultSectionList = new ArrayList<QFault2002B>();
		String sql = "select " + SECTION_ID + "," + SECTION_NAME + "," +
		EFFECTIVE_DATE + "," +
		COMMENTS + "," + AVG_SLIP_RATE + "," + SLIP_COMMENTS + "," +
		SLIP_RATE_STDDEV + "," +
		SLIP_DEV_COMMENTS + "," + AVG_DIP + "," + DIP_COMMENTS + "," +
		AVG_UPPER_DEPTH + "," +
		UPPER_D_COMMENT + "," + AVG_LOWER_DEPTH + "," + LOWER_D_COMMENT + "," +
		AVG_RAKE + "," + RAKE_COMMENTS +
		" from " + TABLE_NAME + condition;

		try {
			ResultSet rs = dbAccessAPI.queryData(sql);
			while (rs.next()) {
				QFault2002B faultSection = new QFault2002B();
				faultSection.setSectionId(rs.getString(SECTION_ID));
				faultSection.setSectionName(rs.getString(SECTION_NAME));
				faultSection.setEffectiveDate(rs.getDate(EFFECTIVE_DATE));
				faultSection.setComments(rs.getString(COMMENTS));
				faultSection.setAvgSlipRate(rs.getFloat(AVG_SLIP_RATE));
				faultSection.setSlipComments(rs.getString(SLIP_COMMENTS));
				faultSection.setSlipRateStdDev(rs.getFloat(SLIP_RATE_STDDEV));
				faultSection.setSlipDevComment(rs.getString(SLIP_DEV_COMMENTS));
				faultSection.setAveDip(rs.getFloat(AVG_DIP));
				faultSection.setDipComments(rs.getString(DIP_COMMENTS));
				faultSection.setAvgUpperDepth(rs.getFloat(AVG_UPPER_DEPTH));
				faultSection.setUpperDepthComment(rs.getString(UPPER_D_COMMENT));
				faultSection.setAvgLowerDepth(rs.getFloat(AVG_LOWER_DEPTH));
				faultSection.setLowerDepthComment(rs.getString(LOWER_D_COMMENT));
				faultSection.setAveRake(rs.getFloat(AVG_RAKE));
				faultSection.setRakeComments(rs.getString(RAKE_COMMENTS));
				faultSectionList.add(faultSection);
			}
			rs.close();
		}
		catch (SQLException e) {
			throw new QueryException(e.getMessage());
		}
		return faultSectionList;
	}

}
