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

import java.util.ArrayList;

import org.opensha.commons.data.function.ArbDiscrEmpiricalDistFunc;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncList;
/**
 * <p>Title:  FractileCurveCalculator</p>
 * <p>Description: This class calculates fractiles from a list of discretized functions (e.g., hazzard curves) and their relative weights</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author unascribed
 * @version 1.0
 */

public class FractileCurveCalculator {

  // function list to save the curves
  private DiscretizedFuncList funcList;
  // save the relative weight of each curve
  private ArrayList<Double> relativeWeights;
  // save the number of X values
  private int num;
  // vector to save the empirical distributions
  private ArrayList<ArbDiscrEmpiricalDistFunc> empiricalDists;

  // Error Strings to be dispalyed
  private final static String ERROR_WEIGHTS =
     "Error! Number of weights should be equal to number of curves";
  private final static String ERROR_LIST = "No curves exist in the list";
  private final static String ERROR_POINTS =
      "Number of points in each curve should be same";


  /**
   * Constructor : Calls the set function
   * @param functionList : List of curves for which fractile needs to be calculated
   * @param relativeWts : weight assigned to each curves. It expects the ArrayList
   *  to contain Double values
   */
  public FractileCurveCalculator(DiscretizedFuncList functionList,
                               ArrayList<Double> relativeWts) {
    set(functionList, relativeWts);
  }



  /**
   * It accepts the function list for curves and relative weight
   * assigned to each curve.
   * It checks for following condition :
   *   1. Number of weights = number of curves in  list
   *          (i.e. functionList.size() = relativeWts.size()  )
   *   2. Number of X values in all curves are same
   *
   * It makes following asssumption:
   *   X values for in the curves are same
   *
   * @param functionList : List of curves for which fractile needs to be calculated
   * @param relativeWts : Weight assigned to each curve, stored as a Double objects in this
   * array list in the same order as in the functionList. Note that these values do not have to
   * be normalized (they don't have to sum to 1.0) - this normalization is taken care of internally.
   */
  public void set(DiscretizedFuncList functionList,
                                 ArrayList<Double> relativeWts) {

    // check that number of weights are equal to number of curves give
    if(functionList.size()!=relativeWts.size()) throw new RuntimeException(ERROR_WEIGHTS);

    // check that curve list is not empty
    int numFunctions = functionList.size();
    if(numFunctions==0) throw new RuntimeException(ERROR_LIST);

    // check  that all curves in list have same number of X values
    int numPoints = functionList.get(0).getNum();
    for(int i=1; i<numFunctions; ++i)
      if(functionList.get(i).getNum()!=numPoints) throw new RuntimeException(ERROR_POINTS);

    this.funcList = functionList;
    this.relativeWeights = relativeWts; // these do not need to be normalized
    this.num = numPoints;

    //ArrayList for saving empirical distributions
    empiricalDists = new ArrayList<ArbDiscrEmpiricalDistFunc>();

    // make a empirical dist for each X value
    for(int i=0; i<num; ++i) {
      ArbDiscrEmpiricalDistFunc empirical = new ArbDiscrEmpiricalDistFunc();
      for(int j=0; j<numFunctions; ++j)
        empirical.set(funcList.get(j).getY(i),
                      ((Double)relativeWeights.get(j)).doubleValue());
      empiricalDists.add(empirical);
//      System.out.println("111  i="+i+"; dist="+empirical.toString());
    }

  }

  /**
   * This computes the mean curve from the list of functions (and their associated
   * weights).
   * @return
   */
  public ArbitrarilyDiscretizedFunc getMeanCurve() {
    ArbitrarilyDiscretizedFunc result = (ArbitrarilyDiscretizedFunc) funcList.get(0).deepClone();
    double wt, totWt=0;
    int numPoints = funcList.get(0).getNum();
    int numFuncs = funcList.size();
    int i, f;

    // initialize function to zero
    for(i=0;i<numPoints;i++)
      result.set(i,0.0);

    // add all functions (weighted) together
    for(f=0;f<numFuncs;f++) {
       wt = ((Double)relativeWeights.get(f)).doubleValue();
       totWt += wt;
      for(i=0;i<numPoints;i++)
        result.set(i, result.getY(i) + wt*funcList.get(f).getY(i) );
    }

    // now normalize by the total weight
      // initialize result to zero
      for(i=0;i<numPoints;i++)
        result.set(i,result.getY(i)/totWt);

    return result;
  }




  /**
   *  This returns the fractile curve corresponding to the specified fraction
   * @param fraction
   * @return
   */
  public ArbitrarilyDiscretizedFunc getFractile(double fraction) {
    // function to save the result
    ArbitrarilyDiscretizedFunc result = new ArbitrarilyDiscretizedFunc();
    for(int i=0; i<num; ++i) {
      result.set(funcList.get(0).getX(i),
                 ((ArbDiscrEmpiricalDistFunc)empiricalDists.get(i)).getDiscreteFractile(fraction));
    }
    return result;
  }
}
