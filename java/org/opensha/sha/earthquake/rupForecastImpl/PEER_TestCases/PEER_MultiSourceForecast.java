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

package org.opensha.sha.earthquake.rupForecastImpl.PEER_TestCases;


import java.util.ArrayList;

import org.opensha.commons.calc.FaultMomentCalc;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.PEER_testsMagAreaRelationship;
import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.geo.GeoTools;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.FloatingPoissonFaultSource;
import org.opensha.sha.earthquake.rupForecastImpl.PointEqkSource;
import org.opensha.sha.faultSurface.EvenlyGriddedSurface;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.faultSurface.FrankelGriddedSurface;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.YC_1985_CharMagFreqDist;

/**
 * <p>Title: PEER_MultiSourceForecast</p>
 * <p>Description: This is the forecast used for test-set #2, Cases 2a-c</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author Nitin Gupta & Vipin Gupta
 * Date : Oct 24, 2002
 * @version 1.0
 */

public class PEER_MultiSourceForecast extends EqkRupForecast{

  /**
   * @todo variables
   */
  //for Debug purposes
  private static String  C = new String("PEER_MultiSourceForecast");
  private boolean D = false;

  //name for this classs
  public final static String  NAME = "PEER Multi Source";

  PEER_testsMagAreaRelationship magScalingRel = new PEER_testsMagAreaRelationship();
  private double rupAspectRatio = 2;
  private double minMag = 5;  // the minimum magnitude to consider in the forecast


  // the GR distribution used for the area source
  private GutenbergRichterMagFreqDist dist_gr_A_orig;

  // the GR distribution used for the gridded points of the area source
  private GutenbergRichterMagFreqDist dist_GR;

  // the YC distribution used for faults B & C
  private YC_1985_CharMagFreqDist dist_yc_B;
  private YC_1985_CharMagFreqDist dist_yc_C;

  // these are the fault traces for each fault source
  private FaultTrace faultTraceB;
  private FaultTrace faultTraceC;
  private static final Location faultB_loc1 = new Location(38.6749,-121.5691,0);
  private static final Location faultB_loc2 = new Location(38.6749,-122.4309,0);
  private static final Location faultC_loc1 = new Location(37.3242,-121.8590,0);
  private static final Location faultC_loc2 = new Location(37.3242,-122.1410,0);

  // these are the fault sources
  private FloatingPoissonFaultSource fltSourceB;
  private FloatingPoissonFaultSource fltSourceC;

  // this is the dip and rake for all events in all sources

  private static final double DIP = 90.0;
  private static final double RAKE = 0.0;

  // this is the source used for the area-source points
  private PointEqkSource pointPoissonEqkSource;

  // lat & lon data that define the Area source
  private static final double LAT_TOP= 38.901;
  private static final double LAT_BOTTOM = 37.099;
  private static final double LAT_CENTER = 38.0;
  private static final double LONG_LEFT= -123.138;
  private static final double LONG_RIGHT= -120.862;
  private static final double LONG_CENTER= -122.0;
  private static final double MAX_DISTANCE =100;

  // the grid parameter stuff
  public final static String GRID_PARAM_NAME =  "Grid Spacing of Sources";
  public final static String GRID_PARAM_UNITS =  "km";
  private final static double GRID_PARAM_MIN = 0.001;
  private final static double GRID_PARAM_MAX = 100;
  private Double DEFAULT_GRID_VAL = new Double(1);

  // rupture-offset parameter stuff
  public final static String OFFSET_PARAM_NAME =  "Offset";
  private Double DEFAULT_OFFSET_VAL = new Double(1);
  public final static String OFFSET_PARAM_UNITS = "kms";
  private final static double OFFSET_PARAM_MIN = .01;
  private final static double OFFSET_PARAM_MAX = 10000;


  // the lower and upper seismo-depth paramter stuff for the Area Sources
  public final static String DEPTH_LOWER_PARAM_NAME =  "Area Lower Seis Depth";
  public final static String DEPTH_UPPER_PARAM_NAME =  "Area Upper Seis Depth";
  public final static String DEPTH_PARAM_UNITS = "km";
  private final static double DEPTH_PARAM_MIN = 0;
  private final static double DEPTH_PARAM_MAX = 30;
  private final static Double DEPTH_PARAM_DEFAULT = new Double(5);


  // list of area forecast locations
  private LocationList locationList;

