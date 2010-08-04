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

package org.opensha.commons.mapping.gmt.elements;

import java.util.ArrayList;

import org.opensha.commons.data.DataPoint2D;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;

public class PSXYPolygon extends PSXYElement {
	
	/**
	 * default serial version UID
	 */
	private static final long serialVersionUID = 1l;
	
	private ArrayList<DataPoint2D> points = new ArrayList<DataPoint2D>();;
	
	/**
	 * Constructor for a simple line
	 * 
	 * @param point1
	 * @param point2
	 */
	public PSXYPolygon(DataPoint2D point1, DataPoint2D point2) {
		points.add(point1);
		points.add(point2);
	}
	
	public PSXYPolygon(Location loc1, Location loc2) {
		points.add(new DataPoint2D(loc1.getLongitude(), loc1.getLatitude()));
		points.add(new DataPoint2D(loc2.getLongitude(), loc2.getLatitude()));
	}
	
	public PSXYPolygon(ArrayList<DataPoint2D> points) {
		this.points = points;
	}
	
	public PSXYPolygon(LocationList locs) {
		for (Location loc : locs) {
			points.add(new DataPoint2D(loc.getLongitude(), loc.getLatitude()));
		}
	}
	
	public PSXYPolygon() {
		
	}
	
	public ArrayList<DataPoint2D> getPoints() {
		return points;
	}
	
	public void addPoint(DataPoint2D point) {
		points.add(point);
	}
	
	/**
	 * Returns true if polygon has at least 2 points
	 * @return
	 */
	public boolean isValid() {
		return points != null && points.size() >= 2;
	}
	
	public int size() {
		return points.size();
	}
}
