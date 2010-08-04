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
import org.opensha.refFaultParamDb.vo.EstimateInstances;
import org.opensha.refFaultParamDb.vo.PaleoEvent;
import org.opensha.refFaultParamDb.vo.Reference;

/**
 * <p>Title: PaleoEventDB_DAO.java </p>
 * <p>Description: This class interacts with the database to put/get information
 * about paleo events</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class PaleoEventDB_DAO {
	private final static String TABLE_NAME = "Paleo_Event";
	private final static String EVENT_ID = "Event_Id";
	private final static String EVENT_NAME = "Event_Name";
	private final static String SITE_ID = "Site_Id";
	private final static String SITE_ENTRY_DATE = "Site_Entry_Date";
	private final static String CONTRIBUTOR_ID = "Contributor_Id";
	private final static String EVENT_DATE_EST_ID = "Event_Date_Est_Id";
	private final static String DISPLACEMENT_EST_ID = "Displacement_Est_Id";
	private final static String ENTRY_DATE  = "Entry_Date";
	private final static String GENERAL_COMMENTS = "General_Comments";
	private final static String SEQUENCE_NAME = "Paleo_Event_Sequence";
	private final static String REFERENCES_TABLE_NAME ="Paleo_Event_References";
	private final static String REFERENCE_ID = "Reference_Id";
	private final static String PALEO_EVENT_ENTRY_DATE ="Paleo_Event_Entry_Date";
	private final static String PALEO_EVENT_ID="Paleo_Event_Id";
	private final static String SENSE_OF_MOTION_RAKE = "Sense_of_Motion_Rake";
	private final static String SENSE_OF_MOTION_QUAL = "Sense_of_Motion_Qual";
	private final static String MEASURED_SLIP_COMP_QUAL = "Measured_Slip_Comp_Qual";

	private DB_AccessAPI dbAccess;
	// references DAO
	private ReferenceDB_DAO referenceDAO ;
	private TimeInstanceDB_DAO timeInstanceDAO;
	private EstimateInstancesDB_DAO estimateInstancesDAO;

	public PaleoEventDB_DAO(DB_AccessAPI dbAccess) {
		setDB_Connection(dbAccess);
	}

	public void setDB_Connection(DB_AccessAPI dbAccess) {
		this.dbAccess = dbAccess;
		referenceDAO = new ReferenceDB_DAO(dbAccess);
		timeInstanceDAO = new TimeInstanceDB_DAO(dbAccess);
		estimateInstancesDAO = new EstimateInstancesDB_DAO(this.dbAccess);
	}

	/**
	 * Add a new paleo event
	 *
	 * @param paleoEvent
	 * @throws InsertException
	 */
	public void addPaleoevent(PaleoEvent paleoEvent) throws InsertException {
		int paleoEventId, eventTimeEstId, displacementEstId;
		String systemDate;
		try {
			paleoEventId = dbAccess.getNextSequenceNumber(SEQUENCE_NAME);
			systemDate = dbAccess.getSystemDate();
			eventTimeEstId = timeInstanceDAO.addTimeInstance(paleoEvent.getEventTime());
			if(paleoEvent.isDisplacementShared()) {
				// if displacement is shared, it is assumed that displacement id is  already set
				displacementEstId = paleoEvent.getDisplacementEstId();
			}
			else {
				// if displacement is not shared, add the time estimate and get the estimate Id
				displacementEstId = this.estimateInstancesDAO.addEstimateInstance(
						paleoEvent.getDisplacementEst());
			}
		}catch(SQLException e) {
			throw new InsertException(e.getMessage());
		}
		String somQual = paleoEvent.getSenseOfMotionQual();
		String measuredCompQual = paleoEvent.getMeasuredComponentQual();
		String colNames="", colVals="";
		EstimateInstances somRake = paleoEvent.getSenseOfMotionRake();
		if(somRake!=null) { // check whether user entered Sense of motion rake
			colNames += SENSE_OF_MOTION_RAKE+",";
			int rakeEstId = estimateInstancesDAO.addEstimateInstance(somRake);
			colVals += rakeEstId+",";
		}

		if(somQual!=null) {
			colNames+=SENSE_OF_MOTION_QUAL+",";
			colVals += "'"+somQual+"',";
		}
		if(measuredCompQual!=null) {
			colNames += MEASURED_SLIP_COMP_QUAL+",";
			colVals +="'"+measuredCompQual+"',";
		}


		String sql = "insert into "+TABLE_NAME+"("+ EVENT_ID+","+EVENT_NAME+","+
		SITE_ID+","+SITE_ENTRY_DATE+","+CONTRIBUTOR_ID+","+EVENT_DATE_EST_ID+","+
		DISPLACEMENT_EST_ID+","+ENTRY_DATE+","+colNames+GENERAL_COMMENTS+")"+
		" values ("+paleoEventId+",'"+paleoEvent.getEventName()+"',"+paleoEvent.getSiteId()+
		",'"+paleoEvent.getSiteEntryDate()+"',"+SessionInfo.getContributor().getId()+
		","+eventTimeEstId+","+displacementEstId+
		",'"+systemDate+"',"+colVals+"'"+paleoEvent.getComments()+"')";

		try {
			// insert into paleo event table
			dbAccess.insertUpdateOrDeleteData(sql);
			//add the references (for this paleo event) into the database
			ArrayList<Reference> referenceList = paleoEvent.getReferenceList();
			for(int i=0; i<referenceList.size(); ++i) {
				int referenceId = ((Reference)referenceList.get(i)).getReferenceId();
				sql = "insert into "+REFERENCES_TABLE_NAME+"("+PALEO_EVENT_ID+
				","+PALEO_EVENT_ENTRY_DATE+","+REFERENCE_ID+") "+
				"values ("+paleoEventId+",'"+
				systemDate+"',"+referenceId+")";
				dbAccess.insertUpdateOrDeleteData(sql);
			}
		}
		catch(SQLException e) {
			throw new InsertException(e.getMessage());
		}
	}

	/**
	 * Check whether the passed in event names share the same displacement.
	 * If they share same displacement, the diplacement id is returned else
	 * -1 is returned
	 *
	 * @param eventNames
	 * @return
	 */
	public int checkSameDisplacement(ArrayList<String> eventNames) {
		String values ="(";
		for(int i=0; i<eventNames.size();++i) {
			values = values + "'" + eventNames.get(i) + "'";
			if(i!=eventNames.size()-1) values= values+",";
		}
		values = values+")";
		String sql = "select "+DISPLACEMENT_EST_ID+" from "+TABLE_NAME+
		" where "+EVENT_NAME+" in "+values;
		int dispEstId = -1;
		try {
			ResultSet rs = dbAccess.queryData(sql);
			while (rs.next()) {
				if (dispEstId != -1 && dispEstId != rs.getInt(DISPLACEMENT_EST_ID))
					return -1;
				dispEstId = rs.getInt(DISPLACEMENT_EST_ID);
			}
		}catch(SQLException sqlException) {
			throw new QueryException(sqlException.getMessage());
		}

		return dispEstId;
	}

	/**
	 * Get a list of all events for this site
	 * It returns an ArrayList of PaleoEvent objects
	 * @param siteId
	 * @return
	 */
	public ArrayList<PaleoEvent> getAllEvents(int siteId)  throws QueryException {
		String condition = " where "+SITE_ID+"="+siteId;
		return query(condition);
	}

	public PaleoEvent getEvent(int eventId) throws QueryException {
		String condition = " where "+EVENT_ID+"="+eventId;
		ArrayList<PaleoEvent> paleoEventList = query(condition);
		PaleoEvent paleoEvent = null;
		if(paleoEventList.size()>0) paleoEvent = (PaleoEvent)paleoEventList.get(0);
		return paleoEvent;

	}


	/**
	 * Get a list of all event names sharing the given displacement estimate Id
	 * @param displacementEstId
	 * @return
	 * @throws QueryException
	 */
	public ArrayList<String> getEventNamesForDisplacement(int displacementEstId) throws QueryException {
		ArrayList<String> eventNames = new ArrayList<String>();
		String sql = "select "+EVENT_NAME+" from "+TABLE_NAME+" where "+
		DISPLACEMENT_EST_ID+"="+displacementEstId;
		try {
			ResultSet rs = dbAccess.queryData(sql);
			while(rs.next()) eventNames.add(rs.getString(EVENT_NAME));
		}catch(SQLException e) { throw new QueryException(e.getMessage()); }
		return eventNames;
	}


	/**
	 * Query the paleo event table to get paleo events based on the condition
	 * @param condition
	 * @return
	 */
	private ArrayList<PaleoEvent> query(String condition) {
		ArrayList<PaleoEvent> paleoEventList = new ArrayList<PaleoEvent>();
		String sql = "select "+EVENT_ID+","+EVENT_NAME+","+
		SITE_ID+",to_char("+SITE_ENTRY_DATE+") as "+SITE_ENTRY_DATE+","+
		CONTRIBUTOR_ID+","+EVENT_DATE_EST_ID+","+
		DISPLACEMENT_EST_ID+",to_char("+ENTRY_DATE+") as "+ENTRY_DATE+","+
		GENERAL_COMMENTS+","+SENSE_OF_MOTION_RAKE+","+
		SENSE_OF_MOTION_QUAL+","+MEASURED_SLIP_COMP_QUAL+" from "+
		TABLE_NAME+" "+condition;
		try {
			ResultSet rs  = dbAccess.queryData(sql);
			ContributorDB_DAO contributorDAO = new ContributorDB_DAO(dbAccess);
			while(rs.next())  {
				// create paleo event
				PaleoEvent paleoEvent= new PaleoEvent();
				paleoEvent.setEventId(rs.getInt(EVENT_ID));
				paleoEvent.setEventName(rs.getString(EVENT_NAME));
				paleoEvent.setSiteId(rs.getInt(SITE_ID));
				paleoEvent.setSiteEntryDate(rs.getString(SITE_ENTRY_DATE));
				paleoEvent.setContributorName(contributorDAO.getContributor(rs.getInt(CONTRIBUTOR_ID)).getName());
				paleoEvent.setEventTime(this.timeInstanceDAO.getTimeInstance(rs.getInt(EVENT_DATE_EST_ID)));
				paleoEvent.setDisplacementEstId(rs.getInt(DISPLACEMENT_EST_ID));
				paleoEvent.setDisplacementEst(this.estimateInstancesDAO.getEstimateInstance(rs.getInt(DISPLACEMENT_EST_ID)));
				paleoEvent.setEntryDate(rs.getString(ENTRY_DATE));
				paleoEvent.setComments(rs.getString(GENERAL_COMMENTS));

				// get all the references for this site
				ArrayList<Reference> referenceList = new ArrayList<Reference>();
				sql = "select "+REFERENCE_ID+" from "+REFERENCES_TABLE_NAME+
				" where "+PALEO_EVENT_ID+"="+paleoEvent.getEventId()+" and "+
				PALEO_EVENT_ENTRY_DATE+"='"+paleoEvent.getEntryDate()+"'";
				ResultSet referenceResultSet = dbAccess.queryData(sql);
				while(referenceResultSet.next()) {
					referenceList.add(this.referenceDAO.getReference(referenceResultSet.getInt(REFERENCE_ID)));
				}
				referenceResultSet.close();
				// set the references in the VO
				paleoEvent.setReferenceList(referenceList);

				// sense of motion
				int senseOfMotionRakeId = rs.getInt(SENSE_OF_MOTION_RAKE);
				EstimateInstances senseOfMotionRake =null;
				if(!rs.wasNull()) senseOfMotionRake=this.estimateInstancesDAO.getEstimateInstance(senseOfMotionRakeId);
				String senseOfMotionQual = rs.getString(SENSE_OF_MOTION_QUAL);
				if(rs.wasNull()) senseOfMotionQual=null;
				//measured component of slip
				String measuedCompQual = rs.getString(MEASURED_SLIP_COMP_QUAL);
				if(rs.wasNull()) measuedCompQual=null;
				paleoEvent.setSenseOfMotionRake(senseOfMotionRake);
				paleoEvent.setSenseOfMotionQual(senseOfMotionQual);
				paleoEvent.setMeasuredComponentQual(measuedCompQual);

				paleoEventList.add(paleoEvent);
			}
			rs.close();
		} catch(SQLException e) { throw new QueryException(e.getMessage()); }

		return paleoEventList;

	}
}
