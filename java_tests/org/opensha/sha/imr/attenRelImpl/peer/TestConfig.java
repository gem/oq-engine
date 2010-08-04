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

package org.opensha.sha.imr.attenRelImpl.peer;

import static org.opensha.sha.param.MagFreqDistParameter.*;

import static org.opensha.sha.imr.attenRelImpl.peer.TestSet.*;
import static org.opensha.sha.imr.attenRelImpl.peer.TestCase.*;
import static org.opensha.sha.imr.attenRelImpl.peer.TestSite.*;

import java.util.ArrayList;

import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.PEER_testsMagAreaRelationship;
import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.geo.Location;
import org.opensha.commons.param.ParameterList;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.rupForecastImpl.FloatingPoissonFaultERF;
import org.opensha.sha.earthquake.rupForecastImpl.PEER_TestCases.PEER_AreaForecast;
import org.opensha.sha.earthquake.rupForecastImpl.PEER_TestCases.PEER_MultiSourceForecast;
import org.opensha.sha.earthquake.rupForecastImpl.PEER_TestCases.PEER_NonPlanarFaultForecast;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.attenRelImpl.AS_1997_AttenRel;
import org.opensha.sha.imr.attenRelImpl.Campbell_1997_AttenRel;
import org.opensha.sha.imr.attenRelImpl.SadighEtAl_1997_AttenRel;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncLevelParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncTypeParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.magdist.GaussianMagFreqDist;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.SingleMagFreqDist;
import org.opensha.sha.magdist.YC_1985_CharMagFreqDist;
import org.opensha.sha.param.MagFreqDistParameter;
import org.opensha.sha.param.SimpleFaultParameter;

public class TestConfig {

	// maximum permitted distance between fault and site to consider source in
	// hazard analysis for that site; this default value is to allow all PEER
	// test cases to pass through
	public static double MAX_DISTANCE = 300;
	
	private AttenuationRelationship imr;
	private Site site;
	private EqkRupForecast erf;
	private ArbitrarilyDiscretizedFunc function;

	// Stores the test case,
	private TestCase selectedCase;
	private TestSite selectedSite;
	private TestSet selectedSet;
	
	// Test set descriptors
	private static ArrayList<PeerTest> desc1;
	private static ArrayList<PeerTest> desc2;

	// lats, lons, dips, and depths of the faults used in the
	// FloatingPoissonFaultERF
	private ArrayList<Double> fault1and2_Lats;
	private ArrayList<Double> fault1and2_Lons;
	private ArrayList<Double> fault1_Dips;
	private ArrayList<Double> fault2_Dips;
	private ArrayList<Double> fault1_Depths;
	private ArrayList<Double> fault2_Depths;
	private ArrayList<Double> faultE_Lats;
	private ArrayList<Double> faultE_Lons;
	private ArrayList<Double> faultE_Dips;
	private ArrayList<Double> faultE_Depths;

	// X Values for the PEER hazard curves
	private static double[] xVals = {
		0.001, 
		0.01, 
		0.05, 
		0.1, 
		0.15, 
		0.2, 
		0.25, 
		0.3, 
		0.35, 
		0.4, 
		0.45, 
		0.5,
		0.55, 
		0.6, 
		0.7, 
		0.8, 
		0.9, 
		1.0 };

	public TestConfig(PeerTest test) {
		selectedSet = test.getSet();
		selectedCase = test.getCase();
		selectedSite = test.getSite();
		initFaultData();
		initFunction();
		initTest();
	}

	public AttenuationRelationship getIMR() {
		return imr;
	}
	
	public Site getSite() {
		return site;
	}
	
	public EqkRupForecast getERF() {
		return erf;
	}
	
	public ArbitrarilyDiscretizedFunc getFunction() {
		return function;
	}
	
	private void initTest() {
		site = new Site();
		if (is(SET_1)) {
			init_Set1();
		} else if (is(SET_2)) {
			init_Set2();
		}
	}

