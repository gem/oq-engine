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

import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.geo.GeoTools;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.PointEqkSource;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.param.MagFreqDistParameter;


/**
 * <p>Title: PEER_AreaForecast</p>
 * <p>Description: PEER's Area earthquake-rupture forecast. The Peer Group Test cases </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author Nitin Gupta & Vipin Gupta
 * Date : Oct 24, 2002
 * @version 1.0
 */

public class PEER_AreaForecast extends EqkRupForecast{

  //for Debug purposes
  private static String  C = new String("PEER_AreaForecast");
  private boolean D = false;

  //name for this classs
  public final static String  NAME = "PEER Area Forecast";

  // this is the GR distribution used for all sources
  private GutenbergRichterMagFreqDist dist_GR;

  // this is the source
  private PointEqkSource pointPoissonEqkSource;


  /**
   * Declaration for the static lat and lons for the Area
   */
  private static final double LAT_TOP= 38.901;
  private static final double LAT_BOTTOM = 37.099;
  private static final double LAT_CENTER = 38.0;
  private static final double LONG_LEFT= -123.138;
  private static final double LONG_RIGHT= -120.862;
  private static final double LONG_CENTER= -122.0;

  private static final double MAX_DISTANCE =100;

  //Param Name
  public final static String GRID_PARAM_NAME =  "Area Grid Spacing";
  public final static String GRID_PARAM_UNITS =  "km";
  private final static double GRID_PARAM_MIN = 0.001;
  private final static double GRID_PARAM_MAX = 100;
  public final static String DEPTH_LOWER_PARAM_NAME =  "Lower Seis Depth";
  public final static String DEPTH_UPPER_PARAM_NAME =  "Upper Seis Depth";
  public final static String DEPTH_PARAM_UNITS = "km";
  private final static double DEPTH_PARAM_MIN = 0;
  private final static double DEPTH_PARAM_MAX = 30;
  private final static Double DEPTH_PARAM_DEFAULT = new Double(5);
  public final static String MAG_DIST_PARAM_NAME = "Mag Dist";

   //Rake Variable
  public final static String RAKE_PARAM_NAME = "Ave Rake";
  public final static String RAKE_PARAM_UNITS = "degrees";
  private final static Double RAKE_PARAM_DEFAULT = new Double(0);
  private final static double RAKE_PARAM_MIN = -180;
  private final static double RAKE_PARAM_MAX = 180;

  //Rake Variable
  public final static String DIP_PARAM_NAME = "Ave Dip";
  public final static String DIP_PARAM_UNITS = "degrees";
  private final static Double DIP_PARAM_DEFAULT = new Double(90);
  private final static double DIP_PARAM_MIN = 0;
  private final static double DIP_PARAM_MAX = 90;


  // default grid spacing is 1km
  private Double DEFAULT_GRID_VAL = new Double(1);

  // list of forecast locations
  private LocationList locationList;


  // create the grid spacing parameter
  DoubleParameter gridParam=new DoubleParameter(GRID_PARAM_NAME,GRID_PARAM_MIN,
                                                GRID_PARAM_MAX,GRID_PARAM_UNITS,
                                                DEFAULT_GRID_VAL);

  // create Depth Lower parameter
  DoubleParameter depthLowerParam = new DoubleParameter(DEPTH_LOWER_PARAM_NAME,DEPTH_PARAM_MIN,
                                                        DEPTH_PARAM_MAX,DEPTH_PARAM_UNITS,
                                                        DEPTH_PARAM_DEFAULT);

  // create depth Upper parameter
  DoubleParameter depthUpperParam = new DoubleParameter(DEPTH_UPPER_PARAM_NAME,DEPTH_PARAM_MIN,
                                                        DEPTH_PARAM_MAX,DEPTH_PARAM_UNITS,
                                                        DEPTH_PARAM_DEFAULT);
 // create the rake parameter
  DoubleParameter rakeParam = new DoubleParameter(RAKE_PARAM_NAME, RAKE_PARAM_MIN,
                                                      RAKE_PARAM_MAX,RAKE_PARAM_UNITS,
                                                      RAKE_PARAM_DEFAULT);
  // create the dip parameter
  DoubleParameter dipParam = new DoubleParameter(DIP_PARAM_NAME, DIP_PARAM_MIN,
                                                      DIP_PARAM_MAX,DIP_PARAM_UNITS,
                                                      DIP_PARAM_DEFAULT);
  // create the supported MagDists
  ArrayList supportedMagDists=new ArrayList();

  //Mag Freq Dist Parameter
  MagFreqDistParameter magDistParam ;


