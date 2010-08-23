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

import org.opensha.commons.calc.MomentMagCalc;
import org.opensha.commons.exceptions.DataPoint2DException;
import org.opensha.commons.exceptions.DiscretizedFuncException;
import org.opensha.commons.exceptions.InvalidRangeException;

/**
 * <p>Title: SingleMagFreqDist</p>
 * <p>Description: This has only a single magnitude with a non-zero rate.
 * Note that this magnitude must equal one of the descrete x-axis points.</p>
 *
 * @author :Nitin Gupta Date:Aug,8,2002
 * @version 1.0
 */

public class SingleMagFreqDist extends IncrementalMagFreqDist {

  /**
   * todo variables
   */
  public static String NAME = "Single-Mag Dist" ;
  private double mag;
  private double rate;

  /**
   * to do constructors
   */

  /**
   * Constructor
   * @param min
   * @param num
   * @param delta
   */
  public SingleMagFreqDist(double min,int num,double delta) throws InvalidRangeException {
    super(min,num,delta);
  }

  /**
   * Constructor
   * @param min
   * @param max
   * @param num
   */
  public SingleMagFreqDist(double min,double max,int num) throws DiscretizedFuncException,
                           InvalidRangeException {
    super(min,max,num);
  }

  /**
   * Constructor
   * @param min
   * @param delta
   * @param num
   * @param mag
   * @param moRate
   */

  public SingleMagFreqDist(double min,int num,double delta, double mag,double moRate)
                           throws InvalidRangeException,DataPoint2DException {
    super(min,num,delta);
    rate = moRate/MomentMagCalc.getMoment(mag);
    setMagAndRate(mag, rate);
  }

  /**
   * returns the rate for which  magnitude has non-zero rate
   * @return
   */
  public double getRate() {
    return rate;
  }

  /**
   *Gets the magnitude which has non-zero rate
   * @return
   */
  public double getMag() {
    return mag;
  }

  /**
   * sets the magnitude for non-zero rate
   * @param mag
   * @param rate
   */
  public void setMagAndRate(double mag, double rate) throws DataPoint2DException{
    this.mag=mag;
    this.rate=rate;
    for(int i=0;i<num;++i)
       set(i,0.0);
    set(mag,rate);
  }

  /**
   * Sets the magnitude
   * For this magnitude it calculates the non-zero rate from a static function
   * getMoment of the class MomentMagCalc and moRate
   * @param mag
   * @param moRate
   */
  public void setMagAndMomentRate(double mag,double moRate) throws DataPoint2DException{
    this.rate=moRate/MomentMagCalc.getMoment(mag);
    setMagAndRate(mag,rate);
  }

  /**
   * sets the non-zero rate
   * For this rate the magnitude is calculated using the static function
   * getMag of the class MomentMagCalc  and moRate.  NOTE: this does not
   * give the exact magnitude, but rather the closest magnitude given the
   * discretization.
   * @param rate
   * @param moRate
   */
  public void setRateAndMomentRate(double rate,double moRate, boolean relaxTotMoRate) throws DataPoint2DException{

    this.mag = MomentMagCalc.getMag(moRate/rate);
    int index = (int) Math.rint((mag - minX)/delta);
    if (relaxTotMoRate)
      setMagAndRate(getX(index),rate);
    else
      setMagAndMomentRate(getX(index),moRate);
  }

  /**
   *
   * @return the name of the class which was invoked by the user
   */
 public String getDefaultName() {
   return NAME;
 }

 /**
  *
  * @return the total information stored in the class in form of a string
  */
 public String getDefaultInfo() {
   double totMoRate= this.rate * MomentMagCalc.getMoment(this.mag);
   return "minMag="+minX+"; maxMag="+maxX+"; numMag="+num+"; mag="+(float) mag+"; rate="+(float)rate+"; totMoRate="+(float)totMoRate;
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