	// sets the parameter values for the selected test cases in Set-1
	private void init_Set1() {

		// *****************************************************
		// ****** Set the IMR, IMT, & Site-Related Params ******
		// ******          (except lat and lon)           ******
		// *****************************************************
		
		// the following settings apply to most test cases; 
		// these are subsequently overridded where needed below
		imr = new SadighEtAl_1997_AttenRel(null);
		imr.setParamDefaults();
		imr.getParameter(SigmaTruncTypeParam.NAME).setValue(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_NONE);
		imr.getParameter(StdDevTypeParam.NAME).setValue(StdDevTypeParam.STD_DEV_TYPE_NONE);
		imr.setIntensityMeasure(PGA_Param.NAME);
		
		site.addParameter(imr.getParameter(SadighEtAl_1997_AttenRel.SITE_TYPE_NAME));
		site.setValue(SadighEtAl_1997_AttenRel.SITE_TYPE_NAME, SadighEtAl_1997_AttenRel.SITE_TYPE_ROCK);
		
		if (is(CASE_8A)) {
			imr.getParameter(SigmaTruncTypeParam.NAME).setValue(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_NONE);
			imr.getParameter(StdDevTypeParam.NAME).setValue(StdDevTypeParam.STD_DEV_TYPE_TOTAL);
			imr.setIntensityMeasure(PGA_Param.NAME);  // needed because IMT gets reset to SA afer the above
			// NOTE: I don't think the above comment applies now that tests
			// are not gui based -- powers
		
		} else if (is(CASE_8B)) {
			imr.getParameter(SigmaTruncTypeParam.NAME).setValue(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_1SIDED);
			imr.getParameter(SigmaTruncLevelParam.NAME).setValue(new Double(2.0));
			imr.getParameter(StdDevTypeParam.NAME).setValue(StdDevTypeParam.STD_DEV_TYPE_TOTAL);
			imr.setIntensityMeasure(PGA_Param.NAME);  // needed because IMT gets reset to SA afer the above
		
		} else if (is(CASE_8C)) {
			imr.getParameter(SigmaTruncTypeParam.NAME).setValue(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_1SIDED);
			imr.getParameter(SigmaTruncLevelParam.NAME).setValue(new Double(3.0));
			imr.getParameter(StdDevTypeParam.NAME).setValue(StdDevTypeParam.STD_DEV_TYPE_TOTAL);
			imr.setIntensityMeasure(PGA_Param.NAME);  // needed because IMT gets reset to SA afer the above
		
		} else if (is(CASE_9A)) {
			imr = new SadighEtAl_1997_AttenRel(null);
			imr.setParamDefaults();
			imr.getParameter(SigmaTruncTypeParam.NAME).setValue(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_1SIDED);
			imr.getParameter(SigmaTruncLevelParam.NAME).setValue(new Double(3.0));
			imr.getParameter(StdDevTypeParam.NAME).setValue(StdDevTypeParam.STD_DEV_TYPE_TOTAL);
			imr.setIntensityMeasure(PGA_Param.NAME);

		} else if (is(CASE_9B)){
			imr = new AS_1997_AttenRel(null);
			imr.setParamDefaults();
			imr.getParameter(SigmaTruncTypeParam.NAME).setValue(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_NONE);
			imr.getParameter(SigmaTruncLevelParam.NAME).setValue(new Double(3.0)); // this shouldn't matter
			imr.getParameter(StdDevTypeParam.NAME).setValue(StdDevTypeParam.STD_DEV_TYPE_NONE);
			imr.setIntensityMeasure(PGA_Param.NAME);
			
			site.addParameter(imr.getParameter(AS_1997_AttenRel.SITE_TYPE_NAME));
			site.setValue(AS_1997_AttenRel.SITE_TYPE_NAME, AS_1997_AttenRel.SITE_TYPE_ROCK);

		} else if (is(CASE_9C)){
			imr = new Campbell_1997_AttenRel(null);
			imr.setParamDefaults();
			imr.getParameter(SigmaTruncTypeParam.NAME).setValue(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_1SIDED);
			imr.getParameter(SigmaTruncLevelParam.NAME).setValue(new Double(3.0));
			imr.getParameter(StdDevTypeParam.NAME).setValue(StdDevTypeParam.STD_DEV_TYPE_TOTAL_PGA_DEP);
			imr.setIntensityMeasure(PGA_Param.NAME);
			
			site.addParameter(imr.getParameter(Campbell_1997_AttenRel.SITE_TYPE_NAME));
			site.setValue(Campbell_1997_AttenRel.SITE_TYPE_NAME, Campbell_1997_AttenRel.SITE_TYPE_SOFT_ROCK);
			site.addParameter(imr.getParameter(Campbell_1997_AttenRel.BASIN_DEPTH_NAME));
			site.setValue(Campbell_1997_AttenRel.BASIN_DEPTH_NAME, new Double(2.0));

		} else if (is(CASE_12)){
			imr.getParameter(SigmaTruncTypeParam.NAME).setValue(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_1SIDED);
			imr.getParameter(SigmaTruncLevelParam.NAME).setValue(new Double(3.0));
			imr.getParameter(StdDevTypeParam.NAME).setValue(StdDevTypeParam.STD_DEV_TYPE_TOTAL);
			imr.setIntensityMeasure(PGA_Param.NAME);  // needed because IMT gets reset to SA afer the above
		}

		// *****************************************************
		// ******         Set the ERF parameters         *******
		// *****************************************************
		
		// if it's one of the "PEER fault" problems (cases 1-9 or 12)
		if (!is(CASE_10) && !is(CASE_11)) {

			erf = new FloatingPoissonFaultERF();
		
			// set offset and fault grid spacing (these were determined by trial and error)
			double gridSpacing;
			if (is(CASE_1) || is(CASE_2) || is(CASE_4) || is(CASE_9B) ) {
				gridSpacing = 0.05;
		   
			} else if (is(CASE_3)) {
				gridSpacing = 0.25;
		   
			} else {
				gridSpacing = 0.5;
			}
		
			// set the special cases (improvements found by hand using GUI -NF)
			if (is(CASE_8C) && is(SITE_5)) {
				gridSpacing = 0.05;
			}
			if (is(CASE_9C) && is(SITE_7)) {
				gridSpacing = 0.1;
			}
			if (is(CASE_2) && (is(SITE_1) || is(SITE_4) || is(SITE_6))) {
				gridSpacing = 0.025;
			}

			// set the common parameters like timespan
			erf.getParameter(FloatingPoissonFaultERF.OFFSET_PARAM_NAME).setValue(new Double(gridSpacing));
			erf.getParameter(FloatingPoissonFaultERF.MAG_SCALING_REL_PARAM_NAME).setValue(PEER_testsMagAreaRelationship.NAME);
			erf.getParameter(FloatingPoissonFaultERF.SIGMA_PARAM_NAME).setValue(new Double(0));
			erf.getParameter(FloatingPoissonFaultERF.ASPECT_RATIO_PARAM_NAME).setValue(new Double(2.0));
			erf.getParameter(FloatingPoissonFaultERF.MIN_MAG_PARAM_NAME).setValue(new Double(5.0));
			erf.getTimeSpan().setDuration(1.0);

			// magScalingSigma parameter is changed if the test case chosen is 3
			if (is(CASE_3)) {
				erf.getParameter(FloatingPoissonFaultERF.SIGMA_PARAM_NAME).setValue(new Double(0.25));
			}

			// set the rake for all cases
			if (is(CASE_4) || is(CASE_9A) || is(CASE_9B) || is(CASE_9C) ) {
				erf.getParameter(FloatingPoissonFaultERF.RAKE_PARAM_NAME).setValue(new Double(90.0));
			
			} else {
				erf.getParameter(FloatingPoissonFaultERF.RAKE_PARAM_NAME).setValue(new Double(0.0));
			}

			// set the Fault Parameter
			SimpleFaultParameter fault = (SimpleFaultParameter) erf.getParameter(FloatingPoissonFaultERF.FAULT_PARAM_NAME);
			if (is(CASE_4) || is(CASE_9A) || is(CASE_9B) || is(CASE_9C) ) {
				fault.setAll(gridSpacing,fault1and2_Lats,fault1and2_Lons,fault2_Dips,fault2_Depths,SimpleFaultParameter.STIRLING);
			
			} else {
				fault.setAll(gridSpacing,fault1and2_Lats,fault1and2_Lons,fault1_Dips,fault1_Depths,SimpleFaultParameter.STIRLING);
			}
			
			fault.setEvenlyGriddedSurfaceFromParams();
			
		// it's an area ERF (case 10 or 11)
		} else {
			erf = new PEER_AreaForecast();
			erf.getParameter(PEER_AreaForecast.DEPTH_UPPER_PARAM_NAME).setValue(new Double(5));
			erf.getParameter(PEER_AreaForecast.DIP_PARAM_NAME).setValue(new Double(90));
			erf.getParameter(PEER_AreaForecast.RAKE_PARAM_NAME).setValue(new Double(0));
			erf.getTimeSpan().setDuration(1.0);

			if (is(CASE_10)) {
				erf.getParameter(PEER_AreaForecast.DEPTH_LOWER_PARAM_NAME).setValue(new Double(5));
				erf.getParameter(PEER_AreaForecast.GRID_PARAM_NAME).setValue(new Double(1.0));
			
			} else {
				erf.getParameter(PEER_AreaForecast.DEPTH_LOWER_PARAM_NAME).setValue(new Double(10));
				
				// NOTE Case_11 grid spacing had been set to 0.25 km which
				// yields a better result, but which takes an exorbitant
				// amount of time and can lead to uncaught OutOfMemoryErrors
				// in multi-threaded test runs.
				
				//erf.getParameter(PEER_AreaForecast.GRID_PARAM_NAME).setValue(new Double(0.25));   	 
				erf.getParameter(PEER_AreaForecast.GRID_PARAM_NAME).setValue(new Double(1.0));   	 
			}
		}
		
		// *****************************************************
		// ****** Set the magFreqDist params separately  *******
		// *****************************************************
		initMFD_Set1();

		// and update
		erf.updateForecast();
		
		

		// *****************************************************
		// ******           Set Site lat & lon           *******
		// *****************************************************

		if (!is(CASE_10) && !is(CASE_11)) { // for fault sites

			if (is(SITE_1)) {
				site.setLocation(new Location(38.113,-122.000));
			
			} else if (is(SITE_2)) {
				site.setLocation(new Location(38.113,-122.114));

			} else if (is(SITE_3)) {
				site.setLocation(new Location(38.111,-122.570));

			} else if (is(SITE_4)) {
				site.setLocation(new Location(38.000,-122.000));

			} else if (is(SITE_5)) {
				site.setLocation(new Location(37.910,-122.000));

			} else if (is(SITE_6)) {
				site.setLocation(new Location(38.225,-122.000));

			} else if (is(SITE_7)) {
				site.setLocation(new Location(38.113,-121.886));
			}
			
		} else { // for area sites

			if (is(SITE_1)) {
				site.setLocation(new Location(38.000,-122.000));
			
			} else if (is(SITE_2)) {
				site.setLocation(new Location(37.550,-122.000));

			} else if (is(SITE_3)) {
				site.setLocation(new Location(37.099,-122.000));

			} else if (is(SITE_4)) {
				site.setLocation(new Location(36.875,-122.000));
			}
		}
	}

