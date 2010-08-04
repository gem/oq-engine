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

import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.ListIterator;
import java.util.StringTokenizer;

import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.geo.Location;
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
 * @Date : March 24, 2003
 * @version 1.0
 */

  public class STEP_AlaskanPipeForecast extends EqkRupForecast
    implements ParameterChangeListener{

  //for Debug purposes
  private static String  C = new String("STEP_AlaskanPipeForecast");
  private boolean D = false;

  // name of this ERF
  public static String  NAME = new String("STEP Alaskan Pipeline ERF");

  // Input file name
  //private final static String INPUT_FILE_NAME = "/opt/install/apache-tomcat-5.5.20/webapps/OpenSHA/WEB-INF/dataFiles/PipelineGrid.txt";
  private final static String INPUT_FILE_NAME = "org/opensha/sha/earthquake/rupForecastImpl/step/PipelineGrid.txt";


  // ArrayList of input file lines
  private ArrayList inputFileLines;

  /**
   * timespan field in yrs for now (but have to ultimately make it a TimeSpan class variable)
   */
//  private TimeSpan timeSpan;

  private static final double RAKE=0.0;
  private static final double DIP=90.0;
  private static final double MAG_LOWER=4;
  private static final double MAG_UPPER=8;
  private static final int    NUM_MAG=41;
  private static final double DEPTH=0;

  // vector to hold the sources
  ArrayList sources;


  /**
   *
   * No argument constructor
   */
  public STEP_AlaskanPipeForecast() {

    // read the lines of the input files into a list
    try{ inputFileLines = FileUtils.loadJarFile( INPUT_FILE_NAME ); }
    catch( FileNotFoundException e){ System.out.println(e.toString()); }
    catch( IOException e){ System.out.println(e.toString());}

    // Create the timeSpan & set its constraints
    StringTokenizer st = new StringTokenizer(inputFileLines.get(0).toString());
    int year =  (new Integer(st.nextToken())).intValue();
    int month =  (new Integer(st.nextToken())).intValue();
    int day =  (new Integer(st.nextToken())).intValue();
    int hour =  (new Integer(st.nextToken())).intValue();
    int minute =  (new Integer(st.nextToken())).intValue();
    int second =  (new Integer(st.nextToken())).intValue();

    if(D) System.out.println("year="+year+"; month="+month+"; day="+day+"; hour="+
                             hour+"; minute="+minute+"; second="+second);

    st = new StringTokenizer(inputFileLines.get(1).toString());
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

    if (D) System.out.println("Number of lines in file = "+inputFileLines.size());

    // Make the sources
    makeSources();
    inputFileLines = null;
  }


  /**
  * Make the sources
  *
  */
  private  void makeSources() {

    // Debug
    String S = C + ": makeSources(): ";
    if( D ) System.out.println(S + "Starting");

    this.sources = new ArrayList();
    double lat, lon;
    double duration = timeSpan.getDuration();

    IncrementalMagFreqDist magFreqDist;
    PointEqkSource ptSource;

    // Get iterator over input-file lines
    ListIterator it = inputFileLines.listIterator();

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
        if (D) System.out.println("rate(mag="+magFreqDist.getX(i)+")="+rate);
        if(i <20)
          magFreqDist.set(i,0.0);
        else {
          // Lucy's 1 day --> 18 months correction, divided by the number of days to get the rate per day
//          rate *= 230/timeSpan.getDuration();
          // rupLen correction
          double rupLen = Math.pow(10.0,-3.55 + 0.74*magFreqDist.getX(i) );
//          if (D) System.out.println("rupLen(mag="+magFreqDist.getX(i)+")="+rupLen);
          rate *= rupLen/10.6;
          magFreqDist.set(i,rate);
        }
      }

      ptSource = new PointEqkSource(new Location(lat,lon,DEPTH),magFreqDist,duration,RAKE,DIP);
      sources.add(ptSource);

      if(D) System.out.println(C+"makeSources(): numRups="+ptSource.getNumRuptures()+
                               " for source "+sources.size());
    }
  }





  /**
   * This method sets the time-span field
   * @param time
   */
  public void setTimeSpan(TimeSpan timeSpan){
  }


    /**
     * Returns the  ith earthquake source
     *
     * @param iSource : index of the source needed
    */
    public ProbEqkSource getSource(int iSource) {

      return (ProbEqkSource) sources.get(iSource);
    }

    /**
     * Get the number of earthquake sources
     *
     * @return integer
     */
    public int getNumSources(){
      return sources.size();
    }

    /**
     * Return  iterator over all the earthquake sources
     *
     * @return Iterator over all earhtquake sources
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
       return sources;
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
//     if(parameterChangeFlag) {


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
   public static void main(String[] args) {

     STEP_AlaskanPipeForecast forecast = new STEP_AlaskanPipeForecast();
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
     double cumRate=0;
     for(int i=qkSrc.getNumRuptures()-1;i>=0;i--) {
       rup = qkSrc.getRupture(i);
       Location loc = (Location) rup.getRuptureSurface().get(0,0);
       if(i==0) System.out.println("Last Source:\n" + loc.getLongitude()+"  "+loc.getLatitude());
       rate = -Math.log(1-rup.getProbability());
       cumRate += rate;
       System.out.println((float)rup.getMag()+"  "+rate+"  "+cumRate);
     }

   }

}
