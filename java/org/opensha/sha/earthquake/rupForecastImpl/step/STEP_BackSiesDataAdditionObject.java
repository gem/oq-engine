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

/**
 * <p>Title: STEP_BackSiesDataAdditionObject</p>
 * <p>Description: This Class adds the BackSies ERF dataset the Step ERF dataSet</p>
 * @author : Edward (Ned) Field, Nitin Gupta and Vipin Gupta
 * @created : Aug 29,2003
 * @version 1.0
 */

public class STEP_BackSiesDataAdditionObject {

  // message to display if no data exits
  private static final String NO_DATA_EXISTS = "No Hazard Map Data Exists";

  //String to store the Metadata,Lats and Lons for the Step DataSet
  String stepMetaData;

  //Stores the Region definition for the step
  String stepLatitude;
  String stepLongitude;

  //String to store the Metadata,Lats and Lons for the Step DataSet
  String backSiesMetaData;

  //Stores the Region definition for the step
  String backSeisLatitude;
  String backSiesLongitude;


  //default class constructor
  public STEP_BackSiesDataAdditionObject() {
  }


  /**
   * Adds the 2 dataset for the backSies and Step and generates a final dataset
   * @param backSies : ArrayList for the Step BackGround Prob
   * @param step : ArrayList for the Step Addon Prob
   * backGround and Addon
   */
  public double[] addDataSet(double[] backSiesDataSet,double[] stepDataSet){

    int size = backSiesDataSet.length;
    double[] resultSet = new double[size];
    for(int i=0;i<size;++i){
    	double finalProb = backSiesDataSet[i] + stepDataSet[i];
      //double finalProb = backSiesDataSet[i] + stepDataSet[i] - (backSiesDataSet[i])*(stepDataSet[i]);
      resultSet[i] = finalProb;
    }
    return resultSet;
  }

}