	// Sets the default magdist values for Set-1
	private void initMFD_Set1() {

		// NOTE kinda klunky; each time the mfd is set, the fix and all_but
		// constraints need to be updated manually; too much info encapsulated
		// in mfd param???
		
		MagFreqDistParameter mfd;
		ParameterList plist;
		
		if (!is(CASE_10) && !is(CASE_11)) {
			mfd = (MagFreqDistParameter) erf.getParameter(FloatingPoissonFaultERF.MAG_DIST_PARAM_NAME);
			plist = mfd.getAdjustableParams();
		} else {
			mfd = (MagFreqDistParameter) erf.getParameter(PEER_AreaForecast.MAG_DIST_PARAM_NAME);
			plist = mfd.getAdjustableParams();
		}
		
		// these apply to most (overridden below where not)
		plist.getParameter(MIN).setValue(new Double(6));
		plist.getParameter(MAX).setValue(new Double(6.5));
		plist.getParameter(NUM).setValue(new Integer(6));

		if (is(CASE_1) || is(CASE_12)) {
			plist.getParameter(DISTRIBUTION_NAME).setValue(SingleMagFreqDist.NAME);
			plist.getParameter(FIX).setConstraint(mfd.getSingleDistFixOptions());
			plist.getParameter(SINGLE_PARAMS_TO_SET).setValue(MagFreqDistParameter.MAG_AND_MO_RATE);
			plist.getParameter(MAG).setValue(new Double(6.5));
			plist.getParameter(MO_RATE).setValue(new Double(1.8e16));
		
		} else if (is(CASE_2)) {
			plist.getParameter(DISTRIBUTION_NAME).setValue(SingleMagFreqDist.NAME);
			plist.getParameter(FIX).setConstraint(mfd.getSingleDistFixOptions());
			plist.getParameter(SINGLE_PARAMS_TO_SET).setValue(MagFreqDistParameter.MAG_AND_MO_RATE);
			plist.getParameter(MAG).setValue(new Double(6.0));
			plist.getParameter(MO_RATE).setValue(new Double(1.8e16));
		
		} else if (is(CASE_3)) {
			plist.getParameter(DISTRIBUTION_NAME).setValue(SingleMagFreqDist.NAME);
			plist.getParameter(FIX).setConstraint(mfd.getSingleDistFixOptions());
			plist.getParameter(SINGLE_PARAMS_TO_SET).setValue(MagFreqDistParameter.MAG_AND_MO_RATE);
			plist.getParameter(MAG).setValue(new Double(6.0));
			plist.getParameter(MO_RATE).setValue(new Double(1.8e16));
		
		} else if (is(CASE_4)) {
			plist.getParameter(DISTRIBUTION_NAME).setValue(SingleMagFreqDist.NAME);
			plist.getParameter(FIX).setConstraint(mfd.getSingleDistFixOptions());
			plist.getParameter(SINGLE_PARAMS_TO_SET).setValue(MagFreqDistParameter.MAG_AND_MO_RATE);
			plist.getParameter(MAG).setValue(new Double(6.0));
			plist.getParameter(MO_RATE).setValue(new Double(1.905e16));

		} else if (is(CASE_5)) {
			plist.getParameter(DISTRIBUTION_NAME).setValue(GutenbergRichterMagFreqDist.NAME);
			plist.getParameter(SET_ALL_PARAMS_BUT).setConstraint(mfd.getGRSetAllButOptions());
			plist.getParameter(FIX).setConstraint(mfd.getGRFixOptions());
			plist.getParameter(MIN).setValue(new Double(0.005));
			plist.getParameter(MAX).setValue(new Double(9.995));
			plist.getParameter(NUM).setValue(new Integer(1000));
			plist.getParameter(SET_ALL_PARAMS_BUT).setValue(MagFreqDistParameter.TOT_CUM_RATE);
			plist.getParameter(GR_MAG_LOWER).setValue(new Double(0.005));
			plist.getParameter(GR_MAG_UPPER).setValue(new Double(6.495));
			plist.getParameter(GR_BVALUE).setValue(new Double(0.9));
			plist.getParameter(TOT_MO_RATE).setValue(new Double(1.8e16));
			plist.getParameter(SET_ALL_PARAMS_BUT).setValue(MagFreqDistParameter.TOT_CUM_RATE);

		} else if (is(CASE_6)) {
			plist.getParameter(DISTRIBUTION_NAME).setValue(GaussianMagFreqDist.NAME);
			plist.getParameter(SET_ALL_PARAMS_BUT).setConstraint(mfd.getGaussianDistSetAllButOptions());
			plist.getParameter(MIN).setValue(new Double(0.005));
			plist.getParameter(MAX).setValue(new Double(9.995));
			plist.getParameter(NUM).setValue(new Integer(1000));
			plist.getParameter(SET_ALL_PARAMS_BUT).setValue(MagFreqDistParameter.TOT_CUM_RATE);
			plist.getParameter(TOT_MO_RATE).setValue(new Double(1.8e16));
			plist.getParameter(STD_DEV).setValue(new Double(0.25));
			plist.getParameter(MEAN).setValue(new Double(6.2));
			plist.getParameter(TRUNCATION_REQ).setValue(MagFreqDistParameter.TRUNCATE_UPPER_ONLY);
			plist.getParameter(TRUNCATE_NUM_OF_STD_DEV).setValue(new Double(1.19));

		} else if (is(CASE_7)) {
			plist.getParameter(DISTRIBUTION_NAME).setValue(YC_1985_CharMagFreqDist.NAME);
			plist.getParameter(SET_ALL_PARAMS_BUT).setConstraint(mfd.getYCSetAllButOptions());
			plist.getParameter(MIN).setValue(new Double(0.005));
			plist.getParameter(MAX).setValue(new Double(10.005));
			plist.getParameter(NUM).setValue(new Integer(1001));
			plist.getParameter(GR_BVALUE).setValue(new Double(0.9));
			plist.getParameter(YC_DELTA_MAG_CHAR).setValue(new Double(0.49));
			plist.getParameter(YC_DELTA_MAG_PRIME).setValue(new Double(1.0));
			plist.getParameter(GR_MAG_LOWER).setValue(new Double(0.005));
			plist.getParameter(YC_MAG_PRIME).setValue(new Double(5.945));
			plist.getParameter(GR_MAG_UPPER).setValue(new Double(6.445));
			plist.getParameter(TOT_MO_RATE).setValue(new Double(1.8e16));
		
		} else if (is(CASE_8A)) {
			plist.getParameter(DISTRIBUTION_NAME).setValue(SingleMagFreqDist.NAME);
			plist.getParameter(FIX).setConstraint(mfd.getSingleDistFixOptions());
			plist.getParameter(SINGLE_PARAMS_TO_SET).setValue(MagFreqDistParameter.MAG_AND_MO_RATE);
			plist.getParameter(MAG).setValue(new Double(6.0));
			plist.getParameter(MO_RATE).setValue(new Double(1.8e16));
		
		} else if (is(CASE_8B)) {
			plist.getParameter(DISTRIBUTION_NAME).setValue(SingleMagFreqDist.NAME);
			plist.getParameter(FIX).setConstraint(mfd.getSingleDistFixOptions());
			plist.getParameter(SINGLE_PARAMS_TO_SET).setValue(MagFreqDistParameter.MAG_AND_MO_RATE);
			plist.getParameter(MAG).setValue(new Double(6.0));
			plist.getParameter(MO_RATE).setValue(new Double(1.8e16));
		
		} else if (is(CASE_8C)) {
			plist.getParameter(DISTRIBUTION_NAME).setValue(SingleMagFreqDist.NAME);
			plist.getParameter(FIX).setConstraint(mfd.getSingleDistFixOptions());
			plist.getParameter(SINGLE_PARAMS_TO_SET).setValue(MagFreqDistParameter.MAG_AND_MO_RATE);
			plist.getParameter(MAG).setValue(new Double(6.0));
			plist.getParameter(MO_RATE).setValue(new Double(1.8e16));
		
		} else if (is(CASE_9A)) {
			plist.getParameter(DISTRIBUTION_NAME).setValue(SingleMagFreqDist.NAME);
			plist.getParameter(FIX).setConstraint(mfd.getSingleDistFixOptions());
			plist.getParameter(SINGLE_PARAMS_TO_SET).setValue(MagFreqDistParameter.MAG_AND_MO_RATE);
			plist.getParameter(MAG).setValue(new Double(6.0));
			plist.getParameter(MO_RATE).setValue(new Double(1.905e16));
		
		} else if (is(CASE_9B)) {
			plist.getParameter(DISTRIBUTION_NAME).setValue(SingleMagFreqDist.NAME);
			plist.getParameter(FIX).setConstraint(mfd.getSingleDistFixOptions());
			plist.getParameter(SINGLE_PARAMS_TO_SET).setValue(MagFreqDistParameter.MAG_AND_MO_RATE);
			plist.getParameter(MAG).setValue(new Double(6.0));
			plist.getParameter(MO_RATE).setValue(new Double(1.905e16));
		
		} else if (is(CASE_9C)) {
			plist.getParameter(DISTRIBUTION_NAME).setValue(SingleMagFreqDist.NAME);
			plist.getParameter(FIX).setConstraint(mfd.getSingleDistFixOptions());
			plist.getParameter(SINGLE_PARAMS_TO_SET).setValue(MagFreqDistParameter.MAG_AND_MO_RATE);
			plist.getParameter(MAG).setValue(new Double(6.0));
			plist.getParameter(MO_RATE).setValue(new Double(1.905e16));
		
		} else if (is(CASE_10)) {
			plist.getParameter(DISTRIBUTION_NAME).setValue(GutenbergRichterMagFreqDist.NAME);
			plist.getParameter(SET_ALL_PARAMS_BUT).setConstraint(mfd.getGRSetAllButOptions());
			plist.getParameter(FIX).setConstraint(mfd.getGRFixOptions());
			plist.getParameter(MIN).setValue(new Double(0.05));
			plist.getParameter(MAX).setValue(new Double(9.95));
			plist.getParameter(NUM).setValue(new Integer(100));
			plist.getParameter(SET_ALL_PARAMS_BUT).setValue(MagFreqDistParameter.TOT_MO_RATE);
			plist.getParameter(GR_MAG_LOWER).setValue(new Double(5.05));
			plist.getParameter(GR_MAG_UPPER).setValue(new Double(6.45));
			plist.getParameter(GR_BVALUE).setValue(new Double(0.9));
			plist.getParameter(TOT_CUM_RATE).setValue(new Double(.0395));
		
		} else if (is(CASE_11)) {
			plist.getParameter(DISTRIBUTION_NAME).setValue(GutenbergRichterMagFreqDist.NAME);
			plist.getParameter(SET_ALL_PARAMS_BUT).setConstraint(mfd.getGRSetAllButOptions());
			plist.getParameter(FIX).setConstraint(mfd.getGRFixOptions());
			plist.getParameter(MIN).setValue(new Double(0.05));
			plist.getParameter(MAX).setValue(new Double(9.95));
			plist.getParameter(NUM).setValue(new Integer(100));
			plist.getParameter(SET_ALL_PARAMS_BUT).setValue(MagFreqDistParameter.TOT_MO_RATE);
			plist.getParameter(GR_MAG_LOWER).setValue(new Double(5.05));
			plist.getParameter(GR_MAG_UPPER).setValue(new Double(6.45));
			plist.getParameter(GR_BVALUE).setValue(new Double(0.9));
			plist.getParameter(TOT_CUM_RATE).setValue(new Double(.0395));
		}

		// create the actual magFreqDist
		mfd.setMagDist();
	}

