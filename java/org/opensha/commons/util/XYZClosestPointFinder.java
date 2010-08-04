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

package org.opensha.commons.util;

import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.opensha.commons.geo.Location;

/**
 * This class takes the path to a Generic Mapping Tools style XYZ file and loads in all of the
 * locations and values. It then allows one to find the value from the file that is closest to
 * a given location.
 * 
 * @author kevin
 *
 */
public class XYZClosestPointFinder {
	ArrayList<double[]> vals;
	
	public XYZClosestPointFinder(String fileName) throws FileNotFoundException, IOException {
		
		ArrayList<String> lines = null;
		lines = FileUtils.loadFile(fileName);
		
		vals = new ArrayList<double[]>();
		
		for (String line : lines) {
			line = line.trim();
			if (line.length() < 2)
				continue;
			StringTokenizer tok = new StringTokenizer(line);
			double lat = Double.parseDouble(tok.nextToken());
			double lon = Double.parseDouble(tok.nextToken());
			double val = Double.parseDouble(tok.nextToken());
			double doub[] = new double[3];
			doub[0] = lat;
			doub[1] = lon;
			doub[2] = val;
			vals.add(doub);
		}
	}
	
	/**
	 * Returns the value at the closest location in the XYZ file (no matter how far
	 * away the closest point is).
	 * 
	 * @param loc
	 * @return
	 */
	public double getClosestVal(Location loc) {
		return getClosestVal(loc.getLatitude(), loc.getLongitude());
	}
	
	/**
	 * Returns the value at the closest location in the XYZ file (no matter how far
	 * away the closest point is).
	 * 
	 * @param lat
	 * @param lon
	 * @return
	 */
	public double getClosestVal(double lat, double lon) {
		return getClosestVal(lat, lon, Double.MAX_VALUE);
	}
	
	/**
	 * Returns the value at the closest location in the XYZ file within a given tolerance.
	 * 
	 * @param loc
	 * @param tolerance
	 * @return
	 */
	public double getClosestVal(Location loc, double tolerance) {
		return getClosestVal(loc.getLatitude(), loc.getLongitude(), tolerance);
	}
	
	/**
	 * Returns the value at the closest location in the XYZ file within a given tolerance.
	 * 
	 * @param lat
	 * @param lon
	 * @param tolerance
	 * @return
	 */
	public double getClosestVal(double lat, double lon, double tolerance) {
		double closest = Double.MAX_VALUE;
		double closeVal = 0;
		
		for (double[] val : vals) {
			double dist = Math.pow(val[0] - lat, 2) + Math.pow(val[1] - lon, 2);
			if (dist < closest) {
				closest = dist;
				closeVal = val[2];
			}
		}
		
		if (closest < tolerance)
			return closeVal;
		else
			return Double.NaN;
	}
}
