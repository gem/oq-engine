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
import java.nio.ShortBuffer;
import java.util.ArrayList;

import org.opensha.commons.data.siteData.AbstractSiteData;
import org.opensha.commons.data.siteData.servlet.SiteDataServletAccessor;
import org.opensha.commons.exceptions.RegionConstraintException;
import org.opensha.commons.geo.GeoTools;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.Region;
import org.opensha.commons.util.ServerPrefUtils;
import org.opensha.commons.util.binFile.BinaryMesh2DCalculator;
import org.opensha.commons.util.binFile.GeolocatedRectangularBinaryMesh2DCalculator;

public class SRTM30PlusTopography extends AbstractSiteData<Double> {
	
	public static final String NAME = "SRTM30 Plus Topography/Bathymetry";
	public static final String SHORT_NAME = "SRTM30_Plus";
	
	public static final double arcSecondSpacing = 30.0;
	// for 30 arc seconds this is 0.008333333333333333
	public static final double spacing = GeoTools.secondsToDeg(arcSecondSpacing);
	
	public static final int nx = 43200;
	public static final int ny = 21600;
	
	public static final double minLon = 0 + (spacing / 2d);
	public static final double minLat = -90 + (spacing / 2d);
	
	public static final String SERVLET_URL = ServerPrefUtils.SERVER_PREFS.getServletBaseURL() + "SiteData/SRTM30_Plus";
	
	private boolean useServlet;
	
	private Region region;
	
	private RandomAccessFile file = null;
	private byte[] recordBuffer = null;
	private ShortBuffer shortBuff = null;
	
	private GeolocatedRectangularBinaryMesh2DCalculator calc = null;
	
	private SiteDataServletAccessor<Double> servlet = null;
	
	public SRTM30PlusTopography() throws IOException {
		this(null, true);
	}
	
	public SRTM30PlusTopography(String fileName) throws IOException {
		this(fileName, false);
	}
	
	private SRTM30PlusTopography(String fileName, boolean useServlet) throws IOException {
		this.useServlet = useServlet;
		if (useServlet) {
			servlet = new SiteDataServletAccessor<Double>(SERVLET_URL);
		} else {
			file = new RandomAccessFile(new File(fileName), "r");
			
			recordBuffer = new byte[2];
			ByteBuffer record = ByteBuffer.wrap(recordBuffer);
			record.order(ByteOrder.BIG_ENDIAN);
			shortBuff = record.asShortBuffer();
		}
		
		calc = new GeolocatedRectangularBinaryMesh2DCalculator(
				BinaryMesh2DCalculator.TYPE_SHORT,nx, ny, minLat, minLon, spacing);
		
		calc.setStartBottom(false);
		calc.setStartLeft(true);
		
		region = Region.getGlobalRegion();
	}

	public Region getApplicableRegion() {
		return region;
	}

	public Location getClosestDataLocation(Location loc) throws IOException {
		return calc.calcClosestLocation(loc);
	}

	public String getMetadata() {
		return "Topography/Bathymetry from version 5.0 (September 16, 2008) of STRM30_PLUS 30 Arcsecond Digital" +
				"Elevation Model.\n\n" +
				"Downloaded from: http://topex.ucsd.edu/WWW_html/srtm30_plus.html\n\n (February, 2009)" +
				"From the web page:\n" +
				"Land data are based on the 1-km averages of topography derived from the USGS SRTM30 grided DEM" +
				" data product created with data from the NASA Shuttle Radar Topography Mission. GTOPO30 data are " +
				"used for high latitudes where SRTM data are not available.\n\n" +
				"Ocean data are based on the Smith and Sandwell global 1-minute grid between latitudes +/- 81 degrees. " +
				"Higher resolution grids have been added from the LDEO Ridge Multibeam Synthesis Project, the JAMSTEC " +
				"Data Site for Research Cruises, and the NGDC Coastal Relief Model. Arctic bathymetry is from the " +
				"International Bathymetric Chart of the Oceans (IBCAO) [Jakobsson et al., 2003].";
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
		return TYPE_ELEVATION;
	}

	public String getDataMeasurementType() {
		return TYPE_FLAG_MEASURED;
	}

	public Double getValue(Location loc) throws IOException {
		if (useServlet) {
			return servlet.getValue(loc);
		} else {
			long pos = calc.calcClosestLocationFileIndex(loc);
			
			if (pos < 0 || pos > calc.getMaxFilePos())
				return Double.NaN;
			
			file.seek(pos);
			file.read(recordBuffer);
			
			int val = shortBuff.get(0);
			
			return (double)val;
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
//		SRTM30Topography data = new SRTM30Topography("/home/kevin/data/topo30");
		SRTM30PlusTopography data = new SRTM30PlusTopography();
		
		System.out.println(data.getValue(new Location(34, -118)));
		// top of mammoth
		System.out.println(data.getValue(new Location(37.630173, -119.032681)));
		
//		EvenlyGriddedRectangularGeographicRegion region = new EvenlyGriddedRectangularGeographicRegion(32, 35, -121, -115, 0.02);
//		EvenlyGriddedRectangularGeographicRegion region = new EvenlyGriddedRectangularGeographicRegion(-60, 60, -180, 180, 1);
		
//		SiteDataToXYZ.writeXYZ(data, region, "/tmp/topo2.txt");
	}
}
