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

package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.data;

import java.util.ArrayList;

/**
 * It saves the low, high and mean recurrence interval for segments on the A-faults
 *  
 * @author vipingupta
 *
 */
public class SegmentRecurIntv {
	private String faultName;
	private ArrayList meanRecurIntv = new ArrayList();
	private ArrayList lowRecurIntv = new ArrayList();
	private ArrayList highRecurIntv= new ArrayList();
	
	public SegmentRecurIntv(String faultName) {
		this.faultName = faultName;
	}
	
	/**
	 * Add mean recurrence interval
	 * @param recurIntv
	 */
	public void addMeanRecurIntv(double recurIntv) {
		meanRecurIntv.add(new Double(recurIntv));
	}
	
	/**
	 * Add low recurrence interval
	 * @param recurIntv
	 */
	public void addLowRecurIntv(double recurIntv) {
		lowRecurIntv.add(new Double(recurIntv));
	}
	
	/**
	 * Add high recurrence interval
	 * @param recurIntv
	 */
	public void addHighRecurIntv(double recurIntv) {
		highRecurIntv.add(new Double(recurIntv));
	}
	
	/**
	 * Get mean recurrence interval
	 * @param recurIntv
	 */
	public double getMeanRecurIntv(int segIndex) {
		return ((Double)meanRecurIntv.get(segIndex)).doubleValue();
	}
	
	/**
	 * Get low recurrence interval
	 * @param recurIntv
	 */
	public double getLowRecurIntv(int segIndex) {
		return ((Double)lowRecurIntv.get(segIndex)).doubleValue();
	}
	
	/**
	 * Get high recurrence interval
	 * @param recurIntv
	 */
	public double getHighRecurIntv(int segIndex) {
		return  ((Double)highRecurIntv.get(segIndex)).doubleValue();
	}
	
	/**
	 * Get fault name
	 * @return
	 */
	public String getFaultName() {
		return this.faultName;
	}
	
}