	// sets the parameter values for the selected test cases in Set-2
	private void init_Set2() {
		
		// *****************************************************
		// ****** Set the IMR, IMT, & Site-Related Params ******
		// ******          (except lat and lon)           ******
		// *****************************************************

		imr = new SadighEtAl_1997_AttenRel(null);
		imr.setParamDefaults();
		imr.getParameter(SigmaTruncTypeParam.NAME).setValue(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_NONE);
		imr.getParameter(StdDevTypeParam.NAME).setValue(StdDevTypeParam.STD_DEV_TYPE_NONE);
		imr.setIntensityMeasure(PGA_Param.NAME);

		site.addParameter(imr.getParameter(SadighEtAl_1997_AttenRel.SITE_TYPE_NAME));
		site.setValue(SadighEtAl_1997_AttenRel.SITE_TYPE_NAME, SadighEtAl_1997_AttenRel.SITE_TYPE_ROCK);

		// change IMR sigma if it's Case 2
		if (is(CASE_2) || is(CASE_5)){
			imr.getParameter(SigmaTruncTypeParam.NAME).setValue(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_1SIDED);
			imr.getParameter(SigmaTruncLevelParam.NAME).setValue(new Double(3.0));
			imr.getParameter(StdDevTypeParam.NAME).setValue(StdDevTypeParam.STD_DEV_TYPE_TOTAL);
		}

		// *****************************************************
		// ******           Set Site lat & lon           *******
		// *****************************************************

		if (is(CASE_1) || is(CASE_5)) {
			
			if (is(SITE_1) || is(SITE_4)) {
				site.setLocation(new Location(38.1126,-121.8860));
			
			} else if (is(SITE_2) || is(SITE_5)) {
				site.setLocation(new Location(38.1800,-121.8860));
			
			} else if (is(SITE_3) || is(SITE_6)) {
				site.setLocation(new Location(38.2696,-122.1140));
			}
		
		} else if (is(CASE_2)) {
			
			if (is(SITE_1)) {
				site.setLocation(new Location(37.5495,-122.000));
			
			} else if (is(SITE_2)) {
				site.setLocation(new Location(37.0990,-122.000));
		
			} else if (is(SITE_3)) {
				site.setLocation(new Location(36.8737,-122.000));
			}
		
		} else { // all others have the same set of sites
			
			if (is(SITE_1)) {
				site.setLocation(new Location(38.1126,-121.886));
		
			} else if (is(SITE_2)) {
				site.setLocation(new Location(38.2252,-121.000));
		
			} else if (is(SITE_3)) {
				site.setLocation(new Location(38.000,-122.000));
			}
		}

		// *****************************************************
		// ******         Set the ERF parameters         *******
		// *****************************************************
		
		if (is(CASE_1)){
			erf = new PEER_NonPlanarFaultForecast();
			// add sigma for maglength(0-1)
			erf.getParameter(PEER_NonPlanarFaultForecast.SIGMA_PARAM_NAME).setValue(new Double(0));
			erf.getTimeSpan().setDuration(1.0);
			erf.getParameter(PEER_NonPlanarFaultForecast.GRID_PARAM_NAME).setValue(new Double(1.0));
			erf.getParameter(PEER_NonPlanarFaultForecast.OFFSET_PARAM_NAME).setValue(new Double(1.0));
			erf.getParameter(PEER_NonPlanarFaultForecast.GR_MAG_UPPER).setValue(new Double(6.95));
			erf.getParameter(PEER_NonPlanarFaultForecast.SLIP_RATE_NAME).setValue(new Double(2.0));
			erf.getParameter(PEER_NonPlanarFaultForecast.SEGMENTATION_NAME).setValue(PEER_NonPlanarFaultForecast.SEGMENTATION_NO);
			erf.getParameter(PEER_NonPlanarFaultForecast.FAULT_MODEL_NAME).setValue(PEER_NonPlanarFaultForecast.FAULT_MODEL_STIRLING);
			
			// set the dip direction depending on the chosen
			if (is(SITE_1) || is(SITE_2) || is(SITE_3)) {
				
				erf.getParameter(PEER_NonPlanarFaultForecast.DIP_DIRECTION_NAME).setValue(PEER_NonPlanarFaultForecast.DIP_DIRECTION_EAST);

			} else {
				erf.getParameter(PEER_NonPlanarFaultForecast.DIP_DIRECTION_NAME).setValue(PEER_NonPlanarFaultForecast.DIP_DIRECTION_WEST);
			}
			
		} else if (is(CASE_2)) {
			erf = new PEER_MultiSourceForecast();
			erf.getParameter(PEER_MultiSourceForecast.DEPTH_LOWER_PARAM_NAME).setValue(new Double(10));
			erf.getParameter(PEER_MultiSourceForecast.DEPTH_UPPER_PARAM_NAME).setValue(new Double(5));
			erf.getParameter(PEER_MultiSourceForecast.GRID_PARAM_NAME).setValue(new Double(1.0));
			erf.getParameter(PEER_MultiSourceForecast.OFFSET_PARAM_NAME).setValue(new Double(1.0));
			erf.getTimeSpan().setDuration(1.0);
		
		} else if (is(CASE_3) || is(CASE_4) ) {

			erf = new FloatingPoissonFaultERF();
			erf.getParameter(FloatingPoissonFaultERF.OFFSET_PARAM_NAME).setValue(new Double(1.0));
			erf.getParameter(FloatingPoissonFaultERF.MAG_SCALING_REL_PARAM_NAME).setValue(PEER_testsMagAreaRelationship.NAME);
			erf.getParameter(FloatingPoissonFaultERF.SIGMA_PARAM_NAME).setValue(new Double(0));
			erf.getParameter(FloatingPoissonFaultERF.ASPECT_RATIO_PARAM_NAME).setValue(new Double(2.0));
			erf.getParameter(FloatingPoissonFaultERF.MIN_MAG_PARAM_NAME).setValue(new Double(5.0));
			erf.getTimeSpan().setDuration(1.0);
			erf.getParameter(FloatingPoissonFaultERF.RAKE_PARAM_NAME).setValue(new Double(0.0));

			// set the Fault Parameter
			SimpleFaultParameter fault = (SimpleFaultParameter) erf.getParameter(FloatingPoissonFaultERF.FAULT_PARAM_NAME);
			fault.setAll(1.0,fault1and2_Lats,fault1and2_Lons,fault1_Dips,fault1_Depths,SimpleFaultParameter.STIRLING);
			fault.setEvenlyGriddedSurfaceFromParams();


		} else if (is(CASE_5) ) {

			// NOTE Set2 Case5 disabled as PEER test runners are not 
			// yet set up to handle epistemic lists
//			erf = new PEER_LogicTreeERF_List(); 
//			erf.getParameter(PEER_LogicTreeERF_List.FAULT_MODEL_NAME).setValue(PEER_LogicTreeERF_List.FAULT_MODEL_STIRLING);
//			erf.getParameter(PEER_LogicTreeERF_List.OFFSET_PARAM_NAME).setValue(new Double(1));
//			erf.getParameter(PEER_LogicTreeERF_List.GRID_PARAM_NAME).setValue(new Double(1));
//			erf.getParameter(PEER_LogicTreeERF_List.SIGMA_PARAM_NAME).setValue(new Double(0.0));
//			erf.getTimeSpan().setDuration(1.0);
		
		} else if (is(CASE_6)){
			erf = new FloatingPoissonFaultERF();
			erf.getParameter(FloatingPoissonFaultERF.OFFSET_PARAM_NAME).setValue(new Double(1.0));
			erf.getParameter(FloatingPoissonFaultERF.MAG_SCALING_REL_PARAM_NAME).setValue(PEER_testsMagAreaRelationship.NAME);
			erf.getParameter(FloatingPoissonFaultERF.SIGMA_PARAM_NAME).setValue(new Double(0));
			erf.getParameter(FloatingPoissonFaultERF.ASPECT_RATIO_PARAM_NAME).setValue(new Double(2.0));
			erf.getParameter(FloatingPoissonFaultERF.MIN_MAG_PARAM_NAME).setValue(new Double(5.0));
			erf.getTimeSpan().setDuration(1.0);
			erf.getParameter(FloatingPoissonFaultERF.RAKE_PARAM_NAME).setValue(new Double(0.0));

			// set the Fault Parameter
			SimpleFaultParameter fault = (SimpleFaultParameter) erf.getParameter(FloatingPoissonFaultERF.FAULT_PARAM_NAME);
			fault.setAll(1.0,faultE_Lats,faultE_Lons,faultE_Dips,faultE_Depths,SimpleFaultParameter.STIRLING);
			fault.setEvenlyGriddedSurfaceFromParams();
		}

		
		// *****************************************************
		// ****** Set the magFreqDist params separately  *******
		// *****************************************************
		initMFD_Set2();
		
		// and update
		erf.updateForecast();
	}

