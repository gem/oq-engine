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

import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.Region;

public class GeolocatedRectangularBinaryMesh2DCalculator extends
		BinaryMesh2DCalculator {
	
	public static final boolean D = false;
	
	private double minLat;
	private double maxLat;
	private double minLon;
	private double maxLon;
	private double gridSpacing;
	
	private boolean startBottom = true;
	private boolean startLeft = true;
	
	private boolean wrapX = false;
	private boolean wrapY= false;
	
	private boolean allLonPos = false;

	/**
	 * Creates a new GeolocatedRectangularBinaryMesh2DCalculator assuming that the data starts at the bottom left
	 * corner of the region (at minLat, minLon) and is ordered fast-X-Y.
	 * 
	 * @param numType
	 * @param nx
	 * @param ny
	 * @param minLat
	 * @param minLon
	 * @param gridSpacing
	 */
	public GeolocatedRectangularBinaryMesh2DCalculator(int numType, int nx, int ny,
			double minLat, double minLon, double gridSpacing) {
		super(numType, nx, ny);
		
		this.minLat = minLat;
		this.minLon = minLon;
		this.maxLat = minLat + gridSpacing * (ny-1);
		this.maxLon = minLon + gridSpacing * (nx-1);
		this.gridSpacing = gridSpacing;
		
		if (minLon >= 0)
			allLonPos = true;
		
		if (D) {
			System.out.println("minLat: " + minLat + ", maxLat: " + maxLat);
			System.out.println("minLon: " + minLon + ", maxLon: " + maxLon);
		}
		
		if ((minLat + 180) == (maxLat + gridSpacing)) {
			if (D) System.out.println("Wrapping Y!");
			wrapY = true;
		}
		if ((minLon + 360) == (maxLon + gridSpacing)) {
			if (D) System.out.println("Wrapping X!");
			wrapX = true;
		}
	}
	
	public long[] calcClosestLocationIndices(Location loc) {
		return calcClosestLocationIndices(loc.getLatitude(), loc.getLongitude());
	}
	
	public long[] calcClosestLocationIndices(double lat, double lon) {
		long x = calcX(lon);
		long y = calcY(lat);
		
		if (x < 0 || y < 0) {
			return null;
		}
		
		if (x >= nx) {
			if (wrapX)
				x = x % nx;
			else
				return null;
		}
		
		if (y >= ny) {
			if (wrapY)
				y = y % ny;
			else
				return null;
		}
		
		long pt[] = { x, y };
		
		return pt;
	}
	
	public long calcClosestLocationIndex(Location loc) {
		return calcClosestLocationIndex(loc.getLatitude(), loc.getLongitude());
	}
	
	public long calcClosestLocationIndex(double lat, double lon) {
		long pt[] = calcClosestLocationIndices(lat, lon);
		
		// if pt is null, return -1, else return mesh index
		if (pt == null)
			return -1;
		else
			return this.calcMeshIndex(pt[0], pt[1]);
	}
	
	public long calcClosestLocationFileIndex(Location loc) {
		return calcClosestLocationFileIndex(loc.getLatitude(), loc.getLongitude());
	}
	
	public long calcClosestLocationFileIndex(double lat, double lon) {
		long pt[] = calcClosestLocationIndices(lat, lon);
		
		// if pt is null, return -1, else return file index
		if (pt == null)
			return -1;
		else
			return this.calcFileIndex(pt[0], pt[1]);
	}
	
	public Location getLocationForPoint(long x, long y) {
		double lat = maxLat - y * gridSpacing;
		double lon = minLon + x * gridSpacing;
		
		return new Location(lat, lon);
	}
	
	public Location calcClosestLocation(Location loc) {
		return calcClosestLocation(loc.getLatitude(), loc.getLongitude());
	}
	
	public Location calcClosestLocation(double lat, double lon) {
		long pt[] = calcClosestLocationIndices(lat, lon);
		
		// if pt is null, return null, else return location
		if (pt == null)
			return null;
		else
			return getLocationForPoint(pt[0], pt[1]);
	}
	
	private long calcX(double lon) {
		if (allLonPos && lon < 0)
			lon += 360;
		if (startLeft)
			return ((long)((lon - minLon) / gridSpacing + 0.5));
		else
			return (long)((maxLon - lon) / gridSpacing + 0.5);
	}
	
	private long calcY(double lat) {
		if (startBottom)
			return ((long)((lat - minLat) / gridSpacing + 0.5));
		else
			return ((long)((maxLat - lat) / gridSpacing + 0.5));
	}

	public double getMinLat() {
		return minLat;
	}

	public double getMaxLat() {
		return maxLat;
	}

	public double getMinLon() {
		return minLon;
	}

	public double getMaxLon() {
		return maxLon;
	}

	public double getGridSpacing() {
		return gridSpacing;
	}

	public boolean isStartBottom() {
		return startBottom;
	}

	public void setStartBottom(boolean startBottom) {
		this.startBottom = startBottom;
	}

	public boolean isStartLeft() {
		return startLeft;
	}

	public void setStartLeft(boolean startLeft) {
		this.startLeft = startLeft;
	}
	
	public Region getApplicableRegion() {
//		try {
			return new Region(
					new Location(minLat,minLon),
					new Location(maxLat,maxLon));
//		} catch (RegionConstraintException e) {
//			e.printStackTrace();
//			return null;
//		}
	}

}
