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

package org.opensha.sha.earthquake.rupForecastImpl.Frankel96;

import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.ArrayList;
import java.util.ListIterator;
import java.util.StringTokenizer;

import org.opensha.commons.calc.MomentMagCalc;
import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.exceptions.FaultException;
import org.opensha.commons.geo.Location;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.PointEqkSource;
import org.opensha.sha.faultSurface.EvenlyGriddedSurface;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.faultSurface.FrankelGriddedSurface;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;


/**
 * <p>Title: Frankel96_EqkRupForecast</p>
 * <p>Description:Frankel 1996 Earthquake Rupture Forecast. This class
 * reads a single file for the fault sources, and another file for the
 * background seismicity, and then creates the USGS/CGS 1996 California ERF.
 * This does not yet include any C zones.
 * </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author : Nitin Gupta, Vipin Gupta, and Edward Field
 * @Date : Aug 31, 2002
 * @version 1.0
 */

public class Frankel96_EqkRupForecast extends EqkRupForecast{

  //for Debug purposes
  private static String  C = new String("Frankel96_EqkRupForecast");
  private boolean D = false;

  // name of this ERF
  public static String NAME = new String("USGS/CGS 1996 Cal. ERF");

  private double GRID_SPACING = 1.0;
  private double B_VALUE =0.9;
  private double MAG_LOWER = 6.5;
  private double DELTA_MAG = 0.1;

  private String FAULT_CLASS_A = "A";
  private String FAULT_CLASS_B = "B";
  private String FAULTING_STYLE_SS = "SS";
  private String FAULTING_STYLE_R = "R";
  private String FAULTING_STYLE_N = "N";

  /**
   * used for error checking
   */
  protected final static FaultException ERR = new FaultException(
           C + ": loadFaultTraces(): Missing metadata from trace, file bad format.");

  /**
   * Static variable for input file names
   */
  private final static String INPUT_FAULT_FILE_NAME = "org/opensha/sha/earthquake/rupForecastImpl/Frankel96/Frankel96_CAL_all.txt";
  private final static String INPUT_BACK_SEIS_FILE_NAME = "org/opensha/sha/earthquake/rupForecastImpl/Frankel96/CAagrid.asc";

  /**
   * Vectors for holding the various sources, separated by type
   */
  private ArrayList FrankelA_CharEqkSources;
  private ArrayList FrankelB_CharEqkSources;
  private ArrayList FrankelB_GR_EqkSources;
  private ArrayList FrankelBackgrSeisSources;
  private ArrayList allSources;


  // This is an array holding each line of the input file
  private ArrayList inputFaultFileLines = null;
  private ArrayList inputBackSeisFileLines = null;


  // fault-model parameter stuff
  public final static String FAULT_MODEL_NAME = new String ("Fault Model");
  public final static String FAULT_MODEL_FRANKEL = new String ("Frankel's");
  public final static String FAULT_MODEL_STIRLING = new String ("Stirling's");
  // make the fault-model parameter
  ArrayList faultModelNamesStrings = new ArrayList();
  StringParameter faultModelParam;

  // fault-model parameter stuff
  public final static String BACK_SEIS_NAME = new String ("Background Seismicity");
  public final static String BACK_SEIS_INCLUDE = new String ("Include");
  public final static String BACK_SEIS_EXCLUDE = new String ("Exclude");
  public final static String BACK_SEIS_ONLY = new String ("Only Background");
  // make the fault-model parameter
  ArrayList backSeisOptionsStrings = new ArrayList();
  StringParameter backSeisParam;


  // For fraction of moment rate on GR parameter
  private final static String FRAC_GR_PARAM_NAME ="GR Fraction on B Faults";
  private Double DEFAULT_FRAC_GR_VAL= new Double(0.5);
  private final static String FRAC_GR_PARAM_UNITS = null;
  private final static String FRAC_GR_PARAM_INFO = "Fraction of moment-rate put into GR dist on class-B faults";
  private final static double FRAC_GR_PARAM_MIN = 0;
  private final static double FRAC_GR_PARAM_MAX = 1;
  DoubleParameter fracGR_Param;

