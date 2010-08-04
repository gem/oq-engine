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

package org.opensha.commons.calc;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncList;

/**
 * <p>Title: FunctionListCalc</p>
 * <p>Description: This is the calculator for calculating mean and other
 * statistics for all the functions in a function list</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author Nitin Gupta , Vipin Gupta
 * @ date Dec 11, 2002
 * @version 1.0
 */

public class FunctionListCalc {

  /**
   * This function accepts the functionlist and returns another function after
   * calculating the mean of all the functions in this function list
   *
   * @param funcList  List conatining all the functins for which mean needs to be calculated
   * @return A function for mean of all the functions in the list
   */
  public static DiscretizedFunc getMean(DiscretizedFuncList funcList) {
    DiscretizedFunc meanFunc = new ArbitrarilyDiscretizedFunc();
    int numFunctions = funcList.size(); // number of functions in the list
    int numPoints; // number of x,y points
    if(numFunctions >= 1)  numPoints = funcList.get(0).getNum();
    else throw new RuntimeException("No function exists in functionlist to calculate mean");

    // now we need to iterate over all the points
    // here we assume that all the functions in the list have same number of x and y values

    // iterate over all points
    for(int i=0; i <numPoints; ++i) {
      double sum=0;
      // now iterate over all functions in the list
      for(int j=0; j<numFunctions; ++j)
        sum+=funcList.get(j).getY(i); // get the y value at this index
      // add the poin to the mean function
      meanFunc.set(funcList.get(0).getX(i),sum/numFunctions);
    }

    return meanFunc;
  }

}
