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

package org.opensha.commons.calc.magScalingRelations.magScalingRelImpl;


import org.opensha.commons.calc.magScalingRelations.MagAreaRelationship;
import org.opensha.commons.util.FaultUtils;


/**
 * <b>Title:</b>WC1994_MagAreaRelationship<br>
 *
 * <b>Description:</b>  This implements the Wells and Coppersmith (1994, Bull.
 * Seism. Soc. Am., pages 974-2002) magnitude versus rupture area relationships.  The
 * values are a function of rake.  Setting the rake to Double.NaN causes their "All"
 * rupture-types to be applied (and this is the default value for rake).  Note that the
 * standard deviation for area as a function of mag is given for log(area) (base-10)
 * not area.  <p>
 *
 * @author Edward H. Field
 * @version 1.0
 */

public class WC1994_MagAreaRelationship extends MagAreaRelationship {

    final static String C = "WC1994_MagAreaRelationship";
    public final static String NAME = "Wells & Coppersmith (1994)";


    /**
     * no-argument constructor.  All this does is set the rake to Double.NaN
     * (as the default)
     */
    public WC1994_MagAreaRelationship() {
      this.rake = Double.NaN;
    }


    /**
     * Computes the median magnitude from rupture area (for the previously set or default rake).
     * Note that thier "All" case is applied if rake=Double.NaN.
     * @param area in km
     * @return median magnitude
     */
    public double getMedianMag(double area){
      if (Double.isNaN(rake))
        // apply the "All" case
        return  4.07 + 0.98*Math.log(area)*lnToLog;
      else if (( rake <= 45 && rake >= -45 ) || (rake >= 135 && rake <= -135))
        // strike slip
        return  3.98 + 1.02*Math.log(area)*lnToLog;
      else if (rake > 0)
        // thrust/reverse
        return  4.33 + 0.90 * Math.log(area)*lnToLog;
      else
        // normal
        return  3.93 + 1.02*Math.log(area)*lnToLog;
    }

    /**
     * Gives the standard deviation for the magnitude as a function of area
     *  (for the previously set or default rake). Note that thier "All" case is applied
     * if rake=Double.NaN
     * @param area in km
     * @return standard deviation
     */
    public double getMagStdDev(){
      if (Double.isNaN(rake))
        // apply the "All" case
        return  0.24;
      else if (( rake <= 45 && rake >= -45 ) || (rake >= 135 && rake <= -135))
        // strike slip
        return  0.23;
      else if (rake > 0)
        // thrust/reverse
        return  0.25;
      else
        // normal
        return  0.25;

    }

    /**
     * Computes the median rupture area from magnitude (for the previously set
     * or default rake). Note that thier "All" case is applied if rake=Double.NaN
     * @param mag - moment magnitude
     * @return median area in km
     */
    public double getMedianArea(double mag){
      if  (Double.isNaN(rake))
          // their "All" case
          return Math.pow(10.0,-3.49+0.91*mag);
      else if (( rake <= 45 && rake >= -45 ) || (rake >= 135 && rake <= -135))
          // strike slip
          return  Math.pow(10.0, -3.42 + 0.90*mag);
      else if (rake > 0)
          // thrust/reverse
          return  Math.pow(10.0, -3.99 + 0.98*mag);
      else
          // normal
          return  Math.pow(10.0, -2.87 + 0.82*mag);

    }


    /**
     * Computes the standard deviation of log(area) (base-10) from magnitude
     *  (for the previously set or default rake)
     * @param mag - moment magnitude
     * @param rake in degrees
     * @return standard deviation
     */
    public double getAreaStdDev() {
      if (Double.isNaN(rake))
        // apply the "All" case
        return  0.24;
      else if (( rake <= 45 && rake >= -45 ) || (rake >= 135 && rake <= -135))
        // strike slip
        return  0.22;
      else if (rake > 0)
        // thrust/reverse
        return  0.26;
      else
        // normal
        return  0.22;

    }

