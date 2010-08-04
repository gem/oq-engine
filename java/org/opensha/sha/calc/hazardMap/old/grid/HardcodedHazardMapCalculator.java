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

package org.opensha.sha.calc.hazardMap.old.grid;

import java.text.DecimalFormat;

import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.region.CaliforniaRegions;
import org.opensha.commons.data.region.SitesInGriddedRegion;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.earthquake.rupForecastImpl.Frankel96.Frankel96_AdjustableEqkRupForecast;
import org.opensha.sha.gui.infoTools.IMT_Info;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.attenRelImpl.CB_2008_AttenRel;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;


/**
 * GridHardcodedHazardMapCalculator
 * 
 * Class to calculate a set of hazard curves from a region as part of a grid hazard map
 * computation. All values except for the start and end indices should be hard coded into
 * this class before distributing to compute nodes.
 * @author kevin
 *
 */
public class HardcodedHazardMapCalculator implements ParameterChangeWarningListener {

	boolean timer = true;
	boolean loadERFFromFile = false;
	boolean lessPrints = false;
	boolean skipPoints = false;
	int skipFactor = 10;

	SitesInGriddedRegion sites;
	int startIndex;
	int endIndex;
	boolean debug;
	// location to store output files if debugging
	static final String DEBUG_RESULT_FOLDER = "/home/kevin/OpenSHA/condor/test_results/";

	boolean useCVM = false;
	String cvmFileName = "";
	
	String outputDir = "";

	/**
	 * Sets variables for calculation of hazard curves in hazard map
	 * @param sites - sites in gridded region
	 * @param startIndex - index  to start at within sites
	 * @param endIndex - index to end at (the very last one is NOT computed)
	 * @param debug - flag to enable debugging mode. if true, the timer and graph window will be enabled
	 * 		if hard coded in.
	 */
	public HardcodedHazardMapCalculator(SitesInGriddedRegion sites, int startIndex, int endIndex, boolean debug) {
		this.sites = sites;
		this.startIndex = startIndex;
		this.endIndex = endIndex;
		this.debug = debug;

		// show timing results if debug mode and timer is selected
		timer = timer & debug;
	}

	public void calculateCurves() {
		long start = 0;
		if (timer) {
			start = System.currentTimeMillis();
		}
		// max cutoff distance for calculator
		double maxDistance =  200.0;
		
		String imt = PGA_Param.NAME;

		// create IMR
		ScalarIntensityMeasureRelationshipAPI imr = new CB_2008_AttenRel(this);
		//AttenuationRelationshipAPI imr = new BJF_1997_AttenRel(this);
		// set the Intensity Measure Type
		imr.setIntensityMeasure(imt);
		// set default parameters
		imr.setParamDefaults();

		// create the ERF
		System.out.println("Creating Forecast");
		EqkRupForecastAPI erf = null;
		if (loadERFFromFile) { // load the ERF from a file with a pre-updated forecast for less overhead
			long start_erf = 0;
			if (timer) {
				start_erf = System.currentTimeMillis();
			}
			erf = (EqkRupForecastAPI)FileUtils.loadObject("erf.obj");
			if (timer) {
				System.out.println("Took " + getTime(start_erf) + " seconds to load ERF.");
			}
		} else { // create a new forecast, but you have to update the forecast
			erf = new Frankel96_AdjustableEqkRupForecast();


//			erf = new MeanUCERF2();
//			ParameterAPI backgroundParam = erf.getAdjustableParameterList().getParameter(UCERF2.BACK_SEIS_NAME);
//			backgroundParam.setValue(UCERF2.BACK_SEIS_INCLUDE);
//			System.out.println("Background Seismicity: " + backgroundParam.getValue());


//			erf = new Frankel02_AdjustableEqkRupForecast();
//			ParameterAPI backgroundParam = erf.getAdjustableParameterList().getParameter(Frankel02_AdjustableEqkRupForecast.BACK_SEIS_NAME);
//			backgroundParam.setValue(Frankel02_AdjustableEqkRupForecast.BACK_SEIS_INCLUDE);
//			System.out.println("Background Seismicity: " + backgroundParam.getValue());


			System.out.println("Updating Forecast");
			long start_erf = 0;
			if (timer) {
				start_erf = System.currentTimeMillis();
			}

			// update the forecast
			TimeSpan time = new TimeSpan(TimeSpan.YEARS, TimeSpan.YEARS);
			time.setStartTime(2007);
			time.setDuration(50);
			erf.setTimeSpan(time);
			erf.updateForecast();
			if (timer) {
				System.out.println("Took " + getTime(start_erf) + " seconds to update forecast.");
			}
		}
		
		IMT_Info imtInfo = new IMT_Info();
		// get the default function for the specified IMT
		ArbitrarilyDiscretizedFunc hazFunction = imtInfo.getDefaultHazardCurve(imr.getIntensityMeasure().getName());
		
		HazardMapPortionCalculator calculator = new HazardMapPortionCalculator(sites, erf, imr, hazFunction, null, maxDistance, outputDir);
		
		calculator.setTimer(timer);
		calculator.setLessPrints(lessPrints);
		calculator.setSkipPoints(skipPoints);
		calculator.setSkipFactor(skipFactor);
		
		if (timer) {
			System.out.println(getTime(start) + " seconds total pre-calculator overhead");
		}
		
		calculator.calculateCurves(startIndex, endIndex);
	}

