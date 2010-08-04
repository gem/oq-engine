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

package org.opensha.commons.data.estimate;

import org.opensha.commons.data.function.ArbDiscrEmpiricalDistFunc;
import org.opensha.commons.data.function.DiscretizedFunc;
/**
 * <p>Title: DiscreteValueEstimate.java </p>
 * <p>Description:  This can be used to specify probabilities associated with
 * discrete values from a DiscretizedFunction. Use an EvenlyDiscretizedFunction for
 * a continuous PDF (where it is asssumed that the first and last values are the
 * first and last non-zero values, respectively), or use an ArbitrarilyDiscretizedFunction
 * if the nonzero values are not evenly discretized.
 * </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public abstract class DiscretizedFuncEstimate extends Estimate {
  protected ArbDiscrEmpiricalDistFunc func=null;
  protected DiscretizedFunc cumDistFunc = null;

  // tolerance for checking normalization
  protected double tol = 1e-6;


  /**
   * Constructor - Accepts a DiscretizedFunc and an indication of whether it is
   * normalized. Note that the function passed in is cloned.
   * MaxX and MinX are set according to those of the function
   * passed in.
   * @param func
   */
  public DiscretizedFuncEstimate(DiscretizedFunc func, boolean isNormalized) {
    setValues(func, isNormalized);
  }

  public String toString() {
	  String text =  "EstimateType="+getName()+"\n";
	  text+=super.toString()+"\n";
	  text+="Values from toString() method of specific estimate\nValue\tProbability\n";
	  for(int i=0; func!=null && i<func.getNum(); ++i) {
		  text += "\n"+func.getX(i) + "\t"+func.getY(i);
	  }	
	  text+="\ngetFractile(0.5) = "+this.getFractile(0.5)+"\n"+
	  		"getDiscreteFractile(0.5) = "+this.getDiscreteFractile(0.5)+"\n";
	  return text;
  }

  /**
   * As implemented, the function passed in is cloned.
   *  Max and Min are set by those in the function passed in.
   *
   * @param func
   */
  public void setValues(DiscretizedFunc newFunc, boolean isNormalized) {


    // Check normalization and value range
    double sum=0, val;
    int num = newFunc.getNum();
    if(isNormalized) { // check values
      for (int i = 0; i < num; ++i) {
        val = newFunc.getY(i);
        if (val < 0 || val > 1)throw new InvalidParamValException(EST_MSG_INVLID_RANGE);
        sum += val;
      }
      // make sure sum is close to 1.0
      if ( Math.abs(sum-1.0) > tol)
        throw new InvalidParamValException(EST_MSG_NOT_NORMALIZED);
    }
    else { // sum y vals and check positivity
      for (int i = 0; i < num; ++i) {
        val = newFunc.getY(i);
        if (val < 0)throw new InvalidParamValException(EST_MSG_PROB_POSITIVE);
        sum += val;
      }
      if(sum==0) throw new InvalidParamValException(MSG_ALL_PROB_ZERO);
      // normalize the function
      for (int i = 0; i < num; ++i) {
        val = newFunc.getY(i);
        newFunc.set( i, val/sum );
      }
    }
	func = new ArbDiscrEmpiricalDistFunc();
    for(int i=0; i<newFunc.getNum(); ++i)
    	func.set(newFunc.getX(i), newFunc.getY(i));
    
    min = func.getMinX();
    max = func.getMaxX();
    this.cumDistFunc = func.getCumDist();
  }

  /**
   * get the values and corresponding probabilities from this estimate
   * @return
   */
  public DiscretizedFunc getValues() {
    return func;
  }


  /**
   * Get the mode (X value where Y is maximum).
   * Returns the most cental mode value in case of multi-modal distribution
   * Calls the getMostCentralMode() method of ArbDiscrEmpiricalDistFunc
   *
   * @return
   */
  public double getMode() {
    return func.getMostCentralMode();
 }
  
  /**
   * Whether the estimate has more than one mode
   * @return
   */
  public boolean isMultiModal() {
  	return func.isMultiModal();
  }

 /**
  * Get the median which is same as fractile at probability of 0.5.
  *
  * @return
  */
  public double getMedian() {
    return func.getMedian();
  }

  /**
   * Get standard deviation
   * @return
   */
  public double getStdDev() {
    return func.getStdDev();
  }


  /**
   * Get mean
   * @return
   */
  public double getMean() {
   return func.getMean();
 }

 /**
  * This allows the user to set the tolerance used for checking normalization (and
  * perhaps other things in subclasses).
  * @param tol double
  */
 public void setTolerance(double tol) {this.tol = tol;}

 /**
  * Get the function in which values are stored
  * @return
  */
 public DiscretizedFunc getFunc() { return this.func;}

 /**
  * Get fractile for a given probability (the value where the CDF equals prob).
  * This gets the interpolated fractile. To get the discrete fractile. getDiscretFractile() funcation can be used
  *
  * @param prob
  * @return
  */
 public double getFractile(double prob) {
   return func.getInterpolatedFractile(prob);
 }
 
 /**
  * Get fractile for a given probability (the value where the CDF equals prob).
  * this gets the discrete fractile. 
  *
  * @param prob
  * @return
  */
 public double getDiscreteFractile(double prob) {
   return func.getDiscreteFractile(prob);
 }

}
