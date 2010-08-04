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

package org.opensha.sha.earthquake.rupForecastImpl.GEM;

import java.awt.Color;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.geo.BorderType;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.RegionUtils;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.FaultRuptureSource;
import org.opensha.sha.earthquake.rupForecastImpl.GriddedRegionPoissonEqkSource;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.SingleMagFreqDist;

public class TestGEM_ERF extends EqkRupForecast{


	public static final String NAME = "GEM Test ERF";
	private ArrayList<ProbEqkSource> allSources = null;

	public final static String GRID_SPACING_PARAM_NAME = "Grid Spacing";
	private Double GRID_SPACING_DEFAULT = new Double(0.1);
	private final static String GRID_SPACING_UNITS = "Degrees";
	private final static String GRID_SPACING_INFO = "Grid spacing of source zones";
	private final static double GRID_SPACING_MIN = 0.001;
	private final static double GRID_SPACING_MAX = 1;
	private DoubleParameter gridSpacingParam;


	public final static String MAG_BIN_WIDTH_PARAM_NAME = "Mag Bin Width";
	private Double MAG_BIN_WIDTH_DEFAULT = new Double(0.1);
	private final static String MAG_BIN_WIDTH_UNITS = null;
	private final static String MAG_BIN_WIDTH_INFO = "Discretization of mag-freq distribution";
	private final static double MAG_BIN_WIDTH_MIN = 0.01;
	private final static double MAG_BIN_WIDTH_MAX = 1;
	private DoubleParameter magBinWidthParam;


	// No argument constructor
	public TestGEM_ERF(){

		// create the timespan object with start time and duration in years
		timeSpan = new TimeSpan(TimeSpan.NONE, TimeSpan.YEARS);
		timeSpan.addParameterChangeListener(this);

		initAdjParams();

	}

	// make the adjustable parameters & the list
	private void initAdjParams() {


		gridSpacingParam = new DoubleParameter(GRID_SPACING_PARAM_NAME, GRID_SPACING_MIN,
				GRID_SPACING_MAX, GRID_SPACING_UNITS, GRID_SPACING_DEFAULT);
		gridSpacingParam.setInfo(GRID_SPACING_INFO);

		magBinWidthParam = new DoubleParameter(MAG_BIN_WIDTH_PARAM_NAME, MAG_BIN_WIDTH_MIN,
				MAG_BIN_WIDTH_MAX, MAG_BIN_WIDTH_UNITS, MAG_BIN_WIDTH_DEFAULT);
		magBinWidthParam.setInfo(MAG_BIN_WIDTH_INFO);


		// add adjustable parameters to the list
		adjustableParams.addParameter(gridSpacingParam);
		adjustableParams.addParameter(magBinWidthParam);

	}


	public void updateForecast() {

		// make sure something has changed (e.g., timeSpan)
		if (parameterChangeFlag) {
			//		    	System.out.println("Param changed");

			allSources = new ArrayList<ProbEqkSource>();

			// add fault sources
			allSources.addAll(getFaultSources());

			// add source zones
			String SSZfname = "testSrcZonesData.txt";

			allSources.addAll(getSourceZoneSources(SSZfname));
		}
	}



