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

package org.opensha.sha.magdist;

import org.opensha.commons.data.DataPoint2D;
import org.opensha.commons.exceptions.DataPoint2DException;
import org.opensha.commons.exceptions.DiscretizedFuncException;
import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.exceptions.MagFreqDistException;





/**
 * <p>Title:GaussianMagFreqDist </p>
 *
 * <p>Description: This assumes a Gaussian distribution with a given mean and standard deviation, with
 * the option of being truncated at some number of standard deviations(one or two sided truncation).
 * The trucation levels are rounded to the nearest point, and these are given non-zero rates (zeros
 * are above and below these points.  The mean can be any value (it doesn not have to exactly equal
 * one of the descrete x-axis values).
 *
 * @author : Nitin Gupta (Aug,8,2002) & Ned Field (Nov, 21, 2002)
 * @version 1.0
 */

public class GaussianMagFreqDist extends IncrementalMagFreqDist {

  public  static String NAME = "Gaussian Dist";
  private double mean= Double.NaN;
  private double stdDev= Double.NaN;

  /**
   * The # of stdDev (from Mean) where truncation occurs
   */
  private double truncLevel = Double.NaN;

  /**
   * truncType = 0 for none, = 1 for upper only, and = 2 for double sided
   */
  private int truncType =0  ;

  /**
   * todo constructors
   * All the constructors call the function computeRates which sets up the rate
   * as Y-axis values based on the X-axis values provided in the form of min,num,delta of mag.
   */

  /**
   * constructor
   * @param min - minimum mag of distribution
   * @param num - number of points in distribution
   * @param delta - discretization interval
   */
  public GaussianMagFreqDist(double min,int num,double delta) throws InvalidRangeException{
    super(min,num,delta);

  }

  /**
   * Constructor
   * @param min - minimum mag of distribution
   * @param max - maximum mag of distribution
   * @param num - number of points in distribution
   */
  public GaussianMagFreqDist(double min,double max,int num)
    throws DiscretizedFuncException,InvalidRangeException {

    super(min,max,num);

  }


  /**
   * Constructor: This applies no trucation.
   * @param min - minimum mag of distribution
   * @param max - maximum mag of distribution
   * @param num - number of points in distribution
   * @param mean - the mean maginitude of the gaussian distribution
   * @param stdDev - the standard deviation
   * @param totMoRate - the total moment rate
   */
  public GaussianMagFreqDist(double min,double max,int num,double mean,double stdDev,
                             double totMoRate) throws DiscretizedFuncException,
                             InvalidRangeException,DataPoint2DException {
    super(min,max,num);
    this.mean=mean;
    this.stdDev=stdDev;
    this.truncType = 0;
    calculateRelativeRates();
    scaleToTotalMomentRate(totMoRate);
  }

  /**
   * Constructor: This applies no trucation.
   * @param min - minimum mag of distribution
   * @param num - number of points in distribution
   * @param delta - discretization interval
   * @param mean - the mean maginitude of the gaussian distribution
   * @param stdDev - the standard deviation
   * @param totMoRate - the total moment rate
   */

  public GaussianMagFreqDist(double min,int num,double delta,double mean,double stdDev,
                             double totMoRate) throws DataPoint2DException,InvalidRangeException {
    super(min,num,delta);
    this.mean=mean;
    this.stdDev=stdDev;
    this.truncType = 0;
    calculateRelativeRates();
    scaleToTotalMomentRate(totMoRate);
  }


  /**
   * Constructor:  This applies whatever truncation is specified.
   * @param min - minimum mag of distribution
   * @param num - number of points in distribution
   * @param delta - discretization interval
   * @param mean - the mean maginitude of the gaussian distribution
   * @param stdDev - the standard deviation
   * @param totMoRate - the total moment rate
   * @param truncLevel - in units of stdDev from the mean
   * @param truncType - 0 for none; 1 for upper only; and 2 for upper and lower
   */
  public GaussianMagFreqDist(double min,int num,double delta,double mean,double stdDev,
                             double totMoRate,double truncLevel,int truncType)
                             throws DataPoint2DException, InvalidRangeException{
    super(min,num,delta);
    this.mean=mean;
    this.stdDev=stdDev;
    this.truncLevel=truncLevel;
    this.truncType = truncType;
    calculateRelativeRates();
    scaleToTotalMomentRate(totMoRate);
  }


