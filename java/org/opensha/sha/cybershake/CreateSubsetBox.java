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

package org.opensha.sha.cybershake;

import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.opensha.commons.geo.BorderType;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.Region;
import org.opensha.commons.util.FileUtils;


public class CreateSubsetBox {

	Region region;
	public CreateSubsetBox(){
		LocationList locList = new LocationList();
		locList.add(new Location(31.082920,-116.032285));
		locList.add(new Location(33.122341,-113.943965));
		locList.add(new Location(36.621696,-118.9511292));
		locList.add(new Location(34.5,-121));
		region = new Region(locList, BorderType.MERCATOR_LINEAR);
		createSubsetFile();
	}
	
	
	public void createSubsetFile(){
		
		try {
			FileWriter fw = new FileWriter("RegionSubset.txt");
			ArrayList fileLines = FileUtils.loadFile("map_data.txt");
			int numLines = fileLines.size();
			for(int i=0;i<numLines;++i){
				StringTokenizer st = new StringTokenizer((String)fileLines.get(i));
				double lat = Double.parseDouble(st.nextToken().trim());
				double lon = Double.parseDouble(st.nextToken().trim());
				Location loc = new Location(lat,lon);
				if(region.contains(loc)){
					fw.write((String)fileLines.get(i)+"\n");
				}
			}
			fw.close();
				
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}
	
	public static void main(String[] args){
		new CreateSubsetBox();
	}
	
}
