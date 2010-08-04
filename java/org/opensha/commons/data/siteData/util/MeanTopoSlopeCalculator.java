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

package org.opensha.commons.data.siteData.util;

import java.io.IOException;
import java.util.ArrayList;

import org.opensha.commons.data.siteData.SiteDataAPI;
import org.opensha.commons.data.siteData.impl.SRTM30PlusTopoSlope;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;

public class MeanTopoSlopeCalculator {
	
	SiteDataAPI<Double> topoSlopeProvider;
	
	public MeanTopoSlopeCalculator(SiteDataAPI<Double> topoSlopeProvider) {
		if (!topoSlopeProvider.getDataType().equals(SiteDataAPI.TYPE_TOPOGRAPHIC_SLOPE)) {
			throw new IllegalArgumentException("The given Site Data provider must be of type 'Topographic Slope'");
		}
		
		this.topoSlopeProvider = topoSlopeProvider;
	}
	
	private GriddedRegion createRegionAroundSite(Location loc, double radius, double gridSpacing) {
		return new GriddedRegion(loc, radius, gridSpacing, new Location(0,0));
	}
	
	/**
	 * Get mean topographic slope for a circular region around the given location
	 * 
	 * @param loc - location for center of circle
	 * @param radius - radius in KM
	 * @param gridSpacing - grid spacing in degrees
	 * @return
	 * @throws IOException
	 */
	public double getMeanSlope(Location loc, double radius, double gridSpacing) throws IOException {
		GriddedRegion region = createRegionAroundSite(loc, radius, gridSpacing);
		
		return getMeanSlope(region);
	}
	
	public double getMeanSlope(GriddedRegion region) throws IOException {
		return getMeanSlope(region.getNodeList());
	}
	
	public double getMeanSlope(LocationList locs) throws IOException {
		ArrayList<Double> vals = topoSlopeProvider.getValues(locs);
		
		double tot = 0;
		
		for (double val : vals) {
			tot += val;
		}
		
		double mean = tot / (double)vals.size();
		
		return mean;
	}
	
	public static void main(String args[]) throws IOException {
		SiteDataAPI<Double> topoSlopeProvider = new SRTM30PlusTopoSlope();
		MeanTopoSlopeCalculator calc = new MeanTopoSlopeCalculator(topoSlopeProvider);
		
		System.out.println("34, -118: " + calc.getMeanSlope(new Location(34, -118), 300, 0.1));
	}

}
