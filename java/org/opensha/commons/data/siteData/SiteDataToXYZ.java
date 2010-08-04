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

package org.opensha.commons.data.siteData;

import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;

import org.opensha.commons.geo.BorderType;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;

/**
 * This class takes a SiteDataAPI object and writes it's data to a GMT XYZ file for a given region.
 * If no region is given, the applicable region for the data provider is used.
 * 
 * @author Kevin Milner
 *
 */
public class SiteDataToXYZ {
	
	public static void writeXYZ(SiteDataAPI<?> data, GriddedRegion region,
			String fileName) throws IOException {
		writeXYZ(data, region, fileName, true);
	}
	
	public static void writeXYZ(SiteDataAPI<?> data, double gridSpacing,
			String fileName) throws IOException {
		GriddedRegion region =
				new GriddedRegion(
						data.getApplicableRegion().getBorder(), BorderType.MERCATOR_LINEAR, gridSpacing, new Location(0,0));
		writeXYZ(data, region, fileName, true);
	}
	
	public static void writeXYZ(SiteDataAPI<?> data, GriddedRegion region,
			String fileName, boolean latFirst) throws IOException {
		FileWriter fw = new FileWriter(fileName);
		LocationList locs = region.getNodeList();
		ArrayList<?> vals = data.getValues(locs);
		for (int i=0; i<locs.size(); i++) {
			Location loc = locs.get(i);
			String str;
			if (latFirst)
				str = loc.getLatitude() + "\t" + loc.getLongitude() + "\t";
			else
				str = loc.getLongitude() + "\t" + loc.getLatitude() + "\t";
			
			str += vals.get(i).toString();
			
			fw.write(str + "\n");
		}
		
		fw.close();
	}

}
