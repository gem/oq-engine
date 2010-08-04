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
 * <p>Title: TaperedGR_MagFreqDist </p>
 * <p>Description: This is a tapered incremental Gutenberg-Richter distribution.</p>
 *
 * @author Edward Field
 * @version 1.0
 */


public class TaperedGR_MagFreqDist
    extends IncrementalMagFreqDist {

  public static String NAME = new String("Tapered GR Dist"); // for showing messages

  //for Debug purposes
  private boolean D = false;

  private double magLower; // lowest magnitude that has non zero rate
  private double magCorner; // the taper magnitude
  private double bValue; // the b value

  /**
   * constructor : this is same as parent class constructor
   * @param min
   * @param num
   * @param delta
   * using the parameters we call the parent class constructors to initialise the parent class variables
   */

  public TaperedGR_MagFreqDist(double min, int num, double delta) throws
      InvalidRangeException {
    super(min, num, delta);
    this.magLower = min;
  }

  /**
   * constructor: this is sameas parent class constructor
   * @param min
   * @param max
   * @param num
   * using the min, max and num we calculate the delta
   */

  public TaperedGR_MagFreqDist(double min, double max, int num) throws
      DiscretizedFuncException, InvalidRangeException {
    super(min, max, num);
    
  }

  /**
   * constructor: this is sameas parent class constructor
   * @param min
   * @param max
   * @param num
   * using the min, max and num we calculate the delta
   */

  public TaperedGR_MagFreqDist(double bValue, double totCumRate,
                                     double min, double max, int num) throws
      DiscretizedFuncException, InvalidRangeException {
    super(min, max, num);
    setAllButTotMoRate(min, max, totCumRate, bValue);
  }


  /**
   * constructor:
   * @param min
   * @param num
   * @param delta
   * @param magLower  :  lowest magnitude that has non zero rate
   * @param magCorner  :  the corner magnitude
   * @param totMoRate :  total Moment Rate
   * @param bValue : b value for this distribution
   */

  public TaperedGR_MagFreqDist(double min, int num, double delta,
                                     double magLower, double magCorner,
                                     double totMoRate, double bValue) throws
      InvalidRangeException,
      DataPoint2DException {
    super(min, num, delta);
    setAllButTotCumRate(magLower, magCorner, totMoRate, bValue);
  }

  /**
   * Set all values except Cumulative Rate
   * @param magLower  : lowest magnitude that has non zero rate
   * @param magCorner  : the corner magnitude
   * @param totMoRate : Total Moment Rate
   * @param bValue    : b Value
   */
  public void setAllButTotCumRate(double magLower, double magCorner,
                                  double totMoRate, double bValue) throws
      DataPoint2DException {

    this.magLower = magLower;
    this.magCorner = magCorner;
    this.bValue = bValue;
    calculateRelativeRates();
    scaleToTotalMomentRate(totMoRate);
  }

  /**
   * Set all values except total moment rate
   * @param magLower   : lowest magnitude that has non zero rate
   * @param magCorner   : the corner magnitude
   * @param totCumRate : Total Cumulative Rate
   * @param bValue     : b value
   */

  public void setAllButTotMoRate(double magLower, double magCorner,
                                 double totCumRate, double bValue) throws
      DataPoint2DException {

    this.magLower = magLower;
    this.magCorner = magCorner;
    this.bValue = bValue;
    calculateRelativeRates();
    scaleToCumRate(magLower, totCumRate);
  }

  /**
   * Set All but magCorner.  This finds the corner magnitude iteratively, such that the final 
   * corner magnitude is guaranteed to be within 0.0001 of the "true" corner magnitude (and
   * accordingly, there is a slight discrepancy in the final moment rate as well - typically
   * orig/final moment rate = 1.0001).  This throws a runtime exception if it cannot find a corner
   * magnitude between magLower and maxX+0.0001 that satisfies the totMoRate.
   * TO DO: FIX EXCEPTION THROWING TO BE CONSISTENT WITH OTHER METHODS AND THE MFD PARAMETER CLASS
   * @param magLower      : lowest magnitude that has non zero rate
   * @param totMoRate     : total moment rate
   * @param totCumRate    : total cumulative rate
   * @param bValue        : b value
   */
  public void setAllButCornerMag(double magLower, double totMoRate,
		  double totCumRate, double bValue) throws
		  MagFreqDistException, DiscretizedFuncException,
		  DataPoint2DException {
	  
	  this.magLower = magLower;
	  this.bValue = bValue;
	  
	  // find magCorner iteratively
	  double deltaMag = 1;
	  double magStart = magLower;
	  for(int loop=0; loop<5; loop++) {
//		  System.out.println("loop #"+loop);
		  for(double mag=magStart; mag <= maxX+deltaMag; mag+= deltaMag) {
//			  System.out.println("mag = "+mag);
			  setAllButTotMoRate(magLower, mag, totCumRate, bValue);
//			  System.out.println("    totMoRate = "+getTotalMomentRate());
			  if(getTotalMomentRate() > totMoRate) {
//				  System.out.println("got in if statement");
				  magStart = mag-deltaMag;
				  if(magStart < magLower)
					  throw new RuntimeException(this.NAME+": Error - could not find corner magnitude that satisfies the moment rate (magLower too high?).");
				  deltaMag /= 10.0;
				  break;
			  }
		  }
	  }
	  
	  //make sure the moment rate for final magnitude is below the target
	  magCorner = magStart;
	  setAllButTotMoRate(magLower, magCorner, totCumRate, bValue);
	  double moRateBelow = getTotalMomentRate();
	  
	  // now get the final (mag just above) distribution
	  magCorner = magStart+0.0001; 
	  setAllButTotMoRate(magLower, magCorner, totCumRate, bValue);
	  
	  // make sure the two cases bracked the target moment rate
	  boolean success = (getTotalMomentRate() >= totMoRate && moRateBelow < totMoRate);
	  if(!success)
		  throw new RuntimeException(this.NAME+": Error - could not find corner magnitude that satisfies the moment rate (maxX too low?).");
	  
	  if(D) {
	  System.out.println("magLower = " + magLower);
	  System.out.println("magCorner = " + magCorner);
	  System.out.println("Orig totMoRate = " + totMoRate);
	  System.out.println("Final totMoRate = " + getTotalMomentRate());
	  System.out.println("Final/Orig totMoRate = " + getTotalMomentRate()/totMoRate+" (should be just greater than one)");
	  System.out.println("totCumRate = " + getTotCumRate());
	  System.out.println("bValue = " + bValue);
	  }
	  
  }
  
	public static void main(String[] args) {
		TaperedGR_MagFreqDist tgr = new TaperedGR_MagFreqDist(0.0,201,0.05);
		tgr.setAllButCornerMag(5, 1e19, 5, 1.0);
//		System.out.println(tgr.toString());
	}


  /**
   * Throws the exception if the set functions are called from outside the class
   * These have been made to prevent the access to the set functions of the EvenlyDiscretizedFunc class
   * by making a objects of the GutenbergRitcherMagFreqDist class and calling the set functions of this from outside
   * @param point
   * @throws MagFreqDistException
   */
  public void set(DataPoint2D point) throws MagFreqDistException {
    throw new MagFreqDistException("Cannot Access the set function of the GutenbergRichterMagFreqDist from outside this class");
  }

  /**
   * Throws the exception if the set functions are called from outside the class
   * These have been made to prevent the access to the set functions of the EvenlyDiscretizedFunc class
   * by making a objects of the GutenbergRitcherMagFreqDist class and calling the set functions of this from outside
   * @param x
   * @param y
   * @throws MagFreqDistException
   */
  public void set(double x, double y) throws MagFreqDistException {
    throw new MagFreqDistException("Cannot Access the set function of the GutenbergRichterMagFreqDist from outside this class");
  }

  /**
   * Throws the exception if the set functions are called from outside the class
   * These have been made to prevent the access to the set functions of the EvenlyDiscretizedFunc class
   * by making a objects of the GutenbergRitcherMagFreqDist class and calling the set functions of this from outside.
   * @param index
   * @param y
   * @throws MagFreqDistException
   */
  public void set(int index, double y) throws MagFreqDistException {
    throw new MagFreqDistException("Cannot Access the set function of the GutenbergRichterMagFreqDist from outside this class");
  }

  /**
   * private function to set the rate values
   */

  private void calculateRelativeRates() throws DataPoint2DException {

    // checks that magCorner, magLower lie between minX and maxX
    // it also checks that magCorner > magLower
    if (magLower < minX || magLower > maxX)
      throw new DataPoint2DException(
          "magLower should lie between minX and maxX");
    if (magLower > magCorner)
      throw new InvalidRangeException("magLower must be < magCorner");

    int indexLow = getXIndex(magLower); // find the index of magLower

    int i;
    
    //make an array with the cumulative distribution values (offset by delta/2, with one additional point)
    double[] cumRate = new double[num+1];
    for (i = 0; i < cumRate.length; ++i) {
    		double mag = i*delta + minX - delta/2.0;
		cumRate[i] = Math.pow(10, -bValue * mag) * Math.exp(-Math.pow(10, 1.5 * (mag-magCorner)));
    }

    	// now set the incremental rates
    for (i = 0; i < cumRate.length-1; ++i) {
    		super.set(i, cumRate[i]-cumRate[i+1]);
    }
    
    for (i = 0; i < indexLow; ++i) // set all rates below magLower to 0
        super.set(i, 0.0);

  }

  /**
   *
   * @returns the cumulative rate at magLower
   */

  public double getTotCumRate() throws DataPoint2DException {
    return getCumRate(magLower);
  }

  /**
   * @returns th bValue for this distribution
   */

  public double get_bValue() {
    return bValue;
  }

  /**
   *
   * @returns the magLower : lowest magnitude that has non zero rate
   */
  public double getMagLower() {
    return magLower;
  }

  /**
   *
   * @returns the magCorner : highest magnitude that has non zero rate
   */
  public double getmagCorner() {
    return magCorner;
  }

  /**
   * returns the name of this class
   * @return
   */

  public String getDefaultName() {
    return NAME;
  }

  /**
   * this function returns String for drawing Legen in JFreechart
   * @return : returns the String which is needed for Legend in graph
   */
  public String getDefaultInfo() throws DataPoint2DException {
    return ("minMag=" + minX + "; maxMag=" + maxX + "; numMag=" + num +
            "; bValue=" + bValue + "; magLower=" + magLower + "; magCorner=" +
            (float) magCorner +
            "; totMoRate=" + (float)this.getTotalMomentRate() + "; totCumRate=" +
            (float) getCumRate(magLower));
  }

  /** Returns a rcopy of this and all points in this GutenbergRichter */
  /*public DiscretizedFuncAPI deepClone() throws DataPoint2DException {

    GutenbergRichterMagFreqDist f = new GutenbergRichterMagFreqDist(minX, num,
        delta);
    f.setAllButTotMoRate(this.magLower, this.magCorner, this.getTotCumRate(),
                         this.bValue);
    f.tolerance = tolerance;
    return f;
  }*/

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
