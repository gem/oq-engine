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
 * <p>Title: LogNormalEstimate.java  </p>
 * <p>Description: This exstimate assumes a log-normal distribution.  The linear-median,
 * and standard deviation must be positive, and minX and maxX can only be 0.0 and Infinity,
 * respectively (at least for now.  One must also specify
 * whether natural or base-10 log is assumed.
 * </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class LogNormalEstimate extends Estimate {
  public final static String NAME  =  "Log Normal";

  private double linearMedian;
  private double stdDev;
  // flag to specify whether it will be base10 or natural log
  private boolean isBase10 = true;
  private final static String MSG_INVALID_MEDIAN = "Error: linear-median must be positive.";
  private final static String MSG_INVALID_MINMAX =
      "Error: the minimum and maximum X-axis values can only be 0.0 and  Infinity, respectively.";
  private final static double LOG10_VAL = Math.log(10.0);

  /**
   * Constructor - set the linear median and standard deviation.
   * For allowed values of median and stdDev, check their respective setValue
   * function documentation
   *
   * @param linearMedian
   * @param stdDev
   */
  public LogNormalEstimate(double linearMedian, double stdDev) {
    setLinearMedian(linearMedian);
    setStdDev(stdDev);
    min = 0.0;
    max = Double.POSITIVE_INFINITY;
  }

  public String toString() {
    String logBase = "E";
    if(isBase10) logBase="10";
    return "Estimate Type="+getName()+"\n"+
    
        "Linear Median="+ this.getLinearMedian()+"\n"+
        "Standard Deviation="+ getStdDev()+"\n"+
        "Log Base="+logBase+"\n"+
        "Left Truncation Sigma="+ getMinSigma()+"\n"+
        "Right Truncation Sigma="+ getMaxSigma();
  }


  /**
   * Set the linear median . Median should be > 0 else InvalidParamValException
   * is thrown
   *
   * @param median linear median for this estimate
   */
  public void setLinearMedian(double median) {
    if (median < 0)
      throw new InvalidParamValException(MSG_INVALID_MEDIAN);
    this.linearMedian = median;
  }

  /**
   * Return the median for this distribution
   *
   * @return
   */
  public double getLinearMedian() {
    return linearMedian;
  }

  /**
   * Set the standard deviation. It should be >=0 else InvalidParamValException
   * is thrown
   *
   * @param stdDev
   */
  public void setStdDev(double stdDev) {
    if (stdDev < 0)
      throw new InvalidParamValException(MSG_INVALID_STDDEV);
    this.stdDev = stdDev;
  }

  /**
   * Get the standard deviation
   *
   * @return
   */
  public double getStdDev() {
    return stdDev;
  }

  /**
   * Whether we are using natural log or log to base 10 for this
   *
   * @return True if we are using log to base of 10, returns false if natural
   * log is being used
   */
  public boolean getIsBase10() {
    return this.isBase10;
  }

  /**
   * set whether to use natural log or log to base 10
   *
   * @param isBase10 true if you user wants to use log to base 10, false if
   * natural log is desired
   */
  public void setIsBase10(boolean isBase10) {
    this.isBase10 = isBase10;
  }

  /**
   * Return the mean
   * @return
   */
  public double getMean() {
    throw new java.lang.UnsupportedOperationException(
        "Method getMean() not yet implemented.");
  }

  /**
  *
  * Returns the max x value such that probability of occurrence of this x value
  * is <=prob
  *
  * @param prob - probability value
  */
public double getFractile(double prob) {
  /**
   * NOTE: In the statement below, we have to use (1-prob) because GaussianDistCalc
   * accepts the probability of exceedance as the parameter
   */
   double stdRndVar = GaussianDistCalc.getStandRandVar(1-prob, getStandRandVar(min),
       getStandRandVar(max), 1e-6);
   return getUnLogVal(getLogVal(linearMedian) + stdRndVar*stdDev);
 }

 /**
  * It gets the log value for passed in "val". This checks whether the log normal estimate
  * is for base 10 or for base E and then returns the log value based on it.
  *
  * @param val
  * @return
  */
 private double getLogVal(double val) {
   double logVal = Math.log(val);
   if(this.isBase10) return logVal/LOG10_VAL;
   else return logVal;
 }

 /**
  * It unlogs the value. It checks whether this estimate is based on base 10 or
  * base E and unlogs the value depending on that.
  *
  * @param val Value in log domain
  * @return
  */
 private double getUnLogVal(double logVal) {
   if(this.isBase10) return Math.pow(10, logVal);
   else return Math.exp(logVal);
 }

  /**
   * get the standard random variable
   *
   * @param val
   * @return
   */
  private double getStandRandVar(double val) {
    if(val==Double.NEGATIVE_INFINITY) return 0;
    else if(val==Double.POSITIVE_INFINITY) return Double.POSITIVE_INFINITY;
    else return getLogVal(val/linearMedian)/stdDev;
  }


  /**
   * Get the mode
   * @return
   */
  public double getMode() {
    throw new java.lang.UnsupportedOperationException(
        "Method getMode() not yet implemented.");
  }

  /**
   * Get the median
   * @return
   */
  public double getMedian() {
    return 0.0;
  }

  /**
   * Get the name of this estimate. This is the name displayed to the user
   * @return
   */
  public String getName() {
   return NAME;
 }

 /**
  * Set the minimum and maximum  values
  *
  * @param min double
  * @param max double
  */
 public void setMinMax(double min, double max) {
   if(max < min) throw new InvalidParamValException(EST_MSG_MAX_LT_MIN);
   if(min<0 || max<0) throw new InvalidParamValException(MSG_INVALID_MINMAX);
   this.max = max;
   this.min = min;
 }

 /**
  * Sigma values for truncation.
  * For left truncation, negative value of minSigma may be used
  *
  * @param minSigma
  * @param maxSigma
  */
 public void setMinMaxSigmas(double minSigma, double maxSigma) {
   if(maxSigma<minSigma) throw new InvalidParamValException(EST_MSG_MAX_LT_MIN);
   double min, max;
   min = getUnLogVal(getLogVal(this.linearMedian)+getLogVal(minSigma*this.stdDev));
   max = getUnLogVal(getLogVal(this.linearMedian)+getLogVal(maxSigma*stdDev));
   if(min<0 || max<0) throw new InvalidParamValException(MSG_INVALID_MINMAX);
   this.min = min;
   this.max = max;
 }

 public double getMinSigma() {
   return getUnLogVal(getLogVal(min)-getLogVal(linearMedian))/stdDev;
 }

 public double getMaxSigma() {
   return getUnLogVal(getLogVal(max)-getLogVal(linearMedian))/stdDev;
 }


 /**
  * Get the probability density function.
  * It calculates the PDF for x values.
  * The PDF is calculated for evenly discretized  values with min=0,
  * max=linearMedian*Math.exp(4*stdDev), num=160
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
     if((x - deltaX / 2)<=0) // log values does not exist for negative values
       func.set(i, getProbLessThanEqual(x + deltaX / 2));
     else func.set(i, getProbLessThanEqual(x + deltaX / 2) - getProbLessThanEqual(x - deltaX / 2));
   }
   func.setInfo("PDF from LogNormal Distribution");
   return func;
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
   func.setInfo("CDF from LogNormal Distribution using getProbLessThanEqual() method");
   return func;
 }


 /**
  * Make the Evenly discretized function for use in getPDF_Test() and getCDF_Test()
  * @return
  */
 private EvenlyDiscretizedFunc getEvenlyDiscretizedFunc() {
   double minX = 0;
   double maxX = linearMedian*getUnLogVal(3*stdDev);
   int numPoints = 320;
   EvenlyDiscretizedFunc func = new EvenlyDiscretizedFunc(minX, maxX, numPoints);
   return func;
 }


 /**
   * Get the probability for that the true value is less than or equal to provided
   *  value
   *
   * @param val
   * @return
   */
  public  double getProbLessThanEqual(double val) {
    return (1-GaussianDistCalc.getExceedProb(getStandRandVar(val), getStandRandVar(min),
       getStandRandVar(max)));
  }

 public static void main(String args[]) {
   LogNormalEstimate estimate = new LogNormalEstimate(5, 0.5);
   estimate.setMinMaxSigmas(2,2);
   System.out.println(estimate.getMinSigma());
   System.out.println(estimate.getMaxSigma());
 }

}
