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
 * <p>Title: CombinedDisplacementInfo.java </p>
 * <p>Description: This class saves the information if the user wants to enter
 * displacement info for a site.</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class CombinedDisplacementInfo {
	private EstimateInstances displacementEstimate;
	private EstimateInstances aSeismicSlipFactorEstimateForDisp;
	private EstimateInstances senseOfMotionRake;
	private String senseOfMotionQual;
	private String measuredComponentQual;
	private String displacementComments;

	public CombinedDisplacementInfo() {
	}

	public String toString() {
		String dispEstStr=null, aSeismicSlipEstStr=null, rakeStr=null;
		if(displacementEstimate!=null) dispEstStr = displacementEstimate.toString();
		if(aSeismicSlipFactorEstimateForDisp!=null) aSeismicSlipEstStr = aSeismicSlipFactorEstimateForDisp.toString();
		if(senseOfMotionRake!=null) rakeStr = senseOfMotionRake.toString();
		return "Displacement Estimate="+dispEstStr+"\n"+
		"Aseismic Slip Factor Estimate="+aSeismicSlipEstStr+"\n"+
		"Sense of Motion Rake="+rakeStr+"\n"+
		"Sense of Motion Qualitative="+senseOfMotionQual+"\n"+
		"Measured Component Qualitative="+measuredComponentQual+"\n"+
		"Displacement Comments="+displacementComments;
	}

	public  String getSenseOfMotionQual() {
		return this.senseOfMotionQual;
	}
	public String getMeasuredComponentQual() {
		return this.measuredComponentQual;
	}
	public EstimateInstances getASeismicSlipFactorEstimateForDisp() {
		return aSeismicSlipFactorEstimateForDisp;
	}
	public String getDisplacementComments() {
		return displacementComments;
	}
	public EstimateInstances getDisplacementEstimate() {
		return displacementEstimate;
	}
	public void setDisplacementEstimate(EstimateInstances displacementEstimate) {
		this.displacementEstimate = displacementEstimate;
	}
	public void setDisplacementComments(String displacementComments) {
		this.displacementComments = displacementComments;
	}
	public void setASeismicSlipFactorEstimateForDisp(EstimateInstances aSeismicSlipFactorEstimateForDisp) {
		this.aSeismicSlipFactorEstimateForDisp = aSeismicSlipFactorEstimateForDisp;
	}
	public EstimateInstances getSenseOfMotionRake() {
		return this.senseOfMotionRake;
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
}