  // create the grid spacing parameter
  DoubleParameter gridParam=new DoubleParameter(GRID_PARAM_NAME,GRID_PARAM_MIN,
                                                GRID_PARAM_MAX,GRID_PARAM_UNITS,
                                                DEFAULT_GRID_VAL);

  // add the rupOffset spacing field
DoubleParameter offsetParam = new DoubleParameter(OFFSET_PARAM_NAME,OFFSET_PARAM_MIN,
                                             OFFSET_PARAM_MAX,OFFSET_PARAM_UNITS,DEFAULT_OFFSET_VAL);

  // create Depth Lower parameter
  DoubleParameter depthLowerParam = new DoubleParameter(DEPTH_LOWER_PARAM_NAME,DEPTH_PARAM_MIN,
                                                        DEPTH_PARAM_MAX,DEPTH_PARAM_UNITS,
                                                        DEPTH_PARAM_DEFAULT);
  // create depth Upper parameter
  DoubleParameter depthUpperParam = new DoubleParameter(DEPTH_UPPER_PARAM_NAME,DEPTH_PARAM_MIN,
                                                        DEPTH_PARAM_MAX,DEPTH_PARAM_UNITS,
                                                        DEPTH_PARAM_DEFAULT);



  /**
   * This constructor constructs the source
   *
   * No argument constructor
   */
  public PEER_MultiSourceForecast() {

    // create the timespan object with start time and duration in years
    timeSpan = new TimeSpan(TimeSpan.NONE,TimeSpan.YEARS);
    timeSpan.addParameterChangeListener(this);

    // make adj params list
    adjustableParams.addParameter(gridParam);
    adjustableParams.addParameter(offsetParam);
    adjustableParams.addParameter(depthLowerParam);
    adjustableParams.addParameter(depthUpperParam);

    // listen for change in the parameters
    gridParam.addParameterChangeListener(this);
    offsetParam.addParameterChangeListener(this);
    depthLowerParam.addParameterChangeListener(this);
    depthUpperParam.addParameterChangeListener(this);

    // make the mag-freq dists for the sources
    double bValue = 0.9;
    // area source distribution:
    dist_gr_A_orig = new GutenbergRichterMagFreqDist(5.05, 6.45, 15);
    dist_gr_A_orig.setAllButTotMoRate(5.05, 6.45,0.0395,bValue);
    // Fault B distribution
    double tempMoRate = FaultMomentCalc.getMoment(75.0e3*12.0e3, 2e-3);
    double minMag = 0.0;
    double maxMag = 10.0;
    int    numMag = 1001;
    double magLower = 0.01;
    double magUpper = 7.25;
    double deltaMagChar = 0.5;
    double magPrime = 6.75;
    double deltaMagPrime = 1.0;
    dist_yc_B = new YC_1985_CharMagFreqDist(minMag,maxMag, numMag);
    dist_yc_B.setAllButTotCharRate(magLower, magUpper,deltaMagChar,magPrime,deltaMagPrime,bValue,tempMoRate);
    // Fault C distribution
    tempMoRate = FaultMomentCalc.getMoment(25.0e3*12.0e3, 1e-3);
    magUpper = 6.75;
    magPrime = 6.25;
    dist_yc_C = new YC_1985_CharMagFreqDist(minMag,maxMag, numMag);
    dist_yc_C.setAllButTotCharRate(magLower, magUpper,deltaMagChar,magPrime,deltaMagPrime,bValue,tempMoRate);

    // make the fault traces for the fault sources.
    faultTraceB = new FaultTrace("Fault B");
    faultTraceB.add(faultB_loc1);
    faultTraceB.add(faultB_loc2);

    faultTraceC = new FaultTrace("Fault C");
    faultTraceC.add(faultC_loc1);
    faultTraceC.add(faultC_loc2);
  }