  // For rupture offset lenth along fault parameter
  private final static String RUP_OFFSET_PARAM_NAME ="Rupture Offset";
  private Double DEFAULT_RUP_OFFSET_VAL= new Double(10);
  private final static String RUP_OFFSET_PARAM_UNITS = "km";
  private final static String RUP_OFFSET_PARAM_INFO = "Length of offset for floating ruptures";
  private final static double RUP_OFFSET_PARAM_MIN = 1;
  private final static double RUP_OFFSET_PARAM_MAX = 100;
  DoubleParameter rupOffset_Param;

  /**
   *
   * No argument constructor
   */
  public Frankel96_EqkRupForecast() {

    // create the timespan object with start time and duration in years
    timeSpan = new TimeSpan(TimeSpan.NONE,TimeSpan.YEARS);
    timeSpan.addParameterChangeListener(this);

    // create and add adj params to list
    initAdjParams();


    // add the change listener to parameters so that forecast can be updated
    // whenever any paramater changes
    faultModelParam.addParameterChangeListener(this);
    fracGR_Param.addParameterChangeListener(this);
    rupOffset_Param.addParameterChangeListener(this);
    backSeisParam.addParameterChangeListener(this);

    // read the lines of the input files into a list
    try{ inputFaultFileLines = FileUtils.loadJarFile( INPUT_FAULT_FILE_NAME ); }
    catch( FileNotFoundException e){ System.out.println(e.toString()); }
    catch( IOException e){ System.out.println(e.toString());}

    try{ inputBackSeisFileLines = FileUtils.loadJarFile( INPUT_BACK_SEIS_FILE_NAME ); }
    catch( FileNotFoundException e){ System.out.println(e.toString()); }
    catch( IOException e){ System.out.println(e.toString());}

    // Exit if no data found in list
    if( inputFaultFileLines == null) throw new
           FaultException(C + "No data loaded from "+INPUT_FAULT_FILE_NAME+". File may be empty or doesn't exist.");

    // Exit if no data found in list
    if( inputBackSeisFileLines == null) throw new
           FaultException(C + "No data loaded from "+INPUT_BACK_SEIS_FILE_NAME+". File may be empty or doesn't exist.");

  }

	// make the adjustable parameters & the list
	  private void initAdjParams() {
	
	  faultModelNamesStrings.add(FAULT_MODEL_FRANKEL);
	  faultModelNamesStrings.add(FAULT_MODEL_STIRLING);
	  faultModelParam = new StringParameter(FAULT_MODEL_NAME, faultModelNamesStrings,
	                                        (String)faultModelNamesStrings.get(0));
	
	  backSeisOptionsStrings.add(BACK_SEIS_EXCLUDE);
	  backSeisOptionsStrings.add(BACK_SEIS_INCLUDE);
	  backSeisOptionsStrings.add(BACK_SEIS_ONLY);
	  backSeisParam = new StringParameter(BACK_SEIS_NAME, backSeisOptionsStrings,BACK_SEIS_INCLUDE);
	
	  fracGR_Param = new DoubleParameter(FRAC_GR_PARAM_NAME,FRAC_GR_PARAM_MIN,
	                                     FRAC_GR_PARAM_MAX,FRAC_GR_PARAM_UNITS,DEFAULT_FRAC_GR_VAL);
	  fracGR_Param.setInfo(FRAC_GR_PARAM_INFO);
	
	  rupOffset_Param = new DoubleParameter(RUP_OFFSET_PARAM_NAME,RUP_OFFSET_PARAM_MIN,
	                                        RUP_OFFSET_PARAM_MAX,RUP_OFFSET_PARAM_UNITS,DEFAULT_RUP_OFFSET_VAL);
	  rupOffset_Param.setInfo(RUP_OFFSET_PARAM_INFO);
	
	/* COMMENTED OUT FOR THIS VERSION
	// add adjustable parameters to the list
	  adjustableParams.addParameter(faultModelParam);
	  adjustableParams.addParameter(fracGR_Param);
	  adjustableParams.addParameter(rupOffset_Param);
	  adjustableParams.addParameter(backSeisParam);
	*/
	
	}
  
