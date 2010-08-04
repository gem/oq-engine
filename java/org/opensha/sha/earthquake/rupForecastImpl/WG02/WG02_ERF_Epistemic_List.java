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

package org.opensha.sha.earthquake.rupForecastImpl.WG02;

import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.exceptions.FaultException;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.IntegerParameter;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.earthquake.ERF_EpistemicList;
import org.opensha.sha.earthquake.EqkRupForecastAPI;

/**
 * <p>Title: WG02_ERF_Epistemic_List</p>
 * <p>Description: Working Group 2002 Epistemic List of ERFs. This class
 * reads a single file and constructs the forecasts.
 * </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author : Edward Field
 * @Date : April, 2003
 * @version 1.0
 */

public class WG02_ERF_Epistemic_List extends ERF_EpistemicList{

  //for Debug purposes
  private static final String  C = new String("WG02 ERF List");
  private boolean D = false;

  public static final String  NAME = new String("WG02 ERF List");

  /**
   * Static variable for input file name
   */
  private final static String INPUT_FILE_NAME_30yr = "org/opensha/sha/earthquake/rupForecastImpl/WG02/base_mod_23_wgt_n100.OpenSHA.30yr.txt";
  private final static String INPUT_FILE_NAME_20yr = "org/opensha/sha/earthquake/rupForecastImpl/WG02/base_mod_23_wgt_n100.OpenSHA.20yr.txt";
  private final static String INPUT_FILE_NAME_10yr = "org/opensha/sha/earthquake/rupForecastImpl/WG02/base_mod_23_wgt_n100.OpenSHA.10yr.txt";
  private final static String INPUT_FILE_NAME_5yr  = "org/opensha/sha/earthquake/rupForecastImpl/WG02/base_mod_23_wgt_n100.OpenSHA.5yr.txt";
  private final static String INPUT_FILE_NAME_1yr  = "org/opensha/sha/earthquake/rupForecastImpl/WG02/base_mod_23_wgt_n100.OpenSHA.1yr.txt";
  private String INPUT_FILE_NAME;

  // vector to hold the line numbers where each iteration starts
  private ArrayList iterationLineNumbers;

  // adjustable parameter primitives
  private int numIterations;
  private double rupOffset;
  private double deltaMag;
  private double gridSpacing;
  private String backSeis;
  private String grTail;

  // This is an array holding each line of the input file
  private ArrayList inputFileLines = null;

  // Stuff for background & GR tail seismicity params
  public final static String BACK_SEIS_NAME = new String ("Background Seismicity");
  public final static String GR_TAIL_NAME = new String ("GR Tail Seismicity");
  public final static String SEIS_INCLUDE = new String ("Include");
  public final static String SEIS_EXCLUDE = new String ("Exclude");
  ArrayList backSeisOptionsStrings = new ArrayList();
  ArrayList grTailOptionsStrings = new ArrayList();
  StringParameter backSeisParam;
  StringParameter grTailParam;

  // For rupture offset along fault parameter
  private final static String RUP_OFFSET_PARAM_NAME ="Rupture Offset";
  private Double DEFAULT_RUP_OFFSET_VAL= new Double(5);
  private final static String RUP_OFFSET_PARAM_UNITS = "km";
  private final static String RUP_OFFSET_PARAM_INFO = "Length of offset for floating ruptures";
  private final static double RUP_OFFSET_PARAM_MIN = 1;
  private final static double RUP_OFFSET_PARAM_MAX = 50;
  DoubleParameter rupOffset_Param;

  // Grid spacing for fault discretization
  private final static String GRID_SPACING_PARAM_NAME ="Fault Discretization";
  private Double DEFAULT_GRID_SPACING_VAL= new Double(1.0);
  private final static String GRID_SPACING_PARAM_UNITS = "km";
  private final static String GRID_SPACING_PARAM_INFO = "Grid spacing of fault surface";
  private final static double GRID_SPACING_PARAM_MIN = 0.1;
  private final static double GRID_SPACING_PARAM_MAX = 5;
  DoubleParameter gridSpacing_Param;

  // For delta mag parameter (magnitude discretization)
  private final static String DELTA_MAG_PARAM_NAME ="Delta Mag";
  private Double DEFAULT_DELTA_MAG_VAL= new Double(0.1);
  private final static String DELTA_MAG_PARAM_INFO = "Discretization of magnitude frequency distributions";
  private final static double DELTA_MAG_PARAM_MIN = 0.005;
  private final static double DELTA_MAG_PARAM_MAX = 0.5;
  DoubleParameter deltaMag_Param;

