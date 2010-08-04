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
import java.util.HashMap;
import java.util.StringTokenizer;

import org.opensha.commons.geo.Location;

/**
 * HashMap that loads and stores the values in a Generic Mapping Tools stle XYZ files.
 * 
 * @author kevin
 *
 */
public class XYZHashMap extends HashMap<Location, Double> {

	public XYZHashMap(String xyzFile) throws FileNotFoundException, IOException {
		super();
		
		ArrayList<String> lines = FileUtils.loadFile(xyzFile);
		
		for (String line : lines) {
			line = line.trim();
			if (line.length() < 2)
				continue;
			StringTokenizer tok = new StringTokenizer(line);
			double lat = Double.parseDouble(tok.nextToken());
			double lon = Double.parseDouble(tok.nextToken());
			double val = Double.parseDouble(tok.nextToken());
			
			this.put(lat, lon, val);
		}
	}
	
	public double get(double lat, double lon) {
		Location loc = new Location(lat, lon);
		return this.get(loc);
	}
	
	public void put(double lat, double lon, double val) {
		Location loc = new Location(lat, lon);
		this.put(loc, val);
	}
}
