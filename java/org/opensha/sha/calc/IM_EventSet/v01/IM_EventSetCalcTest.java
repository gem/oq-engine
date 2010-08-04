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

package org.opensha.sha.calc.IM_EventSet.v01;


import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.apache.commons.lang.SystemUtils;
import org.opensha.commons.calc.GaussianDistCalc;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.util.FileUtils;

/**
 * <p>Title: IM_EventSetCalcTest</p>
 *
 * <p>Description: This class test the IM_EventSetCalc by averaging the annualized rates produced by
 * selected AttenuationRelationship. The results can then be compared with the USGS website at
 * http://eqint.cr.usgs.gov/eq-men/html/lookup-2002-interp-06.html.
 * </p>
 * <p>
 * It produces the output curve on the console.
 * </p>
 * <p>
 * NOTE :Summation of curves is not really correct
 * for non-poissonian sources (e.g., UCERF 1).
 * This we can fix later before the release of UCERF 2.
 *  </p>
 *
 * @author Nitin Gupta
 * @version 1.0
 */
public class IM_EventSetCalcTest{

  private String dirName ;
  private float[] rupRates;
  private float[] meanVals;
  private float[] sigVals;

  private ArbitrarilyDiscretizedFunc averagedFunction;
  //checks to see if this teh first IMR/IMT it is reading.
  private boolean first = true;
  private int numIMRsToAverageTheCurve = 0;

  public IM_EventSetCalcTest(String dirName) {

    this.dirName = dirName;

  }

  double[] imlVals = {.005,.007,.0098,.0137,.0192,.0269,.0376,.0527,.0738,.103,
		  .145,.203,.284,.397,.556,.778,1.09,1.52,2.13};


  private void readFile(String fileName) throws FileNotFoundException, IOException {
    ArrayList fileLines = FileUtils.loadFile(fileName);
    int numEntries = fileLines.size();
    if(first){
    	  rupRates = new float[numEntries];
    	  meanVals = new float[numEntries];
      sigVals = new float[numEntries];
    }
    //getting the Mean and Sigma for each rup from the output file
    for(int i=0;i<numEntries;++i){
      StringTokenizer st = new StringTokenizer((String)fileLines.get(i));
      st.nextToken();
      st.nextToken();
      meanVals[i] = Float.parseFloat(st.nextToken().trim());
      sigVals[i] = Float.parseFloat(st.nextToken().trim());
    }
    fileLines = null;
	if(first){
	    fileLines = FileUtils.loadFile(dirName+SystemUtils.FILE_SEPARATOR
                                           +"src_rup_metadata.txt");
	    //getting the event rates for each rup from Src-Rup file
	    for(int i=0;i<numEntries;++i){
	      StringTokenizer st = new StringTokenizer((String)fileLines.get(i));
	      st.nextToken();
	      st.nextToken();
	      rupRates[i] = Float.parseFloat(st.nextToken().trim());
	     }
	}
	first = false;
    fileLines = null;
  }


  /**
   * Reads each Attenuation Relationship file and IMT file to get the
   * averaged annualized rates
   */
  private void getAverageAnnualizedRates() {
    initArbFunction();
    try {
      File file = new File(dirName);
      String absPath = file.getAbsolutePath()+SystemUtils.FILE_SEPARATOR;
      File[] files = file.listFiles();
      int numFiles = files.length;

      for (int i = 0; i < numFiles; ++i) {
        String fileName = files[i].getName();
        if (fileName.endsWith(".txt") && ! (fileName.contains("rup"))) {
          ++numIMRsToAverageTheCurve;

          readFile(absPath+fileName);
          createArbFuncForEachIML();

        }
      }
    }
    catch (FileNotFoundException e) {

      e.printStackTrace();
    }
    catch (IOException e) {

      e.printStackTrace();
    }
    averageArbFunction();
    System.out.println(averagedFunction.toString());
  }

  /**
   * Initializes the function with the 0.0
   *
   */
  private void initArbFunction(){
    averagedFunction = new ArbitrarilyDiscretizedFunc();
    int numIMLs = imlVals.length;
    for (int i = 0; i < numIMLs; ++i) {
      averagedFunction.set(imlVals[i], 0.0);
    }
  }
  /**
   * Averages the annualized rates values in the function with the number of AttennuationRelationships for which
   * calcualtion was done.
   *
   */
  private void averageArbFunction(){
    int numIMLs = imlVals.length;

    for (int i = 0; i < numIMLs; ++i)
      averagedFunction.set(i, averagedFunction.getY(i) / numIMRsToAverageTheCurve);

  }

  private void createArbFuncForEachIML(){

    int numIMLs = imlVals.length;
    int numMeanVals = meanVals.length;
    for(int i=0;i<numIMLs;++i){
      double imlExceedRate = 0 ;
      for(int j=0;j<numMeanVals;++j){
        double stRndVar = (Math.log(imlVals[i]) - meanVals[j]) / sigVals[j];
        imlExceedRate += (GaussianDistCalc.getExceedProb(stRndVar,1,3.0)*rupRates[j]);
      }
      //double val = 1-Math.exp(-imlExceedRate*50.0);
      averagedFunction.set(imlVals[i],averagedFunction.getY(i)+imlExceedRate);
    }

   }

  public static void main(String[] args) {
    if (args.length != 1) {
      System.out.println("Usage :\n\t" +
          "java -jar [jarfileName] [inputDirectory]\n\n");
      System.out.println("jarfileName : Name of the executable jar file, by default it is IM_EventSetCalcTest.jar");
      System.out.println("input directory name : Name of the input directory where all the data files are located for"+
    		  " each AttennuationRelationship. This test application will read those files and then generate the averaged" +
    		  " annualized rates curves.");
      System.exit(0);
    }

    IM_EventSetCalcTest imEventSetCalcTest = new
        IM_EventSetCalcTest(args[0]);

    imEventSetCalcTest.getAverageAnnualizedRates();
  }
}
