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

public class CybershakeIM implements Comparable<CybershakeIM> {
	
	private int id;
	private String measure;
	private double val;
	private String units;
	
	public CybershakeIM(int id, String measure, double val, String units) {
		this.id = id;
		this.measure = measure;
		this.val = val;
		this.units = units;
	}

	public int getID() {
		return id;
	}

	public String getMeasure() {
		return measure;
	}

	public double getVal() {
		return val;
	}

	public String getUnits() {
		return units;
	}
	
	public String toString() {
		return this.measure + ": " + this.val + " (" + this.units + ")";
	}
	
	public boolean equals(Object im) {
		if (im instanceof CybershakeIM)
			return id == ((CybershakeIM)im).id;
		return false;
	}

	public int compareTo(CybershakeIM im) {
		if (val > im.val)
			return 1;
		if (val < im.val)
			return -1;
		return 0;
	}
}