  /**
   * Constructor:  This applies whatever truncation is specified.
   * @param min - minimum mag of distribution
   * @param max - maximum mag of distribution
   * @param num - number of points in distribution
   * @param mean - the mean maginitude of the gaussian distribution
   * @param stdDev - the standard deviation
   * @param totMoRate - the total moment rate
   * @param truncLevel - in units of stdDev from the mean
   * @param truncType - 0 for none; 1 for upper only; and 2 for upper and lower
   */
  public GaussianMagFreqDist(double min,double max,int num,double mean,double stdDev,
                             double totMoRate,double truncLevel,int truncType)
                             throws DiscretizedFuncException, InvalidRangeException,
                             DataPoint2DException {
    super(min,max,num);
    this.mean=mean;
    this.stdDev=stdDev;
    this.truncLevel=truncLevel;
    this.truncType = truncType;
    calculateRelativeRates();
    scaleToTotalMomentRate(totMoRate);
  }


  /**
   * This updates the distribution, applying no truncation (truncType set to 0)
   * @param mean - the mean maginitude of the gaussian distribution
   * @param stdDev - the standard deviation
   * @param totMoRate - the total moment rate
   */
  public void setAllButCumRate(double mean,double stdDev, double totMoRate)
                               throws DataPoint2DException {
  this.mean=mean;
  this.stdDev=stdDev;
  this.truncType = 0;
  calculateRelativeRates();
  scaleToTotalMomentRate(totMoRate);
  }


  /**
   * This updates the distribution, applying the truncation specified
   * @param mean - the mean maginitude of the gaussian distribution
   * @param stdDev - the standard deviation
   * @param totMoRate - the total moment rate
   * @param truncLevel - in units of stdDev from the mean
   * @param truncType - 0 for none; 1 for upper only; and 2 for upper and lower
   */
  public void setAllButCumRate(double mean,double stdDev, double totMoRate,
                               double truncLevel,int truncType) throws DataPoint2DException{
    this.mean=mean;
    this.stdDev=stdDev;
    this.truncLevel=truncLevel;
    this.truncType = truncType;
    calculateRelativeRates();
    scaleToTotalMomentRate(totMoRate);
  }



  /**
   * This updates the distribution, applying no truncation (truncType set to 0)
   * @param mean - the mean maginitude of the gaussian distribution
   * @param stdDev - the standard deviation
   * @param totCumRate - the total cumulative rate (at the lowest magnitude)
   */
  public void setAllButTotMoRate(double mean,double stdDev, double totCumRate)
                                throws DataPoint2DException {
  this.mean=mean;
  this.stdDev=stdDev;
  this.truncType = 0;
  calculateRelativeRates();
  scaleToCumRate(0,totCumRate);
  }


  /**
   * This updates the distribution, applying the truncation specified
   * @param mean - the mean maginitude of the gaussian distribution
   * @param stdDev - the standard deviation
   * @param totCumRate - the total cumulative rate (at the lowest magnitude)
   * @param truncLevel - in units of stdDev from the mean
   * @param truncType - 0 for none; 1 for upper only; and 2 for upper and lower
  */
  public void setAllButTotMoRate(double mean,double stdDev, double totCumRate,
                                 double truncLevel,int truncType)
                                 throws DataPoint2DException{
    this.mean=mean;
    this.stdDev=stdDev;
    this.truncLevel=truncLevel;
    this.truncType = truncType;
    calculateRelativeRates();
    scaleToCumRate(0,totCumRate);
  }


  /**
   * get the mean for this distribution
   * @return
   */
  public double getMean() {
    return this.mean;
  }


  /**
   * get the stdDev for this distribution
   * @return
   */
  public double getStdDev() {
    return this.stdDev;
  }

  /**
   * get the truncLevel which specifies the # of stdDev(from Mean) where the dist. cuts to zero.
   * @return
   */
  public double getTruncLevel() {
    return this.truncLevel;
  }


  /**
   * get the truncType which specifies whether it is no truncation  or 1 sided or 2 sided truncation
   * @return
   */
  public int getTruncType() {
   return this.truncType;
  }

