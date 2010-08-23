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


import org.opensha.commons.exceptions.DataPoint2DException;
import org.opensha.commons.exceptions.DiscretizedFuncException;
import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.exceptions.MagFreqDistException;


/**
 * <p>Title: GutenbergRichterMagFreqDist.java </p>
 * <p>Description: This is a truncated incremental Gutenberg-Richter distribution.
 * Note that magLower and magUpper must exactly equal one of the descrete x-axis
 * values.</p>
 *
 * @author Nitin Gupta & Vipin Gupta   Date: Aug 8, 2002
 * @version 1.0
 */


public class GutenbergRichterMagFreqDist
    extends IncrementalMagFreqDist {

  public static String NAME = new String("Gutenberg Richter Dist"); // for showing messages

  //for Debug purposes
  private boolean D = false;

  private double magLower; // lowest magnitude that has non zero rate
  private double magUpper; // highest magnitude that has non zero rate
  private double bValue; // the b value

  /**
   * constructor : this is same as parent class constructor
   * @param min
   * @param num
   * @param delta
   * using the parameters we call the parent class constructors to initialise the parent class variables
   */

  public GutenbergRichterMagFreqDist(double min, int num, double delta) throws
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

  public GutenbergRichterMagFreqDist(double min, double max, int num) throws
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

  public GutenbergRichterMagFreqDist(double bValue, double totCumRate,
                                     double min, double max, int num) throws
      DiscretizedFuncException, InvalidRangeException {
    super(min, max, num);
    this.setAllButTotMoRate(min, max, totCumRate, bValue);
  }

  /**
   * constructor: this constructor assumes magLower is minX and
   *               magUpper to be maxX
   * @param min
   * @param num
   * @param delta
   * @param totMoRate : total Moment Rate
   * @param bValue : b value for this distribution
   */

  public GutenbergRichterMagFreqDist(double min, int num, double delta,
                                     double totMoRate, double bValue) throws
      DataPoint2DException {
    super(min, num, delta);
    // assumes magLower = minX and magUpper = maxX
    setAllButTotCumRate(minX, maxX, totMoRate, bValue);
  }

  /**
   * constructor:
   * @param min
   * @param num
   * @param delta
   * @param magLower  :  lowest magnitude that has non zero rate
   * @param magUpper  :  highest magnitude that has non zero rate
   * @param totMoRate :  total Moment Rate
   * @param bValue : b value for this distribution
   */

  public GutenbergRichterMagFreqDist(double min, int num, double delta,
                                     double magLower, double magUpper,
                                     double totMoRate, double bValue) throws
      InvalidRangeException,
      DataPoint2DException {
    super(min, num, delta);
    setAllButTotCumRate(magLower, magUpper, totMoRate, bValue);
  }

  /**
   * Set all values except Cumulative Rate
   * @param magLower  : lowest magnitude that has non zero rate
   * @param magUpper  : highest magnitude that has non zero rate
   * @param totMoRate : Total Moment Rate
   * @param bValue    : b Value
   */
  public void setAllButTotCumRate(double magLower, double magUpper,
                                  double totMoRate, double bValue) throws
      DataPoint2DException {

    this.magLower = magLower;
    this.magUpper = magUpper;
    this.bValue = bValue;
    calculateRelativeRates();
    scaleToTotalMomentRate(totMoRate);
  }

  /**
   * Set all values except total moment rate
   * @param magLower   : lowest magnitude that has non zero rate
   * @param magUpper   : highest magnitude that has non zero rate
   * @param totCumRate : Total Cumulative Rate
   * @param bValue     : b value
   */

  public void setAllButTotMoRate(double magLower, double magUpper,
                                 double totCumRate, double bValue) throws
      DataPoint2DException {

    this.magLower = magLower;
    this.magUpper = magUpper;
    this.bValue = bValue;
    calculateRelativeRates();
    scaleToCumRate(magLower, totCumRate);
  }

  /**
   * Set All but magUpper
   * @param magLower      : lowest magnitude that has non zero rate
   * @param totMoRate     : total moment rate
   * @param totCumRate    : total cumulative rate
   * @param bValue        : b value
   * @param relaxTotMoRate  : It is "true" or "false". It accounts for tha fact
   * that due to magnitude discretization, the specified totCumRate and totMoRate
   * cannot both be satisfied simultaneously. if it is false, it means that match
   * totMoRate exactly else it matches totCumRate exactly
   */
  public void setAllButMagUpper(double magLower, double totMoRate,
                                double totCumRate,
                                double bValue, boolean relaxTotMoRate) throws
      MagFreqDistException, DiscretizedFuncException,
      DataPoint2DException {

    if (D) System.out.println("magLower = " + magLower);
    if (D) System.out.println("totMoRate = " + totMoRate);
    if (D) System.out.println("totCumRate = " + totCumRate);
    if (D) System.out.println("bValue = " + bValue);
    if (D) System.out.println("relaxCumRate = " + relaxTotMoRate);

    // create variables for analytical moment integration
    double b = bValue;
    double N = totCumRate;
    double z = 1.5 - b;
    double X = N * b * Math.pow(10.0, 9.05) / z;
    double M1 = magLower;
    double M2;
    double tempTotMoRate = 0.0, lastMoRate = 0.0; // initialize this temporary moment rate

    int index;

    // now we find magUpper by trying each mag as magUpper, computing the total
    // moment rate analytically, and stopping when we get above the target moment
    //rate.
    for (index = getXIndex(M1) + 1; tempTotMoRate < totMoRate && index < num;
         index++) {
      lastMoRate = tempTotMoRate;
      M2 = getX(index);
      tempTotMoRate = X * (Math.pow(10, z * M2) - Math.pow(10, z * M1)) /
          (Math.pow(10, -b * M1) - Math.pow(10, -b * M2));
    }

    index--;

    if (D) System.out.println("just above target: index=" + index + "; mag=" +
                              getX(index));
    if (D) System.out.println("lastMoRate = " + lastMoRate);
    if (D) System.out.println("tempTotMoRate = " + tempTotMoRate);
    if (D) System.out.println("targetMoRate = " + totMoRate);

    // find which mag point it's closer:
    if (lastMoRate <= totMoRate && tempTotMoRate >= totMoRate) {
      double diff1 = tempTotMoRate - totMoRate;
      double diff2 = totMoRate - lastMoRate;

      // if it's closer to previous point
      if (diff2 < diff1) index--;
    }
    else
      throw new MagFreqDistException("Moment rate not attainable");

    magUpper = getX(index);

    if (D) System.out.println("chosen magUpper=" + magUpper);

    if (relaxTotMoRate)
      setAllButTotMoRate(magLower, magUpper, totCumRate, bValue);
    else
      setAllButTotCumRate(magLower, magUpper, totMoRate, bValue);
  }

  /**
   * Throws the exception if the set functions are called from outside the class
   * These have been made to prevent the access to the set functions of the EvenlyDiscretizedFunc class
   * by making a objects of the GutenbergRitcherMagFreqDist class and calling the set functions of this from outside
   * @param point
   * @throws MagFreqDistException
   */
  /*public void set(DataPoint2D point) throws MagFreqDistException {
    throw new MagFreqDistException("Cannot Access the set function of the GutenbergRichterMagFreqDist from outside this class");
  }*/

  /**
   * Throws the exception if the set functions are called from outside the class
   * These have been made to prevent the access to the set functions of the EvenlyDiscretizedFunc class
   * by making a objects of the GutenbergRitcherMagFreqDist class and calling the set functions of this from outside
   * @param x
   * @param y
   * @throws MagFreqDistException
   */
  /*public void set(double x, double y) throws MagFreqDistException {
    throw new MagFreqDistException("Cannot Access the set function of the GutenbergRichterMagFreqDist from outside this class");
  }*/

  /**
   * Throws the exception if the set functions are called from outside the class
   * These have been made to prevent the access to the set functions of the EvenlyDiscretizedFunc class
   * by making a objects of the GutenbergRitcherMagFreqDist class and calling the set functions of this from outside.
   * @param index
   * @param y
   * @throws MagFreqDistException
   */
  /*public void set(int index, double y) throws MagFreqDistException {
    throw new MagFreqDistException("Cannot Access the set function of the GutenbergRichterMagFreqDist from outside this class");
  }*/

  /**
   * private function to set the rate values
   */

  private void calculateRelativeRates() throws DataPoint2DException {

    // checks that magUpper, magLower lie between minX and maxX
    // it also checks that magUpper > magLower
    if (magLower < minX || magLower > maxX)
      throw new DataPoint2DException(
          "magLower should lie between minX and maxX");
    if (magLower > magUpper)
      throw new InvalidRangeException("magLower must be < magUpper");

    int indexLow = getXIndex(magLower); // find the index of magLower

    int indexUp = getXIndex(magUpper); // find the index of magUpper

    int i;

    for (i = 0; i < indexLow; ++i) // set all rates below magLower to 0
      super.set(i, 0.0);

    for (i = indexLow; i <= indexUp; ++i) // assign correct values to rates between magLower and magUpper
      super.set(i, Math.pow(10, -bValue * getX(i)));

    for (i = indexUp + 1; i < num; ++i) // set all rates above magUpper tp 0
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
   * @returns the magUpper : highest magnitude that has non zero rate
   */
  public double getMagUpper() {
    return magUpper;
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
            "; bValue=" + bValue + "; magLower=" + magLower + "; magUpper=" +
            (float) magUpper +
            "; totMoRate=" + (float)this.getTotalMomentRate() + "; totCumRate=" +
            (float) getCumRate(magLower));
  }

  /** Returns a rcopy of this and all points in this GutenbergRichter */
  /*public DiscretizedFuncAPI deepClone() throws DataPoint2DException {

    GutenbergRichterMagFreqDist f = new GutenbergRichterMagFreqDist(minX, num,
        delta);
    f.setAllButTotMoRate(this.magLower, this.magUpper, this.getTotCumRate(),
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
