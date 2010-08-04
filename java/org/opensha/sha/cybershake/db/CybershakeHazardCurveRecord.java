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

package org.opensha.sha.cybershake.db;

import java.util.Date;

public class CybershakeHazardCurveRecord implements Comparable<CybershakeHazardCurveRecord> {
	
	private int curveID;
	private int runID;
	private int imTypeID;
	private Date date;
	
	public CybershakeHazardCurveRecord(int curveID, int runID, int imTypeID, Date date) {
		this.curveID = curveID;
		this.runID = runID;
		this.imTypeID = imTypeID;
		this.date = date;
	}

	public int getCurveID() {
		return curveID;
	}

	public int getRunID() {
		return runID;
	}

	public int getImTypeID() {
		return imTypeID;
	}

	public Date getDate() {
		return date;
	}

	public int compareTo(CybershakeHazardCurveRecord o) {
		if (o.getImTypeID() < this.getImTypeID())
			return -1;
		else if (o.getImTypeID() > this.getImTypeID())
			return 1;
		return 0;
	}

}