  // For num realizations parameter
  private final static String NUM_REALIZATIONS_PARAM_NAME ="Num Realizations";
  private Integer DEFAULT_NUM_REALIZATIONS_VAL= new Integer(10);
  private int NUM_REALIZATIONS_MIN = 1;
  private int NUM_REALIZATIONS_MAX = 100;
  private final static String NUM_REALIZATIONS_PARAM_INFO = "Number of Monte Carlo ERF realizations";
  IntegerParameter numRealizationsParam;

  /**
   *
   * No argument constructor
   */
  public WG02_ERF_Epistemic_List() {


    // create the timespan object with start time and duration in years
    timeSpan = new TimeSpan(TimeSpan.YEARS,TimeSpan.YEARS);
    // set the duration constraint as a list of Doubles
    ArrayList durationOptions = new ArrayList();
    durationOptions.add(new Double(1));
    durationOptions.add(new Double(5));
    durationOptions.add(new Double(10));
    durationOptions.add(new Double(20));
    durationOptions.add(new Double(30));
    timeSpan.setDurationConstraint(durationOptions);
    // set the start year - hard coded for now
    timeSpan.setStartTimeConstraint(TimeSpan.START_YEAR,2002,2002);
    timeSpan.setStartTime(2002);
    timeSpan.setDuration(30);
    timeSpan.addParameterChangeListener(this);

    // create and add adj params to list
    initAdjParams();

    // add the change listener to parameters so that forecast can be updated
    // whenever any paramater changes
    rupOffset_Param.addParameterChangeListener(this);
    deltaMag_Param.addParameterChangeListener(this);
    gridSpacing_Param.addParameterChangeListener(this);
    backSeisParam.addParameterChangeListener(this);
    grTailParam.addParameterChangeListener(this);
    numRealizationsParam.addParameterChangeListener(this);

  }


