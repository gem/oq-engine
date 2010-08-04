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

package org.opensha.sha.earthquake.rupForecastImpl.YuccaMountain;


import java.io.IOException;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.FaultRuptureSource;
import org.opensha.sha.earthquake.rupForecastImpl.GriddedRegionPoissonEqkSource;
import org.opensha.sha.faultSurface.EvenlyGriddedSurface;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;
import org.opensha.sha.magdist.GaussianMagFreqDist;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;

public class YuccaMountainERF extends EqkRupForecast{

	//for Debug purposes
	private static String  C = new String("YuccaMountainERF");
	private boolean D = false;
	// name of this ERF
	public final static String NAME = new String("Yucca mountain Adj. ERF");


	private final static String FAULT_SOURCE_FILENAME = "org/opensha/sha/earthquake/rupForecastImpl/YuccaMountain/FAULTmodelYM.txt";
	private final static String BG_FILE_NAME = "org/opensha/sha/earthquake/rupForecastImpl/YuccaMountain/BACKGROUNDmodelYM.txt";

	// Min/Max/Num Mags for Mag Freq Dist for making fault sources
	private final static double MIN_MAG = 5.5;
	private final static double MAX_MAG = 8.5;
	private final static int NUM_MAGS = 31;

	// Default Grid Spacing for making Evenly Gridded Surface
	private final static double DEFAULT_GRID_SPACING = 1.0;


	public final static String BACK_SEIS_NAME = new String ("Background Seismicity");
	public final static String BACK_SEIS_INCLUDE = new String ("Include");
	public final static String BACK_SEIS_EXCLUDE = new String ("Exclude");
	private StringParameter backSeisParam;


	private ArrayList<String> sourceNames = new ArrayList<String>();
	private ArrayList<Double> sourceMags = new ArrayList<Double>();
	private ArrayList<Double> sourceSigmas = new ArrayList<Double>();
	private ArrayList<Double> sourceRakes = new ArrayList<Double>();
	private ArrayList<Double> sourceMoRates = new ArrayList<Double>();
	private ArrayList<EvenlyGriddedSurface> sourceGriddedSurface = new ArrayList<EvenlyGriddedSurface>();

	private ArrayList<ProbEqkSource> allSources;
	private GutenbergRichterMagFreqDist backgroundMagDist;
	private GriddedRegion backgroundRegion;

	public YuccaMountainERF(){

		createFaultSurfaces();
		mkBackRegion();
		initAdjParams();

		//create the timespan object with start time and duration in years
		timeSpan = new TimeSpan(TimeSpan.NONE,TimeSpan.YEARS);
		timeSpan.addParameterChangeListener(this);
		timeSpan.setDuration(50);

	}


	/*
	 * Initialize the adjustable parameters
	 */
	private void initAdjParams(){	

		ArrayList<String> backSeisOptionsStrings = new ArrayList<String>();
		backSeisOptionsStrings.add(BACK_SEIS_INCLUDE);
		backSeisOptionsStrings.add(BACK_SEIS_EXCLUDE);

		backSeisParam = new StringParameter(BACK_SEIS_NAME,backSeisOptionsStrings,BACK_SEIS_INCLUDE);
		backSeisParam.addParameterChangeListener(this);

		adjustableParams.addParameter(backSeisParam);
	}


	/**
	 * Make Background sources
	 */

	private void mkBackRegion(){
		try {
			ArrayList<String> fileLines = FileUtils.loadJarFile(BG_FILE_NAME);
			int i=5;
			String sourceName = fileLines.get(i);

			StringTokenizer st = new StringTokenizer(sourceName);
			String srcCode = st.nextToken();
			int srcCodeLength = srcCode.length();
			String sourceNameString = sourceName.substring(srcCodeLength);
			++i;
			String magDistInfo  = fileLines.get(i);
			st = new StringTokenizer(magDistInfo);
			double aVal = Double.parseDouble(st.nextToken().trim());
			double uncertainity = Double.parseDouble(st.nextToken().trim());
			double bVal = Double.parseDouble(st.nextToken().trim());
			double sigma = Double.parseDouble(st.nextToken().trim());
			double minMag = Double.parseDouble(st.nextToken().trim());
			double maxMag = Double.parseDouble(st.nextToken().trim());
			int numMag = Integer.parseInt(st.nextToken().trim());
			double totCumRate = Double.parseDouble(st.nextToken().trim());
			backgroundMagDist = new GutenbergRichterMagFreqDist(bVal,totCumRate,minMag,maxMag,numMag);
			++i;
			String regionInfo = fileLines.get(i);
			st = new StringTokenizer(regionInfo);
			double minLat = Double.parseDouble(st.nextToken().trim());
			double maxLat = Double.parseDouble(st.nextToken().trim());
			double minLon = Double.parseDouble(st.nextToken().trim());
			double maxLon = Double.parseDouble(st.nextToken().trim());
			double gridSpacing = Double.parseDouble(st.nextToken().trim());
//			try {
//				backgroundRegion = new GriddedRegion(minLat, 
//						maxLat, minLon, maxLon, gridSpacing);
			    backgroundRegion = new GriddedRegion(
			    		new Location(minLat, minLon),
			    		new Location(maxLat, maxLon),
			    		gridSpacing, new Location(0,0));
//			} catch (RegionConstraintException e) {
//				// TODO Auto-generated catch block
//				e.printStackTrace();
//			}


		}catch(IOException e){
			e.printStackTrace();
		}
	}


