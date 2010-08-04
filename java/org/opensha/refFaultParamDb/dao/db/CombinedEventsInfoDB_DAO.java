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
import org.opensha.refFaultParamDb.gui.infotools.SessionInfo;
import org.opensha.refFaultParamDb.vo.CombinedDisplacementInfo;
import org.opensha.refFaultParamDb.vo.CombinedEventsInfo;
import org.opensha.refFaultParamDb.vo.CombinedNumEventsInfo;
import org.opensha.refFaultParamDb.vo.CombinedSlipRateInfo;
import org.opensha.refFaultParamDb.vo.EventSequence;
import org.opensha.refFaultParamDb.vo.Reference;

/**
 * <p>Title: CombinedEventsInfoDB_DAO.java </p>
 * <p>Description: This class interacts with the Combined Events info table in the database.</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class CombinedEventsInfoDB_DAO {
	private final static String TABLE_NAME = "Combined_Events_Info";
	private final static String SEQUENCE_NAME="Combined_Events_Sequence";
	private final static String INFO_ID = "Info_Id";
	private final static String SITE_ID = "Site_Id";
	private final static String SITE_ENTRY_DATE = "Site_Entry_Date";
	private final static String ENTRY_DATE="Entry_Date";
	private final static String CONTRIBUTOR_ID ="Contributor_Id";
	private final static String START_TIME_ID = "Start_Time_Id";
	private final static String END_TIME_ID="End_Time_Id";
	private final static String DATED_FEATURE_COMMENTS = "Dated_Feature_Comments";
	private final static String NEOKINEMA_FAULT_NUMBER = "NeoKinema_Fault_Number";
	private final static String FAULT_SECTION_ID = "Fault_Section_Id";
	private final static String DATA_SOURCE = "Data_Source";
	//table for references
	private final static String REFERENCES_TABLE_NAME = "Combined_Events_References";
	private final static String COMBINED_EVENTS_ID = "Combined_Events_Id";
	private final static String COMBINED_EVENTS_ENTRY_DATE="Combined_Events_Entry_Date";
	private final static String REFERENCE_ID= "Reference_Id";
	private final static String IS_EXPERT_OPINION = "Is_Expert_Opinion";
	private final static String IS_RECORD_DELETED = "Is_Record_Deleted";
	private final static String NO = "N";
	private final static String YES = "Y";

	private DB_AccessAPI dbAccess;
	private TimeInstanceDB_DAO timeInstanceDAO;
	private ReferenceDB_DAO referenceDAO;
	private ContributorDB_DAO contributorDAO;
	private CombinedDisplacementInfoDB_DAO combinedDispInfoDB_DAO;
	private CombinedNumEventsInfoDB_DAO combinedNumEventsInfoDB_DAO;
	private CombinedSlipRateInfoDB_DAO combinedSlipRateInfoDB_DAO;
	private EventSequenceDB_DAO eventSequenceDAO;
	private PaleoSitePublicationsDB_DAO paleoSitePublicationDAO;

	public CombinedEventsInfoDB_DAO(DB_AccessAPI dbAccess) {
		setDB_Connection(dbAccess);
	}

	public void setDB_Connection(DB_AccessAPI dbAccess) {
		this.dbAccess = dbAccess;
		timeInstanceDAO = new TimeInstanceDB_DAO(dbAccess);
		referenceDAO = new ReferenceDB_DAO(dbAccess);
		contributorDAO = new ContributorDB_DAO(dbAccess);
		combinedDispInfoDB_DAO = new CombinedDisplacementInfoDB_DAO(dbAccess);
		combinedNumEventsInfoDB_DAO = new CombinedNumEventsInfoDB_DAO(dbAccess);
		combinedSlipRateInfoDB_DAO = new CombinedSlipRateInfoDB_DAO(dbAccess);
		eventSequenceDAO = new EventSequenceDB_DAO(dbAccess);
		paleoSitePublicationDAO = new PaleoSitePublicationsDB_DAO(dbAccess);
	}


	/**
	 * Add the combined events info into the database
	 *
	 * @param combinedEventsInfo
	 */
	public void addCombinedEventsInfo(CombinedEventsInfo combinedEventsInfo) {
		String systemDate;
		int infoId;
		try {
			infoId = dbAccess.getNextSequenceNumber(SEQUENCE_NAME);
			systemDate = dbAccess.getSystemDate();
		}catch(SQLException e) {
			throw new InsertException(e.getMessage());
		}

		// get the start time Id (if available)
		String colNames="", colVals="";
		if(combinedEventsInfo.getStartTime()!=null) {
			int startTimeId = timeInstanceDAO.addTimeInstance(combinedEventsInfo.getStartTime());
			colNames+=START_TIME_ID+",";
			colVals+=startTimeId+",";
		}
		// get the end time Id (if available)
		if(combinedEventsInfo.getEndTime()!=null) {
			int endTimeId = timeInstanceDAO.addTimeInstance(combinedEventsInfo.getEndTime());
			colNames+=END_TIME_ID+",";
			colVals+=endTimeId+",";
		}
		// get the data source
		if(combinedEventsInfo.getDataSource()!=null) {
			colNames+=DATA_SOURCE+",";
			colVals+="'"+combinedEventsInfo.getDataSource()+"',";
		}
		String expertOpinion = NO;
		if(combinedEventsInfo.getIsExpertOpinion()) expertOpinion= YES;


		String sql = "insert into "+TABLE_NAME+"("+INFO_ID+","+SITE_ID+","+
		SITE_ENTRY_DATE+","+ENTRY_DATE+","+CONTRIBUTOR_ID+","+
		colNames+
		DATED_FEATURE_COMMENTS+","+IS_EXPERT_OPINION+","+IS_RECORD_DELETED+","+
		NEOKINEMA_FAULT_NUMBER+") "+
		"values ("+infoId+","+combinedEventsInfo.getSiteId()+",'"+
		combinedEventsInfo.getSiteEntryDate()+"','"+systemDate+"',"+
		SessionInfo.getContributor().getId()+","+colVals+"'"+
		combinedEventsInfo.getDatedFeatureComments()+"','"+expertOpinion+"','"+
		NO+"','"+combinedEventsInfo.getNeokinemaFaultNumber()+"')";

		try {
			dbAccess.insertUpdateOrDeleteData(sql);
			// add site publication info
			paleoSitePublicationDAO.addPaleoSitePublicationInfo(combinedEventsInfo.getPaleoSitePublication());
			// add displacement info
			CombinedDisplacementInfo combinedDispInfo = combinedEventsInfo.getCombinedDisplacementInfo();
			if(combinedDispInfo!=null) this.combinedDispInfoDB_DAO.addDisplacementInfo(infoId, systemDate, combinedDispInfo);
			// add slip rate info
			CombinedSlipRateInfo combinedSlipRateInfo = combinedEventsInfo.getCombinedSlipRateInfo();
			if(combinedSlipRateInfo!=null) this.combinedSlipRateInfoDB_DAO.addSlipRateInfo(infoId, systemDate, combinedSlipRateInfo);
			// add num events info
			CombinedNumEventsInfo combinedNumEventsInfo = combinedEventsInfo.getCombinedNumEventsInfo();
			if(combinedNumEventsInfo!=null) this.combinedNumEventsInfoDB_DAO.addNumEventsInfo(infoId, systemDate, combinedNumEventsInfo);
			// add the events sequences
			ArrayList<EventSequence> eventSequenceList = combinedEventsInfo.getEventSequence();
			if(eventSequenceList!=null && eventSequenceList.size()!=0)
				this.eventSequenceDAO.addEventSequence(infoId, systemDate, eventSequenceList);
			// now insert the references in the combined info references table
			ArrayList<Reference> referenceList = combinedEventsInfo.getReferenceList();
			for(int i=0; i<referenceList.size(); ++i) {
				int referenceId =(referenceList.get(i)).getReferenceId();
				sql = "insert into "+REFERENCES_TABLE_NAME+"("+COMBINED_EVENTS_ID+
				","+COMBINED_EVENTS_ENTRY_DATE+","+REFERENCE_ID+") "+
				"values ("+infoId+",'"+
				systemDate+"',"+referenceId+")";
				dbAccess.insertUpdateOrDeleteData(sql);
			}
		}
		catch(SQLException e) {
			e.printStackTrace();
			throw new InsertException(e.getMessage());
		}
	}


	/**
	 * Get the combined events info list for a particular site
	 *
	 * @param siteId
	 * @return
	 */
	public ArrayList<CombinedEventsInfo> getCombinedEventsInfoList(int siteId, int referenceId) {
		String condition = " where "+SITE_ID+"="+siteId+" and "+IS_RECORD_DELETED+
		"='"+NO+"'";
		return query(condition, referenceId);
	}

	/**
	 * Query the combined info table based on condition
	 *
	 * @param condition
	 * @return
	 */
	private ArrayList<CombinedEventsInfo> query(String condition, int referenceId) {
		ArrayList<CombinedEventsInfo> combinedInfoList = new ArrayList<CombinedEventsInfo>();
		String sql =  "select "+INFO_ID+","+SITE_ID+",to_char("+SITE_ENTRY_DATE+") as "+SITE_ENTRY_DATE+","+
		"to_char("+ENTRY_DATE+") as "+ENTRY_DATE+","+
		START_TIME_ID+","+END_TIME_ID+","+CONTRIBUTOR_ID+","+DATED_FEATURE_COMMENTS+
		","+IS_EXPERT_OPINION+","+NEOKINEMA_FAULT_NUMBER+","+DATA_SOURCE+","+FAULT_SECTION_ID+" from "+TABLE_NAME+condition;
		try {
			ResultSet rs  = dbAccess.queryData(sql);
			while(rs.next())  {

				// get all the references for this site
				ArrayList<Reference> referenceList = new ArrayList<Reference>();
				sql = "select "+REFERENCE_ID+" from "+REFERENCES_TABLE_NAME+
				" where "+COMBINED_EVENTS_ID+"="+rs.getInt(INFO_ID)+" and "+
				COMBINED_EVENTS_ENTRY_DATE+"='"+rs.getString(ENTRY_DATE)+"'";
				ResultSet referenceResultSet = dbAccess.queryData(sql);
				boolean found = false;
				while(referenceResultSet.next()) {
					int refId = referenceResultSet.getInt(REFERENCE_ID);
					if(refId==referenceId) found = true;
					referenceList.add(referenceDAO.getReference(refId));
				}
				referenceResultSet.close();
				if(!found) continue;

				CombinedEventsInfo combinedEventsInfo = new  CombinedEventsInfo();
				// set the references in the VO
				combinedEventsInfo.setReferenceList(referenceList);
				combinedEventsInfo.setInfoId(rs.getInt(INFO_ID));
				combinedEventsInfo.setFaultSectionId(rs.getInt(FAULT_SECTION_ID));
				combinedEventsInfo.setEntryDate(rs.getString(ENTRY_DATE));
				combinedEventsInfo.setSiteId(rs.getInt(SITE_ID));
				combinedEventsInfo.setSiteEntryDate(rs.getString(SITE_ENTRY_DATE));
				int startTimeId = rs.getInt(START_TIME_ID);
				if(!rs.wasNull()) combinedEventsInfo.setStartTime(this.timeInstanceDAO.getTimeInstance(startTimeId));
				int endTimeId = rs.getInt(END_TIME_ID);
				if(!rs.wasNull()) combinedEventsInfo.setEndTime(this.timeInstanceDAO.getTimeInstance(endTimeId));
				String dataSource = rs.getString(DATA_SOURCE);
				if(!rs.wasNull()) combinedEventsInfo.setDataSource(dataSource);
				combinedEventsInfo.setDatedFeatureComments(rs.getString(DATED_FEATURE_COMMENTS));
				combinedEventsInfo.setNeokinemaFaultNumber(rs.getString(NEOKINEMA_FAULT_NUMBER));
				// set displacement
				combinedEventsInfo.setCombinedDisplacementInfo(
						this.combinedDispInfoDB_DAO.getDisplacementInfo(rs.getInt(INFO_ID), rs.getString(ENTRY_DATE)));
				// set num events info
				combinedEventsInfo.setCombinedNumEventsInfo(
						this.combinedNumEventsInfoDB_DAO.getCombinedNumEventsInfo(rs.getInt(INFO_ID), rs.getString(ENTRY_DATE)));
				// set slip rate info
				combinedEventsInfo.setCombinedSlipRateInfo(
						this.combinedSlipRateInfoDB_DAO.getCombinedSlipRateInfo(rs.getInt(INFO_ID), rs.getString(ENTRY_DATE)));
				// set the sequences info
				combinedEventsInfo.setEventSequenceList(
						this.eventSequenceDAO.getSequences(rs.getInt(INFO_ID), rs.getString(ENTRY_DATE)));
				// get the contributor info
				combinedEventsInfo.setContributorName(this.contributorDAO.getContributor(rs.getInt(CONTRIBUTOR_ID)).getName());
				if(rs.getString(IS_EXPERT_OPINION).equalsIgnoreCase(YES))
					combinedEventsInfo.setIsExpertOpinion(true);
				else combinedEventsInfo.setIsExpertOpinion(false);

				combinedInfoList.add(combinedEventsInfo);
			}
			rs.close();
		} catch(SQLException e) {
			e.printStackTrace();
			throw new QueryException(e.getMessage());
		}
		return combinedInfoList;
	}

}
