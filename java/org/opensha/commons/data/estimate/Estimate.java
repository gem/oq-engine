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
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFunc;

/**
 * <p>Title: Estimate.java </p>
 * <p>Description: This is the abstract class for various types of estimates.
 * Most methods here throw unsupported exceptions because this will often be the
 * case in subclasses.  </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author
 * @version 1.0
 */

public abstract class Estimate {

  // comments associated with this object
  protected final static String EST_MSG_MAX_LT_MIN = "Error: Minimum must be less than Maximum";
  protected final static String EST_MSG_NOT_NORMALIZED = "Error: The probability values do not sum to 1";
  protected final static String EST_MSG_PROB_POSITIVE = "Error: All probability values must be positive";
  protected final static String EST_MSG_INVLID_RANGE = "Error: All probabilities must be � 0 and � 1";
  protected final static String EST_MSG_FIRST_LAST_PROB_ZERO = "Error: First and Last probability values must be 0";
  protected final static String MSG_INVALID_STDDEV = "Error: Standard deviation must be positive.";
  protected final static String MSG_ALL_PROB_ZERO = "Error: At least one probability value must be > 0.";
  protected final static String EST_MSG_PROBS_NOT_INCREASING = "Error: Probabilities must be in increasing order";
  protected final static String MEDIAN_UNDEFINED = "Error: Median is undefined";
  protected final static String FRACTILE_UNDEFINED = "Error: Fractile is undefined";

  protected String comments="";
  protected double min, max;
  protected String units;

  /**
   * Get units for this estimate
   * @return
   */
  public String getUnits() {
    return units;
  }

  /**
   * Set the units in this estimate
   * @param units
   */
  public void setUnits(String units) {
    this.units = units;
  }

  /**
   * Get the mean for this estimate
   *
   * @return
   */
  public double getMean() {
    throw new java.lang.UnsupportedOperationException("Method getMean() not supported");
  }


  /**
   * Get median for this estimate
   *
   * @return
   */
  public double getMedian() {
    throw new java.lang.UnsupportedOperationException("Method getMedian() not supported");
  }


  /**
   * Get Std Dev for this estimate
   *
   * @return
   */
  public double getStdDev() {
    throw new java.lang.UnsupportedOperationException("Method getStdDev() not supported");
  }

  /**
   * Get fractile for a given probability (the value where the CDF equals prob).
   *
   * @param prob
   * @return
   */
  public double getFractile(double prob) {
    throw new java.lang.UnsupportedOperationException("Method getFractile() not supported");
  }


  /**
   * Get mode for this estimate
   *
   * @return
   */
  public double getMode() {
    throw new java.lang.UnsupportedOperationException("Method getMode() not supported");
  }



  /**
   * Checks whether there exist any X values which are less than 0.
   *
   * @return It returns true if any x<0. If all x>=0, it returns false
   */
  public boolean isNegativeValuePresent() {
    return (getMin()<0.0);
  }

  /**
   * Get the maximum  value (on X axis)
   *
   * @return maximum value (on X axis)
   */
  public double getMax() {return max;};

  /**
   * Get the minimum value (on X axis)
   *
   * @return minimum value (on X axis)
   */
  public double getMin() {return min;}


   /**
    * Get the comments associated with this object
    *
    * @return String value containing the comments
    */
   public String getComments() {
     return comments;
   }

   /**
    * Set the comments in this object
    *
    * @param comments comments to be set for this object
    */
   public void setComments(String comments) {
     this.comments = comments;
   }

   /**
    * Get the name. this is the name displayed to the user in the estimate
    * type chooser.
    * @return
    */
   public abstract String getName() ;

   /**
    * Test function to find the PDF for this estimate. It uses the
    * getProbLessThanEqual() function internally.
    *
    * @return
    */
   public DiscretizedFunc getPDF_Test() {
    throw new java.lang.UnsupportedOperationException("Method getPDF_Test() not supported");
  }


   /**
    * Test function to get the CDF for this estimate. It uses the
    * getProbLessThanEqual() function internally.
    *
    * @return
    */
   public DiscretizedFunc getCDF_Test() {
    throw new java.lang.UnsupportedOperationException("Method getCDF_Test() not supported");
  }


   /**
    * Get the probability that the true value is less than or equal to the provided
    * x value (the CDF for a probability density funtion)
    *
    * @param x
    * @return
    */
   public double getProbLessThanEqual(double x) {
    throw new java.lang.UnsupportedOperationException("Method getProbLessThanEqual() not supported");
  }


   /**
   * Test function to get the CDF for this estimate. It uses the
   * getFractile() function internally. It discretizes the Y values and then
   * calls the getFractile() method to get corresponding x values and then
   * plot them.
   *
   * @return
   */
  public  DiscretizedFunc getCDF_TestUsingFractile() {
    ArbitrarilyDiscretizedFunc func = new ArbitrarilyDiscretizedFunc();
    //discretize the Y values
    double minProb = 0.00001;
    double maxProb = 0.99999;
    int numPoints = 100;
    double deltaProb = (maxProb-minProb)/(numPoints-1);
    // find the X values correpsoding to Y values
    for(double prob=minProb; prob<=maxProb;prob=prob+deltaProb)
      func.set(getFractile(prob),prob);
    func.setInfo("CDF using getFractile() method");
    return func;
  }

  public String toString() {
    String text = "Values from Methods:\n";
    
    // mean
    try {
      text += "Mean = "+getMean()+"\n";
    }
    catch ( UnsupportedOperationException e) {
      text += "Mean = NA\n";
    }
    
    // mode
    try {
      text += "Mode = "+getMode()+"\n";
    }
    catch ( UnsupportedOperationException e) {
      text += "Mode = NA\n";
    }
    
    // median
    try {
        text += "Median = "+getMedian()+"\n";
    }
     catch ( UnsupportedOperationException e) {
        text += "Median = NA\n";
    }
     
    // std Dev
     try {
         text += "Std Dev = "+getStdDev()+"\n";
     }
      catch ( UnsupportedOperationException e) {
         text += "Std Dev = NA\n";
     } 
      
     // fractile
      try {
    	  text += "Fractile(0.5) = "+getFractile(0.5)+"\n";
      } catch(UnsupportedOperationException e) {
    	  text += "Fractile(0.5) = NA\n";
      }
      
      //isNegativeValuePresent
      text += "IsNegativeValPresent = "+this.isNegativeValuePresent()+"\n";
      
      // max
      text += "Max = "+this.getMax()+"\n";
      
      // min
      text += "Min = "+this.getMin()+"\n";
      
   
    return text;
  }

}
