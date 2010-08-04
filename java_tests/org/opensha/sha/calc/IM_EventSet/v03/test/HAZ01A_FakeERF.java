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

import java.util.ArrayList;

import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.earthquake.ProbEqkSource;

public class HAZ01A_FakeERF extends EqkRupForecast {
	
	ArrayList<ProbEqkSource> sources;
	
	public EqkRupForecastAPI erf;
	
	public HAZ01A_FakeERF() {}
	
	public HAZ01A_FakeERF(EqkRupForecastAPI erf) {
		this.erf = erf;
	}

	@Override
	public int getNumSources() {
		return sources.size();
	}

	@Override
	public ProbEqkSource getSource(int source) {
		return sources.get(source);
	}

	@Override
	public ArrayList getSourceList() {
		return erf.getSourceList();
	}

	public String getName() {
		return erf.getName() + " (HAZ01A Test Stub!)";
	}

	public void updateForecast() {
		sources = new ArrayList<ProbEqkSource>();
		erf.updateForecast();
		for (int i=0; i<erf.getNumSources(); i++) {
			sources.add(new HAZ01A_FakeSource(erf.getSource(i), i));
		}
	}

}
