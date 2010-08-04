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

import org.opensha.commons.data.Site;
import org.opensha.commons.geo.LocationList;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;

public class HAZ01A_FakeSource extends ProbEqkSource {
	
	private ArrayList<HAZ01A_FakeRupture> rups;
	private ProbEqkSource source;
	
	public HAZ01A_FakeSource() {}
	
	public HAZ01A_FakeSource(ProbEqkSource source, int sourceID) {
		rups = new ArrayList<HAZ01A_FakeRupture>();
		this.source = source;
		
		for (int i=0; i<source.getNumRuptures(); i++) {
			rups.add(new HAZ01A_FakeRupture(source.getRupture(i), sourceID, i));
		}
	}

	@Override
	public double getMinDistance(Site site) {
		return source.getMinDistance(site);
	}

	@Override
	public int getNumRuptures() {
		return rups.size();
	}

	@Override
	public ProbEqkRupture getRupture(int rupture) {
		return rups.get(rupture);
	}

	public LocationList getAllSourceLocs() {
		return source.getAllSourceLocs();
	}

	public EvenlyGriddedSurfaceAPI getSourceSurface() {
		return source.getSourceSurface();
	}

}
