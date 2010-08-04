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

package org.opensha.commons.util.binFile;

import static org.junit.Assert.*;

import org.junit.Test;
import org.opensha.commons.geo.Location;
import org.opensha.commons.util.binFile.BinaryMesh2DCalculator;
import org.opensha.commons.util.binFile.GeolocatedRectangularBinaryMesh2DCalculator;

public class GeolocatedBinaryMesh2DTest {
	
	private boolean verbose = true;

	public GeolocatedBinaryMesh2DTest() {
	}
	
	private void doTestPoint(GeolocatedRectangularBinaryMesh2DCalculator calc, Location loc, long correctX, long correctY) {
		long[] ind = calc.calcClosestLocationIndices(loc);
		assertNotNull(ind);
		if (verbose) {
			System.out.println(loc.getLatitude() + ", " + loc.getLongitude() + " ==> " + ind[0] + ", " + ind[1]);
		}
		assertTrue(ind[0] == correctX);
		assertTrue(ind[1] == correctY);
	}
	
	private void doAssertPointNull(GeolocatedRectangularBinaryMesh2DCalculator calc, Location loc) {
		long[] ind = calc.calcClosestLocationIndices(loc);
		assertNull(ind);
	}
	
	@Test
	public void testCorners() {
		if (verbose)
			System.out.println("GLOBAL CORNERS");
		GeolocatedRectangularBinaryMesh2DCalculator global =
			new GeolocatedRectangularBinaryMesh2DCalculator(BinaryMesh2DCalculator.TYPE_FLOAT, 360, 180, -90, -180, 1);
		double minLat = global.getMinLat();
		double maxLat = global.getMaxLat();
		double minLon = global.getMinLon();
		double maxLon = global.getMaxLon();
		
		if (verbose)
			System.out.println(minLat + " => " + maxLat + ", " + minLon + " => " + maxLon);
		
		assertTrue(minLat == -90);
		assertTrue(maxLat == 89);
		assertTrue(minLon == -180);
		assertTrue(maxLon == 179);
		
		// these are all the same point, the origin
		doTestPoint(global, new Location(-90, -180), 0, 0);
		doTestPoint(global, new Location(-90, 180), 0, 0);
		doTestPoint(global, new Location(90, -180), 0, 0);
		doTestPoint(global, new Location(90, 180), 0, 0);
		
		// now again adding/subtracting a little bit
		doTestPoint(global, new Location(-90 + 0.1, -180 + 0.1), 0, 0);
		doTestPoint(global, new Location(-90 + 0.1, 180 - 0.1), 0, 0);
		doTestPoint(global, new Location(90 - 0.1, -180 + 0.1), 0, 0);
		doTestPoint(global, new Location(90 - 0.1, 180 - 0.1), 0, 0);
		
		// the actual top corners of the file
		doTestPoint(global, new Location(-90, 179), 359, 0);
		doTestPoint(global, new Location(89, -180), 0, 179);
		doTestPoint(global, new Location(89, 179), 359, 179);
//		
//		loc = new Location(-90, 179);
//		ind = global.calcClosestLocationIndices(loc);
//		System.out.println(loc.getLatitude() + ", " + loc.getLongitude() + " ==> " + ind[0] + ", " + ind[1]);
//		assertTrue(ind[0] == 359);
//		assertTrue(ind[1] == 0);
//		
//		loc = new Location(89, -180);
//		ind = global.calcClosestLocationIndices(loc);
//		System.out.println(loc.getLatitude() + ", " + loc.getLongitude() + " ==> " + ind[0] + ", " + ind[1]);
//		assertTrue(ind[0] == 0);
//		assertTrue(ind[1] == 179);
//		
//		loc = new Location(89, 179);
//		ind = global.calcClosestLocationIndices(loc);
//		System.out.println(loc.getLatitude() + ", " + loc.getLongitude() + " ==> " + ind[0] + ", " + ind[1]);
//		assertTrue(ind[0] == 359);
//		assertTrue(ind[1] == 179);
	}
	
	@Test
	public void testRegional() {
		if (verbose)
			System.out.println("REGIONAL");
		GeolocatedRectangularBinaryMesh2DCalculator regional =
			new GeolocatedRectangularBinaryMesh2DCalculator(BinaryMesh2DCalculator.TYPE_FLOAT, 13, 9, 32, -122, .5);
		double minLat = regional.getMinLat();
		double maxLat = regional.getMaxLat();
		double minLon = regional.getMinLon();
		double maxLon = regional.getMaxLon();
		
		assertTrue(minLat == 32);
		assertTrue(maxLat == 36);
		assertTrue(minLon == -122);
		assertTrue(maxLon == -116);
		
		if (verbose)
			System.out.println(minLat + " => " + maxLat + ", " + minLon + " => " + maxLon);
		
		// normal right on cases
		doTestPoint(regional, new Location(32, -122), 0, 0);
		doTestPoint(regional, new Location(36, -116), 12, 8);
		doTestPoint(regional, new Location(34, -119), 6, 4);
		doTestPoint(regional, new Location(33.5, -120.5), 3, 3);
		doTestPoint(regional, new Location(33.5, -120), 4, 3);
		
		// inside, close cases
		doTestPoint(regional, new Location(32.1, -121.9), 0, 0);
		doTestPoint(regional, new Location(35.75, -116), 12, 8);
		doTestPoint(regional, new Location(35.74, -116), 12, 7);
		doTestPoint(regional, new Location(33.71, -120.38), 3, 3);
		doTestPoint(regional, new Location(33.7499, -120.26), 3, 3);
		
		// outside, close cases
		doTestPoint(regional, new Location(31.9, -122), 0, 0);
		doTestPoint(regional, new Location(31.9, -122.25), 0, 0);
		doTestPoint(regional, new Location(31.9, -115.76), 12, 0);
		doTestPoint(regional, new Location(36.2, -117), 10, 8);
		
		// outside, far cases
		doAssertPointNull(regional, new Location(0, 0));
		doAssertPointNull(regional, new Location(37, -119));
		doAssertPointNull(regional, new Location(31.9, -123));
		doAssertPointNull(regional, new Location(31.9, -115.74));
	}

}
