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

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.ListIterator;
import java.util.StringTokenizer;

import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.exceptions.FaultException;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.IntegerParameter;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.TreeBranchWeightsParameter;
import org.opensha.commons.util.FileUtils;
import org.opensha.commons.util.RunScript;
import org.opensha.sha.earthquake.ERF_EpistemicList;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.earthquake.rupForecastImpl.remote.RemoteEqkRupForecastAPI;
import org.opensha.sha.earthquake.rupForecastImpl.remoteERF_Clients.WG02_EqkRupForecastClient;

/**
 * <p>Title: WG02_FortranWrappedERF_EpistemicList</p>
 * <p>Description: Working Group 2002 Epistemic List of ERFs. This class
 * reads a single file and constructs the forecasts.
 * </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author : Edward Field, Nitin Gupta & Vipin Gupta
 * @Date : October 6, 2003
 * @Modified: October 16,2003 : Added The new parameters
 * @version 1.0
 */

public class WG02_FortranWrappedERF_EpistemicList extends ERF_EpistemicList{

  //for Debug purposes
  private static final String  C = new String("WG02_FortranWrappedERF_EpistemicList");
  private boolean D = false;

  public static final String  NAME = new String("WG02 Fortran Wrapped ERF List");

  /**
   * Static variable for input file name
   */
  private final static String WG02_CODE_PATH ="/usr/local/tomcat/default/webapps/OpenSHA/wg99/wg99_src_v27/";
  // this is the old path on gravity
//  private final static String WG02_CODE_PATH ="/opt/install/apache-tomcat-5.5.20/webapps/OpenSHA/wg99/wg99_src_v27/";
  private final static String WG02_INPUT_FILE ="base_OpenSHA.inp";   // the templet WG02-code input file modified for OpenSHA purposes
  private final static String WG02_OPENSHA_INPUT_FILE = "OpenSHA.inp";     // the WG02-code input file that we create on the fly
  public final static String INPUT_FILE_NAME_1 = "WG02_WRAPPER_INPUT.DAT"; // the WG02-code output file that we read
  // output file from WG-02 code that contains substanial info., not used anywhere in OpenSHA just created for info purposes
  public final static String INPUT_FILE_NAME_2 ="OpenSHA.out3";
  public final static String WG02_DIRS = "wg02_dirs/";

  private final static String TIME_PRED_FILE_01YRS = "time_pred_2002_1yr_n1000_rand.txt";
  private final static String TIME_PRED_FILE_05YRS = "time_pred_2002_5yr_n1000_rand.txt";
  private final static String TIME_PRED_FILE_10YRS = "time_pred_2002_10yr_n1000_rand.txt";
  private final static String TIME_PRED_FILE_20YRS = "time_pred_2002_20yr_n1000_rand.txt";
  private final static String TIME_PRED_FILE_30YRS = "time_pred_2002_30yr_rand.dat";


  // vector to hold the line numbers where each iteration starts
  protected ArrayList iterationLineNumbers;

  // adjustable parameter primitives
  protected int numIterations;
  protected double rupOffset;
  protected double deltaMag;
  protected double gridSpacing;
  protected String backSeis;
  protected String grTail;

  // This is an array holding each line of the input file
  protected ArrayList inputFileLines = null;

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
  private Integer NUM_REALIZATIONS_MIN= new Integer(1);
  private Integer NUM_REALIZATIONS_MAX= new Integer(1000);
  private final static String NUM_REALIZATIONS_PARAM_INFO = "Number of Monte Carlo ERF realizations";
  IntegerParameter numRealizationsParam;


  //Static String Declaration
  private final static String NUMBER_OF_ITERATIONS = "number of Monte Carlo realizations";
  private final static String NUM_FAULTS = "*** Fault Inputs";
  private final static String FAULT_READ ="*** Fault ";
  private final static String PROB_NUM_STRING ="*** Probability Model";
  private final static String PROB_WTS_STRING ="            weights for probability models";
  private final static String N_YEAR_STRING = "nYr (length of probability interval in years)";


