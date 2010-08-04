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

import java.io.File;
import java.io.IOException;
import java.io.RandomAccessFile;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;
import java.util.ArrayList;

import org.dom4j.Element;
import org.opensha.commons.data.siteData.AbstractSiteData;
import org.opensha.commons.data.siteData.SiteDataToXYZ;
import org.opensha.commons.data.siteData.servlet.SiteDataServletAccessor;
import org.opensha.commons.exceptions.RegionConstraintException;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.Region;
import org.opensha.commons.util.ServerPrefUtils;
import org.opensha.commons.util.binFile.BinaryMesh2DCalculator;
import org.opensha.commons.util.binFile.GeolocatedRectangularBinaryMesh2DCalculator;

public class USGSBayAreaBasinDepth extends AbstractSiteData<Double> {
	
	public static final String NAME = "USGS Bay Area Velocity Model Release 8.3.0";
	public static final String SHORT_NAME = "USGSBayAreaBasin";
	
	public static final double minLat = 35;
	public static final double minLon = -127;
	
	private static final int nx = 851;
	private static final int ny = 651;
	
	private static final long MAX_FILE_POS = (nx-1) * (ny-1) * 4;
	
	public static final double gridSpacing = 0.01;
	
	public static final String DEPTH_2_5_FILE = "data/siteData/SF06/depth_2.5.bin";
	public static final String DEPTH_1_0_FILE = "data/siteData/SF06/depth_1.0.bin";
	
	public static final String SERVLET_2_5_URL = ServerPrefUtils.SERVER_PREFS.getServletBaseURL() + "SiteData/SF06_2_5";
	public static final String SERVLET_1_0_URL = ServerPrefUtils.SERVER_PREFS.getServletBaseURL() + "SiteData/SF06_1_0";
	
	private RandomAccessFile file = null;
	private String fileName = null;
	
	private GeolocatedRectangularBinaryMesh2DCalculator calc = null;
	
	private byte[] recordBuffer = null;
	private FloatBuffer floatBuff = null;
	
	private boolean useServlet;
	
	private String type;
	
	private SiteDataServletAccessor<Double> servlet = null;
	
	public USGSBayAreaBasinDepth(String type) throws IOException {
		this(type, null, true);
	}
	
	public USGSBayAreaBasinDepth(String type, String dataFile) throws IOException {
		this(type, dataFile, false);
	}

	public USGSBayAreaBasinDepth(String type, boolean useServlet) throws IOException {
		this(type, null, useServlet);
	}
	
	public USGSBayAreaBasinDepth(String type, String dataFile, boolean useServlet) throws IOException {
		super();
		this.useServlet = useServlet;
		this.fileName = dataFile;
		this.type = type;
		
		calc = new GeolocatedRectangularBinaryMesh2DCalculator(
				BinaryMesh2DCalculator.TYPE_FLOAT, nx, ny, minLat, minLon, gridSpacing);
		
		if (useServlet) {
			if (type.equals(TYPE_DEPTH_TO_1_0))
				servlet = new SiteDataServletAccessor<Double>(SERVLET_1_0_URL);
			else
				servlet = new SiteDataServletAccessor<Double>(SERVLET_2_5_URL);
		} else {
			if (dataFile == null) {
				if (type.equals(TYPE_DEPTH_TO_1_0))
					dataFile = DEPTH_1_0_FILE;
				else
					dataFile = DEPTH_2_5_FILE;
			}
			
			file = new RandomAccessFile(new File(dataFile), "r");
			
			calc.setStartBottom(true);
			calc.setStartLeft(true);
			
			recordBuffer = new byte[4];
			ByteBuffer record = ByteBuffer.wrap(recordBuffer);
			record.order(ByteOrder.LITTLE_ENDIAN);
			
			floatBuff = record.asFloatBuffer();
		}
		initDefaultBasinParams();
		this.paramList.addParameter(minBasinDoubleParam);
		this.paramList.addParameter(maxBasinDoubleParam);
	}

	public Region getApplicableRegion() {
		return calc.getApplicableRegion();
	}

	public Location getClosestDataLocation(Location loc) {
		return calc.calcClosestLocation(loc);
	}

	public String getName() {
		return NAME;
	}
	
	public String getShortName() {
		return SHORT_NAME;
	}
	
	public String getMetadata() {
		return type + ", extracted from version 8.3.0 of the USGS Bay Area Velocity Model (used in the SF06" +
				" simulation project). Extracted March 4, 2009 by Kevin Milner.\n\n" +
				"It has a grid spacing of " + gridSpacing + " degrees";
	}

	public double getResolution() {
		return gridSpacing;
	}

	public String getDataType() {
		return type;
	}
	
	// TODO: what should we set this to?
	public String getDataMeasurementType() {
		return TYPE_FLAG_INFERRED;
	}

	public Double getValue(Location loc) throws IOException {
		if (useServlet) {
			return certifyMinMaxBasinDepth(servlet.getValue(loc));
		} else {
			long pos = calc.calcClosestLocationFileIndex(loc);
			
			if (pos > MAX_FILE_POS || pos < 0)
				return Double.NaN;
			
			file.seek(pos);
			file.read(recordBuffer);
			
			// this is in meters
			double val = floatBuff.get(0);
			
			if (val >= 100000000.0) {
//				System.out.println("Found a too big...");
				return Double.NaN;
			}
			
			// convert to KM
			Double dobVal = (double)val / 1000d;
			return certifyMinMaxBasinDepth(dobVal);
		}
	}

	public ArrayList<Double> getValues(LocationList locs) throws IOException {
		if (useServlet) {
			ArrayList<Double> vals = servlet.getValues(locs);
			for (int i=0; i<vals.size(); i++) {
				vals.set(i, certifyMinMaxBasinDepth(vals.get(i)));
			}
			return vals;
		} else {
			return super.getValues(locs);
		}
	}

	public boolean isValueValid(Double val) {
		return val != null && !Double.isNaN(val);
	}
	
	@Override
	protected Element addXMLParameters(Element paramsEl) {
		paramsEl.addAttribute("useServlet", this.useServlet + "");
		paramsEl.addAttribute("fileName", this.fileName);
		paramsEl.addAttribute("type", this.type);
		return super.addXMLParameters(paramsEl);
	}
	
	public static USGSBayAreaBasinDepth fromXMLParams(org.dom4j.Element paramsElem) throws IOException {
		boolean useServlet = Boolean.parseBoolean(paramsElem.attributeValue("useServlet"));
		String fileName = paramsElem.attributeValue("fileName");
		String type = paramsElem.attributeValue("type");
		
		return new USGSBayAreaBasinDepth(type, fileName, useServlet);
	}
	
	public static void main(String args[]) throws RegionConstraintException {
		try {
			USGSBayAreaBasinDepth cvm = new USGSBayAreaBasinDepth(TYPE_DEPTH_TO_1_0, DEPTH_2_5_FILE, true);
//			EvenlyGriddedRectangularGeographicRegion region = new EvenlyGriddedRectangularGeographicRegion(37, 38.5, -122.75, -121.5, 0.01);
//			SiteDataToXYZ.writeXYZ(cvm, region, "/tmp/sfbasin.txt");
			SiteDataToXYZ.writeXYZ(cvm, 0.05, "/tmp/sfbasin.txt");
			
			System.out.println(cvm.getValue(new Location(35.1, -125)));
			System.out.println(cvm.getValue(new Location(36.1, -125)));
			System.out.println(cvm.getValue(new Location(40, -124)));
		} catch (IOException e) {
			e.printStackTrace();
		}
	}

}
