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

package org.opensha.commons.gridComputing;

import org.dom4j.Attribute;
import org.dom4j.Element;
import org.opensha.commons.metadata.XMLSaveable;

public class GridJob implements XMLSaveable {
	
	public static final String XML_METADATA_NAME = "GridJob";
	
	private GridResources resources;
	protected GridCalculationParameters calcParams;
	
	private String jobID;
	private String jobName;
	private String email;
	private String configFileName;
	
	public GridJob(GridResources resources, GridCalculationParameters calcParams, String jobID, String jobName,
			String email, String configFileName) {
		
		this.resources = resources;
		this.calcParams = calcParams;
		this.jobID = jobID;
		this.jobName = jobName;
		this.email = email;
		this.configFileName = configFileName;
		
	}

	public GridResources getResources() {
		return resources;
	}

	public GridCalculationParameters getCalcParams() {
		return calcParams;
	}

	public void setJobID(String jobID) {
		this.jobID = jobID;
	}
	
	public String getJobID() {
		return jobID;
	}

	public String getJobName() {
		return jobName;
	}

	public String getEmail() {
		return email;
	}
	
	public void setEmail(String email) {
		this.email = email;
	}

	public void setConfigFileName(String configFileName) {
		this.configFileName = configFileName;
	}
	
	public String getConfigFileName() {
		return configFileName;
	}

	public Element toXMLMetadata(Element root) {
		Element xml = root.addElement(XML_METADATA_NAME);
		
		xml = this.resources.toXMLMetadata(xml);
		xml = this.calcParams.toXMLMetadata(xml);
		
		xml.addAttribute("jobID", jobID);
		xml.addAttribute("jobName", jobName);
		xml.addAttribute("email", email);
		xml.addAttribute("configFileName", configFileName);
		
		return root;
	}
	
	public static GridJob fromXMLMetadata(Element jobElem) {
		GridResources resources = GridResources.fromXMLMetadata(jobElem.element(GridResources.XML_METADATA_NAME));
		GridCalculationParameters resourceProvider = new GridCalculationParameters(jobElem, XML_METADATA_NAME);
		
		String jobID = jobElem.attributeValue("jobID");
		Attribute jobNameAtt = jobElem.attribute("jobName");
		String jobName;
		if (jobNameAtt == null)
			jobName = jobID;
		else
			jobName = jobNameAtt.getValue();
		String email = jobElem.attributeValue("email");
		String configFileName = jobElem.attributeValue("configFileName");
		
		return new GridJob(resources, resourceProvider, jobID, jobName, email, configFileName);
	}
	
	@Override
	public String toString() {
		String str = "";
		
		str += "************************" + "\n";
		str += "******* Grid Job *******" + "\n";
		str += "************************" + "\n";
		str += this.resources.toString() + "\n";
		str += this.calcParams.toString() + "\n";
		str += "jobID: " + jobID + "\n";
		str += "jobName: " + jobName + "\n";
		str += "email: " + email + "\n";
		str += "configFileName: " + configFileName;
		
		return str;
	}
	
	public static String indentString(String str) {
		str = "\t" + str;
		str = str.replace("\n", "\n\t");
		
		return str;
	}
}