  /**
   * Read the Fault file and make the sources
   *
   * @throws FaultException
   */
  private  void makeFaultSources() throws FaultException{

    FrankelA_CharEqkSources = new ArrayList();
    FrankelB_CharEqkSources = new ArrayList();
    FrankelB_GR_EqkSources = new ArrayList();

    // Debug
    String S = C + ": makeSoureces(): ";
    if( D ) System.out.println(S + "Starting");
    EvenlyGriddedSurfaceAPI surface;
    String  faultClass="", faultingStyle, faultName="";
    int i;
    double   lowerSeismoDepth, upperSeismoDepth;
    double lat, lon, rake=0;
    double mag=0;  // used for magChar and magUpper (latter for the GR distributions)
    double charRate=0, dip=0, downDipWidth=0, depthToTop=0;

    // get adjustable parameters values
    double fracGR = ((Double) fracGR_Param.getValue()).doubleValue();
    String faultModel = (String) faultModelParam.getValue();
    double rupOffset = ((Double) rupOffset_Param.getValue()).doubleValue();

    double timeDuration =  timeSpan.getDuration();

    // Loop over lines of input file and create each source in the process
    ListIterator it = inputFaultFileLines.listIterator();
    while( it.hasNext() ){
          StringTokenizer st = new StringTokenizer(it.next().toString());

            //first word of first line is the fault class (A or B)
            faultClass = new String(st.nextToken());

            // 2nd word is the faulting style; set rake accordingly
            faultingStyle = new String(st.nextToken());

            //for Strike slip fault
            if(faultingStyle.equalsIgnoreCase(FAULTING_STYLE_SS))
              rake =0;

            //for reverse fault
            if(faultingStyle.equalsIgnoreCase(FAULTING_STYLE_R))
              rake =90;

            //for normal fault
            if(faultingStyle.equalsIgnoreCase(FAULTING_STYLE_N))
              rake =-90;

            //reading the fault name
            faultName = new String(st.nextToken());

            if(D) System.out.println(C+":FaultName::"+faultName);

          // get the 2nd line from the file
          st = new StringTokenizer(it.next().toString());

          // 1st word is magnitude
          mag=Double.parseDouble(st.nextToken());

          // 2nd word is charRate
          charRate=Double.parseDouble(st.nextToken());


          // get the third line from the file
          st=new StringTokenizer(it.next().toString());

          // 1st word is dip
          dip=Double.parseDouble(st.nextToken());
          // 2nd word is down dip width
          downDipWidth=Double.parseDouble(st.nextToken());
          // 3rd word is the depth to top of fault
          depthToTop=Double.parseDouble(st.nextToken());

          // Calculate upper and lower seismogenic depths
          upperSeismoDepth = depthToTop;
          lowerSeismoDepth = depthToTop + downDipWidth*Math.sin((Math.toRadians(Math.abs(dip))));

          // get the 4th line from the file that gives the number of points on the fault trace
          int numOfDataLines = Integer.parseInt(it.next().toString().trim());

          FaultTrace faultTrace= new FaultTrace(faultName);

          //based on the num of the data lines reading the lat and long points for rthe faults
          for(i=0;i<numOfDataLines;++i) {
              if( !it.hasNext() ) throw ERR;
              st =new StringTokenizer(it.next().toString().trim());

              try{ lat = new Double(st.nextToken()).doubleValue(); }
              catch( NumberFormatException e){ throw ERR; }
              try{ lon = new Double(st.nextToken()).doubleValue(); }
              catch( NumberFormatException e){ throw ERR; }

              Location loc = new Location(lat, lon, upperSeismoDepth);
              faultTrace.add(loc.clone());
          }

         // reverse data ordering if dip negative, make positive and reverse trace order
          if( dip < 0 ) {
             faultTrace.reverse();
             dip *= -1;
          }

          if( D ) System.out.println(C+":faultTrace::"+faultTrace.toString());

          if(faultModel.equals(FAULT_MODEL_FRANKEL)) {
            surface = new FrankelGriddedSurface( faultTrace, dip, upperSeismoDepth,
                                                   lowerSeismoDepth, GRID_SPACING);
          }
          else {
            surface = new StirlingGriddedSurface( faultTrace, dip, upperSeismoDepth,
                                                   lowerSeismoDepth, GRID_SPACING);
          }
          // Now make the source(s)
          if(faultClass.equalsIgnoreCase(FAULT_CLASS_B) && mag>6.5){
            // divide the rate according the faction assigned to GR dist
            double rate = (1.0-fracGR)*charRate;
            double moRate = fracGR*charRate*MomentMagCalc.getMoment(mag);

            // make the GR source
            if(moRate>0.0) {
              Frankel96_GR_EqkSource frankel96_GR_src = new Frankel96_GR_EqkSource(rake,B_VALUE,MAG_LOWER,
                                                   mag,moRate,DELTA_MAG,rupOffset,(EvenlyGriddedSurface)surface, faultName);
              frankel96_GR_src.setTimeSpan(timeDuration);
              FrankelB_GR_EqkSources.add(frankel96_GR_src);
            }
            // now make the Char source
            if(rate>0.0) {
              Frankel96_CharEqkSource frankel96_Char_src = new  Frankel96_CharEqkSource(rake,mag,rate,
                                                      (EvenlyGriddedSurface)surface, faultName);
              frankel96_Char_src.setTimeSpan(timeDuration);
              FrankelB_CharEqkSources.add(frankel96_Char_src);
            }
          }
          else if (faultClass.equalsIgnoreCase(FAULT_CLASS_B)) {    // if class B and mag<=6.5, it's all characteristic
            Frankel96_CharEqkSource frankel96_Char_src = new  Frankel96_CharEqkSource(rake,mag,charRate,
                                                      (EvenlyGriddedSurface)surface, faultName);
            frankel96_Char_src.setTimeSpan(timeDuration);
            FrankelB_CharEqkSources.add(frankel96_Char_src);

          }
          else if (faultClass.equalsIgnoreCase(FAULT_CLASS_A)) {   // class A fault
            Frankel96_CharEqkSource frankel96_Char_src = new  Frankel96_CharEqkSource(rake,mag,charRate,
                                                      (EvenlyGriddedSurface)surface, faultName);
            frankel96_Char_src.setTimeSpan(timeDuration);
            FrankelA_CharEqkSources.add(frankel96_Char_src);
          }
          else {
            throw new FaultException(C+" Error - Bad fault Class :"+faultClass);
          }

    }  // bottom of loop over input-file lines

  }









