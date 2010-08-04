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

package org.opensha.sha.cybershake.param;

import java.util.ArrayList;

import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.StringParameter;
import org.opensha.sha.cybershake.db.CybershakeERF;

public class CyberShakeERFSelectorParam extends StringParameter {
	
	public static final String NAME = "CyberShake Earthquake Rupture Forecast";
	
	private ArrayList<String> erfNames;
	private ArrayList<CybershakeERF> erfs;
	
	public CyberShakeERFSelectorParam(ArrayList<CybershakeERF> erfs) {
		super(NAME);
		this.erfs = erfs;
		erfNames = new ArrayList<String>();
		
		for (CybershakeERF erf : erfs) {
	    	erfNames.add(erf.id + ": " + erf.description);
	    }
		
		this.setConstraint(new StringConstraint(erfNames));
		
		int maxID = 0;
		int maxIndex = -1;
		for (int i=0; i<erfs.size(); i++) {
			CybershakeERF erf = erfs.get(i);
			if (erf.id > maxID) {
				maxID = erf.id;
				maxIndex = i;
			}
		}
		if (maxIndex >= 0) {
			this.setValue(erfNames.get(maxIndex));
		}
	}
	
	public CybershakeERF getSelectedERF() {
		String name = (String)this.getValue();
		for (int i=0; i<erfNames.size(); i++) {
			if (name.equals(erfNames.get(i)))
				return erfs.get(i);
		}
		return null;
	}
}
