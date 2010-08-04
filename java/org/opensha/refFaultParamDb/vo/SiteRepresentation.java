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
 * <p>Title: SiteRepresentation.java </p>
 * <p>Description: Various representations possible for a site like "Entire Fault",
 * "Most Significant Strand", "One of Several Strands", "Unknown"</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class SiteRepresentation {
	private int siteRepresentationId;
	private String siteRepresentationName;

	/**
	 *
	 * @param siteRepresentationId
	 * @param siteRepresentationName
	 */
	public SiteRepresentation(int siteRepresentationId, String siteRepresentationName) {
		setSiteRepresentationId(siteRepresentationId);
		setSiteRepresentationName(siteRepresentationName);
	}

	// various get/set methods
	public int getSiteRepresentationId() {
		return siteRepresentationId;
	}
	public void setSiteRepresentationId(int siteRepresentationId) {
		this.siteRepresentationId = siteRepresentationId;
	}
	public void setSiteRepresentationName(String siteRepresentationName) {
		this.siteRepresentationName = siteRepresentationName;
	}
	public String getSiteRepresentationName() {
		return siteRepresentationName;
	}

}
