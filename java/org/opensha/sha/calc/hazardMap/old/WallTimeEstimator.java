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

package org.opensha.sha.calc.hazardMap.old;

import java.rmi.RemoteException;
import java.util.Random;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.region.SitesInGriddedRegion;
import org.opensha.commons.exceptions.RegionConstraintException;
import org.opensha.sha.calc.HazardCurveCalculator;
import org.opensha.sha.calc.hazardMap.old.grid.HazardMapPortionCalculator;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.imr.AttenuationRelationship;

public class WallTimeEstimator {
	
	public static double calcTimePerCurve(EqkRupForecast erf, AttenuationRelationship attenRel,
			SitesInGriddedRegion sites, ArbitrarilyDiscretizedFunc hazFunction, int numSamples) {
		int numLocs = sites.getRegion().getNodeCount();
		erf.updateForecast();
		if (numLocs < numSamples) {
			numSamples = numLocs;
		}
		
		HazardCurveCalculator calc = null;
		try {
			calc = new HazardCurveCalculator();
		} catch (RemoteException e) {
			return -1;
		}
		
		Random rand = new Random(System.currentTimeMillis());
		
		double times = 0;
		for (int i=0; i<numSamples; i++) {
			long start = System.currentTimeMillis();
			ArbitrarilyDiscretizedFunc logFunc = HazardMapPortionCalculator.getLogFunction(hazFunction);
			
			int siteNum = rand.nextInt(numLocs);
			
			try {
				calc.getHazardCurve(hazFunction, sites.getSite(siteNum), attenRel, erf);
			} catch (RemoteException e) {
				e.printStackTrace();
			} catch (RegionConstraintException e) {
				e.printStackTrace();
			}
			
			hazFunction = HazardMapPortionCalculator.unLogFunction(hazFunction, logFunc);
			long end = System.currentTimeMillis();
			times += (double)(end - start) / 1000d;
		}
		
		return times / (double)numSamples;
	}
	
	

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		// TODO Auto-generated method stub

	}

}