  /**
   * This constructor constructs the source
   *
   * No argument constructor
   */
  public PEER_AreaForecast() {

    // create the timespan object with start time and duration in years
    timeSpan = new TimeSpan(TimeSpan.NONE,TimeSpan.YEARS);
    timeSpan.addParameterChangeListener(this);

    // make adj params list
    adjustableParams.addParameter(gridParam);
    adjustableParams.addParameter(depthLowerParam);
    adjustableParams.addParameter(depthUpperParam);
    adjustableParams.addParameter(rakeParam);
    adjustableParams.addParameter(dipParam);

    // create the supported Mag-Dist parameter
    supportedMagDists.add(GutenbergRichterMagFreqDist.NAME);
    magDistParam = new MagFreqDistParameter(MAG_DIST_PARAM_NAME, supportedMagDists);
    adjustableParams.addParameter(this.magDistParam);


    // listen for change in the parameters
    gridParam.addParameterChangeListener(this);
    depthLowerParam.addParameterChangeListener(this);
    depthUpperParam.addParameterChangeListener(this);
    magDistParam.addParameterChangeListener(this);
    rakeParam.addParameterChangeListener(this);
    dipParam.addParameterChangeListener(this);

  }


  /**
   * update the sources based on the user paramters, only when user has changed a parameter
   */
  public void updateForecast(){

    if(parameterChangeFlag) {

      // check if magDist is null
      if(this.magDistParam.getValue()==null)
          throw new RuntimeException("Magnitude Distribution is null");

      double gridSpacing = ((Double)gridParam.getValue()).doubleValue();
      double depthLower =((Double)this.depthLowerParam.getValue()).doubleValue();
      double depthUpper =((Double)this.depthUpperParam.getValue()).doubleValue();

      if (depthUpper > depthLower)
          throw new RuntimeException("Upper Seis Depth must be � Lower Seis Depth");

      //gets the change in latitude for grid spacing specified
      Location gridCenter = new Location(LAT_CENTER, LONG_CENTER);
//      double latDiff = LocationUtils.getDeltaLatFromKm(gridSpacing);
//      double longDiff= LocationUtils.getDeltaLonFromKm(LAT_CENTER,gridSpacing);
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

      /* getting the Gutenberg magnitude distribution and scaling its cumRate to the original cumRate
       * divided by the number of the locations (note that this is a clone of what's in the magDistParam)
       */
//      System.out.println(((GutenbergRichterMagFreqDist)magDistParam.getValue()).getName());
//      dist_GR = (GutenbergRichterMagFreqDist) ((GutenbergRichterMagFreqDist)magDistParam.getValue()).deepClone();
      dist_GR = (GutenbergRichterMagFreqDist)magDistParam.getValue();
      IncrementalMagFreqDist dist = new IncrementalMagFreqDist(dist_GR.getMinX(), dist_GR.getMaxX(), dist_GR.getNum());

//      double cumRate = dist_GR.getCumRate((int) 0);
//      cumRate /= numLocs;
      for(int i=0; i<dist.getNum();i++)
    	  dist.set(i, dist_GR.getY(i)/numLocs);
 //     dist_GR.scaleToCumRate(0,cumRate);

      double rake = ((Double) rakeParam.getValue()).doubleValue();
      double dip = ((Double) dipParam.getValue()).doubleValue();

      // Dip is hard wired at 90 degrees
      pointPoissonEqkSource = new PointEqkSource(new Location(0,0,0),
          dist, timeSpan.getDuration(), rake, dip);

      if (D) System.out.println(C+" updateForecast(): rake="+pointPoissonEqkSource.getRupture(0).getAveRake() +
                          "; dip="+ pointPoissonEqkSource.getRupture(0).getRuptureSurface().getAveDip());

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

    pointPoissonEqkSource.setLocation(locationList.get(iSource));
    pointPoissonEqkSource.setDuration(timeSpan.getDuration());

    if (D) System.out.println(iSource + "th source location: "+ locationList.get(iSource).toString() +
                              "; numRups="+pointPoissonEqkSource.getNumRuptures());
    if (D) System.out.println("                     rake="+pointPoissonEqkSource.getRupture(0).getAveRake() +
                              "; dip="+ pointPoissonEqkSource.getRupture(0).getRuptureSurface().getAveDip());

    return pointPoissonEqkSource;
  }

  /**
   * Get the number of earthquake sources
   *
   * @return integer value specifying the number of earthquake sources
   */
  public int getNumSources(){
    return locationList.size();
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
  public String getName() {
    return NAME;
  }


}
