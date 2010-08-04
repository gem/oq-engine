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

package org.opensha.commons.data.siteData.impl;

import java.io.IOException;
import java.util.ArrayList;

import org.opensha.commons.data.siteData.AbstractSiteData;
import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.Region;
import org.opensha.sha.util.SiteTranslator;

public class WillsMap2000TranslatedVs30 extends AbstractSiteData<Double> {
	
	public static final String NAME = WillsMap2000.NAME + " - Translated to Vs30";
	public static final String SHORT_NAME = WillsMap2000.SHORT_NAME + "_Vs30";
	
	WillsMap2000 map;
	
	public WillsMap2000TranslatedVs30() {
		this(null, true);
	}
	
	public WillsMap2000TranslatedVs30(String fileName) {
		this(fileName, false);
	}
	
	private WillsMap2000TranslatedVs30(String fileName, boolean useServlet) {
		if (useServlet)
			map = new WillsMap2000(useServlet);
		else
			map = new WillsMap2000(fileName);
		initDefaultVS30Params();
		this.paramList.addParameter(minVs30Param);
		this.paramList.addParameter(maxVs30Param);
	}

	public Region getApplicableRegion() {
		return map.getApplicableRegion();
	}

	public Location getClosestDataLocation(Location loc) throws IOException {
		return map.getClosestDataLocation(loc);
	}

	public String getMetadata() {
		String meta = map.getMetadata();
		meta += "\n\nTranslated to Vs30 values with the following table:\n" + SiteTranslator.getWillsVs30TranslationString();
		return null;
	}

	public String getName() {
		return NAME;
	}

	public double getResolution() {
		return map.getResolution();
	}

	public String getShortName() {
		return SHORT_NAME;
	}

	public String getDataType() {
		return TYPE_VS30;
	}

	public String getDataMeasurementType() {
		return map.getDataMeasurementType();
	}
	
	private Double getValueFromWillsClass(String wills) {
		Double val = SiteTranslator.getVS30FromWillsClass(wills);
		
		return certifyMinMaxVs30(val);
	}

	public Double getValue(Location loc) throws IOException {
		String wills = map.getValue(loc);
		return getValueFromWillsClass(wills);
	}
	
	public ArrayList<Double> getValues(LocationList locs) throws IOException {
		ArrayList<String> willsVals = map.getValues(locs);
		ArrayList<Double> vsVals = new ArrayList<Double>();
		
		for (String wills : willsVals) {
			vsVals.add(getValueFromWillsClass(wills));
		}
		return vsVals;
	}

	public boolean isValueValid(Double val) {
		return val != null && !val.isNaN() && val > 0;
	}
	
	/**
	 * @param args
	 * @throws IOException 
	 * @throws InvalidRangeException 
	 */
	public static void main(String[] args) throws InvalidRangeException, IOException {
		WillsMap2000TranslatedVs30 data = new WillsMap2000TranslatedVs30();
		
		System.out.println(data.getValue(new Location(34, -118)));
	}

}