  /**
   * update the sources based on the user paramters, only when user has changed a parameter
   */
  public void updateForecast(){

    if(parameterChangeFlag) {

      // set the grid spacing used for all sources
      double gridSpacing = ((Double)gridParam.getValue()).doubleValue();

      // Now make/update the source used for all area-source grid points
      double depthLower =((Double)this.depthLowerParam.getValue()).doubleValue();
      double depthUpper =((Double)this.depthUpperParam.getValue()).doubleValue();

      if (depthUpper > depthLower)
          throw new RuntimeException("Upper Seis Depth must be � Lower Seis Depth");

      //gets the change in latitude for grid spacing specified
      Location gridCenter = new Location(LAT_CENTER, LONG_CENTER);
//    double latDiff = LocationUtils.getDeltaLatFromKm(gridSpacing);
//    double longDiff= LocationUtils.getDeltaLonFromKm(LAT_CENTER,gridSpacing);
      double latDiff = GeoTools.degreesLatPerKm(gridCenter) * gridSpacing;
      double longDiff= GeoTools.degreesLonPerKm(gridCenter) * gridSpacing;

      // Create the grid of locations in the circular area
      locationList = new LocationList();
      for (double lat=LAT_TOP;lat >=LAT_BOTTOM; lat-=latDiff)
        for (double lon=LONG_LEFT;lon <=LONG_RIGHT; lon+=longDiff)
          if (LocationUtils.horzDistance(
        		  new Location(LAT_CENTER,LONG_CENTER),
        		  new Location(lat,lon)) <= MAX_DISTANCE)
            for (double depth=depthUpper;depth<=depthLower;depth+=gridSpacing)
                locationList.add(new Location(lat,lon,depth));

      int numLocs = locationList.size();

      dist_GR = (GutenbergRichterMagFreqDist) dist_gr_A_orig.deepClone();

      double cumRate = dist_GR.getCumRate((int) 0);
      cumRate /= numLocs;
      dist_GR.scaleToCumRate((int) 0,cumRate);

      pointPoissonEqkSource = new PointEqkSource(new Location(0,0,0),
          dist_GR, timeSpan.getDuration(), RAKE, DIP);

      if (D) System.out.println(C+" updateForecast(): rake="+pointPoissonEqkSource.getRupture(0).getAveRake() +
                          "; dip="+ pointPoissonEqkSource.getRupture(0).getRuptureSurface().getAveDip());

      // now make the fault sources
      double seisUpper = 0;
      double seisLower = 12;
      double offset = ((Double)offsetParam.getValue()).doubleValue();
      double lengthSigma = 0;

      // Make gridded surface factory for the two faults (create with fault B trace)

      FrankelGriddedSurface surfaceB = new FrankelGriddedSurface( faultTraceB,
                                                                     DIP,
                                                                     seisUpper,
                                                                     seisLower,
                                                                     gridSpacing );

      fltSourceB = new  FloatingPoissonFaultSource(dist_yc_B,surfaceB,
                                                 magScalingRel,lengthSigma,rupAspectRatio,offset,
                                                 RAKE,timeSpan.getDuration(),minMag);

      // for fault C:
      EvenlyGriddedSurfaceAPI surfaceC = new FrankelGriddedSurface( faultTraceC,
                                                                     DIP,
                                                                     seisUpper,
                                                                     seisLower,
                                                                     gridSpacing );

      fltSourceC = new  FloatingPoissonFaultSource(dist_yc_C,(EvenlyGriddedSurface) surfaceC,
                                                 magScalingRel,lengthSigma,rupAspectRatio,offset,
                                                 RAKE,timeSpan.getDuration(),minMag);

    }
    parameterChangeFlag = false;
  }



  /**
   * Return the earhthquake source at index i. This methos returns the reference to
   * the class variable. So, when you call this method again, result from previous
   * method call may no longer bevalid.
   * this is secret, fast but dangerous method
   *
   * @param iSource : index of the source needed
   *
   * @return Returns the ProbEqkSource at index i
   *
   */
  public ProbEqkSource getSource(int iSource) {
    int numSrc = this.getNumSources();

    if(iSource < numSrc-2 && iSource >= 0) {
      pointPoissonEqkSource.setLocation(locationList.get(iSource));
      return pointPoissonEqkSource;
    }
    else if(iSource == numSrc-2)
      return fltSourceB;
    else if (iSource == numSrc-1)
      return fltSourceC;
    else
      throw new RuntimeException("bad source index");

  }

  /**
   * Get the number of earthquake sources
   *
   * @return integer value specifying the number of earthquake sources
   */
  public int getNumSources(){
    return locationList.size() + 2;
  }


  /**
   * Not yet implemented
   *
   * @return ArrayList of Prob Earthquake sources
   */
  public ArrayList  getSourceList(){

    return null;
  }



  /**
   * Return the name for this class
   *
   * @return : return the name for this class
   */
  public String getName(){
    return NAME;
  }


}