  /**
  * Read the Background Seismicity file and make the sources
  *
  */
  private  void makeBackSeisSources() {

    // Debug
    String S = C + ": makeBackSeisSources(): ";
    if( D ) System.out.println(S + "Starting");

    FrankelBackgrSeisSources = new ArrayList();

    double lat, lon, rate, rateAtMag5;

    double aveRake=0.0;
    double aveDip=90;
    double tempMoRate = 1.0;
    double bValue = B_VALUE;
    double magUpper=7.0;
    double magDelta=0.2;
    double magLower1=0.0;
    int    numMag1=36;
    double magLower2=5.0;
    int    numMag2=11;

    // GR dist between mag 0 and 7, delta=0.2
    GutenbergRichterMagFreqDist grDist1 = new GutenbergRichterMagFreqDist(magLower1,numMag1,magDelta,
                                                                          tempMoRate,bValue);

    // GR dist between mag 5 and 7, delta=0.2
    GutenbergRichterMagFreqDist grDist2;

    PointEqkSource pointPoissonSource;

    // set timespan
    double timeDuration = timeSpan.getDuration();

    // Get iterator over input-file lines
    ListIterator it = inputBackSeisFileLines.listIterator();

    // skip first five header lines
    StringTokenizer st = new StringTokenizer(it.next().toString());
    st = new StringTokenizer(it.next().toString());
    st = new StringTokenizer(it.next().toString());
    st = new StringTokenizer(it.next().toString());
    st = new StringTokenizer(it.next().toString());

    while( it.hasNext() ){

      // get next line
      st = new StringTokenizer(it.next().toString());

      lon =  Double.parseDouble(st.nextToken());
      lat =  Double.parseDouble(st.nextToken());
      rate = Double.parseDouble(st.nextToken());

      if (rate > 0.0) {  // ignore locations with a zero rate

        // scale all so the incremental rate at mag=0 index equals rate
        grDist1.scaleToIncrRate((int) 0,rate);

        // now get the rate at the mag=5 index
        rateAtMag5 = grDist1.getIncrRate((int) 25);

        // now scale all in the dist we want by rateAtMag5 (index 0 here)
        grDist2 = new GutenbergRichterMagFreqDist(magLower2,numMag2,magDelta,tempMoRate,bValue);
        grDist2.scaleToIncrRate((int) (0),rateAtMag5);

        // now make the source
        pointPoissonSource = new PointEqkSource(new Location(lat,lon),
            grDist2, timeDuration, aveRake,aveDip);

        // add the source
        FrankelBackgrSeisSources.add(pointPoissonSource);
      }
    }
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
      * Get the list of all earthquake sources.
      *
      * @return ArrayList of Prob Earthquake sources
      */
     public ArrayList  getSourceList(){

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

       // get value of background seismicity paramter
       String backSeis = (String) backSeisParam.getValue();

       allSources = new ArrayList();

       if (backSeis.equalsIgnoreCase(BACK_SEIS_INCLUDE)) {
         makeFaultSources();
         makeBackSeisSources();
         // now create the allSources list:
         allSources.addAll(FrankelA_CharEqkSources);
         allSources.addAll(FrankelB_CharEqkSources);
         allSources.addAll(FrankelB_GR_EqkSources);
         allSources.addAll(FrankelBackgrSeisSources);
       }
       else if (backSeis.equalsIgnoreCase(BACK_SEIS_EXCLUDE)) {
         makeFaultSources();
         // now create the allSources list:
         allSources.addAll(FrankelA_CharEqkSources);
         allSources.addAll(FrankelB_CharEqkSources);
         allSources.addAll(FrankelB_GR_EqkSources);
       }
       else {// only background sources
        makeBackSeisSources();
        // now create the allSources list:
        allSources.addAll(FrankelBackgrSeisSources);
       }

       parameterChangeFlag = false;
/*
String tempName;
for(int i=0;i<allSources.size();i++) {
  tempName = ((ProbEqkSource) allSources.get(i)).getName();
  System.out.println("source "+ i +"is "+tempName);
}
*/
     }

   }


