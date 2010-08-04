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

package org.opensha.sha.calc.hazardMap.old;

import org.dom4j.Element;
import org.opensha.commons.gridComputing.GridCalculationParameters;

public class HazardMapCalculationParameters extends GridCalculationParameters {
	
	public static final String XML_METADATA_NAME = "HazardMapCalculationParameters";
	
	private int sitesPerJob;
	private double maxSourceDistance;
	private boolean useCVM;
	private boolean serializeERF;

	public HazardMapCalculationParameters(int maxWallTime, int sitesPerJob, double maxSourceDistance, boolean useCVM, boolean serializeERF) {
		super(maxWallTime);
		
		this.sitesPerJob = sitesPerJob;
		this.maxSourceDistance = maxSourceDistance;
		this.useCVM = useCVM;
		this.serializeERF = serializeERF;
	}
	
	public HazardMapCalculationParameters(Element parentElement) {
		super(parentElement, XML_METADATA_NAME);
		
		sitesPerJob = Integer.parseInt(element.attribute("sitesPerJob").getValue());
		maxSourceDistance = Double.parseDouble(element.attribute("maxSourceDistance").getValue());
		useCVM = Boolean.parseBoolean(element.attribute("useCVM").getValue());
		serializeERF = Boolean.parseBoolean(element.attribute("serializeERF").getValue());
	}

	@Override
	public Element toXMLMetadata(Element root) {
		// TODO Auto-generated method stub
		Element xml =  root.addElement(XML_METADATA_NAME);
		
		xml.addAttribute("maxWallTime", maxWallTime + "");
		xml.addAttribute("sitesPerJob", sitesPerJob + "");
		xml.addAttribute("maxSourceDistance", (float)maxSourceDistance + "");
		xml.addAttribute("useCVM", useCVM + "");
		xml.addAttribute("serializeERF", serializeERF + "");
		
		return root;
	}
	
	@Override
	public String toString() {
		String str = super.toString();
		
		str += "\n";
		str += "\tsitesPerJob: " + sitesPerJob + "\n";
		str += "\tmaxSourceDistance: " + maxSourceDistance + "\n";
		str += "\tuseCVM: " + useCVM + "\n";
		str += "\tserializeERF: " + serializeERF;
		
		return str;
	}

	public int getSitesPerJob() {
		return sitesPerJob;
	}
	
	public double getMaxSourceDistance() {
		return maxSourceDistance;
	}

	public boolean isUseCVM() {
		return useCVM;
	}

//	public boolean isBasinFromCVM() {
//		return basinFromCVM;
//	}

	public boolean isSerializeERF() {
		return serializeERF;
	}
}