  //static Param Names
  private final static String POISSON ="Poisson";
  private final static String BPT = "BPT";
  private final static String BPT_STEP = "BPT w/ STEP";
  private final static String EMPIRICAL = "Empirical";
  private final static String TIME_PRED = "Time Pred.";
  private final static String PROB_MODEL_WTS = " Prob. Model Wts";

  /**
   *
   * No argument constructor
   */
  public WG02_FortranWrappedERF_EpistemicList() {

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
    timeSpan.addParameterChangeListener(this);
    // the default value is set in the initAdjParams() method

    // create and add adj params to list
    initAdjParams();
  }


  // configures the WG02 Fortran code input file and runs the code
   private void runFortranCode(String dirName){

     int numRealization = ((Integer)adjustableParams.getParameter(NUM_REALIZATIONS_PARAM_NAME).getValue()).intValue();

     double duration = timeSpan.getDuration();

     // set the filename for the time-dependent SAF model according to duration
     String timeDepFile;
     if(duration == 1)
       timeDepFile = TIME_PRED_FILE_01YRS;
     else if (duration == 5)
       timeDepFile = TIME_PRED_FILE_05YRS;
     else if (duration == 10)
       timeDepFile = TIME_PRED_FILE_10YRS;
     else if (duration == 20)
       timeDepFile = TIME_PRED_FILE_20YRS;
     else
       timeDepFile = TIME_PRED_FILE_30YRS;


     try {
       FileReader fr = new FileReader(WG02_CODE_PATH+WG02_INPUT_FILE);
       BufferedReader  br = new BufferedReader(fr);
       String lineFromInputFile = br.readLine();
       ArrayList fileLines = new ArrayList();

       //number of Faults
       int numFaults=7;   // hard coded with known value
       int faultsRead = 0;

       //reading each line of file until the end of file
       while(lineFromInputFile != null){

         // looking for number-of-years duration line
         if(lineFromInputFile.endsWith(N_YEAR_STRING))
           lineFromInputFile = ((int) duration) +"  "+N_YEAR_STRING;

         // looking for number of realizations value line
         if(lineFromInputFile.endsWith(NUMBER_OF_ITERATIONS))
           lineFromInputFile = numRealization +"  "+NUMBER_OF_ITERATIONS;

         // If it's a fault, set the probability model weights
         if(lineFromInputFile.startsWith(FAULT_READ+(faultsRead+1))){
           if(D) System.out.println("Reading Fault: "+lineFromInputFile);
           fileLines.add(lineFromInputFile);
           ++faultsRead;
           //reading the fault Name
           String faultName =br.readLine();
           fileLines.add(faultName);
           //reading the file further below till num of prob models for that fault
           lineFromInputFile =br.readLine();
           fileLines.add(lineFromInputFile);
           while(!lineFromInputFile.startsWith(PROB_NUM_STRING)){
             lineFromInputFile=br.readLine();
             fileLines.add(lineFromInputFile);
           }
           if(D) System.out.println("After while to iterate till the Prob String");
           lineFromInputFile =br.readLine();
           fileLines.add(lineFromInputFile);
           StringTokenizer st = new StringTokenizer(lineFromInputFile);
           //extracting the number fo prob model for that fault from the file
           int numberOfProbModels =Integer.parseInt(st.nextToken());
           fileLines.add(br.readLine());

           //reading the line from the file that tells wts for different prob. model for that fault
           String probModels = br.readLine();
           ParameterList paramList =(ParameterList)this.adjustableParams.getParameter(faultName+this.PROB_MODEL_WTS).getValue();
           double pois = ((Double)paramList.getParameter(this.POISSON).getValue()).doubleValue();
           double bpt = ((Double)paramList.getParameter(this.BPT).getValue()).doubleValue();
           double bpt_step = ((Double)paramList.getParameter(this.BPT_STEP).getValue()).doubleValue();
           double empirical = ((Double)paramList.getParameter(this.EMPIRICAL).getValue()).doubleValue();
           String probModelWts = empirical+" "+pois+" "+bpt_step+" "+bpt;
           if(D) System.out.println("Prob Model Wts :  "+probModelWts);
           if(numberOfProbModels ==5){
             double time_pred = ((Double)paramList.getParameter(this.TIME_PRED).getValue()).doubleValue();
             probModelWts += " "+time_pred;
           }
           probModelWts += PROB_WTS_STRING;
           if(D) System.out.println("Putting the wts line in the fortran code:  "+probModelWts);
           lineFromInputFile = probModelWts;

           // add the time predictable file-name if necessary
           if(numberOfProbModels ==5){
             // add the previous weights line
             fileLines.add(lineFromInputFile);
             // get & set the time-predictable model filename line
             lineFromInputFile = br.readLine();
             lineFromInputFile = timeDepFile;
           }
         }
         fileLines.add(lineFromInputFile);
         lineFromInputFile = br.readLine();
       }
       br.close();

       //generates the new input file and run the WG-02 fortran code only if
       //number of realizations have changed.
       if(D)System.out.println("Creating the input files");
       //overwriting the WG-02 input file with the changes in the file
       FileWriter fw = new FileWriter(WG02_CODE_PATH+dirName+"/"+WG02_OPENSHA_INPUT_FILE);
       BufferedWriter bw = new BufferedWriter(fw);
       ListIterator it= fileLines.listIterator();
       while(it.hasNext())
         bw.write((String)it.next()+"\n");
       bw.close();

       //Command to be executed for the WG-02
       String wg02_Command="./wg99_main  "+ dirName+"/"+WG02_OPENSHA_INPUT_FILE;
       //creating the shell script  file to run the WG-02 code
       fw= new FileWriter(WG02_CODE_PATH+dirName+"/"+"wg02.sh");
       bw=new BufferedWriter(fw);
       bw.write("#!/bin/bash\n");
       bw.write("\n");
       bw.write("set -o errexit\n");
       bw.write("\n");
       bw.write("cd "+WG02_CODE_PATH+"\n");
       bw.write(wg02_Command+"\n");
       bw.write("mv "+INPUT_FILE_NAME_1+" "+WG02_CODE_PATH+dirName+"/.\n");
       bw.write("mv "+INPUT_FILE_NAME_2+" "+WG02_CODE_PATH+dirName+"/.\n");
       bw.close();
       //command to be executed during the runtime.
       String[] command ={"sh","-c","sh "+ WG02_CODE_PATH+dirName+"/wg02.sh"};
       RunScript.runScript(command);
       //command[2]="rm "+WG02_CODE_PATH+"*.out*";
       //RunScript.runScript(command);
//       command[2]="rm "+WG02_CODE_PATH+dirName+"/wg02.sh";
//       RunScript.runScript(command);
     }catch(Exception e){
       e.printStackTrace();
     }
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
                                                NUM_REALIZATIONS_MAX,DEFAULT_NUM_REALIZATIONS_VAL);
    numRealizationsParam.setInfo(NUM_REALIZATIONS_PARAM_INFO);

