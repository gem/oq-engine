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

import java.util.ArrayList;

import org.opensha.commons.geo.Location;
import org.opensha.sha.faultSurface.EvenlyGriddedSurface;

public class CyberShakeEvenlyGriddedSurface extends EvenlyGriddedSurface {

	public CyberShakeEvenlyGriddedSurface( int numRows, int numCols, double gridSpacing) {
		super(numRows, numCols, gridSpacing);
	}
	
	public void setAllLocations(ArrayList<Location> locs) {
		int num = numRows * numCols;
		if (num != locs.size())
			throw new RuntimeException("ERROR: Not the right amount of locations! (expected " + num + ", got " + locs.size() + ")");
		
		int count = 0;
		
		for (int i=0; i<numRows; i++) {
			for (int j=0; j<numCols; j++) {
				this.set(i, j, locs.get(count));
				
				count++;
			}
		}
	}

	public void set( int row, int column, Location loc ) throws ArrayIndexOutOfBoundsException {

		String S = C + ": set(): ";
		checkBounds( row, column, S );
		data[row * numCols + column] = loc;
	}

}
