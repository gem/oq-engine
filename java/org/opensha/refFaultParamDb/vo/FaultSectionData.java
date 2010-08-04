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

import org.opensha.commons.data.estimate.DiscreteValueEstimate;
import org.opensha.commons.data.estimate.Estimate;
import org.opensha.commons.data.estimate.MinMaxPrefEstimate;
import org.opensha.commons.data.estimate.NormalEstimate;
import org.opensha.sha.faultSurface.FaultTrace;

/**
 * <p>Title: FaultSectionVer2.java </p>
 * <p>Description: Fault Section information saved in the database</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class FaultSectionData implements Cloneable {

	private int sectionId=-1;
	private String sectionName;
	private String shortName;
	private EstimateInstances aveLongTermSlipRateEst;
	private EstimateInstances aveDipEst;
	private EstimateInstances aveRakeEst;
	private EstimateInstances aveUpperDepthEst;
	private EstimateInstances aveLowerDepthEst;
	private EstimateInstances aseismicSlipFactorEst;
	private String entryDate;
	private String source;
	private String comments="";
	private FaultTrace faultTrace;
	private float dipDirection;
	private String qFaultId;

	public FaultSectionData() {
	}

	public String getShortName() {
		return this.shortName;
	}

	public void setShortName(String shortName) {
		this.shortName = shortName;
	}

	public String getQFaultId() {
		return this.qFaultId;
	}

	public void setQFaultId(String qfaultId) {
		this.qFaultId = qfaultId;
	}

	public EstimateInstances getAseismicSlipFactorEst() {
		return aseismicSlipFactorEst;
	}
	public EstimateInstances getAveDipEst() {
		return aveDipEst;
	}
	public EstimateInstances getAveLongTermSlipRateEst() {
		return aveLongTermSlipRateEst;
	}
	public EstimateInstances getAveLowerDepthEst() {
		return aveLowerDepthEst;
	}
	public EstimateInstances getAveRakeEst() {
		return aveRakeEst;
	}
	public EstimateInstances getAveUpperDepthEst() {
		return aveUpperDepthEst;
	}
	public String getComments() {
		return comments;
	}
	public float getDipDirection() {
		return dipDirection;
	}
	public String getEntryDate() {
		return entryDate;
	}

	public FaultTrace getFaultTrace() {
		return faultTrace;
	}
	public int getSectionId() {
		return sectionId;
	}
	public String getSectionName() {
		return sectionName;
	}

	public void setSectionName(String sectionName) {
		this.sectionName = sectionName;
	}
	public void setSectionId(int sectionId) {
		this.sectionId = sectionId;
	}
	public void setFaultTrace(FaultTrace faultTrace) {
		this.faultTrace = faultTrace;
	}

	public void setEntryDate(String entryDate) {
		this.entryDate = entryDate;
	}
	public void setDipDirection(float dipDirection) {
		this.dipDirection = dipDirection;
	}
	public void setComments(String comments) {
		this.comments = comments;
	}
	public void setAveUpperDepthEst(EstimateInstances aveUpperDepthEst) {
		this.aveUpperDepthEst = aveUpperDepthEst;
	}
	public void setAveRakeEst(EstimateInstances aveRakeEst) {
		this.aveRakeEst = aveRakeEst;
	}
	public void setAveLowerDepthEst(EstimateInstances aveLowerDepthEst) {
		this.aveLowerDepthEst = aveLowerDepthEst;
	}
	public void setAveLongTermSlipRateEst(EstimateInstances aveLongTermSlipRateEst) {
		this.aveLongTermSlipRateEst = aveLongTermSlipRateEst;
	}
	public void setAveDipEst(EstimateInstances aveDipEst) {
		this.aveDipEst = aveDipEst;
	}
	public void setAseismicSlipFactorEst(EstimateInstances aseismicSlipFactorEst) {
		this.aseismicSlipFactorEst = aseismicSlipFactorEst;
	}
	public String getSource() {
		return source;
	}

	public void setSource(String source) {
		this.source = source;
	}

	/**
	 * Convert the estimates nt o a single preffered value and return the FaultSectionPrefData object
	 * @return
	 */
	 public FaultSectionPrefData getFaultSectionPrefData() {
		 FaultSectionPrefData faultSectionPrefData = new FaultSectionPrefData();
		 faultSectionPrefData.setAseismicSlipFactor(getPrefForEstimate(aseismicSlipFactorEst));
		 faultSectionPrefData.setAveDip(getPrefForEstimate(aveDipEst));
		 faultSectionPrefData.setSlipRateStdDev(getSlipRateStdDev(aveLongTermSlipRateEst));
		 faultSectionPrefData.setAveLongTermSlipRate(getPrefForEstimate(aveLongTermSlipRateEst));
		 faultSectionPrefData.setAveLowerDepth(getPrefForEstimate(aveLowerDepthEst));
		 faultSectionPrefData.setAveRake(getPrefForEstimate(aveRakeEst));
		 faultSectionPrefData.setAveUpperDepth(getPrefForEstimate(aveUpperDepthEst));
		 faultSectionPrefData.setDipDirection(dipDirection);
		 faultSectionPrefData.setSectionId(sectionId);
		 faultSectionPrefData.setSectionName(sectionName);
		 faultSectionPrefData.setShortName(this.shortName);
		 faultSectionPrefData.setFaultTrace(this.faultTrace);
		 return faultSectionPrefData;
	 }

	 private double getSlipRateStdDev(EstimateInstances estimateInstance) {
		 if(estimateInstance==null) return Double.NaN;
		 Estimate estimate = estimateInstance.getEstimate();
		 if(estimate instanceof NormalEstimate) {
			 return ((NormalEstimate)estimate).getStdDev();
		 }  else return Double.NaN;
	 }

	 /**
	  * Extract a single preferred value from the estimate  
	  * @param estimateInstance
	  * @return
	  */
	 public static double getPrefForEstimate(EstimateInstances estimateInstance) {
		 if(estimateInstance==null) return Double.NaN;
		 Estimate estimate = estimateInstance.getEstimate();
		 if(estimate instanceof MinMaxPrefEstimate) {
			 return ((MinMaxPrefEstimate)estimate).getPreferred();
		 } else if(estimate instanceof NormalEstimate) {
			 return ((NormalEstimate)estimate).getMean();
		 } else if(estimate instanceof DiscreteValueEstimate) {
			 DiscreteValueEstimate discValEst = (DiscreteValueEstimate)estimate;
			 //if(discValEst.isMultiModal()) System.out.println("*************Multi Modal***************");
			 return discValEst.getMean();
		 } else throw new RuntimeException("FaultSectionData: Unable to handle this estimate type");
	 }

	@Override
	public FaultSectionData clone() {
		FaultSectionData data = new FaultSectionData();
		
		data.setSectionId(getSectionId());
		data.setSectionName(getSectionName());
		data.setShortName(getShortName());
		data.setAveLongTermSlipRateEst(getAveLongTermSlipRateEst());
		data.setAveDipEst(getAveDipEst());
		data.setAveRakeEst(getAveRakeEst());
		data.setAveUpperDepthEst(getAveUpperDepthEst());
		data.setAveLowerDepthEst(getAveLowerDepthEst());
		data.setAseismicSlipFactorEst(getAseismicSlipFactorEst());
		data.setEntryDate(getEntryDate());
		data.setSource(getSource());
		data.setComments(getComments());
		data.setFaultTrace(getFaultTrace());
		data.setDipDirection(getDipDirection());
		data.setQFaultId(getQFaultId());
		
		return data;
	}

}
