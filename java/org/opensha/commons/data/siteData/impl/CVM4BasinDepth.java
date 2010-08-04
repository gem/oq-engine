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

import org.dom4j.Document;
import org.dom4j.Element;
import org.opensha.commons.data.siteData.AbstractSiteData;
import org.opensha.commons.data.siteData.CachedSiteDataWrapper;
import org.opensha.commons.data.siteData.servlet.SiteDataServletAccessor;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.Region;
import org.opensha.commons.util.ServerPrefUtils;
import org.opensha.commons.util.XMLUtils;
import org.opensha.commons.util.binFile.BinaryMesh2DCalculator;
import org.opensha.commons.util.binFile.GeolocatedRectangularBinaryMesh2DCalculator;

public class CVM4BasinDepth extends AbstractSiteData<Double> {
	
	public static final String NAME = "SCEC Community Velocity Model Version 4 Basin Depth";
	public static final String SHORT_NAME = "CVM4";
	
	public static final double minLat = 31;
	public static final double minLon = -121;
	
	private static final int nx = 1701;
	private static final int ny = 1101;
	
	private static final long MAX_FILE_POS = (nx-1) * (ny-1) * 4;
	
	public static final double gridSpacing = 0.005;
	
	public static final String DEPTH_2_5_FILE = "data/siteData/CVM4/depth_2.5.bin";
	public static final String DEPTH_1_0_FILE = "data/siteData/CVM4/depth_1.0.bin";
	
	public static final String SERVLET_2_5_URL = ServerPrefUtils.SERVER_PREFS.getServletBaseURL() + "SiteData/CVM4_2_5";
	public static final String SERVLET_1_0_URL = ServerPrefUtils.SERVER_PREFS.getServletBaseURL() + "SiteData/CVM4_1_0";
	
	private RandomAccessFile file = null;
	private String fileName = null;
	
	private GeolocatedRectangularBinaryMesh2DCalculator calc = null;
	
	private byte[] recordBuffer = null;
	private FloatBuffer floatBuff = null;
	
	private boolean useServlet;
	
	private String type;
	
	private SiteDataServletAccessor<Double> servlet = null;
	
	/**
	 * Constructor for creating a CVM accessor using servlets
	 * 
	 * @param type
	 * @throws IOException
	 */
	public CVM4BasinDepth(String type) throws IOException {
		this(type, null, true);
	}
	
	/**
	 * Constructor for creating a CVM accessor using either servlets or default file names
	 * 
	 * @param type
	 * @throws IOException
	 */
	public CVM4BasinDepth(String type, boolean useServlet) throws IOException {
		this(type, null, useServlet);
	}
	
	/**
	 * Constructor for creating a CVM accessor using the given file
	 * 
	 * @param type
	 * @throws IOException
	 */
	public CVM4BasinDepth(String type, String dataFile) throws IOException {
		this(type, dataFile, false);
	}
	
	public CVM4BasinDepth(String type, String dataFile, boolean useServlet) throws IOException {
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
		return type + ", extracted from version 4 of the SCEC Community Velocity Model with patches from" +
				"Geoff Ely and others. Extracted Feb 17, 2009 by Kevin Milner.\n\n" +
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
	
	public static CVM4BasinDepth fromXMLParams(org.dom4j.Element paramsElem) throws IOException {
		boolean useServlet = Boolean.parseBoolean(paramsElem.attributeValue("useServlet"));
		String fileName = paramsElem.attributeValue("fileName");
		String type = paramsElem.attributeValue("type");
		
		return new CVM4BasinDepth(type, fileName, useServlet);
	}
	
	public static void main(String[] args) throws IOException {
		CVM4BasinDepth map = new CVM4BasinDepth(TYPE_DEPTH_TO_1_0);
		
		Document doc = XMLUtils.createDocumentWithRoot();
		org.dom4j.Element root = doc.getRootElement();
		map.getAdjustableParameterList().getParameter(PARAM_MIN_BASIN_DEPTH_DOUBLE_NAME).setValue(new Double(1.0));
		org.dom4j.Element mapEl = map.toXMLMetadata(root).element(XML_METADATA_NAME);
		XMLUtils.writeDocumentToFile("/tmp/cvm4.xml", doc);
		
		map = (CVM4BasinDepth)AbstractSiteData.fromXMLMetadata(mapEl);
		
		System.out.println("Min: " + map.getAdjustableParameterList().getParameter(PARAM_MIN_BASIN_DEPTH_DOUBLE_NAME).getValue());
		
		CachedSiteDataWrapper<Double> cache = new CachedSiteDataWrapper<Double>(map);
//		SiteDataToXYZ.writeXYZ(map, 0.02, "/tmp/basin.txt");
		LocationList locs = new LocationList();
		locs.add(new Location(34.01920, -118.28800));
		locs.add(new Location(34.91920, -118.3200));
		locs.add(new Location(34.781920, -118.88600));
		locs.add(new Location(34.21920, -118.38600));
		locs.add(new Location(34.781920, -118.88600));
		locs.add(new Location(34.21920, -118.38600));
		locs.add(new Location(34.781920, -118.88600));
		locs.add(new Location(34.21920, -118.38600));
		locs.add(new Location(34.7920, -118.800));
		locs.add(new Location(34.2920, -118.3860));
		locs.add(new Location(34.61920, -118.18600));
		locs.add(new Location(34.7920, -118.800));
		locs.add(new Location(34.2920, -118.3860));
		locs.add(new Location(34.7920, -118.800));
		locs.add(new Location(34.2920, -118.3860));
		locs.add(new Location(34.7920, -118.800));
		locs.add(new Location(34.2920, -118.3860));
		
		map.getValues(locs);
		
		long time = System.currentTimeMillis();
		for (Location loc : locs) {
			double val = map.getValue(loc);
		}
//		ArrayList<Double> vals = cache.getValues(locs);
		double secs = (double)(System.currentTimeMillis() - time) / 1000d;
		System.out.println("Raw time: " + secs + "s");
		
		time = System.currentTimeMillis();
		for (Location loc : locs) {
			double val = cache.getValue(loc);
		}
//		ArrayList<Double> vals2 = map.getValues(locs);
		secs = (double)(System.currentTimeMillis() - time) / 1000d;
		System.out.println("Cache time: " + secs + "s");
		
		time = System.currentTimeMillis();
		for (Location loc : locs) {
			double val = map.getValue(loc);
		}
//		ArrayList<Double> vals = cache.getValues(locs);
		secs = (double)(System.currentTimeMillis() - time) / 1000d;
		System.out.println("Raw time: " + secs + "s");
		
		time = System.currentTimeMillis();
		for (Location loc : locs) {
			double val = cache.getValue(loc);
		}
//		ArrayList<Double> vals2 = map.getValues(locs);
		secs = (double)(System.currentTimeMillis() - time) / 1000d;
		System.out.println("Cache time: " + secs + "s");
		
		
		
		
//		for (double val : vals)
//			System.out.println(val);
	}

}