	// sets the default magdist values for the Set-2
	// (only cases 3, 4, and 6 have magFreqDist as an adjustable parameter)
	private void initMFD_Set2() {
		
		MagFreqDistParameter mfd;
		if (is(CASE_3) || is(CASE_4) || is(CASE_6)) {
			mfd = (MagFreqDistParameter) erf.getParameter(FloatingPoissonFaultERF.MAG_DIST_PARAM_NAME);
			ParameterList plist = mfd.getAdjustableParams();
		
			if (is(CASE_3)) {
				plist.getParameter(DISTRIBUTION_NAME).setValue(YC_1985_CharMagFreqDist.NAME);
				plist.getParameter(SET_ALL_PARAMS_BUT).setConstraint(mfd.getYCSetAllButOptions());
				plist.getParameter(MIN).setValue(new Double(0.0));
				plist.getParameter(MAX).setValue(new Double(10));
				plist.getParameter(NUM).setValue(new Integer(1001));
				plist.getParameter(GR_BVALUE).setValue(new Double(0.9));
				plist.getParameter(YC_DELTA_MAG_CHAR).setValue(new Double(.5));
				plist.getParameter(YC_DELTA_MAG_PRIME).setValue(new Double(1.0));
				plist.getParameter(GR_MAG_LOWER).setValue(new Double(0.01));
				plist.getParameter(YC_MAG_PRIME).setValue(new Double(5.95));
				plist.getParameter(GR_MAG_UPPER).setValue(new Double(6.45));
				plist.getParameter(SET_ALL_PARAMS_BUT).setValue(MagFreqDistParameter.TOT_MO_RATE);
				plist.getParameter(YC_TOT_CHAR_RATE).setValue(new Double(1e-3));
			
			} else if (is(CASE_4)) {
				plist.getParameter(DISTRIBUTION_NAME).setValue(GaussianMagFreqDist.NAME);
				plist.getParameter(SET_ALL_PARAMS_BUT).setConstraint(mfd.getGaussianDistSetAllButOptions());
				plist.getParameter(MIN).setValue(new Double(0.05));
				plist.getParameter(MAX).setValue(new Double(9.95));
				plist.getParameter(NUM).setValue(new Integer(100));
				plist.getParameter(SET_ALL_PARAMS_BUT).setValue(MagFreqDistParameter.TOT_MO_RATE);
				plist.getParameter(TOT_CUM_RATE).setValue(new Double(1e-3));
				plist.getParameter(STD_DEV).setValue(new Double(0.25));
				plist.getParameter(MEAN).setValue(new Double(6.2));
				plist.getParameter(TRUNCATION_REQ).setValue(MagFreqDistParameter.TRUNCATE_UPPER_ONLY);
				plist.getParameter(TRUNCATE_NUM_OF_STD_DEV).setValue(new Double(1.0));
			
			} else if (is(CASE_6)) {
				plist.getParameter(DISTRIBUTION_NAME).setValue(GutenbergRichterMagFreqDist.NAME);
				plist.getParameter(SET_ALL_PARAMS_BUT).setConstraint(mfd.getGRSetAllButOptions());
				plist.getParameter(FIX).setConstraint(mfd.getGRFixOptions());
				plist.getParameter(SET_ALL_PARAMS_BUT).setValue(MagFreqDistParameter.TOT_CUM_RATE);
				plist.getParameter(MIN).setValue(new Double(0.05));
				plist.getParameter(MAX).setValue(new Double(9.95));
				plist.getParameter(NUM).setValue(new Integer(100));
				plist.getParameter(GR_MAG_LOWER).setValue(new Double(0.05));
				plist.getParameter(GR_MAG_UPPER).setValue(new Double(6.45));
				plist.getParameter(GR_BVALUE).setValue(new Double(0.9));
				plist.getParameter(TOT_MO_RATE).setValue(new Double(3.8055e16));
			}

		// create the actual magFreqDist
		mfd.setMagDist();
		}
	}

