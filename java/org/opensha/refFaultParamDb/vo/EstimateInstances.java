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
import org.opensha.commons.data.estimate.Estimate;

/**
 * <p>Title: EstimateInstances.java </p>
 * <p>Description: Insert/retrieve/update/delete estimates in the database</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class EstimateInstances {
	private int estimateInstanceId;
	private Estimate estimate;
	private String units;

	public EstimateInstances() {
	}


	public String toString() {
		return estimate.toString();
	}

	public EstimateInstances(Estimate estimate, String units) {
		setEstimate(estimate);
		setUnits(units);
	}

	public Estimate getEstimate() {
		return estimate;
	}
	public int getEstimateInstanceId() {
		return estimateInstanceId;
	}
	public void setEstimate(Estimate estimate) {
		this.estimate = estimate;
	}
	public void setEstimateInstanceId(int estimateInstanceId) {
		this.estimateInstanceId = estimateInstanceId;
	}
	public String getUnits() {
		return units;
	}
	public void setUnits(String units) {
		this.units = units;
	}


}
