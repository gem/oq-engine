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

package org.opensha.sha.calc.IM_EventSet.v03.test;

import java.io.IOException;
import java.util.HashMap;

import org.opensha.sha.calc.IM_EventSet.v03.outputImpl.HAZ01ASegment;
import org.opensha.sha.imr.AttenuationRelationship;

public class HAZ01A_FakeAttenRel extends AttenuationRelationship {
	
	HAZ01ASegment segment;
	HashMap<String, Integer> sourceRupIDMap;
	
	public HAZ01A_FakeAttenRel() {}
	
	public HAZ01A_FakeAttenRel(String fileName) throws IOException {
		System.out.println("Loading HAZ01A file");
		segment = HAZ01ASegment.loadHAZ01A(fileName).get(0);
		sourceRupIDMap = new HashMap<String, Integer>();
		
		for (int i=0; i<segment.size(); i++) {
			String key = getSourceRupKey(segment.getSourceID(i), segment.getRupID(i));
			sourceRupIDMap.put(key, (Integer)i);
		}
		super.initOtherParams();
	}
	
	public static String getSourceRupKey(int sourceID, int rupID) {
		return sourceID + "_" + rupID;
	}
	
	private int getIndex(int sourceID, int rupID) {
		return sourceRupIDMap.get(getSourceRupKey(sourceID, rupID));
	}

	@Override
	protected void initEqkRuptureParams() {}

	@Override
	protected void initPropagationEffectParams() {}

	@Override
	protected void initSiteParams() {}

	@Override
	protected void initSupportedIntensityMeasureParams() {}

	@Override
	protected void setPropagationEffectParams() {}

	public double getMean() {
		HAZ01A_FakeRupture rup = (HAZ01A_FakeRupture)eqkRupture;
		return segment.getMeanVal(getIndex(rup.getSourceID(), rup.getRupID()));
	}

	public double getStdDev() {
		HAZ01A_FakeRupture rup = (HAZ01A_FakeRupture)eqkRupture;
		return segment.getStdDevVal(getIndex(rup.getSourceID(), rup.getRupID()));
	}

	public String getShortName() {
		return "HAZ01A_IMR";
	}

	public void setParamDefaults() {}

}
