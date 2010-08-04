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
import org.opensha.commons.calc.GaussianDistCalc;
import org.opensha.commons.data.function.DiscretizedFunc;
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;

/**
 * <p>Title: NormalEstimate.java  </p>
 * <p>Description:  This represents a Normal Distribution defined by a
 * mean and standard deviation (the latter must be positive).
 * The Min and Max values serve to truncate the distribution, such that
 * probabilities are zero below and above these values, respectively (the defaults
 * are +/- infinity).
 *
 * </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class NormalEstimate extends Estimate {
  public final static String NAME  =  "Normal (Gaussian)";
  private double mean=Double.NaN;
  private double stdDev=Double.NaN;
  private final static String MSG_TRUNCATION_ERR = "Error: Lower and Upper Truncation must be below and above the mean respectively";

  /**
   * Default constructor - accepts mean and standard deviation.
   *
   * @param mean
   * @param stdDev
   */
  public NormalEstimate(double mean, double stdDev) {
    setMean(mean);
    setStdDev(stdDev);
    this.min=Double.NEGATIVE_INFINITY;
    this.max=Double.POSITIVE_INFINITY;
  }


  public String toString() {
	  String text= "Estimate Type="+getName()+"\n"+super.toString()+"\n"+	
	    "Values from toString() method of specific estimate:\n "+
      	"Mean="+ getMean()+"\n"+
      	"Standard Deviation="+ getStdDev()+"\n";
	  if (!Double.isInfinite(getMin())) // min value
		  text += "Lower Truncation(absolute):" + getMin() +"\n" +
		  		"Lower Truncation(# of sigmas):" + getMinSigma() + "\n";
	  if (!Double.isInfinite(getMax()))
		  text += "Upper Truncation(absolute):" +getMax() + "\n" +
	     "Upper Truncation(# of sigmas):" + getMaxSigma()+"\n";
	  if(Double.isInfinite(getMin()) && Double.isInfinite(getMax()))
		  text += "No Truncation";
	  return text;
  }

  /**
   * This accepts minimum and maximum x-axis values that will be used as trunctions.
   *
   * @param mean
   * @param stdDev
   */
  public NormalEstimate(double mean, double stdDev, double min, double max) {
    setMean(mean);
    setStdDev(stdDev);
    this.setMinMax(min,max);
  }

  /**
   * Set mean for this distribution
   *
   * @param value specifying the mean for this distribution
   */
  public void setMean(double mean) {
    this.mean = mean;
  }

  /**
   * Get the mean for this distribution
   *
   * @return double value containing the mean for this distribution
   */
  public double getMean() {
    return mean;
  }


  /**
   * Set the stanndard deviation. It should be >=0 else exception
   * will be thrown
   *
   * @param stdDev standard deviation
   */
  public void setStdDev(double stdDev) {
    if(stdDev<0) throw new InvalidParamValException(MSG_INVALID_STDDEV);
    this.stdDev = stdDev;
  }

  /**
   * Return the standard deviation
   *
   * @return standard deviation for this class
   */
  public double getStdDev() {
    return stdDev;
  }


  /**
   * Get median. It should be noted that mean, median and mode
   * have same values for a normal distribution
   *
   * @return median value
   */
  public double getMedian() {
    return getMean();
  }

  /**
   * Get mode. It should be noted that mean, median and mode
   * have same values for a normal distribution
   *
   * @return mode value
   */
  public double getMode() {
   return getMean();
  }

  /**
   *
   * Returns the max x value such that probability of occurrence of this  value (on X axis)
   * is <= prob.  This assumes that min and max (the truncations) are below and
   * above the mean, respectively.
   *
   * @param prob - probability value
   */
 public double getFractile(double prob) {
   /**
    * NOTE: In the statement below, we have to use (1-prob) because GaussianDistCalc
    * accepts the probability of exceedance as the parameter
    */
	 try {
		 double stdRndVar = GaussianDistCalc.getStandRandVar(1-prob, getStandRandVar(min),
				 getStandRandVar(max), 1e-6);
		 return getMean() + stdRndVar*getStdDev();
	 }catch(RuntimeException e) {
		 throw new RuntimeException(MSG_TRUNCATION_ERR);
	 }

 }


 /**
  * get the truncation level
  * @param val
  * @return
  */
 private double getStandRandVar(double val) {
   /* if min is negative infinity, return negative infinity.
     If max is positive infinity, return positive infinity
    */
   if(Double.isInfinite(val)) return val;
   else return (val-mean)/stdDev;
 }

 /**
  * Set the truncations in absolute units
  *
  * @param minX double
  * @param maxX double
  */
 public void setMinMax(double min, double max) {
   if(max < min) throw new InvalidParamValException(EST_MSG_MAX_LT_MIN);
   this.max = max;
   this.min = min;
 }

 /**
  * Set the truncations in units or sigma
  * (using negative values for truncation below the mean).
  *
  * @param minSigma
  * @param maxSigma
  */
 public void setMinMaxSigmas(double minSigma, double maxSigma) {
   if(maxSigma<minSigma) throw new InvalidParamValException(EST_MSG_MAX_LT_MIN);
   this.min = this.mean+minSigma*this.stdDev;
   this.max = this.mean+maxSigma*this.stdDev;
 }

 /**
  * This gets the lower truncation in units of sigma (standard deviations)
  * @return double
  */
 public double getMinSigma() {
   return (min-mean)/stdDev;
 }

 /**
  * This gets the upper truncation in units of sigma (standard deviations)
  * @return double
  */
 public double getMaxSigma() {
   return (max-mean)/stdDev;
 }

 /**
  * Get the name displayed to the user
  * @return
  */
 public String getName() {
   return NAME;
 }


 /**
  * Get the probability density function.
  * It calculates the PDF for x values.
  * The PDF is calculated for evenly discretized X values with minX=(mean-4*stdDev),
  * maxX=(mean+4*stdDev), numX=80
  *
  * @return
  */
  public DiscretizedFunc getPDF_Test() {
    EvenlyDiscretizedFunc func = getEvenlyDiscretizedFunc();
    double deltaX = func.getDelta();
    int numPoints = func.getNum();
    double x;
    for(int i=0; i<numPoints; ++i) {
      x = func.getX(i);
      func.set(i, getProbLessThanEqual(x + deltaX / 2) - getProbLessThanEqual(x - deltaX / 2));
    }
    func.setInfo("PDF from Normal Distribution");
    return func;
  }

  /**
   * Get the probability for that the true value is less than or equal to provided
   *  value (on X axis)
   *
   * @param x
   * @return
   */
  public double getProbLessThanEqual(double x) {
    return (1-GaussianDistCalc.getExceedProb(getStandRandVar(x), getStandRandVar(min),
       getStandRandVar(max)));
  }


  /**
   * Get the cumulative distribution function
   * @return
   */
  public DiscretizedFunc getCDF_Test() {
    EvenlyDiscretizedFunc func = getEvenlyDiscretizedFunc();
    int numPoints = func.getNum();
    for(int i=0; i<numPoints; ++i)
      func.set(i, getProbLessThanEqual(func.getX(i)));
    func.setInfo("CDF from Normal Distribution using getProbLessThanEqual() method");
    return func;
  }

  /**
   * Make the Evenly discretized function for use in getPDF_Test() and getCDF_Test()
   * @return
   */
  private EvenlyDiscretizedFunc getEvenlyDiscretizedFunc() {
    double min = mean-4*stdDev;
    double max = mean+4*stdDev;
    int numPoints = 81;
    EvenlyDiscretizedFunc func = new EvenlyDiscretizedFunc(min, max, numPoints);
    return func;
  }
  
  
}
