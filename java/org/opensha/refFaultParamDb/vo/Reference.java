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
 * <p>Title: Reference.java </p>
 * <p>Description: This class has information about the references </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class Reference {

	private int referenceId=-1; // reference ID
	private String refAuth; // short citation
	private String refYear;
	private String fullBiblioReference; // full bibliographic reference
	private int qfaultReferenceId = -1;

	public Reference() {
	}

	public String toString() {
		return "Reference Author="+refAuth+"\n"+
		"Reference Year="+refYear+"\n"+
		"Full Bibliographic Ref="+this.fullBiblioReference;
	}

	public Reference(int referenceId, String author, String year, String fullBiblioReference) {
		this(author, year, fullBiblioReference);
		setReferenceId(referenceId);
	}

	public Reference(String author, String year, String fullBiblioReference) {
		this.setRefAuth(author);
		this.setRefYear(year);
		this.setFullBiblioReference(fullBiblioReference);
	}

	public int getReferenceId() {
		return referenceId;
	}
	public void setReferenceId(int referenceId) {
		this.referenceId = referenceId;
	}
	public int getQfaultReferenceId() {
		return this.qfaultReferenceId;
	}
	public void setQfaultReferenceId(int qfaultRefId) {
		this.qfaultReferenceId = qfaultRefId;
	}
	public String getFullBiblioReference() {
		return fullBiblioReference;
	}
	public void setFullBiblioReference(String fullBiblioReference) {
		this.fullBiblioReference = fullBiblioReference;
	}
	public String getRefAuth() {
		return refAuth;
	}
	public void setRefAuth(String refAuth) {
		this.refAuth = refAuth;
	}
	public void setRefYear(String refYear) {
		this.refYear = refYear;
	}
	public String getRefYear() {
		return refYear;
	}
	public String getSummary() {
		return this.refAuth+" ("+refYear+")";
	}

}