   // this is temporary for testing purposes
   public static void main(String[] args) {

     Frankel96_EqkRupForecast frankCast = new Frankel96_EqkRupForecast();
     frankCast.updateForecast();
     System.out.println("num sources="+frankCast.getNumSources());

     System.out.println("\n"+frankCast.getSource(0).getName()+":\n");
     for(int i=0; i<frankCast.getSource(0).getNumRuptures(); i++)
       System.out.println("  rupture #"+i+": \n\n"+frankCast.getSource(0).getRupture(i).getInfo());

//     for(int i=0; i<frankCast.getNumSources(); i++)
//       System.out.println(i+"th source: "+frankCast.getSource(i).getName());
/*
     double totRate=0, totProb=1, prob;
     int i,j, totRup;
     int totSrc= frankCast.getNumSources();
     for(i=0; i<totSrc; i++){
       ProbEqkSource src = (ProbEqkSource) frankCast.getSource(i);
       totRup=src.getNumRuptures();
       if(i==0) System.out.println("numRup for src0 ="+totRup);
       for(j=0; j<totRup; j++) {
         prob = src.getRupture(j).getProbability();
         totProb *= (1-prob);
         totRate += -1*Math.log(1-prob)/50;
         if(j==0 && i==0)
           System.out.println("mag, prob for src0, rup 0="+src.getRupture(j).getMag()+"; "+prob);
         if(j==0 && i==1)
           System.out.println("mag, prob for src1, rup 0="+src.getRupture(j).getMag()+"; "+prob);
         if(j==0 && i==2)
           System.out.println("mag, prob for src2, rup 0="+src.getRupture(j).getMag()+"; "+prob);

       }
     }
       System.out.println("main(): totRate="+totRate+"; totProb="+totProb);
*/
  }

}
