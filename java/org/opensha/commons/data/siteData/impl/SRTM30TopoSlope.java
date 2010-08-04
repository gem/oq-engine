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

import org.opensha.commons.data.siteData.AbstractSiteData;
import org.opensha.commons.data.siteData.SiteDataToXYZ;
import org.opensha.commons.data.siteData.servlet.SiteDataServletAccessor;
import org.opensha.commons.exceptions.RegionConstraintException;
import org.opensha.commons.geo.GeoTools;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.Region;
import org.opensha.commons.util.ServerPrefUtils;
import org.opensha.commons.util.binFile.BinaryMesh2DCalculator;
import org.opensha.commons.util.binFile.GeolocatedRectangularBinaryMesh2DCalculator;

public class SRTM30TopoSlope extends AbstractSiteData<Double> {
	
	public static final String NAME = "SRTM30 Topographic Slope";
	public static final String SHORT_NAME = "SRTM30_Slope";
	
	public static final double arcSecondSpacing = 30.0;
	// for 30 arc seconds this is 0.008333333333333333
	public static final double spacing = GeoTools.secondsToDeg(arcSecondSpacing);
	
	public static final int nx = 43200;
	public static final int ny = 18000;
	
	public static final double minLon = -180 + (spacing / 2d);
	public static final double minLat = -60 + (spacing / 2d);
	
	public static final String SERVLET_URL = ServerPrefUtils.SERVER_PREFS.getServletBaseURL() + "SiteData/SRTM30_Slope";
	
	private boolean useServlet;
	
	private Region region;
	
	private RandomAccessFile file = null;
	private byte[] recordBuffer = null;
	private FloatBuffer floatBuff = null;
	
	private GeolocatedRectangularBinaryMesh2DCalculator calc = null;
	
	private SiteDataServletAccessor<Double> servlet = null;
	
	public SRTM30TopoSlope() throws IOException {
		this(null, true);
	}
	
	public SRTM30TopoSlope(String fileName) throws IOException {
		this(fileName, false);
	}
	
	private SRTM30TopoSlope(String fileName, boolean useServlet) throws IOException {
		this.useServlet = useServlet;
		if (useServlet) {
			servlet = new SiteDataServletAccessor<Double>(SERVLET_URL);
		} else {
			file = new RandomAccessFile(new File(fileName), "r");
			
			recordBuffer = new byte[4];
			ByteBuffer record = ByteBuffer.wrap(recordBuffer);
			record.order(ByteOrder.LITTLE_ENDIAN);
			floatBuff = record.asFloatBuffer();
		}
		
		calc = new GeolocatedRectangularBinaryMesh2DCalculator(
				BinaryMesh2DCalculator.TYPE_FLOAT, nx, ny, minLat, minLon, spacing);
		
		calc.setStartBottom(true);
		calc.setStartLeft(true);
		
//		try {
			//region = new Region(-60, 90, -180, 180);
			region = new Region(
					new Location(-60, -180),
					new Location(90, 180));
//		} catch (RegionConstraintException e) {
//			e.printStackTrace();
//		}
	}

	public Region getApplicableRegion() {
		return region;
	}

	public Location getClosestDataLocation(Location loc) throws IOException {
		return calc.calcClosestLocation(loc);
	}

	public String getMetadata() {
		return "Topographic slope derived from version 2 of STRM30 30 Arcsecond Digital" +
				"Elevation Model.";
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

	public String getDataType() {
		return TYPE_TOPOGRAPHIC_SLOPE;
	}

	public String getDataMeasurementType() {
		return TYPE_FLAG_MEASURED;
	}

	public Double getValue(Location loc) throws IOException {
		if (useServlet) {
			return servlet.getValue(loc);
		} else {
			long pos = calc.calcClosestLocationFileIndex(loc);
			
//			System.out.println("Seek pos: " + pos);
			
			if (pos < 0 || pos > calc.getMaxFilePos())
				return Double.NaN;
			
			file.seek(pos);
			file.read(recordBuffer);
			
			double val = floatBuff.get(0);
			
			return val;
		}
	}
	
	public ArrayList<Double> getValues(LocationList locs) throws IOException {
		if (useServlet) {
			return servlet.getValues(locs);
		} else {
			return super.getValues(locs);
		}
	}

	public boolean isValueValid(Double val) {
		return val != null && !Double.isNaN(val);
	}
	
	public static void main(String args[]) throws IOException, RegionConstraintException {
		SRTM30TopoSlope data = new SRTM30TopoSlope();
		
		System.out.println(data.getValue(new Location(34, -118)));
		System.out.println(data.getValue(new Location(32, -118)));
		
		//GriddedRegion region = new GriddedRegion(32, 35, -121, -115, 0.02);
		GriddedRegion region = new GriddedRegion(
				new Location(32, -121),
				new Location(25, 115),
				0.02, new Location(0,0));
//		EvenlyGriddedRectangularGeographicRegion region = new EvenlyGriddedRectangularGeographicRegion(-60, 60, -180, 180, 1);
//		
		SiteDataToXYZ.writeXYZ(data, region, "/tmp/topo_slope.txt");
	}
}