	// fault-data vectors needed for the tests that utilize
	// FloatingPoissonFaultERF
	private void initFaultData() {

		// Set1 faults
		fault1and2_Lats = new ArrayList();
		fault1and2_Lats.add(new Double(38.22480));
		fault1and2_Lats.add(new Double(38.0));

		fault1and2_Lons = new ArrayList();
		fault1and2_Lons.add(new Double(-122.0));
		fault1and2_Lons.add(new Double(-122.0));

		fault1_Dips = new ArrayList();
		fault1_Dips.add(new Double(90.0));

		fault1_Depths = new ArrayList();
		fault1_Depths.add(new Double(0.0));
		fault1_Depths.add(new Double(12.0));

		fault2_Dips = new ArrayList();
		fault2_Dips.add(new Double(60.0));

		fault2_Depths = new ArrayList();
		fault2_Depths.add(new Double(1.0));
		fault2_Depths.add(new Double(12.0));

		// Set2 faults
		faultE_Lats = new ArrayList();
		faultE_Lats.add(new Double(38.0));
		faultE_Lats.add(new Double(38.2248));

		faultE_Lons = new ArrayList();
		faultE_Lons.add(new Double(-122.0));
		faultE_Lons.add(new Double(-122.0));

		faultE_Dips = new ArrayList();
		faultE_Dips.add(new Double(50.0));
		faultE_Dips.add(new Double(20.0));

		faultE_Depths = new ArrayList();
		faultE_Depths.add(new Double(0.0));
		faultE_Depths.add(new Double(6.0));
		faultE_Depths.add(new Double(12.0));
	}

