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

package org.opensha.refFaultParamDb.vo;

import java.util.ArrayList;

/**
 * <p>Title: EventSequence.java </p>
 * <p>Description: This class saves the information about a event sequence</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class EventSequence {

	private String sequenceName;
	private double sequenceProb;
	private String comments;
	private ArrayList<PaleoEvent> eventsParam;
	private double[] missedEventsProbs;

	public EventSequence() {
	}

	public String toString() {
		String paleoEventStr="", missedEventsProbStr="";
		// ids of events in this sequence
		for(int i=0; eventsParam!=null && i<eventsParam.size(); ++i) {
			PaleoEvent paleoEvent = (PaleoEvent)eventsParam.get(i);
			paleoEventStr+=paleoEvent.getEventId()+",";
		}
		// probabilites of missed events
		for(int i=0; i<missedEventsProbs.length; ++i) {
			missedEventsProbStr+=missedEventsProbs[i]+",";
		}
		return "Sequence Name="+sequenceName+"\n"+
		"Sequence Prob="+sequenceProb+"\n"+
		"Events In sequence="+paleoEventStr+"\n"+
		"Prob of missed events="+missedEventsProbStr+"\n"+
		"Comments="+comments;
	}

	public String getComments() {
		return comments;
	}
	public ArrayList<PaleoEvent> getEventsParam() {
		return eventsParam;
	}
	public double[] getMissedEventsProbs() {
		return missedEventsProbs;
	}
	public String getSequenceName() {
		return sequenceName;
	}
	public double getSequenceProb() {
		return sequenceProb;
	}
	public void setComments(String comments) {
		this.comments = comments;
	}
	public void setEventsParam(ArrayList<PaleoEvent> eventsParam) {
		this.eventsParam = eventsParam;
	}
	public void setMissedEventsProbList(double[] missedEventsProbs) {
		this.missedEventsProbs = missedEventsProbs;
	}
	public void setSequenceName(String sequenceName) {
		this.sequenceName = sequenceName;
	}
	public void setSequenceProb(double sequenceProb) {
		this.sequenceProb = sequenceProb;
	}
}
