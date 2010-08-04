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


/**
 * <p>Title: MinMaxPrefEstimate.java </p>
 * <p>Description: This stores min, max, and preferred values, and the corresonding
 * probabilites that the true value is less than or equal to each. Though this is
 * not a complete estimate, this is needed for Ref Fault paramter database GUI.</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class MinMaxPrefEstimate extends Estimate{
  public final static String NAME  =  "Min, Max and Preferred";
  private double pref;
  private double minProb, maxProb, prefProb;
  private final static double tol = 1e-6;
  private final static String MSG_INVALID_X_VALS = "Error: Preferred value should be �  Min &"+
                                  "\n"+"Max should be � Preferred";
  private final static String MSG_INVALID_PROB_VALS = "Error: Preferred Prob should be > Min Prob &"+
  "\n"+"Max Prob should be >  Preferred Prob";

  /**
   * @param min
   * @param max
   * @param pref
   * @param minProb
   * @param maxProb
   * @param prefProb
   */
  public MinMaxPrefEstimate(double min, double max, double pref,
                            double minProb, double maxProb, double prefProb) {

    // check that min<=pref<=max
    /* THIS HAS BEEN REMOVED DELIBERATELY BECAUSE IT CREATED PROBLEMS WHEN WE WERE DEALING WITH TIME.
      IN THAT CASE, MAX REFERRED TO EARLIEST TIME AND HENCE WAS SMALLER THAN MIN SOMETIMES 
     
     if(!Double.isNaN(min) && !Double.isNaN(pref) && min>pref)
      throw new InvalidParamValException(MSG_INVALID_X_VALS);
    if(!Double.isNaN(min) && !Double.isNaN(max) && min>max)
      throw new InvalidParamValException(MSG_INVALID_X_VALS);
    if(!Double.isNaN(pref) && !Double.isNaN(max) && pref>max)
      throw new InvalidParamValException(MSG_INVALID_X_VALS);*/

    // check that aprobabilites are in increasing order
    if(!Double.isNaN(minProb) && !Double.isNaN(prefProb) && minProb>=prefProb)
        throw new InvalidParamValException(MSG_INVALID_PROB_VALS);
      if(!Double.isNaN(minProb) && !Double.isNaN(maxProb) && minProb>=maxProb)
        throw new InvalidParamValException(MSG_INVALID_PROB_VALS);
      if(!Double.isNaN(prefProb) && !Double.isNaN(maxProb) && prefProb>=maxProb)
        throw new InvalidParamValException(MSG_INVALID_PROB_VALS);

    /* check whether probabilites are between 0 & 1. */
    if(!Double.isNaN(minProb) && (minProb<0 || minProb>1))
     	throw new InvalidParamValException(EST_MSG_INVLID_RANGE);
     if(!Double.isNaN(maxProb) && (maxProb<0 || maxProb>1))
     	throw new InvalidParamValException(EST_MSG_INVLID_RANGE);
     if(!Double.isNaN(prefProb) && (prefProb<0 || prefProb>1))
     	throw new InvalidParamValException(EST_MSG_INVLID_RANGE);

    this.min = min;
    this.max = max;
    this.pref = pref;
    this.minProb = minProb;
    this.maxProb = maxProb;
    this.prefProb = prefProb;
  }

  public String toString() {
    return "Estimate Type="+getName()+"\n"+
    	super.toString()+"\n"+
        "Values from toString() method of specific estimate\n"+
        "Min "+"="+min+"["+minProb+"]\n"+
        "Max "+"="+max+"["+maxProb+"]\n"+
        "Pref "+"="+pref+"["+prefProb+"]\n";
  }


  /**
   * This returns the original Min (even if it's NaN)
   * @return double
   */
  public double getMinimum() { return this.min; }

  /**
  * This returns the original Max (even if it's NaN)
  * @return double
  */
  public double getMaximum() { return this.max; }

  public double getPreferred() { return this.pref; }
  public double getMinimumProb() { return this.minProb; }
  public double getMaximumProb() { return this.maxProb; }
  public double getPreferredProb() { return this.prefProb; }

  /**
   * Get the maximum value among min, preferred, and max (i.e., NaNs excluded)
   *
   * @return maximum value (on X axis)
   */
  public double getMax() {
    if(!Double.isNaN(max)) return max;
    if(!Double.isNaN(pref)) return pref;
    if(!Double.isNaN(min)) return min;
    return Double.NaN;
  }

  /**
   * Get the minimum value  (on X axis) among min, preferred, and max (i.e., NaNs excluded)
   *
   * @return minimum value (on X axis)
   */
  public double getMin() {
    if(!Double.isNaN(min)) return min;
    if(!Double.isNaN(pref)) return pref;
    if(!Double.isNaN(max)) return max;
    return Double.NaN;
  }
  

 public String getName() {
   return NAME;
 }

}