    // add the change listener to parameters so that forecast can be updated
    // whenever any paramater changes
    rupOffset_Param.addParameterChangeListener(this);
    deltaMag_Param.addParameterChangeListener(this);
    gridSpacing_Param.addParameterChangeListener(this);
    backSeisParam.addParameterChangeListener(this);
    grTailParam.addParameterChangeListener(this);
    numRealizationsParam.addParameterChangeListener(this);

    // add adjustable parameters to the list
    adjustableParams.addParameter(rupOffset_Param);
    adjustableParams.addParameter(gridSpacing_Param);
    adjustableParams.addParameter(deltaMag_Param);
    adjustableParams.addParameter(backSeisParam);
    adjustableParams.addParameter(grTailParam);
    adjustableParams.addParameter(numRealizationsParam);

    // make & set initial parameter values based on what's in the default WG02-input file
    createParamsFromDefaultWG02_InputFIle();

    if(D)
      System.out.print("After putting all the params in the Param List");
  }

  /**
   * This function creates the parameter for the Prob. Model given in the
   * input file for the fortran.
   *
   */
  private void createParamsFromDefaultWG02_InputFIle(){

    if(D)System.out.print("Inside the create function to get the params for the fortran code");

    try{
      FileReader fr = new FileReader(WG02_CODE_PATH+WG02_INPUT_FILE);
      BufferedReader  br = new BufferedReader(fr);
      String lineFromInputFile = br.readLine();

      //number of Faults
      int numFaults=7;   // hard coded for now
      int faultsRead = 0;
      //reading each line of file until the end of file
      while(lineFromInputFile != null){

        // set the number of years in the timeSpan if it's the appropriate line
        if(lineFromInputFile.endsWith(N_YEAR_STRING)) {
          StringTokenizer st = new StringTokenizer(lineFromInputFile);
          double nYrs = (new Double(st.nextToken())).doubleValue();
          timeSpan.setDuration(nYrs);
        }

        //reading the probablity model wts for each faults
        if(lineFromInputFile.startsWith(this.FAULT_READ+(faultsRead+1))){
          ++faultsRead;
          //reading the fault Name
          String faultName =br.readLine();
          if(D)System.out.println("Fault Name:"+faultName);
          //reading the file further below till num of prob models for that fault
          while(!br.readLine().startsWith(this.PROB_NUM_STRING));
          StringTokenizer st = new StringTokenizer(br.readLine());
          //extracting the number fo prob model for that fault from the file
          int numberOfProbModels =Integer.parseInt(st.nextToken());
          br.readLine();

          //reading the line from the file that tells wts for different prob. model foo that fault
          String probModels = br.readLine();
          st = new StringTokenizer(probModels);
          //creating the double parameters for the prob. models based on what we info is given in the file
          DoubleParameter empiricalParam = new DoubleParameter(this.EMPIRICAL,0,1,
              new Double(Double.parseDouble(st.nextToken())));
          DoubleParameter poisParam = new DoubleParameter(this.POISSON,0,1,
              new Double(Double.parseDouble(st.nextToken())));
          DoubleParameter bptStepParam = new DoubleParameter(this.BPT_STEP,0,1,
              new Double(Double.parseDouble(st.nextToken())));
          DoubleParameter bptParam = new DoubleParameter(this.BPT,0,1,
              new Double(Double.parseDouble(st.nextToken())));

          ParameterList paramList = new ParameterList();
          //adding the parameters to the parameterList
          paramList.addParameter(poisParam);
          paramList.addParameter(bptParam);
          paramList.addParameter(bptStepParam);
          paramList.addParameter(empiricalParam);
          //checking if there are 4 or 5 prob. models
          if(numberOfProbModels ==5){
            DoubleParameter timeParam = new DoubleParameter(this.TIME_PRED,0,1,
                new Double(Double.parseDouble(st.nextToken())));
            paramList.addParameter(timeParam);
          }
          //creating the instance of the TreeBranchWeightsParameter with name being the name of the fault
          //and adding the parameterList to it.
          TreeBranchWeightsParameter param =
              new TreeBranchWeightsParameter(faultName+this.PROB_MODEL_WTS,paramList);
          //adding the parameter to the adjustable parameterList
          this.adjustableParams.addParameter(param);
        }
        lineFromInputFile = br.readLine();
      }
      br.close();
    }catch(Exception e){
      e.printStackTrace();
    }
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
       // set parameter vaues
       numIterations = ((Integer) numRealizationsParam.getValue()).intValue();
       rupOffset = ((Double)rupOffset_Param.getValue()).doubleValue();
       deltaMag = ((Double)deltaMag_Param.getValue()).doubleValue();
       gridSpacing = ((Double)gridSpacing_Param.getValue()).doubleValue();
       backSeis = (String)backSeisParam.getValue();
       grTail = (String)grTailParam.getValue();

       //gets the current time in milliseconds to be the new director for each user
       String currentMilliSec ="";
       currentMilliSec += System.currentTimeMillis();

       try{
         //Name of the directory in which we are storing all the gmt data for the user
         String newDir= null;
         //all the users wg02 input files will be stored in this directory
         //each user will be having his own specific directory
         File mainDir = new File(WG02_CODE_PATH+WG02_DIRS);
         //create the main directory if it does not exist already
         if(!mainDir.isDirectory()){
           boolean success = (new File(WG02_CODE_PATH+WG02_DIRS)).mkdir();
         }
         newDir = WG02_DIRS+currentMilliSec;
         //create a  directory for each user in which all his wg02 realted input files will be stored files will be stored
         boolean success =(new File(WG02_CODE_PATH+newDir)).mkdir();

         // run the fortran code
         runFortranCode(newDir);

         // read our file generated by the fortran code & put the lines into a list
         try{ inputFileLines = FileUtils.loadFile( WG02_CODE_PATH+newDir+"/"+INPUT_FILE_NAME_1 ); }
         catch( FileNotFoundException e){ System.out.println(e.toString()); }
         catch( IOException e){ System.out.println(e.toString());}

         // Exit if no data found in list
         if( inputFileLines == null) throw new
           FaultException(C + "No data loaded from "+INPUT_FILE_NAME_1+". File may be empty or doesn't exist.");

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
       }catch(Exception e){
         e.printStackTrace();
       }

       if(D) System.out.println(C+": number of iterations read = "+iterationLineNumbers.size());
       if(D)
         for(int i=0;i<iterationLineNumbers.size();i++)
           System.out.print("   "+ (Integer)iterationLineNumbers.get(i));

       // desinate that everything is up to date
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

    ArrayList inputFileStrings = getDataForERF(index);

    return new WG02_EqkRupForecast(inputFileStrings, rupOffset, gridSpacing,
    deltaMag, backSeis, grTail, "no name", timeSpan);
  }


  /**
   * get the remote ERF in the list with the specified index
   * @param index : index of Eqk rup forecast to return
   * @return
   *
   * Note:
   * This function remains same as that of getERF() but only differs
   * when returning each ERF from the ERF List. In getERF() instance of the
   * EqkRupForecastAPI which is transferring the whole object on to the user's machine, but this function
   * return back the RemoteEqkRupForecastAPI. This is useful becuase whole ERF object does not
   * get transfer to the users machine, just a stub of the remotely existing ERF gets
   * transferred.
   *
   */
  public RemoteEqkRupForecastAPI getRemoteERF(int index) {

    ArrayList inputFileStrings = getDataForERF(index);

    try{
      WG02_EqkRupForecastClient wg02 =new WG02_EqkRupForecastClient(inputFileStrings, rupOffset, gridSpacing,
          deltaMag, backSeis, grTail, "no name", timeSpan);
      return wg02.getERF_Server();
    }catch(Exception e){
      e.printStackTrace();
    }

    return null;

  }

  /**
   * gets the data for the ERF at specified index
   * @param index : index of the data that needs to be read from the file
   * @return
   */
  protected ArrayList getDataForERF(int index){
    // get the sublist from the inputFileLines
    int firstLine = ((Integer) iterationLineNumbers.get(index)).intValue();
    int lastLine =0;
    if(index != (numIterations-1))
      lastLine = ((Integer) iterationLineNumbers.get(index+1)).intValue();
    else
      lastLine = inputFileLines.size();

    ArrayList inputFileStrings = new ArrayList();
    for(int i=firstLine;i<lastLine;++i)
      inputFileStrings.add(inputFileLines.get(i));

    return inputFileStrings;
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
     EqkRupForecastAPI fcast = list.getERF(1);
  }

}