	// init function with log of xVals
	private void initFunction() {
		function = new ArbitrarilyDiscretizedFunc();
		for (double val : xVals) {
			function.set(Math.log(val), 1.0);
		}
	}

	// revert function to non-log X values
	public static DiscretizedFuncAPI functionFromLogX(DiscretizedFuncAPI in) {
		DiscretizedFuncAPI out = new ArbitrarilyDiscretizedFunc();
		for (int i=0; i<xVals.length; i++) {
			out.set(xVals[i], in.getY(i));
		}
		return out;
	}

	public static ArrayList<PeerTest> getSetOneDecriptors() {
		return desc1;
	}

	public static ArrayList<PeerTest> getSetTwoDecriptors() {
		return desc2;
	}

	static {

		desc1 = new ArrayList<PeerTest>();

		// indices and any run times >1min in comments
		desc1.add(new PeerTest(SET_1, CASE_1, SITE_1));  //   0
		desc1.add(new PeerTest(SET_1, CASE_1, SITE_2));  //   1
		desc1.add(new PeerTest(SET_1, CASE_1, SITE_3));  //   2
		desc1.add(new PeerTest(SET_1, CASE_1, SITE_4));  //   3
		desc1.add(new PeerTest(SET_1, CASE_1, SITE_5));  //   4
		desc1.add(new PeerTest(SET_1, CASE_1, SITE_6));  //   5
		desc1.add(new PeerTest(SET_1, CASE_1, SITE_7));  //   6 

		desc1.add(new PeerTest(SET_1, CASE_2, SITE_1));  //   7
		desc1.add(new PeerTest(SET_1, CASE_2, SITE_2));  //   8
		desc1.add(new PeerTest(SET_1, CASE_2, SITE_3));  //   9
		desc1.add(new PeerTest(SET_1, CASE_2, SITE_4));  //  10
		desc1.add(new PeerTest(SET_1, CASE_2, SITE_5));  //  11
		desc1.add(new PeerTest(SET_1, CASE_2, SITE_6));  //  12
		desc1.add(new PeerTest(SET_1, CASE_2, SITE_7));  //  13

		desc1.add(new PeerTest(SET_1, CASE_3, SITE_1));  //  14
		desc1.add(new PeerTest(SET_1, CASE_3, SITE_2));  //  15
		desc1.add(new PeerTest(SET_1, CASE_3, SITE_3));  //  16
		desc1.add(new PeerTest(SET_1, CASE_3, SITE_4));  //  17
		desc1.add(new PeerTest(SET_1, CASE_3, SITE_5));  //  18
		desc1.add(new PeerTest(SET_1, CASE_3, SITE_6));  //  19
		desc1.add(new PeerTest(SET_1, CASE_3, SITE_7));  //  20

		desc1.add(new PeerTest(SET_1, CASE_4, SITE_1));  //  21 20m
		desc1.add(new PeerTest(SET_1, CASE_4, SITE_2));  //  22 20m
		desc1.add(new PeerTest(SET_1, CASE_4, SITE_3));  //  23 20m
		desc1.add(new PeerTest(SET_1, CASE_4, SITE_4));  //  24 20m
		desc1.add(new PeerTest(SET_1, CASE_4, SITE_5));  //  25 20m
		desc1.add(new PeerTest(SET_1, CASE_4, SITE_6));  //  26 20m
		desc1.add(new PeerTest(SET_1, CASE_4, SITE_7));  //  27 20m

		desc1.add(new PeerTest(SET_1, CASE_5, SITE_1));  //  28
		desc1.add(new PeerTest(SET_1, CASE_5, SITE_2));  //  29
		desc1.add(new PeerTest(SET_1, CASE_5, SITE_3));  //  30
		desc1.add(new PeerTest(SET_1, CASE_5, SITE_4));  //  31
		desc1.add(new PeerTest(SET_1, CASE_5, SITE_5));  //  32
		desc1.add(new PeerTest(SET_1, CASE_5, SITE_6));  //  33
		desc1.add(new PeerTest(SET_1, CASE_5, SITE_7));  //  34

		desc1.add(new PeerTest(SET_1, CASE_6, SITE_1));  //  35
		desc1.add(new PeerTest(SET_1, CASE_6, SITE_2));  //  36
		desc1.add(new PeerTest(SET_1, CASE_6, SITE_3));  //  37
		desc1.add(new PeerTest(SET_1, CASE_6, SITE_4));  //  38
		desc1.add(new PeerTest(SET_1, CASE_6, SITE_5));  //  39
		desc1.add(new PeerTest(SET_1, CASE_6, SITE_6));  //  40
		desc1.add(new PeerTest(SET_1, CASE_6, SITE_7));  //  41

		desc1.add(new PeerTest(SET_1, CASE_7, SITE_1));  //  42
		desc1.add(new PeerTest(SET_1, CASE_7, SITE_2));  //  43
		desc1.add(new PeerTest(SET_1, CASE_7, SITE_3));  //  44
		desc1.add(new PeerTest(SET_1, CASE_7, SITE_4));  //  45
		desc1.add(new PeerTest(SET_1, CASE_7, SITE_5));  //  46
		desc1.add(new PeerTest(SET_1, CASE_7, SITE_6));  //  47
		desc1.add(new PeerTest(SET_1, CASE_7, SITE_7));  //  48

		desc1.add(new PeerTest(SET_1, CASE_8A, SITE_1)); //  49
		desc1.add(new PeerTest(SET_1, CASE_8A, SITE_2)); //  50
		desc1.add(new PeerTest(SET_1, CASE_8A, SITE_3)); //  51
		desc1.add(new PeerTest(SET_1, CASE_8A, SITE_4)); //  52
		desc1.add(new PeerTest(SET_1, CASE_8A, SITE_5)); //  53
		desc1.add(new PeerTest(SET_1, CASE_8A, SITE_6)); //  54
		desc1.add(new PeerTest(SET_1, CASE_8A, SITE_7)); //  55

		desc1.add(new PeerTest(SET_1, CASE_8B, SITE_1)); //  56
		desc1.add(new PeerTest(SET_1, CASE_8B, SITE_2)); //  57
		desc1.add(new PeerTest(SET_1, CASE_8B, SITE_3)); //  58
		desc1.add(new PeerTest(SET_1, CASE_8B, SITE_4)); //  59
		desc1.add(new PeerTest(SET_1, CASE_8B, SITE_5)); //  60
		desc1.add(new PeerTest(SET_1, CASE_8B, SITE_6)); //  61
		desc1.add(new PeerTest(SET_1, CASE_8B, SITE_7)); //  62

		desc1.add(new PeerTest(SET_1, CASE_8C, SITE_1)); //  63
		desc1.add(new PeerTest(SET_1, CASE_8C, SITE_2)); //  64
		desc1.add(new PeerTest(SET_1, CASE_8C, SITE_3)); //  65
		desc1.add(new PeerTest(SET_1, CASE_8C, SITE_4)); //  66
		desc1.add(new PeerTest(SET_1, CASE_8C, SITE_5)); //  67
		desc1.add(new PeerTest(SET_1, CASE_8C, SITE_6)); //  68
		desc1.add(new PeerTest(SET_1, CASE_8C, SITE_7)); //  69

		desc1.add(new PeerTest(SET_1, CASE_9A, SITE_1)); //  70
		desc1.add(new PeerTest(SET_1, CASE_9A, SITE_2)); //  71
		desc1.add(new PeerTest(SET_1, CASE_9A, SITE_3)); //  72
		desc1.add(new PeerTest(SET_1, CASE_9A, SITE_4)); //  73
		desc1.add(new PeerTest(SET_1, CASE_9A, SITE_5)); //  74
		desc1.add(new PeerTest(SET_1, CASE_9A, SITE_6)); //  75
		desc1.add(new PeerTest(SET_1, CASE_9A, SITE_7)); //  76

		desc1.add(new PeerTest(SET_1, CASE_9B, SITE_1)); //  77 20m
		desc1.add(new PeerTest(SET_1, CASE_9B, SITE_2)); //  78 20m
		desc1.add(new PeerTest(SET_1, CASE_9B, SITE_3)); //  79 20m
		desc1.add(new PeerTest(SET_1, CASE_9B, SITE_4)); //  80 20m
		desc1.add(new PeerTest(SET_1, CASE_9B, SITE_5)); //  81 20m
		desc1.add(new PeerTest(SET_1, CASE_9B, SITE_6)); //  82 20m
		desc1.add(new PeerTest(SET_1, CASE_9B, SITE_7)); //  83 20m

		desc1.add(new PeerTest(SET_1, CASE_9C, SITE_1)); //  84
		desc1.add(new PeerTest(SET_1, CASE_9C, SITE_2)); //  85
		desc1.add(new PeerTest(SET_1, CASE_9C, SITE_3)); //  86
		desc1.add(new PeerTest(SET_1, CASE_9C, SITE_4)); //  87
		desc1.add(new PeerTest(SET_1, CASE_9C, SITE_5)); //  88
		desc1.add(new PeerTest(SET_1, CASE_9C, SITE_6)); //  89
		desc1.add(new PeerTest(SET_1, CASE_9C, SITE_7)); //  90

		desc1.add(new PeerTest(SET_1, CASE_10, SITE_1)); //  91
		desc1.add(new PeerTest(SET_1, CASE_10, SITE_2)); //  92
		desc1.add(new PeerTest(SET_1, CASE_10, SITE_3)); //  93
		desc1.add(new PeerTest(SET_1, CASE_10, SITE_4)); //  94

		desc1.add(new PeerTest(SET_1, CASE_11, SITE_1)); //  95
		desc1.add(new PeerTest(SET_1, CASE_11, SITE_2)); //  96
		desc1.add(new PeerTest(SET_1, CASE_11, SITE_3)); //  97
		desc1.add(new PeerTest(SET_1, CASE_11, SITE_4)); //  98

		desc1.add(new PeerTest(SET_1, CASE_12, SITE_1)); //  99
		desc1.add(new PeerTest(SET_1, CASE_12, SITE_2)); // 100
		desc1.add(new PeerTest(SET_1, CASE_12, SITE_3)); // 101
		desc1.add(new PeerTest(SET_1, CASE_12, SITE_4)); // 102
		desc1.add(new PeerTest(SET_1, CASE_12, SITE_5)); // 103
		desc1.add(new PeerTest(SET_1, CASE_12, SITE_6)); // 104
		desc1.add(new PeerTest(SET_1, CASE_12, SITE_7)); // 105

		desc2 = new ArrayList<PeerTest>();

		desc2.add(new PeerTest(SET_2, CASE_1, SITE_1)); // 
		desc2.add(new PeerTest(SET_2, CASE_1, SITE_2)); // 
		desc2.add(new PeerTest(SET_2, CASE_1, SITE_3)); // 
		desc2.add(new PeerTest(SET_2, CASE_1, SITE_4)); // 
		desc2.add(new PeerTest(SET_2, CASE_1, SITE_5)); // 
		desc2.add(new PeerTest(SET_2, CASE_1, SITE_6)); // 
		 
		desc2.add(new PeerTest(SET_2, CASE_2, SITE_1)); // 
		desc2.add(new PeerTest(SET_2, CASE_2, SITE_2)); // 
		desc2.add(new PeerTest(SET_2, CASE_2, SITE_3)); // 

		desc2.add(new PeerTest(SET_2, CASE_3, SITE_1)); // 
		desc2.add(new PeerTest(SET_2, CASE_3, SITE_2)); // 
		desc2.add(new PeerTest(SET_2, CASE_3, SITE_3)); // 

		desc2.add(new PeerTest(SET_2, CASE_4, SITE_1)); // 
		desc2.add(new PeerTest(SET_2, CASE_4, SITE_2)); // 
		desc2.add(new PeerTest(SET_2, CASE_4, SITE_3)); // 

		// NOTE Set2 Case5 disabled as PEER test runners are not 
		// yet set up to handle epistemic lists
		// desc2.add(new TestDescriptor(SET_2, CASE_5, SITE_1)); // 
		// desc2.add(new TestDescriptor(SET_2, CASE_5, SITE_2)); // 
		// desc2.add(new TestDescriptor(SET_2, CASE_5, SITE_3)); // 

		desc2.add(new PeerTest(SET_2, CASE_6, SITE_1)); // 
		desc2.add(new PeerTest(SET_2, CASE_6, SITE_2)); // 
		desc2.add(new PeerTest(SET_2, CASE_6, SITE_3)); // 
	}
	
	private boolean is(TestSet testSet) {
		return selectedSet.equals(testSet);
	}

	private boolean is(TestCase testCase) {
		return selectedCase.equals(testCase);
	}

	private boolean is(TestSite testSite) {
		return selectedSite.equals(testSite);
	}

}
