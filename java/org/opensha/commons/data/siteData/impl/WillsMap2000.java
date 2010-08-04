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
import java.util.Set;

import org.dom4j.Element;
import org.opensha.commons.data.siteData.AbstractSiteData;
import org.opensha.commons.data.siteData.SiteDataToXYZ;
import org.opensha.commons.data.siteData.servlet.SiteDataServletAccessor;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.Region;
import org.opensha.commons.util.ServerPrefUtils;
import org.opensha.sha.gui.servlets.siteEffect.WillsSiteClass;
import org.opensha.sha.util.SiteTranslator;

public class WillsMap2000 extends AbstractSiteData<String> {
	
	public static final String NAME = "CGS/Wills Preliminary Site Classification Map (2000)";
	public static final String SHORT_NAME = "Wills2000";
	
	public static final double minLat = 31.4;
	public static final double maxLat = 41.983;
	public static final double minLon = -124.45;
	public static final double maxLon = -114;
	
	// approximate...
	public static final double spacing = 0.01667;
	
	private Region applicableRegion;
	
	private String fileName = WillsSiteClass.WILLS_FILE;
	
	private boolean useServlet;
	
	public static final String SERVLET_URL = ServerPrefUtils.SERVER_PREFS.getServletBaseURL() + "SiteData/Wills2000";
	
	SiteDataServletAccessor<String> servlet = null;
	
	public WillsMap2000() {
		this(true);
	}
	
	public WillsMap2000(String fileName) {
		this(false);
		this.fileName= fileName;
	}
	
	public WillsMap2000(boolean useServlet) {
		super();
		this.useServlet = useServlet;
//		try {
			applicableRegion = new Region(
					new Location(minLat, minLon),
					new Location(maxLat, maxLon));
//		} catch (RegionConstraintException e) {
//			// TODO Auto-generated catch block
//			e.printStackTrace();
//		}
		if (useServlet) {
			servlet = new SiteDataServletAccessor<String>(SERVLET_URL);
			servlet.setMaxLocsPerRequest(10000);
		}
	}

	public Region getApplicableRegion() {
		return applicableRegion;
	}

	public Location getClosestDataLocation(Location loc) throws IOException {
		if (useServlet)
			return servlet.getClosestLocation(loc);
		LocationList locs = new LocationList();
		locs.add(loc);
		WillsSiteClass wills = new WillsSiteClass(locs, WillsSiteClass.WILLS_FILE);
		wills.getWillsSiteClass();
		return wills.getLastLocation();
	}

	public String getName() {
		return NAME;
	}

	public double getResolution() {
		return spacing;
	}

	public String getShortName() {
		return SHORT_NAME;
	}
	
	public String getMetadata() {
		return "Wills site classifications as defined in:\n\n" +
				"A Site-Conditions Map for California Based on Geology and Shear-Wave Velocity\n" +
				"by C. J. Wills, M. Petersen, W. A. Bryant, M. Reichle, G. J. Saucedo, " +
				"S. Tan, G. Taylor, and J. Treiman\n" +
				"Bulletin of the Seismological Society of America, 90, 6B, pp. S187–S208, December 2000\n\n" +
				"NOTE: The gridded datafile used for this dataset had lat/lon values rounded to two decimal places " +
				"resulting in an irregular mesh, therefore data results are not precise. It is recommended that you " +
				"use the 2006 version of the map. " +
				"It has a grid spacing of apporximately " + spacing + " degrees";
	}

	public String getDataType() {
		return TYPE_WILLS_CLASS;
	}
	
	public String getDataMeasurementType() {
		return TYPE_FLAG_INFERRED;
	}

	public String getValue(Location loc) throws IOException {
		if (useServlet)
			return servlet.getValue(loc);
		LocationList locs = new LocationList();
		locs.add(loc);
		return getValues(locs).get(0);
	}

	public ArrayList<String> getValues(LocationList locs) throws IOException {
		if (useServlet)
			return servlet.getValues(locs);
		WillsSiteClass wills = new WillsSiteClass(locs, fileName);
		return wills.getWillsSiteClass();
	}

	public boolean isValueValid(String val) {
		Set<String> keys = SiteTranslator.wills_vs30_map.keySet();
		return keys.contains(val);
	}
	
	@Override
	protected Element addXMLParameters(Element paramsEl) {
		paramsEl.addAttribute("useServlet", this.useServlet + "");
		paramsEl.addAttribute("fileName", this.fileName);
		return super.addXMLParameters(paramsEl);
	}
	
	public static WillsMap2000 fromXMLParams(org.dom4j.Element paramsElem) {
		boolean useServlet = Boolean.parseBoolean(paramsElem.attributeValue("useServlet"));
		String fileName = paramsElem.attributeValue("fileName");
		
		if (useServlet) {
			return new WillsMap2000(true);
		} else {
			return new WillsMap2000(fileName);
		}
	}
	
	public static void main(String[] args) throws IOException {
		
		WillsMap2000 map = new WillsMap2000();
		SiteDataToXYZ.writeXYZ(map, 0.02, "/tmp/wills2000.txt");
//		
//		SiteDataServletAccessor<String> serv = new SiteDataServletAccessor<String>(SERVLET_URL);
//		
//		LocationList locs = new LocationList();
//		locs.addLocation(new Location(34.01920, -118.28800));
//		locs.addLocation(new Location(34.91920, -118.3200));
//		locs.addLocation(new Location(34.781920, -118.88600));
//		locs.addLocation(new Location(34.21920, -118.38600));
//		locs.addLocation(new Location(34.61920, -118.18600));
//		
//		ArrayList<String> vals = map.getValues(locs);
//		for (String val : vals)
//			System.out.println(val);
	}

}
