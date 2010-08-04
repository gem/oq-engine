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
 * <p>Title: PaleoSite.java </p>
 * <p>Description: This class saves the information about a paleo site in the database</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class PaleoSite {
	private int siteId=-1;
	private FaultSectionSummary faultSection;
	private String siteName;
	private float siteLat1=Float.NaN;
	private float siteLon1=Float.NaN;
	private float siteElevation1=Float.NaN;
	private float siteLat2=Float.NaN;
	private float siteLon2=Float.NaN;
	private float siteElevation2=Float.NaN;
	private String generalComments;
	private String oldSiteId;
	private String entryDate;
	private EstimateInstances dipEstimate;
	private ArrayList<PaleoSitePublication> paleoSitePubList = new ArrayList<PaleoSitePublication>();

	public PaleoSite() {
	}


	public String toString() {
		String paleoSiteSubString="";
		for(int i=0; paleoSitePubList!=null && i<paleoSitePubList.size();++i)
			paleoSiteSubString+=((PaleoSitePublication)paleoSitePubList.get(i)).toString()+"\n";
		String dipEstStr=null;
		if(dipEstimate!=null) dipEstStr = dipEstimate.toString();
		return /*"Fault Section Name="+faultSection.getSectionName()+"\n"+*/
		"Site Name="+siteName+"\n"+
		"Site Lat1="+siteLat1+"\n"+
		"Site Lon1="+siteLon1+"\n"+
		"Site Elevation1="+siteElevation1+"\n"+
		"Site Lat2="+siteLat2+"\n"+
		"Site Lon2="+siteLon2+"\n"+
		"Site Elevation2="+siteElevation2+"\n"+
		"Old Site Id="+oldSiteId+"\n"+
		"General Comments="+generalComments+"\n"+
		"Dip Estimate=("+dipEstStr+")\n"+
		"References = ("+paleoSiteSubString+")";
	}

	public void setPaleoSitePubList(ArrayList<PaleoSitePublication> paleoSitePubList) {
		this.paleoSitePubList = paleoSitePubList;
	}

	public ArrayList<PaleoSitePublication> getPaleoSitePubList() {
		return this.paleoSitePubList;
	}

	public String getEntryDate() {
		return this.entryDate;
	}

	public void setEntryDate(String entryDate) {
		this.entryDate = entryDate;
	}

	public void setSiteId(int siteId) { this.siteId = siteId; }

	public int getSiteId() { return this.siteId; }

	public void setSiteName(String siteName) { this.siteName = siteName;}
	public String getSiteName() { return this.siteName; }


	public void setOldSiteId(String oldSiteId) { this.oldSiteId = oldSiteId; }
	public String getOldSiteId() { return this.oldSiteId; }
	public float getSiteLon2() {
		return siteLon2;
	}
	public float getSiteLon1() {
		return siteLon1;
	}
	public float getSiteLat2() {
		return siteLat2;
	}
	public float getSiteLat1() {
		return siteLat1;
	}
	public void setSiteLat1(float siteLat1) {
		this.siteLat1 = siteLat1;
	}
	public void setSiteLat2(float siteLat2) {
		this.siteLat2 = siteLat2;
	}
	public void setSiteLon1(float siteLon1) {
		this.siteLon1 = siteLon1;
	}
	public void setSiteLon2(float siteLon2) {
		this.siteLon2 = siteLon2;
	}
	public float getSiteElevation2() {
		return siteElevation2;
	}
	public float getSiteElevation1() {
		return siteElevation1;
	}
	public void setSiteElevation1(float siteElevation1) {
		this.siteElevation1 = siteElevation1;
	}
	public void setSiteElevation2(float siteElevation2) {
		this.siteElevation2 = siteElevation2;
	}
	
	public FaultSectionSummary getFaultSectionSummary() {
		return faultSection;
	}

	public String getFaultSectionName() {
		return this.faultSection.getSectionName();
	}

	public int getFaultSectionId() {
		return this.faultSection.getSectionId();
	}

	public void setFaultSectionNameId(String faultSectionName, int faultSectionId) {
		this.faultSection = new FaultSectionSummary(faultSectionId, faultSectionName);
	}
	public void setGeneralComments(String generalComments) {
		this.generalComments = generalComments;
	}
	public String getGeneralComments() {
		return generalComments;
	}
	public EstimateInstances getDipEstimate() {
		return dipEstimate;
	}
	public void setDipEstimate(EstimateInstances dipEstimate) {
		this.dipEstimate = dipEstimate;
	}
}