	/**
	 * Set Mean Mag for a fault source
	 * 
	 * @param sourceName
	 * @param mag
	 */
	public void setMeanMagForSource(String sourceName, double mag) {
		int srcIndex = sourceNames.indexOf(sourceName);
		this.sourceMags.set(srcIndex, mag);
		parameterChangeFlag = true;
	}

	/**
	 * Set Moment Rate for a fault source
	 * 
	 * @param sourceName
	 * @param momentRate
	 */
	public void setMomentRateForSource(String sourceName, double momentRate) {
		int srcIndex = sourceNames.indexOf(sourceName);
		this.sourceMoRates.set(srcIndex, momentRate);
		parameterChangeFlag = true;
	}
	
	/**
	 * Set background MFD
	 *  
	 * @param backgroundMagDist
	 */
	public void setBackgroundMFD(GutenbergRichterMagFreqDist backgroundMagDist) {
		this.backgroundMagDist = backgroundMagDist;
	}

	
	/**
	 * Read the file and create fault surfaces
	 *
	 */
	private void createFaultSurfaces(){
		try {
			ArrayList<String> fileLines = FileUtils.loadJarFile(FAULT_SOURCE_FILENAME);
			int size = fileLines.size();
			for(int i=6;i<size;++i){ 
				String sourceName = fileLines.get(i);
				if(sourceName.trim().equals(""))
					continue;
				StringTokenizer st = new StringTokenizer(sourceName);
				String srcCode = st.nextToken();
				++i;
				String sourceDipInfo = fileLines.get(i);
				st = new StringTokenizer(sourceDipInfo);
				double dip = Double.parseDouble(st.nextToken().trim());
				double strike = Double.parseDouble(st.nextToken().trim());
				double rake = Double.parseDouble(st.nextToken().trim());
				double upperSeis = Double.parseDouble(st.nextToken().trim());
				double lowerSeis = Double.parseDouble(st.nextToken().trim());
				++i;
				String sourceMFD = fileLines.get(i);
				st = new StringTokenizer(sourceMFD);
				double meanMag = Double.parseDouble(st.nextToken().trim());
				double sigma = Double.parseDouble(st.nextToken().trim());
				double seisMomentRate = Double.parseDouble(st.nextToken().trim());
				++i;
				int numSourceLocations = Integer.parseInt(fileLines.get(i));
				FaultTrace fltTrace = new FaultTrace(srcCode);
				int numLinesDone = i;
				for(i=i+1;i<=(numLinesDone+numSourceLocations);++i){
					String location = fileLines.get(i);
					st = new StringTokenizer(location);
					double lon = Double.parseDouble(st.nextToken().trim());
					double lat = Double.parseDouble(st.nextToken().trim());
					fltTrace.add(new Location(lat,lon));
				}
				--i;
				EvenlyGriddedSurface surface = new StirlingGriddedSurface(fltTrace, dip,upperSeis,lowerSeis,DEFAULT_GRID_SPACING);
				sourceNames.add(srcCode);
				this.sourceMags.add(meanMag);
				this.sourceMoRates.add(seisMomentRate);
				this.sourceRakes.add(rake);
				this.sourceSigmas.add(sigma);
				this.sourceGriddedSurface.add(surface);
			}
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}

	}

	/**
	 * Make Fault Sources
	 *
	 */
	private void mkFaultSources() {
		for(int srcIndex=0; srcIndex<sourceNames.size(); ++srcIndex) {
			EvenlyGriddedSurface surface = this.sourceGriddedSurface.get(srcIndex);
			IncrementalMagFreqDist magDist = new GaussianMagFreqDist(MIN_MAG, MAX_MAG, NUM_MAGS,
					this.sourceMags.get(srcIndex), this.sourceSigmas.get(srcIndex), 
					this.sourceMoRates.get(srcIndex));
			FaultRuptureSource rupSource = new FaultRuptureSource(magDist,surface,sourceRakes.get(srcIndex),timeSpan.getDuration());
			rupSource.setName(sourceNames.get(srcIndex));
			allSources.add(rupSource);
		}

	}

	/**
	 *  This is the main function of this interface. Any time a control
	 *  paramater or independent paramater is changed by the user in a GUI this
	 *  function is called, and a paramater change event is passed in.
	 *
	 *  This sets the flag to indicate that the sources need to be updated
	 *
	 * @param  event
	 */
	public void parameterChange(ParameterChangeEvent event) {
		this.parameterChangeFlag = true;
	}

	@Override
	public int getNumSources() {
		return allSources.size();
	}

	@Override
	public ProbEqkSource getSource(int source) {
		// TODO Auto-generated method stub
		return (ProbEqkSource)allSources.get(source);
	}

	@Override
	public ArrayList getSourceList() {
		// TODO Auto-generated method stub
		return allSources;
	}

	public String getName() {
		// TODO Auto-generated method stub
		return NAME;
	}

	/**
	 * Update the fault Sources with the change in duration.
	 */
	public void updateForecast() {
		// make sure something has changed
		if(parameterChangeFlag) {
			allSources = new ArrayList<ProbEqkSource>();
			mkFaultSources();
			String bgVal = (String)backSeisParam.getValue();
			if(bgVal.equals(BACK_SEIS_INCLUDE)){
				GriddedRegionPoissonEqkSource grSource = new GriddedRegionPoissonEqkSource(this.backgroundRegion,
						backgroundMagDist,
						timeSpan.getDuration(), -90.0, 60, this.backgroundMagDist.getMagLower());
				this.allSources.add(grSource);

			}
		}
		parameterChangeFlag = false;
	}


}
