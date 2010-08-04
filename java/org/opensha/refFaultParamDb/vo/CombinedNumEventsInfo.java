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

/**
 * <p>Title: CombinedNumEventsInfo.java </p>
 * <p>Description: this class saves the combined num events information </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class CombinedNumEventsInfo {
	private EstimateInstances numEventsEstimate;
	private String numEventsComments;

	public CombinedNumEventsInfo() {
	}

	public String toString() {
		String numEventsStr=null;
		if(numEventsEstimate!=null) numEventsStr = numEventsEstimate.toString();
		return "Num Events Estimate="+numEventsStr+"\n"+
		"Comments="+numEventsComments;
	}

	public String getNumEventsComments() {
		return numEventsComments;
	}
	public EstimateInstances getNumEventsEstimate() {
		return numEventsEstimate;
	}
	public void setNumEventsComments(String numEventsComments) {
		this.numEventsComments = numEventsComments;
	}
	public void setNumEventsEstimate(EstimateInstances numEventsEstimate) {
		this.numEventsEstimate = numEventsEstimate;
	}

}
