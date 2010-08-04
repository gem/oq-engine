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
import org.opensha.refFaultParamDb.vo.EventSequence;
import org.opensha.refFaultParamDb.vo.PaleoEvent;

/**
 * <p>Title: EventSequenceDB_DAO.java </p>
 * <p>Description: It interacts with the database to put/get the information about
 * event sequences</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class EventSequenceDB_DAO {
	// main table name and attribute names
	private final static String TABLE_NAME = "Event_Sequence";
	private final static String TABLE_SEQUENCE_NAME = "Event_Sequence_Sequence";
	private final static String SEQUENCE_ID = "Sequence_Id";
	private final static String SEQUENCE_NAME = "Sequence_Name";
	private final static String INFO_ID = "Info_Id";
	private final static String SEQUENCE_PROB = "Sequence_Probability";
	private final static String ENTRY_DATE = "Entry_Date";
	private final static String GENERAL_COMMENT = "General_Comments";
	// reference table name and attribute names
//	private final static String EVENT_SEQUENCE_ID = "Event_Sequence_Id";
//	private final static String EVENT_SEQUENCE_ENTRY_DATE  = "Event_Sequence_Entry_Date";
	// table name which saves the all the events within a sequence
	private final static String SEQUENCE_EVENT_LIST_TABLE_NAME = "Event_Sequence_Event_List";
	private final static String EVENT_ID = "Event_Id";
	private final static String EVENT_ENTRY_DATE = "Event_Entry_Date";
	private final static String SEQUENCE_ENTRY_DATE = "Sequence_Entry_Date";
	private final static String MISSED_PROB = "Missed_Prob";
	private final static String EVENT_INDEX_IN_SEQUENCE="Event_Index_In_Sequence";

	private DB_AccessAPI dbAccess; // database connection
//	private TimeInstanceDB_DAO timeInstanceDAO;
//	private ReferenceDB_DAO referenceDAO;

	public EventSequenceDB_DAO(DB_AccessAPI dbAccess) {
		setDB_Connection(dbAccess);
	}

	public void setDB_Connection(DB_AccessAPI dbAccess) {
		this.dbAccess = dbAccess;
//		timeInstanceDAO = new TimeInstanceDB_DAO(dbAccess);
	}

	/**
	 * Add a list of possible sequences in a particular timespan
	 * @param sequenceList
	 * @param startTime
	 * @param endTime
	 */
	public void addEventSequence(int infoId, String entryDate,
			ArrayList<EventSequence> sequenceList) {
		try {
			// loop over each sequence in the list and put it in database
			for(int i=0; i<sequenceList.size(); ++i) {
				EventSequence eventSequence = (EventSequence)sequenceList.get(i);
				int sequenceId = dbAccess.getNextSequenceNumber(TABLE_SEQUENCE_NAME);
				// put sequence in database
				String sql = "insert into "+TABLE_NAME+ "("+SEQUENCE_ID+","+SEQUENCE_NAME+
				","+INFO_ID+","+ENTRY_DATE+","+SEQUENCE_PROB+","+GENERAL_COMMENT+
				") values ("+sequenceId+",'"+eventSequence.getSequenceName()+"',"+
				infoId+",'"+entryDate+"',"+eventSequence.getSequenceProb()+
				",'"+eventSequence.getComments()+"')";
				dbAccess.insertUpdateOrDeleteData(sql);
				//put references for this sequence in the database
				/* ArrayList shortCitationList = startTime.getReferencesList();
        for(int j=0; j<shortCitationList.size(); ++j) {
          int referenceId = referenceDAO.getReference((String)shortCitationList.get(j)).getReferenceId();
          sql = "insert into "+this.REFERENCE_TABLE_NAME+"("+EVENT_SEQUENCE_ID+
              ","+EVENT_SEQUENCE_ENTRY_DATE+","+REFERENCE_ID+") "+
              "values ("+sequenceId+",'"+systemDate+"',"+referenceId+")";
          dbAccess.insertUpdateOrDeleteData(sql);
        }*/
				// put event list and missed event probs in the database
				ArrayList<PaleoEvent> eventsInSequence = eventSequence.getEventsParam();
				double missedProbs[]  = eventSequence.getMissedEventsProbs();
				int numEventsInSequence = eventsInSequence.size();
				for(int j=0; j<numEventsInSequence; ++j ) {
					PaleoEvent paleoEvent = (PaleoEvent)eventsInSequence.get(j);
					sql = "insert into "+SEQUENCE_EVENT_LIST_TABLE_NAME+"("+
					EVENT_ID+","+EVENT_ENTRY_DATE+","+SEQUENCE_ID+","+
					SEQUENCE_ENTRY_DATE+","+MISSED_PROB+","+
					EVENT_INDEX_IN_SEQUENCE+") values ("+paleoEvent.getEventId()+",'"+
					paleoEvent.getEntryDate()+"',"+sequenceId+",'"+entryDate+"',"+
					missedProbs[j]+","+j+")";
					dbAccess.insertUpdateOrDeleteData(sql);
					if(j==(numEventsInSequence-1)) {
						++j;
						// number of probs are 1 greater than number of number of events in the sequence
						sql = "insert into "+SEQUENCE_EVENT_LIST_TABLE_NAME+"("+
						EVENT_ID+","+EVENT_ENTRY_DATE+","+SEQUENCE_ID+","+
						SEQUENCE_ENTRY_DATE+","+MISSED_PROB+","+
						EVENT_INDEX_IN_SEQUENCE+") values ("+paleoEvent.getEventId()+",'"+
						paleoEvent.getEntryDate()+"',"+sequenceId+",'"+entryDate+"',"+
						missedProbs[j]+","+j+")";
						dbAccess.insertUpdateOrDeleteData(sql);
					}
				}
			}
		}catch(SQLException e) {
			throw new InsertException(e.getMessage());
		}
	}

	/**
	 * Return a list of all the sequences for a particular site
	 *
	 * @param siteId
	 * @return
	 */
	public ArrayList<EventSequence> getSequences(int infoId, String entryDate) {
		String condition = " where "+INFO_ID+"="+infoId+" and "+ENTRY_DATE+
		"='"+entryDate+"'";
		return query(condition);
	}

	/**
	 * Query the event sequence table to get paleo sequences based on the condition
	 * @param condition
	 * @return
	 */
	private ArrayList<EventSequence> query(String condition) {
		ArrayList<EventSequence> sequenceList = new ArrayList<EventSequence>();
		String sql = "select "+SEQUENCE_ID+","+SEQUENCE_NAME+
		","+INFO_ID+",to_char("+ENTRY_DATE+") as "+ENTRY_DATE+",("+
		SEQUENCE_PROB+"+0) " +SEQUENCE_PROB+","+ GENERAL_COMMENT+" from "+
		TABLE_NAME+" "+condition;
		try {
			ResultSet rs  = dbAccess.queryData(sql);
			PaleoEventDB_DAO paleoEventDAO = new PaleoEventDB_DAO(dbAccess);
			while(rs.next())  {
				// create event sequence
				EventSequence eventSequence = new EventSequence();
				eventSequence.setSequenceName(rs.getString(SEQUENCE_NAME));
				eventSequence.setSequenceProb(rs.getFloat(SEQUENCE_PROB));
				eventSequence.setComments(rs.getString(GENERAL_COMMENT));
				// get a list of all the events and missed event probs forming this sequence
				sql = "select "+EVENT_ID+",("+MISSED_PROB+"+0) "+MISSED_PROB+" from "+ SEQUENCE_EVENT_LIST_TABLE_NAME+
				" where "+SEQUENCE_ID+"="+rs.getInt(SEQUENCE_ID)+" and "+
				SEQUENCE_ENTRY_DATE+"='"+rs.getString(ENTRY_DATE)+"' order by "+
				EVENT_INDEX_IN_SEQUENCE;
				ResultSet eventsResults = dbAccess.queryData(sql);
				ArrayList<PaleoEvent> events  = new ArrayList<PaleoEvent>();
				ArrayList<Double> probsList = new ArrayList<Double>();
				while(eventsResults.next()){
					events.add(paleoEventDAO.getEvent(eventsResults.getInt(EVENT_ID)));
					probsList.add(new Double(eventsResults.getFloat(MISSED_PROB)));
				}
				events.remove(events.size()-1);
				eventSequence.setEventsParam(events);
				double probs []= new double[probsList.size()];
				for(int i=0; i<probsList.size(); ++i)
					probs[i] = ((Double)probsList.get(i)).doubleValue();
				eventSequence.setMissedEventsProbList(probs);
				sequenceList.add(eventSequence);
			}
			rs.close();
		} catch(SQLException e) { throw new QueryException(e.getMessage()); }

		return sequenceList;
	}


}