	private ArrayList<ProbEqkSource> getFaultSources(){
		ArrayList<ProbEqkSource> sources = new ArrayList<ProbEqkSource>();

		// Only one fault source for now (from a USGS Input file
		FaultTrace trace = new FaultTrace("Example fault trace");
		trace.add(new Location(40.26392,75.81272));
		trace.add(new Location(40.17707,75.74847));
		trace.add(new Location(40.10844,75.69968));
		trace.add(new Location(40.04114,75.58109));
		trace.add(new Location(40.01505,75.57042));
		trace.add(new Location(39.93080,75.45937));
		trace.add(new Location(39.78529,75.35471));
		trace.add(new Location(39.66522,75.30668));
		trace.add(new Location(39.52629,75.20238));

		double aveDip=50;
		double downDipWidth=19.58;
		double depthToTop=0;
		double charMag=7.5;
		double charRate=8.3516453E-5;	//
		double rake=90;
		double faultGridSpacing=1;

		// Compute the lower seismogenic depth
		double lowerDepth = depthToTop + downDipWidth * Math.sin(aveDip/180*Math.PI);

		// Compute a gridded fault surface 
		StirlingGriddedSurface surf = new StirlingGriddedSurface(trace,aveDip,depthToTop,lowerDepth,faultGridSpacing);

		SingleMagFreqDist mfd = new SingleMagFreqDist(charMag,2,0.1);
		mfd.setMagAndRate(charMag, charRate);
		//		  double prob = 1-Math.exp(-timeSpan.getDuration()*charRate);

		// Create a FaultRuptureSource object
		FaultRuptureSource source = new FaultRuptureSource(mfd, surf, rake, timeSpan.getDuration());
		source.setName("Example Fault Source");

		// Add source to the source list
		sources.add(source);

		return sources; 
	}


	private ArrayList<ProbEqkSource> getSourceZoneSources(String SSZfname){

		// Get the file lines
		ArrayList<String> fileLines;
		try{
			fileLines= FileUtils.loadFile(this.getClass().getResource(SSZfname));
		} catch(Exception e) {
			throw new RuntimeException(SSZfname+" file Not Found", e);
		}

		// declare data to read
		int numSrces = fileLines.size();
		double[] a = new double[numSrces];		// a value
		double[] b = new double[numSrces];		// a value
		double[] mmin = new double[numSrces];		// a value
		double[] mmax = new double[numSrces];		// a value
		LocationList[] region = new LocationList[numSrces]; // region

		// populate the data
		StringTokenizer st;
		for(int line=0;line<numSrces;line++) {
			st = new StringTokenizer(fileLines.get(line));
			a[line] = Double.valueOf(st.nextToken());
			b[line] = Double.valueOf(st.nextToken());
			mmin[line] = Double.valueOf(st.nextToken());
			mmax[line] = Double.valueOf(st.nextToken());
			LocationList polygon = new LocationList();
			while (st.hasMoreTokens()) {
				double lat = Double.valueOf(st.nextToken());
				double lon = Double.valueOf(st.nextToken());
				polygon.add(new Location(lat,lon));
			}
			region[line] = polygon;
		}

		// now make the sources
		ArrayList<ProbEqkSource> sources = new ArrayList<ProbEqkSource>();
		double gridSpacing = gridSpacingParam.getValue();
		double magBinWidth = magBinWidthParam.getValue();

		// make sources
		for(int i=0;i<numSrces;i++){
			// define polygon region
			GriddedRegion gr = 
				new GriddedRegion(
						region[i], BorderType.MERCATOR_LINEAR, gridSpacing,
						GriddedRegion.ANCHOR_0_0);
			RegionUtils.regionToKML(gr, "gem_gr_new", Color.RED);
			//GriddedRegion gr = new GriddedRegion(region[i],gridSpacing);
			// number of magnitude values
			int mnum = (int) Math.round((mmax[i]-mmin[i])/magBinWidth)+1;
			// GR Dist
			GutenbergRichterMagFreqDist grDist = new GutenbergRichterMagFreqDist(b[i],a[i],mmin[i],mmax[i],mnum);
			// make the source
			GriddedRegionPoissonEqkSource sszEqkSource = new GriddedRegionPoissonEqkSource(gr,grDist,timeSpan.getDuration(),0,90,0.0);
			sources.add(sszEqkSource);
		}

		return sources;
	}



	// number of sources
	public int getNumSources() {
		return allSources.size();
	}

	// return source at index source
	public ProbEqkSource getSource(int source) {
		return allSources.get(source);
	}

	// return list of sources
	public ArrayList getSourceList() {
		return allSources;
	}

	// return name of the class
	public String getName() {
		return NAME;
	}

}
