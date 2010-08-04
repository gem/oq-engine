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

package org.opensha.refFaultParamDb.data;

import java.util.ArrayList;

import org.opensha.refFaultParamDb.vo.Reference;

/**
 * <p>Title: TimeAPI.java </p>
 * <p>Description: API for specifying the times. It is used for specifying the
 * event time as well as start time (or an end  time) for timeSpan in a site</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class TimeAPI {
	// constant values for AD/BC
	public final static String AD = "AD";
	public final static String BC = "BC";

	private ArrayList<Reference> referencesList;
	private String datingComments;
	public String getDatingComments() {
		return datingComments;
	}
	public ArrayList<Reference> getReferencesList() {
		return referencesList;
	}
	public void setDatingComments(String datingComments) {
		this.datingComments = datingComments;
	}
	public void setReferencesList(ArrayList<Reference> referencesList) {
		this.referencesList = referencesList;
	}

	public String toString() {
		String referenceString="";
		for(int i=0; referencesList!=null && i<referencesList.size();++i)
			referenceString+=((Reference)referencesList.get(i)).getSummary()+",";
		return "Dating Comments="+ datingComments+"\n"+
		"Time References="+referenceString;
	}
}
