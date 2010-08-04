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
 * <p>Title: EstimateType.java </p>
 * <p>Description: Various estimate types in types available</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class EstimateType {
	private int estimateTypeId;
	private String estimateName;
	private String effectiveDate;

	public EstimateType() {
	}

	public EstimateType(int estimateTypeId, String estimateName, String effectiveDate) {
		setEstimateTypeId(estimateTypeId);
		setEstimateName(estimateName);
		setEffectiveDate(effectiveDate);
	}

	public String getEffectiveDate() {
		return effectiveDate;
	}

	public void setEffectiveDate(String effectiveDate) {
		this.effectiveDate = effectiveDate;
	}
	public String getEstimateName() {
		return estimateName;
	}
	public void setEstimateName(String estimateName) {
		this.estimateName = estimateName;
	}
	public int getEstimateTypeId() {
		return estimateTypeId;
	}
	public void setEstimateTypeId(int estimateTypeId) {
		this.estimateTypeId = estimateTypeId;
	}
}
