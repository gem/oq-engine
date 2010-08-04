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

import org.opensha.refFaultParamDb.data.TimeAPI;

/**
 * <p>Title: Timespan.java </p>
 * <p>Description: This class holds the start and end time for paleo site data.
 * The start and end time can be estimates or exact times. </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class Timespan {
	private TimeAPI startTime;
	private TimeAPI endTime;
	private String datingMethodology;

	public Timespan() {
	}

	public String getDatingMethodology() {
		return datingMethodology;
	}
	public TimeAPI getEndTime() {
		return endTime;
	}
	public TimeAPI getStartTime() {
		return startTime;
	}
	public void setDatingMethodology(String datingMethodology) {
		this.datingMethodology = datingMethodology;
	}
	public void setEndTime(TimeAPI endTime) {
		this.endTime = endTime;
	}

	public void setStartTime(TimeAPI startTime) {
		this.startTime = startTime;
	}
}
