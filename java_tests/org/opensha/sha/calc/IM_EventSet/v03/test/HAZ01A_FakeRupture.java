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

import org.opensha.commons.geo.Location;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;

public class HAZ01A_FakeRupture extends ProbEqkRupture {
	
	int sourceID;
	int rupID;
	
	public HAZ01A_FakeRupture() {}
	
	public HAZ01A_FakeRupture(ProbEqkRupture rup, int sourceID, int rupID) {
		this(rup.getMag(), rup.getAveRake(), rup.getProbability(), rup.getRuptureSurface(),
				rup.getHypocenterLocation(), sourceID, rupID);
	}
	
	public HAZ01A_FakeRupture(double mag,
            double aveRake,
            double probability,
            EvenlyGriddedSurfaceAPI ruptureSurface,
            Location hypocenterLocation, int sourceID, int rupID) {
		super(mag, aveRake, probability, ruptureSurface, hypocenterLocation);
		this.sourceID = sourceID;
		this.rupID = rupID;
	}

	public int getSourceID() {
		return sourceID;
	}

	public int getRupID() {
		return rupID;
	}

}