	/**
	 * Calculate and format the time from 'before'
	 * @param before - currentTimeMillis that should be counted from
	 * @return string in seconds of elapsed time
	 */
	public String getTime(long before) {
		double time = ((double)System.currentTimeMillis() - (double)before)/1000d; 
		return new DecimalFormat(	"###.##").format(time);
	}

	public void parameterChangeWarning(ParameterChangeWarningEvent event) {}

	/**
	 * Main class to calculate hazard curves. If there are less than 2 arguments, it is considered to be
	 * a test and timing messages will be displayed along with a graph window for the first 10 curves.
	 * Otherwise, the first argument is the start index for the site and the sedond argument is the end
	 * index.
	 * @param args: startIndex endIndex
	 */
	public static void main(String[] args) {
		long start = System.currentTimeMillis();

		// create site object
		//Region region = new RELM_TestingRegion();
//		Region region = new EvenlyGriddedCaliforniaRegion();
//		Region region = new EvenlyGriddedSoCalRegion();

		//double gridSpacing = 0.1;

//		GriddedRegion eggr = new GriddedRegion(
//				region.getRegionOutline(), BorderType.MERCATOR_LINEAR, gridSpacing);
		GriddedRegion eggr = 
			new CaliforniaRegions.RELM_TESTING_GRIDDED();
		
		SitesInGriddedRegion sites = new SitesInGriddedRegion(eggr);

//		SitesInGriddedRegionAPI sites = null;
//		try {
//			sites = new SitesInGriddedRectangularRegion(33.5, 34.8, -120.0, -116.0, gridSpacing);
//		} catch (RegionConstraintException e1) {
//			e1.printStackTrace();
//		}

		sites.setSameSiteParams();
		//SitesInGriddedRegionAPI sites = new CustomSitesInGriddedRegion(region.getGridLocationsList(), 1);

		if (args.length >= 2) { // this is from the command line and is real
			// get start and end index of sites to do within region from command line
			int startIndex = Integer.parseInt(args[0]);
			int endIndex = Integer.parseInt(args[1]);
			try {
				// run the calculator with debugging disabled
				HardcodedHazardMapCalculator calc = new HardcodedHazardMapCalculator(sites, startIndex, endIndex, false);
				if (args.length >=3) {
					try {
						boolean timer = Boolean.parseBoolean(args[2]);
						calc.timer = timer;
					} catch (RuntimeException e) {
						System.err.println("BAD BOOLEAN PARSE!");
					}
				}
				if (args.length >=4) {
					if (args[3].toLowerCase().contains("cvm")) {
						calc.useCVM = true;
						calc.cvmFileName = args[3];
						calc.skipPoints = false;
					} else {
						calc.useCVM = false;
						try {
							int skip = Integer.parseInt(args[3]);
							if (skip > 1) {
								calc.skipPoints = true;
								calc.skipFactor = skip;
							}
							//calc.timer = timer;
						} catch (RuntimeException e) {
							System.err.println("BAD SKIP INT PARSE");
							calc.skipPoints = false;
						}
					}
				}
				calc.loadERFFromFile = true;
				calc.calculateCurves();
				System.out.println("Total execution time: " + calc.getTime(start));
			} catch (RuntimeException e) {
				// something bad happened, exit with code 1
				e.printStackTrace();
				System.exit(1);
			}
			// exit without error
			System.exit(0);
		} else { // this is just a test
			// hard coded indices
			int startIndex = 0;
			int endIndex = 10;
			System.out.println("Doing sites " + startIndex + " to " + endIndex + " of " + sites.getRegion().getNodeCount());
			try {
				System.err.println("RUNNING FROM DEBUG MODE!");
				// run the calculator with debugging enabled
				HardcodedHazardMapCalculator calc = new HardcodedHazardMapCalculator(sites, startIndex, endIndex, true);
				calc.timer = true;
				calc.lessPrints = false;
				calc.loadERFFromFile = false;
				calc.skipPoints = false;
				calc.skipFactor = 200;
				calc.useCVM = false;
				//calc.cvmFileName = "/home/kevin/OpenSHA/condor/RELM_0.1.cvm";
				calc.cvmFileName = "/home/kevin/OpenSHA/condor/jobs/jobTest/000100_000200.cvm";
				calc.outputDir = HardcodedHazardMapCalculator.DEBUG_RESULT_FOLDER;
				calc.calculateCurves();
				System.out.println("Total execution time: " + calc.getTime(start));
				// if nothing was calculated, just exit
				System.exit(0);
			} catch (Exception e) {
				// something bad happened, exit with code 1
				e.printStackTrace();
				System.exit(1);
			}
		}
	}

}
