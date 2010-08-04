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

package org.opensha.sha.calc.IM_EventSet.v03;

import java.io.File;
import java.io.IOException;
import java.text.ParseException;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.opensha.commons.data.siteData.SiteDataValue;
import org.opensha.commons.geo.Location;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.calc.IM_EventSet.v03.gui.AddSiteDataPanel;

public class SiteFileLoader {
	
	private ArrayList<Location> locs;
	private ArrayList<ArrayList<SiteDataValue<?>>> valsList;
	
	private String measurementType;
	private boolean lonFirst;
	private ArrayList<String> siteDataTypes;
	
	public SiteFileLoader(boolean lonFirst, String measurementType, ArrayList<String> siteDataTypes) {
		this.lonFirst = lonFirst;
		this.measurementType = measurementType;
		this.siteDataTypes = siteDataTypes;
	}
	
	public void loadFile(File file) throws IOException, ParseException {
		ArrayList<String> lines = FileUtils.loadFile(file.getAbsolutePath());
		
		String measType = measurementType;
		
		locs = new ArrayList<Location>();
		valsList = new ArrayList<ArrayList<SiteDataValue<?>>>();
		
		for (int i=0; i<lines.size(); i++) {
			String line = lines.get(i).trim();
			// skip comments
			if (line.startsWith("#"))
				continue;
			StringTokenizer tok = new StringTokenizer(line);
			if (tok.countTokens() < 2)
				throw new ParseException("Line " + (i+1) + " has less than 2 fields!", 0);
			double lat, lon;
			ArrayList<SiteDataValue<?>> vals = new ArrayList<SiteDataValue<?>>();
			try {
				if (lonFirst) {
					lon = Double.parseDouble(tok.nextToken());
					lat = Double.parseDouble(tok.nextToken());
				} else {
					lat = Double.parseDouble(tok.nextToken());
					lon = Double.parseDouble(tok.nextToken());
				}
				Location loc = new Location(lat, lon);
				for (String type : siteDataTypes) {
					if (!tok.hasMoreTokens())
						break;
					String valStr = tok.nextToken();
					SiteDataValue<?> val = AddSiteDataPanel.getValue(type, measType, valStr);
					vals.add(val);
				}
				locs.add(loc);
				valsList.add(vals);
			} catch (NumberFormatException e) {
				throw new NumberFormatException("Error parsing number at line " + (i+1));
			}
		}
	}
	
	public ArrayList<Location> getLocs() {
		return locs;
	}

	public ArrayList<ArrayList<SiteDataValue<?>>> getValsList() {
		return valsList;
	}

}
