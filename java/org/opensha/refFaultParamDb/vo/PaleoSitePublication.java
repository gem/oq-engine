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

import java.util.ArrayList;

/**
 * <p>Title: PaleoSitePublications.java </p>
 * <p>Description: It saves the paleo site Id, reference associated with it and
 * site types and representative strand indices for it as provided by that reference(publication)</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class PaleoSitePublication {
	private int siteId=-1;
	private String siteEntryDate;
	private ArrayList<String> siteTypeNames;
	private Reference reference;
	private String contributorName;
	private String representativeStrandName;
	private String entryDate;

	public PaleoSitePublication() {
	}

	public String toString() {
		String siteTypeStr= "";
		for(int i=0; siteTypeNames!=null && i<siteTypeNames.size(); ++i)
			siteTypeStr+=siteTypeNames.get(i);
		return "Representative Strand Name="+representativeStrandName+"\n"+
		"Site Types="+siteTypeStr+"\n"+
		"Reference="+reference.getSummary();
	}

	public String getContributorName() {
		return contributorName;
	}
	public Reference getReference() {
		return reference;
	}
	public String getRepresentativeStrandName() {
		return representativeStrandName;
	}
	public String getSiteEntryDate() {
		return siteEntryDate;
	}
	public int getSiteId() {
		return siteId;
	}
	public ArrayList<String> getSiteTypeNames() {
		return siteTypeNames;
	}
	public void setSiteTypeNames(ArrayList<String> siteTypeNames) {
		this.siteTypeNames = siteTypeNames;
	}
	public void setSiteId(int siteId) {
		this.siteId = siteId;
	}
	public void setSiteEntryDate(String siteEntryDate) {
		this.siteEntryDate = siteEntryDate;
	}
	public void setRepresentativeStrandName(String representativeStrandName) {
		this.representativeStrandName = representativeStrandName;
	}
	public void setReference(Reference reference) {
		this.reference = reference;
	}
	public void setContributorName(String contributorName) {
		this.contributorName = contributorName;
	}
	public String getEntryDate() {
		return entryDate;
	}
	public void setEntryDate(String entryDate) {
		this.entryDate = entryDate;
	}
}
