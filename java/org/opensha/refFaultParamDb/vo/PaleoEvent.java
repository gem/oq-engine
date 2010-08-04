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

import org.opensha.refFaultParamDb.data.TimeAPI;

/**
 * <p>Title: PaleoEvent.java </p>
 * <p>Description: This class holds the information existing in the database
 * for Paleo Events </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class PaleoEvent {
	private String eventName;
	private int siteId;
	private String siteEntryDate;
	private String contributorName;
	private TimeAPI eventTime;
	private boolean displacementShared;
	private int displacementEstId;
	private EstimateInstances displacementEst;
	private EstimateInstances senseOfMotionRake=null;
	private String senseOfMotionQual;
	private String measuredComponentQual;
	private String comments;
	private ArrayList<Reference> referenceList;
	private String entryDate;
	private int eventId;


	public PaleoEvent() {
	}

	/**
	 * toString() method implementation so that it can be sent in email when a
	 * event is added to the database
	 *
	 * @return
	 */
	public String toString() {
		String referenceString="";
		for(int i=0; referenceList!=null && i<referenceList.size();++i)
			referenceString+=((Reference)referenceList.get(i)).getSummary()+",";
		String eventTimeStr=null, displacementEstStr=null, senseOfMotionRakeStr=null;
		if(eventTime!=null) eventTimeStr=eventTime.toString();
		if(displacementEst!=null) displacementEstStr = displacementEst.toString();
		if(senseOfMotionRake!=null) senseOfMotionRakeStr = senseOfMotionRake.toString();
		return "Event Name="+eventName+"\n"+
		"Site Id="+siteId+"\n"+
		"Site Entry date="+siteEntryDate+"\n"+
		"Event Time=("+eventTimeStr+")\n"+
		"Displacement Shared="+displacementShared+"\n"+
		"Displacement Estimate Id="+displacementEstId+"\n"+
		"Displacement Estimate=("+displacementEstStr+")\n"+
		"Sense Of Motion Rake=("+senseOfMotionRakeStr+")\n"+
		"Sense of Motion Qualitative="+senseOfMotionQual+"\n"+
		"Measured Component Qualitative="+measuredComponentQual+"\n"+
		"Comments="+comments+"\n"+
		"Paleo Event References="+referenceString;

	}

	public void setDisplacementShared(boolean displacementShared) {
		this.displacementShared = displacementShared;
	}

	public boolean isDisplacementShared() {
		return this.displacementShared;
	}

	public int getEventId() {
		return this.eventId;
	}

	public void setEventId(int eventId) {
		this.eventId = eventId;
	}
	public String getSiteEntryDate() {
		return this.siteEntryDate;
	}
	public void setSiteEntryDate(String siteEntryDate) {
		this.siteEntryDate = siteEntryDate;
	}
	public String getComments() {
		return comments;
	}
	public String getContributorName() {
		return contributorName;
	}
	public int getDisplacementEstId() {
		return displacementEstId;
	}
	public String getEntryDate() {
		return entryDate;
	}
	public String getEventName() {
		return eventName;
	}
	public TimeAPI getEventTime() {
		return eventTime;
	}
	public ArrayList<Reference> getReferenceList() {
		return this.referenceList;
	}
	public int getSiteId() {
		return siteId;
	}
	public void setSiteId(int siteId) {
		this.siteId = siteId;
	}
	public void setReferenceList(ArrayList<Reference> referenceList) {
		this.referenceList = referenceList;
	}
	public void setEventTime(TimeAPI eventTime) {
		this.eventTime = eventTime;
	}
	public void setEventName(String eventName) {
		this.eventName = eventName;
	}
	public void setEntryDate(String entryDate) {
		this.entryDate = entryDate;
	}
	public void setDisplacementEstId(int displacementEst) {
		this.displacementEstId = displacementEst;
	}
	public void setContributorName(String contributorName) {
		this.contributorName = contributorName;
	}
	public void setComments(String comments) {
		this.comments = comments;
	}
	public EstimateInstances getDisplacementEst() {
		return displacementEst;
	}
	public void setDisplacementEst(EstimateInstances displacementEst) {
		this.displacementEst = displacementEst;
	}
	public  String getSenseOfMotionQual() {
		return this.senseOfMotionQual;
	}
	public String getMeasuredComponentQual() {
		return this.measuredComponentQual;
	}
	public void setSenseOfMotionRake(EstimateInstances senseOfMotionRake) {
		this.senseOfMotionRake = senseOfMotionRake;
	}
	public void setMeasuredComponentQual(String measuredComponentQual) {
		this.measuredComponentQual = measuredComponentQual;
	}
	public void setSenseOfMotionQual(String senseOfMotionQual) {
		this.senseOfMotionQual = senseOfMotionQual;
	}
	public EstimateInstances getSenseOfMotionRake() {
		return senseOfMotionRake;
	}


}