    /**
     * This overides the parent method to allow a value of Double.NaN (which is used
     * to designate the "All" rupture-types option here).
     * @param rake
     */
    public void setRake(double rake) {
      if(!Double.isNaN(rake))
        FaultUtils.assertValidRake(rake);
      this.rake = rake;
    }


    /**
     * Returns the name of the object
     *
     */
    public String getName() {
      return NAME;
    }

/*
    // this was used as a quick test; everything looks good
    public static void main(String args[]) {
      WC1994_MagAreaRelationship magRel = new WC1994_MagAreaRelationship();

      System.out.println("Area  SS_Mag  R_Mag  N_Mag  All_Mag");
      System.out.print("1  ");
      System.out.print(magRel.getMedianMag(1.0, 0.0)+"  ");
      System.out.print(magRel.getMedianMag(1.0, 90.0)+"  ");
      System.out.print(magRel.getMedianMag(1.0, -90.0)+"  ");
      System.out.print(magRel.getMedianMag(1.0, Double.NaN)+"\n");

      System.out.print("500  ");
      System.out.print(magRel.getMedianMag(500, 0.0)+"  ");
      System.out.print(magRel.getMedianMag(500, 90.0)+"  ");
      System.out.print(magRel.getMedianMag(500, -90.0)+"  ");
      System.out.print(magRel.getMedianMag(500, Double.NaN)+"\n");

      System.out.print("10000  ");
      System.out.print(magRel.getMedianMag(1e4, 0.0)+"  ");
      System.out.print(magRel.getMedianMag(1e4, 90.0)+"  ");
      System.out.print(magRel.getMedianMag(1e4, -90.0)+"  ");
      System.out.print(magRel.getMedianMag(1e4, Double.NaN)+"\n");


      System.out.println(" ");
      System.out.println("Mag  SS_Area R_Area  N_Area  All_Area");
      System.out.print("4 ");
      System.out.print(magRel.getMedianArea(4, 0.0)+"  ");
      System.out.print(magRel.getMedianArea(4, 90.0)+"  ");
      System.out.print(magRel.getMedianArea(4, -90.0)+"  ");
      System.out.print(magRel.getMedianArea(4, Double.NaN)+"\n");

      System.out.print("6  ");
      System.out.print(magRel.getMedianArea(6, 0.0)+"  ");
      System.out.print(magRel.getMedianArea(6, 90.0)+"  ");
      System.out.print(magRel.getMedianArea(6, -90.0)+"  ");
      System.out.print(magRel.getMedianArea(6, Double.NaN)+"\n");

      System.out.print("8  ");
      System.out.print(magRel.getMedianArea(8, 0.0)+"  ");
      System.out.print(magRel.getMedianArea(8, 90.0)+"  ");
      System.out.print(magRel.getMedianArea(8, -90.0)+"  ");
      System.out.print(magRel.getMedianArea(8, Double.NaN)+"\n");

      System.out.println(" ");
      System.out.println("Mag_stdDev for  SS_Mag  R_Mag  N_Mag and All_Mag:");
      System.out.print(magRel.getMagStdDev(0.0)+"  ");
      System.out.print(magRel.getMagStdDev(90.0)+"  ");
      System.out.print(magRel.getMagStdDev(-90.0)+"  ");
      System.out.print(magRel.getMagStdDev(Double.NaN)+"\n");

      System.out.println(" ");
      System.out.println("Area_stdDev for  SS_Mag  R_Mag  N_Mag and All_Mag:");
      System.out.print(magRel.getAreaStdDev(0.0)+"  ");
      System.out.print(magRel.getAreaStdDev(90.0)+"  ");
      System.out.print(magRel.getAreaStdDev(-90.0)+"  ");
      System.out.print(magRel.getAreaStdDev(Double.NaN)+"\n");


    }
*/

}
