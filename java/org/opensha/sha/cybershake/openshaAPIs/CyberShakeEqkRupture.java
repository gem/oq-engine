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

package org.opensha.sha.cybershake.openshaAPIs;

import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.geo.Location;
import org.opensha.commons.util.FaultUtils;
import org.opensha.sha.cybershake.db.ERF2DB;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;

public class CyberShakeEqkRupture extends ProbEqkRupture {
	
	private int srcID = 0;
	private int rupID = 0;
	private int erfID = 0;
	
	private ERF2DB erf2db = null;

	public CyberShakeEqkRupture(
			double mag, double prob,
			CyberShakeEvenlyGriddedSurface ruptureSurface,
			Location hypocenterLocation, int srcID, int rupID,
			int erfID) throws InvalidRangeException{
		this.mag = mag;
		this.probability = prob;
		FaultUtils.assertValidRake(aveRake);
		this.hypocenterLocation = hypocenterLocation;
		this.aveRake = 0;
		this.ruptureSurface = ruptureSurface;
		
		this.srcID = srcID;
		this.rupID = rupID;
		this.erfID = erfID;
	}
	
	public CyberShakeEqkRupture(
			double mag, double prob,
			Location hypocenterLocation, int srcID, int rupID,
			int erfID, ERF2DB erf2db) throws InvalidRangeException{
		this(mag, prob, null, hypocenterLocation, srcID, rupID, erfID);
		
		this.erf2db = erf2db;
	}
	
	public CyberShakeEqkRupture(ProbEqkRupture rup, int srcID, int rupID, int erfID) {
		this.mag = rup.getMag();
		this.probability = rup.getProbability();
		this.hypocenterLocation = rup.getHypocenterLocation();
		this.aveRake = rup.getAveRake();
		this.ruptureSurface = rup.getRuptureSurface();
		
		this.srcID = srcID;
		this.rupID = rupID;
		this.erfID = erfID;
	}
	
	

	@Override
	public EvenlyGriddedSurfaceAPI getRuptureSurface() {
		if (ruptureSurface == null && erf2db != null) {
			ruptureSurface = erf2db.getRuptureSurface(erfID, srcID, rupID);
		}
		return ruptureSurface;
	}

	public int getSrcID() {
		return srcID;
	}

	public int getRupID() {
		return rupID;
	}

	public int getErfID() {
		return erfID;
	}

}