  /**
   * returns the name of the class
   * @return
   */
  public String getDefaultName() {
    return NAME;
  }


  /**
   * return the info stored in the class in form of a String
   * @return
   */
  public String getDefaultInfo() {

    return "minMag="+minX+"; maxMag="+maxX+"; numMag="+num+"; mean="+mean+"; stdDev="+stdDev+"; totMoRate="+(float)getTotalMomentRate()+
           "; totCumRate="+(float)this.getCumRate(0)+"; truncType="+
           truncType+"; truncLevel="+truncLevel;

  }


  /**
   * Throws the exception if the set functions are called from outside the class
   * These have been made to prevent the access to the set functions of the EvenlyDiscretizedFunc class
   * by making a objects of the GaussianMagFreqDist class and calling the set functions of this from outside
   * @param point
   * @throws MagFreqDistException
   */
  public void set(DataPoint2D point) throws MagFreqDistException {
    throw new MagFreqDistException("Cannot Access the set function of the GaussianMagFreqDist from outside this class");
  }

  /**
   * Throws the exception if the set functions are called from outside the class
   * These have been made to prevent the access to the set functions of the EvenlyDiscretizedFunc class
   * by making a objects of the GaussianMagFreqDist class and calling the set functions of this from outside
   * @param x
   * @param y
   * @throws MagFreqDistException
   */
  public void set(double x,double y) throws MagFreqDistException {
    throw new MagFreqDistException("Cannot Access the set function of the GaussianMagFreqDist from outside this class");
  }

  /**
   * Throws the exception if the set functions are called from outside the class
   * These have been made to prevent the access to the set functions of the EvenlyDiscretizedFunc class
   * by making a objects of the GaussianMagFreqDist class and calling the set functions of this from outside
   * @param index
   * @param y
   * @throws MagFreqDistException
   */
  public void set(int index,double y) throws MagFreqDistException {
    throw new MagFreqDistException("Cannot Access the set function of the GaussianMagFreqDist from outside this class");
  }

  /**
   * This functions call the method set(int,double) in the EvenlyDiscretized class
   * to set the y-axis values based on the x-axis data provided by the user,in form
   * of the mag,mean stdDev. it then sets up the rate as the Y-axis values.
   * Based on the truncType it sets the rate to be zero after setting the
   * truncLevel(which specifies the # of stdDev from mean where dist. cut to zero
   */
  private void calculateRelativeRates()throws DataPoint2DException {
	if(stdDev != 0) {
	    for(int i=0;i<num;++i) {
	      double mag=getX(i);
	      double rate = Math.exp(-Math.pow((mag - mean),2)/(2*stdDev*stdDev));
	      super.set(i,rate);
	    }
	
	    if(truncType !=0) {
	      double magUpper = mean + truncLevel*stdDev;
	      int index = Math.round((float)((magUpper - minX)/delta));
	      // Make this the last non-zero rate by adding one in the next loop
	      for(int i=index+1;i>=0 && i<num;i++)
	        super.set(i,0);
	    }
	
	    if(truncType ==2) {
	      double magLower = this.mean - this.truncLevel *this.stdDev;
	      int index = Math.round((float)((magLower-this.minX)/this.delta));
	      // Make this the first non-zero rate by the <index in the next loop
	      for(int i=0;i<index && i<num;i++)
	        super.set(i,0);
	    }
	}
	else {
	    for(int i=0;i<num;++i) super.set(i,0);
	    try {
	    	super.set(mean, 1.0);
	    } catch(RuntimeException e){
	    	throw new RuntimeException("If sigma=0, then mean must equal one of the discrete X-axis magnitudes");
	    }
  	}


  }

  /**
   * this method (defined in parent) is deactivated here (name is finalized)

  public void setName(String name) throws  UnsupportedOperationException{
    throw new UnsupportedOperationException("setName not allowed for MagFreqDist.");

  }


   * this method (defined in parent) is deactivated here (name is finalized)

  public void setInfo(String info)throws  UnsupportedOperationException{
    throw new UnsupportedOperationException("setInfo not allowed for MagFreqDist.");

  }*/

}
