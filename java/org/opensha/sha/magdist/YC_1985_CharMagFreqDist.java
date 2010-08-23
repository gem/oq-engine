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
 * <p>Title: YC_1985_CharMagFreqDist.java </p>
 *
 * <p>Description: This is the "characteristic" magnitude-frequency distribution
 * defined by Youngs and Coppersmith (1985, Bull. Seism. Soc. Am., 939-964).
 * The distribution is Gutenberg-Richter between magLower and magPrime, and
 * constant between (magUpper-deltaMagChar) and magUpper with a rate equal to
 * that of the Gutenberg-Richter part at (magPrime-deltaMagPrime).
 * See their figure 10 for a graphical explanation of these parameters.
 * Note that magLower, magUpper, magPrime, magUpper-deltaMagChar, and
 * magPrime-deltaMagPrime must all be exactly equal one of the descrete x-axis points. </p>
 *
 * @author Edward H. Field   Date: Sept. 26, 2002
 * @version 1.0
 */


public class YC_1985_CharMagFreqDist extends IncrementalMagFreqDist {

  private String C = new String("YC_1985_CharMagFreqDist"); // for showing messages
  public static String NAME = new String("Youngs and Coppersmith Dist");
  private double magLower;
  private double magUpper;
  private double deltaMagChar;
  private double magPrime;
  private double deltaMagPrime;
  private double bValue;


   /**
    * Constructor : this is the same as the parent class constructor
    * @param min - minimum mag of distribution
    * @param num - number of points in distribution
    * @param delta - discretization interval
    */
   public YC_1985_CharMagFreqDist(double min,int num,double delta) throws InvalidRangeException {
     super(min,num,delta);
   }


   /**
    * Constructor: this is the same as the parent class constructor
    * @param min - minimum mag of distribution
    * @param max - maximum mag of distribution
    * @param num - number of points in distribution
    */
   public YC_1985_CharMagFreqDist(double min,double max,int num)
                                 throws DiscretizedFuncException,InvalidRangeException{
     super(min,max,num);
   }


   /**
    * Constructor: this is the full constructor
    /**
     * Constructor: this constructor assumes magLower is minX and magUpper to be maxX
     * @param min - minimum mag of distribution
     * @param num - number of points in distribution
     * @param delta - discretization interval
     * @param magLower - the lowest non-zero-rate magnitude
     * @param magUpper - the highest non-zero-rate magnitude
     * @param deltaMagChar - the width of the characteristic part (below magUpper)
     * @param magPrime - the upper mag of the GR part
     * @param deltaMagPrime - the distance below magPrime where the rate equals that over the char-rate part
     * @param bValue - the b value
     * @param totMoRate - the total moment rate
     */
   public YC_1985_CharMagFreqDist(double min,int num,double delta, double magLower,
                              double magUpper, double deltaMagChar, double magPrime,
                              double deltaMagPrime, double bValue, double totMoRate)
                              throws InvalidRangeException,DataPoint2DException {
     super(min,num,delta);

     this.magLower = magLower;
     this.magUpper = magUpper;
     this.deltaMagChar = deltaMagChar;
     this.magPrime = magPrime;
     this.deltaMagPrime = deltaMagPrime;
     this.bValue = bValue;

     calculateRelativeRates();
     scaleToTotalMomentRate(totMoRate);
   }


   /**
    * Constructor: this constructor assumes magLower is minX and magUpper to be maxX
    * @param min - minimum mag of distribution
    * @param num - number of points in distribution
    * @param delta - discretization interval
    * @param deltaMagChar - the width of the characteristic part (below magUpper)
    * @param magPrime - the upper mag of the GR part
    * @param deltaMagPrime - the distance below magPrime where the rate equals that over the char-rate part
    * @param bValue - the b value
    * @param totMoRate - the total moment rate
    */
   public YC_1985_CharMagFreqDist(double min,int num,double delta, double deltaMagChar, double magPrime,
                              double deltaMagPrime, double bValue, double totMoRate)
                              throws InvalidRangeException,DataPoint2DException {
     super(min,num,delta);
     // assumes magLower = minX and magUpper = maxX
     magLower=minX;
     magUpper=maxX;

     this.deltaMagChar = deltaMagChar;
     this.magPrime = magPrime;
     this.deltaMagPrime = deltaMagPrime;
     this.bValue = bValue;

     calculateRelativeRates();
     scaleToTotalMomentRate(totMoRate);
   }



   /**
    * Update distribution (using total moment rate rather than the total rate of char events)
    * @param magLower - the lowest non-zero-rate magnitude
    * @param magUpper - the highest non-zero-rate magnitude
    * @param deltaMagChar - the width of the characteristic part (below magUpper)
    * @param magPrime - the upper mag of the GR part
    * @param deltaMagPrime - the distance below magPrime where the rate equals that over the char-rate part
    * @param bValue - the b value
    * @param totMoRate - the total moment rate
    */

   public void setAllButTotCharRate(double magLower, double magUpper, double deltaMagChar,
                      double magPrime, double deltaMagPrime, double bValue,
                      double totMoRate) throws DataPoint2DException,InvalidRangeException {

        this.magLower = magLower;
        this.magUpper = magUpper;
        this.deltaMagChar = deltaMagChar;
        this.magPrime = magPrime;
        this.deltaMagPrime = deltaMagPrime;
        this.bValue = bValue;

        calculateRelativeRates();
        scaleToTotalMomentRate(totMoRate);
   }


