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

package org.opensha.sha.earthquake.rupForecastImpl.step;

import java.net.URL;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.ListIterator;
import java.util.StringTokenizer;

import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.geo.Location;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.PointEqkSource;
import org.opensha.sha.magdist.IncrementalMagFreqDist;

/**
 * <p>Title: STEP_EqkRupForecast</p>
 * <p>Description:
 * </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author :Edward Field
 * @Date : Aug 30, 2003
 * @version 1.0
 */

  public class STEP_EqkRupForecast extends EqkRupForecast
    implements ParameterChangeListener{

  //for Debug purposes
  private static String  C = new String("STEP_EqkRupForecast");
  private boolean D = false;

  // name of this ERF
  public static String  NAME = new String("STEP ERF");

  // Input file names
  private final static String DELTA_RATES_FILE_NAME = "http://www.relm.org/models/step/AllCalDeltaRates.txt";
  //private final static String BACKGROUND_RATES_FILE_NAME = "/opt/install/apache-tomcat-5.5.20/webapps/OpenSHA/WEB-INF/dataFiles/DailyRates96Model.txt";
  //private final static String BACKGROUND_RATES_FILE_NAME = "org/opensha/sha/earthquake/rupForecastImpl/step/DailyRates96Model.txt";
  private final static String BACKGROUND_RATES_FILE_NAME = "/opt/install/apache-tomcat-5.5.20/webapps/OpenSHA/WEB-INF/dataFiles/AllCal96ModelDaily.txt";
  //private final static String BACKGROUND_RATES_FILE_NAME = "org/opensha/sha/earthquake/rupForecastImpl/step/AllCal96ModelDaily.txt";

// ArrayLists of input file lines
  private ArrayList deltaRateFileLines;
  private ArrayList backgroundRateFileLines;

  // misc values
  private static final double RAKE=0.0;
  private static final double DIP=90.0;
  private static final double MAG_LOWER=4;
  private static final double MAG_UPPER=8;
  private static final int    NUM_MAG=41;
  private static final double DEPTH=0;

  private double oldMinMag=MAG_LOWER;

  // vectors to hold the sources
  private ArrayList deltaRateSources;
  private ArrayList backgroundRateSources;
  private ArrayList allSources;

  // booleans to help decide if sources need to be made
  private boolean deltaSourcesAlreadyMade = false;
  private boolean backgroundSourcesAlreadyMade = false;
  private boolean backgroundRatesFileAlreadyRead = false;

  // seismicity type parameter stuff
  public final static String SEIS_TYPE_NAME = new String ("Seismicity Type");
  public final static String SEIS_TYPE_ADD_ON = new String ("STEP Add-On Rates");
  public final static String SEIS_TYPE_BACKGROUND = new String ("Background Rates");
  public final static String SEIS_TYPE_BOTH = new String ("Both");
  public final static String SEIS_TYPE_INFO = new String ("Seismicity-type to use in the forecast");
  private StringParameter seisTypeParam;


  // minimum magnitude parameter stuff
  private final static String MIN_MAG_PARAM_NAME ="Minimum Magnitude";
  private Double MIN_MAG_PARAM_DEFAULT = new Double(4.0);
  private final static String MIN_MAG_PARAM_UNITS = null;
  private final static String MIN_MAG_PARAM_INFO = "The minimum magnitude to be considered (those below are ignored)";
  private final static double MIN_MAG_PARAM_MIN = 4.0;
  private final static double MIN_MAG_PARAM_MAX = 8.0;
  DoubleParameter minMagParam;


  /**
   * No argument constructor
   */
  public STEP_EqkRupForecast() {

    // read the delta rates here so we have the timespan info
    try{
      deltaRateFileLines = FileUtils.loadFile( new URL(DELTA_RATES_FILE_NAME) );
    }catch(Exception e){
      throw new RuntimeException(e.getMessage());
    }

    // Create the timeSpan & set its constraints
    StringTokenizer st = new StringTokenizer(deltaRateFileLines.get(0).toString());
    int year =  (new Integer(st.nextToken())).intValue();
    int month =  (new Integer(st.nextToken())).intValue();
    int day =  (new Integer(st.nextToken())).intValue();
    int hour =  (new Integer(st.nextToken())).intValue();
    int minute =  (new Integer(st.nextToken())).intValue();
    int second =  (new Integer(st.nextToken())).intValue();

    if(D) System.out.println("year="+year+"; month="+month+"; day="+day+"; hour="+
                             hour+"; minute="+minute+"; second="+second);

    st = new StringTokenizer(deltaRateFileLines.get(1).toString());
    double duration = (new Double(st.nextToken())).doubleValue();
    if(D) System.out.println("duration="+duration);

    this.timeSpan = new TimeSpan(TimeSpan.SECONDS,TimeSpan.DAYS);
    timeSpan.setStartTime(year,month,day,hour,minute,second);
    timeSpan.setDuration(duration);
    timeSpan.setStartTimeConstraint(TimeSpan.START_YEAR, year,year);
    timeSpan.setStartTimeConstraint(TimeSpan.START_MONTH, month,month);
    timeSpan.setStartTimeConstraint(TimeSpan.START_DAY, day,day);
    timeSpan.setStartTimeConstraint(TimeSpan.START_HOUR, hour,hour);
    timeSpan.setStartTimeConstraint(TimeSpan.START_MINUTE, minute,minute);
    timeSpan.setStartTimeConstraint(TimeSpan.START_SECOND, second,second);
    timeSpan.setDuractionConstraint(duration,duration);

    if (D) System.out.println("Start-Time Calendar toString: \n"+(timeSpan.getStartTimeCalendar()).toString());

    if (D) System.out.println("Number of lines in delta rate file = "+deltaRateFileLines.size());
    if (D) System.out.println("Number of lines in background rate file = "+backgroundRateFileLines.size());

    // init adjustable params:
    intiAdjParams();

  }


// make the adjustable parameters & the list
  private void intiAdjParams() {

    // make the seisTypeParam
    ArrayList seisOptionsStrings = new ArrayList();
    seisOptionsStrings.add(SEIS_TYPE_ADD_ON);
    seisOptionsStrings.add(SEIS_TYPE_BACKGROUND);
    seisOptionsStrings.add(SEIS_TYPE_BOTH);
    StringConstraint constraint = new StringConstraint(seisOptionsStrings);
    seisTypeParam = new StringParameter(SEIS_TYPE_NAME,constraint,SEIS_TYPE_BOTH);
    seisTypeParam.setInfo(SEIS_TYPE_INFO);


    // make the minMagParam
    minMagParam = new DoubleParameter(MIN_MAG_PARAM_NAME,MIN_MAG_PARAM_MIN,
                                      MIN_MAG_PARAM_MAX, MIN_MAG_PARAM_DEFAULT);
    minMagParam.setInfo(MIN_MAG_PARAM_INFO);

    //add these to the adjustable parameters list
    adjustableParams.addParameter(seisTypeParam);
    adjustableParams.addParameter(minMagParam);

    // add the change listener to parameters so that forecast can be updated
    // whenever any paramater changes
    seisTypeParam.addParameterChangeListener(this);
    minMagParam.addParameterChangeListener(this);
  }




  /**
  * Make the delta rate sources
  *
  */
  private  void makeDeltaRateSources() {

    // Debug
    String S = C + ": makeDeltaRateSources(): ";
    if( D ) System.out.println(S + "Starting");

    deltaRateSources = new ArrayList();
    double lat, lon;
    double duration = timeSpan.getDuration();
    double minMag = ((Double)minMagParam.getValue()).doubleValue();

    IncrementalMagFreqDist magFreqDist;
    PointEqkSource ptSource;

    // Get iterator over input-file lines
    ListIterator it = deltaRateFileLines.listIterator();

    // skip first two lines
    StringTokenizer st;
    st = new StringTokenizer(it.next().toString());
    st = new StringTokenizer(it.next().toString());

    while( it.hasNext() ) {

      // get next line
      st = new StringTokenizer(it.next().toString());

      lon =  Double.parseDouble(st.nextToken());
      lat =  Double.parseDouble(st.nextToken());

      magFreqDist = new IncrementalMagFreqDist(MAG_LOWER,MAG_UPPER,NUM_MAG);

      for(int i=0;i<NUM_MAG;i++) {
        double rate = Double.parseDouble(st.nextToken());
        magFreqDist.set(i,rate);
      }

      ptSource = new PointEqkSource(new Location(lat,lon,DEPTH),magFreqDist,duration,RAKE,DIP,minMag);
      if(ptSource.getNumRuptures() > 0) {
          deltaRateSources.add(ptSource);
          if(D) System.out.println(C+"makeDeltaRateSources(): numRups="+ptSource.getNumRuptures()+
                               " for source "+deltaRateSources.size());
      }
    }
    deltaSourcesAlreadyMade = true;
  }



  /**
  * Make the background rate sources
  *
  */
  private  void makeBackgroundRateSources() {

    // Debug
    String S = C + ": makeBackgroundRateSources(): ";
    if( D ) System.out.println(S + "Starting");

    //read background rates file if needed
    if(!backgroundRatesFileAlreadyRead){
      try {
        backgroundRateFileLines = FileUtils.loadJarFile( BACKGROUND_RATES_FILE_NAME );
      } catch(Exception e) {
        throw new RuntimeException("Background file could not be loaded");
      }
      backgroundRatesFileAlreadyRead = true;
    }

    backgroundRateSources = new ArrayList();
    double lat, lon;
    double duration = timeSpan.getDuration();
    double minMag = ((Double)minMagParam.getValue()).doubleValue();

    IncrementalMagFreqDist magFreqDist;
    PointEqkSource ptSource;

    // Get iterator over input-file lines
    ListIterator it = backgroundRateFileLines.listIterator();

    StringTokenizer st;

    while( it.hasNext() ) {

      // get next line
      st = new StringTokenizer(it.next().toString());

      // skip the event ID
      st.nextToken();

      // get lat and lon
      lon =  Double.parseDouble(st.nextToken());
      lat =  Double.parseDouble(st.nextToken());

      magFreqDist = new IncrementalMagFreqDist(MAG_LOWER,MAG_UPPER,NUM_MAG);

      // skip the mag=2, 2.1, ... 3.9
      for(int j=0; j<20; j++) st.nextToken();

      for(int i=0;i<NUM_MAG;i++) {
        double rate = Double.parseDouble(st.nextToken());
        magFreqDist.set(i,rate);
      }

      ptSource = new PointEqkSource(new Location(lat,lon,DEPTH),magFreqDist,duration,RAKE,DIP,minMag);
      if(ptSource.getNumRuptures() > 0) {
          backgroundRateSources.add(ptSource);

          if(D) System.out.println(C+"makeBackgroundRateSources(): numRups="+ptSource.getNumRuptures()+
                               " for source "+backgroundRateSources.size());
      }
    }
    backgroundSourcesAlreadyMade = true;
  }


    /**
     * Returns the  ith earthquake source
     *
     * @param iSource : index of the source needed
    */
    public ProbEqkSource getSource(int iSource) {
      return (ProbEqkSource) allSources.get(iSource);
    }


    /**
     * Get the number of earthquake sources
     *
     * @return integer
     */
    public int getNumSources(){
      return allSources.size();
    }


    /**
     * Return  iterator over all the earthquake sources
     */
    public Iterator getSourcesIterator() {
      Iterator i = getSourceList().iterator();
      return i;
    }

     /**
      * Get the list of all earthquake sources.
      *
      * @return ArrayList of Prob Earthquake sources
      */
     public ArrayList getSourceList(){
       return allSources;
     }


    /**
     * Return the name for this class
     *
     * @return : return the name for this class
     */
   public String getName(){
     return NAME;
   }


   /**
    * update the forecast
    **/
   public void updateForecast() {

     // make sure something has changed
     if(parameterChangeFlag) {

       allSources = new ArrayList();
       String seisType = (String) seisTypeParam.getValue();
       double minMag = ((Double)minMagParam.getValue()).doubleValue();

       // add delta rates if needed
       if(seisType.equals(SEIS_TYPE_ADD_ON) || seisType.equals(SEIS_TYPE_BOTH)) {
         // make them if needed
         if(!deltaSourcesAlreadyMade || minMag != oldMinMag)
             makeDeltaRateSources();
         allSources.addAll(deltaRateSources);
       }

       if(seisType.equals(SEIS_TYPE_BACKGROUND) || seisType.equals(SEIS_TYPE_BOTH)) {
         if(!backgroundSourcesAlreadyMade || minMag != oldMinMag)
             makeBackgroundRateSources();
         allSources.addAll(backgroundRateSources);
       }

       parameterChangeFlag = false;
       oldMinMag = minMag;

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
   public void parameterChange( ParameterChangeEvent event ) {
     parameterChangeFlag=true;
   }


   // this is temporary for testing purposes
   public static void main(String[] args) throws Exception{

     STEP_EqkRupForecast forecast = new STEP_EqkRupForecast();
     forecast.getAdjustableParameterList().getParameter(STEP_EqkRupForecast.SEIS_TYPE_NAME).setValue(STEP_EqkRupForecast.SEIS_TYPE_ADD_ON);
     forecast.updateForecast();
     System.out.println("startTimeFromCal:\n " + forecast.getTimeSpan().getStartTimeCalendar().toString());
     System.out.println("Duration: " + forecast.getTimeSpan().getDuration()+"  "+
                        forecast.getTimeSpan().getDurationUnits());
     System.out.println("getNumSources(): "+forecast.getNumSources());

     ProbEqkRupture rup;
     double rate;

     // check first one
     int index = 0;
     PointEqkSource qkSrc = (PointEqkSource) forecast.getSource(index);
     System.out.println("getNumRuptures(): "+qkSrc.getNumRuptures());
     double duration = qkSrc.getDuration();
     for(int i=0;i<qkSrc.getNumRuptures();i++) {
       rup = qkSrc.getRupture(i);
       Location loc = (Location) rup.getRuptureSurface().get(0,0);
       if(i==0) System.out.println("First Source:\n" + loc.getLongitude()+"  "+loc.getLatitude());
       rate = -Math.log(1-rup.getProbability())/duration;
       System.out.println((float)rup.getMag()+"  "+rate);
     }
     // check last one
     index = forecast.getNumSources()-1;
     qkSrc = (PointEqkSource) forecast.getSource(index);
     System.out.println("getNumRuptures(): "+qkSrc.getNumRuptures());
     duration = qkSrc.getDuration();
     for(int i=0;i<qkSrc.getNumRuptures();i++) {
       rup = qkSrc.getRupture(i);
       Location loc = (Location) rup.getRuptureSurface().get(0,0);
       if(i==0) System.out.println("Last Source:\n" + loc.getLongitude()+"  "+loc.getLatitude());
       rate = -Math.log(1-rup.getProbability())/duration;
       System.out.println((float)rup.getMag()+"  "+rate);
     }

   }

}