  // make the adjustable parameters & the list
  private void initAdjParams() {


    backSeisOptionsStrings.add(SEIS_EXCLUDE);
    backSeisOptionsStrings.add(SEIS_INCLUDE);
    backSeisParam = new StringParameter(BACK_SEIS_NAME, backSeisOptionsStrings,SEIS_EXCLUDE);

    grTailOptionsStrings.add(SEIS_EXCLUDE);
    grTailOptionsStrings.add(SEIS_INCLUDE);
    grTailParam = new StringParameter(GR_TAIL_NAME, backSeisOptionsStrings,SEIS_EXCLUDE);

    rupOffset_Param = new DoubleParameter(RUP_OFFSET_PARAM_NAME,RUP_OFFSET_PARAM_MIN,
        RUP_OFFSET_PARAM_MAX,RUP_OFFSET_PARAM_UNITS,DEFAULT_RUP_OFFSET_VAL);
    rupOffset_Param.setInfo(RUP_OFFSET_PARAM_INFO);

    gridSpacing_Param = new DoubleParameter(GRID_SPACING_PARAM_NAME,GRID_SPACING_PARAM_MIN,
        GRID_SPACING_PARAM_MAX,GRID_SPACING_PARAM_UNITS,DEFAULT_GRID_SPACING_VAL);
    gridSpacing_Param.setInfo(GRID_SPACING_PARAM_INFO);

    deltaMag_Param = new DoubleParameter(DELTA_MAG_PARAM_NAME,DELTA_MAG_PARAM_MIN,
        DELTA_MAG_PARAM_MAX,null,DEFAULT_DELTA_MAG_VAL);
    deltaMag_Param.setInfo(DELTA_MAG_PARAM_INFO);

    numRealizationsParam = new IntegerParameter(NUM_REALIZATIONS_PARAM_NAME,NUM_REALIZATIONS_MIN,
                                                NUM_REALIZATIONS_MAX, DEFAULT_NUM_REALIZATIONS_VAL);
    numRealizationsParam.setInfo(NUM_REALIZATIONS_PARAM_INFO);

    // add adjustable parameters to the list
    adjustableParams.addParameter(rupOffset_Param);
    adjustableParams.addParameter(gridSpacing_Param);
    adjustableParams.addParameter(deltaMag_Param);
    adjustableParams.addParameter(backSeisParam);
    adjustableParams.addParameter(grTailParam);
    adjustableParams.addParameter(numRealizationsParam);

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

     if(D) System.out.println(NAME+", updateForecast, parameterChangeFlag = " + parameterChangeFlag);
     if(D) System.out.println(NAME+", updateForecast, Duration = " + timeSpan.getDuration());

     // make sure something has changed
     if(parameterChangeFlag) {

       double duration = timeSpan.getDuration();

       // set the input filename according to duration
       if(duration == 1) {
         INPUT_FILE_NAME = INPUT_FILE_NAME_1yr;
       } else if (duration == 5) {
         INPUT_FILE_NAME = INPUT_FILE_NAME_5yr;;
       } else if (duration == 10) {
         INPUT_FILE_NAME = INPUT_FILE_NAME_10yr;
       } else if (duration == 20) {
         INPUT_FILE_NAME = INPUT_FILE_NAME_20yr;
       } else if (duration == 30) {
         INPUT_FILE_NAME = INPUT_FILE_NAME_30yr;
       }
       else
         throw new RuntimeException("that duration is not supported by "+NAME);


       // read the lines of the input files into a list
       try{ inputFileLines = FileUtils.loadJarFile( INPUT_FILE_NAME ); }
       catch( FileNotFoundException e){ System.out.println(e.toString()); }
       catch( IOException e){ System.out.println(e.toString());}

       // Exit if no data found in list
       if( inputFileLines == null) throw new
         FaultException(C + "No data loaded from "+INPUT_FILE_NAME+". File may be empty or doesn't exist.");

       // find the line numbers for the beginning of each iteration
       iterationLineNumbers = new ArrayList();
       StringTokenizer st;
       String test=null;
       for(int lineNum=0; lineNum < inputFileLines.size(); lineNum++) {
         st = new StringTokenizer((String) inputFileLines.get(lineNum));
         st.nextToken(); // skip the first token
         if(st.hasMoreTokens()) {
           test = st.nextToken();
           if(test.equals("ITERATIONS"))
             iterationLineNumbers.add(new Integer(lineNum));
         }
       }

       if(D) System.out.println(C+": number of iterations read = "+iterationLineNumbers.size());
       if(D)
         for(int i=0;i<iterationLineNumbers.size();i++)
           System.out.print("   "+ (Integer)iterationLineNumbers.get(i));

       // now set values for each parameter
       numIterations = ((Integer) numRealizationsParam.getValue()).intValue();
       rupOffset = ((Double)rupOffset_Param.getValue()).doubleValue();
       deltaMag = ((Double)deltaMag_Param.getValue()).doubleValue();
       gridSpacing = ((Double)gridSpacing_Param.getValue()).doubleValue();
       backSeis = (String)backSeisParam.getValue();
       grTail = (String)grTailParam.getValue();
       parameterChangeFlag = false;
     }

   }




   /**
    * get the number of Eqk Rup Forecasts in this list
    * @return : number of eqk rup forecasts in this list
    */
   public int getNumERFs() {
     return numIterations;
   }


  /**
   * get the ERF in the list with the specified index
   * @param index : index of Eqk rup forecast to return
   * @return
   */
  public EqkRupForecastAPI getERF(int index) {

    // get the sublist from the inputFileLines
    int firstLine = ((Integer) iterationLineNumbers.get(index)).intValue();
    int lastLine = ((Integer) iterationLineNumbers.get(index+1)).intValue();
    ArrayList inputFileStrings = new ArrayList();
    for(int i=firstLine;i<lastLine;++i)
      inputFileStrings.add(inputFileLines.get(i));
    return new WG02_EqkRupForecast(inputFileStrings, rupOffset, gridSpacing,
                             deltaMag, backSeis, grTail, "no name", timeSpan);

  }

  /**
   * get the weight of the ERF at the specified index
   * @param index : index of ERF
   * @return : relative weight of ERF
   */
  public double getERF_RelativeWeight(int index) {
    return 1.0;
  }

  /**
   * Return the vector containing the Double values with
   * relative weights for each ERF
   * @return : ArrayList of Double values
   */
  public ArrayList getRelativeWeightsList() {
    ArrayList relativeWeight  = new ArrayList();
    for(int i=0; i<numIterations; i++)
      relativeWeight.add(new Double(1.0));
    return relativeWeight;
  }

   // this is temporary for testing purposes
   public static void main(String[] args) {
     WG02_ERF_Epistemic_List list = new WG02_ERF_Epistemic_List();
     list.updateForecast();
     EqkRupForecastAPI fcast = list.getERF(4);
  }

}