   /**
    * Update distribution (using total rate of char events rather than total moment rate)
    * @param magLower - the lowest non-zero-rate magnitude
    * @param magUpper - the highest non-zero-rate magnitude
    * @param deltaMagChar - the width of the characteristic part (below magUpper)
    * @param magPrime - the upper mag of the GR part
    * @param deltaMagPrime - the distance below magPrime where the rate equals that over the char-rate part
    * @param bValue - the b value
    * @param totCharRate - the total rate of characteristic events (cum rate at magUpper-deltaMagChar).
    */

   public void setAllButTotMoRate(double magLower, double magUpper, double deltaMagChar,
                      double magPrime, double deltaMagPrime, double bValue,
                      double totCharRate) throws DataPoint2DException,InvalidRangeException {

        this.magLower = magLower;
        this.magUpper = magUpper;
        this.deltaMagChar = deltaMagChar;
        this.magPrime = magPrime;
        this.deltaMagPrime = deltaMagPrime;
        this.bValue = bValue;

        calculateRelativeRates();
        this.scaleToCumRate(magUpper-deltaMagChar,totCharRate);
   }





  /**
   * Throws the exception if the set functions are called from outside the class
   * These have been made to prevent the access to the set functions of the EvenlyDiscretizedFunc class
   * by making a objects of this class and calling the set functions of this from outside
   * @param point
   * @throws MagFreqDistException
   */
  public void set(DataPoint2D point) throws MagFreqDistException {
    throw new MagFreqDistException("Cannot Access the set function of the YC_1985_CharMagFreqDist from outside this class");
  }

  /**
   * Throws the exception if the set functions are called from outside the class
   * These have been made to prevent the access to the set functions of the EvenlyDiscretizedFunc class
   * by making a objects of this class and calling the set functions of this from outside
   * @param x
   * @param y
   * @throws MagFreqDistException
   */
  public void set(double x,double y) throws MagFreqDistException {
    throw new MagFreqDistException("Cannot Access the set function of the YC_1985_CharMagFreqDist from outside this class");
  }

  /**
   * Throws the exception if the set functions are called from outside the class
   * These have been made to prevent the access to the set functions of the EvenlyDiscretizedFunc class
   * by making a objects of this class and calling the set functions of this from outside.
   * @param index
   * @param y
   * @throws MagFreqDistException
   */
  public void set(int index,double y) throws MagFreqDistException {
    throw new MagFreqDistException("Cannot Access the set function of the YC_1985_CharMagFreqDist from outside this class");
  }


  /**
    * private function to set the rate values
    */

  private void calculateRelativeRates() throws DataPoint2DException,InvalidRangeException{


    // checks that magUpper, magLower, magPrime, deltaMagPrime, and deltaMagChar
    // are well posed.
    if( deltaMagChar < 0 )
        throw new InvalidRangeException("deltaMagChar must be positive");
    if( deltaMagPrime < 0 )
        throw new InvalidRangeException("deltaMagPrime must be positive");
    if(magLower < minX || magLower > maxX)
        throw new DataPoint2DException("magLower should lie between minX and maxX");
    if(magLower > magUpper)
        throw new InvalidRangeException("magLower cannot be less than magUpper");
    if(magPrime > magUpper || magPrime < magLower)
        throw new InvalidRangeException("magPrime must be between magLower and magUpper");
    if( (magPrime-deltaMagPrime) < magLower)
        throw new InvalidRangeException("magPrime-deltaMagPrime must be greater than magLower");
    if( deltaMagChar > (magUpper-magPrime+deltaMagPrime) )
        throw new InvalidRangeException("deltaMagChar > (magUpper-magPrime+deltaMagPrime), which is not allowed");
    if( magPrime > (magUpper-deltaMagChar) )
        throw new InvalidRangeException("magPrime > (magUpper-deltaMagChar), which is not allowed");


    double magForRate = magPrime - deltaMagPrime;

    int indexLower     = getXIndex(magLower);
    int indexUpper     = getXIndex(magUpper);
    int indexMagPrime  = getXIndex(magPrime);
    int indexForRate   = getXIndex(magForRate);
    int indexCharStart = getXIndex(magUpper-deltaMagChar);

    int i;

    for(i=0;i<num;++i) // initialize all rates to 0
       super.set(i,0.0);

    for(i=indexLower;i<=indexMagPrime;++i) // assign correct values to rates between magLower and magPrime
       super.set(i,Math.pow(10,-bValue*getX(i)));

    for(i=indexCharStart;i<=indexUpper;++i) // set rates over the characteristic-mag range
       super.set(i, Math.pow(10,-bValue*magForRate));

  }


  /**
   *
   * @returns the cumulative rate at magLower
   */

  public double getTotCumRate() {
    return getCumRate(magLower);
  }



  /**
   * @returns the bValue for this distribution
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
   *
   * @returns the magPrime
   */
  public double getMagPrime() {
    return magPrime;
  }

  /**
   *
   * @returns the deltaMagPrime
   */
  public double getDeltaMagPrime() {
    return deltaMagPrime;
  }

  /**
   *
   * @returns the deltaMagChar
   */
  public double getDeltaMagChar() {
    return deltaMagChar;
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
  public String getDefaultInfo() {
    return ("minMag="+minX+"; maxMag="+maxX+"; numMag="+num+"; magLower="+magLower+"; magUpper="+
            magUpper+"; deltaMagChar="+this.getDeltaMagChar()+
        "; magPrime="+this.getMagPrime()+"; deltaMagPrime="+getDeltaMagPrime()+
        " bValue="+bValue+"; totMoRate="+(float)this.getTotalMomentRate()+
        "; totCumRate="+(float)getCumRate(magLower));

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
