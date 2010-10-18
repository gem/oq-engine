/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with the Southern California
 * Earthquake Center (SCEC, http://www.scec.org) at the University of Southern
 * California and the UnitedStates Geological Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not
 * use this file except in compliance with the License. You may obtain a copy of
 * the License at
 * 
 * http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations under
 * the License.
 ******************************************************************************/

package org.opensha.commons.calc.magScalingRelations.magScalingRelImpl;

import org.opensha.commons.calc.magScalingRelations.MagLengthRelationship;
import org.opensha.commons.util.FaultUtils;

/**
 * <b>Title:</b>WC1994_MagLengthRelationship<br>
 * 
 * <b>Description:</b> This implements the Wells and Coppersmith (1994, Bull.
 * Seism. Soc. Am., pages 974-2002) magnitude versus surface-rupture length
 * relationships. The values are a function of rake. Setting the rake to
 * Double.NaN causes their "All" rupture-types to be applied (and this is the
 * default value for rake). Note that the standard deviation for length as a
 * function of mag is given for log(area) (base-10) not length.
 * <p>
 * 
 * @author Edward H. Field
 * @version 1.0
 */

public class WC1994_MagLengthRelationship extends MagLengthRelationship {

    final static String C = "WC1994_MagLengthRelationship";
    public final static String NAME = "W&C 1994 Mag-Length Rel.";

    /**
     * no-argument constructor. All this does is set the rake to Double.NaN (as
     * the default)
     */
    public WC1994_MagLengthRelationship() {
        this.rake = Double.NaN;
    }

    /**
     * Returns the name of the object
     * 
     */
    public String getName() {
        return NAME;
    }

    /**
     * Computes the median magnitude from rupture length (for the previously set
     * or default rake). Note that thier "All" case is applied if
     * rake=Double.NaN
     * 
     * @param length
     *            in km
     * @return median magnitude
     */
    public double getMedianMag(double length) {

        if (Double.isNaN(rake))
            // apply the "All" case
            return 5.08 + 1.16 * Math.log(length) * lnToLog;
        // else if (( rake <= 45 && rake >= -45 ) || (rake >= 135 && rake <=
        // -135))
        else if ((rake <= 45 && rake >= -45) || (rake >= 135 || rake <= -135))
            // strike slip
            return 5.16 + 1.12 * Math.log(length) * lnToLog;
        else if (rake > 0)
            // thrust/reverse
            return 5.0 + 1.22 * Math.log(length) * lnToLog;
        else
            // normal
            return 4.86 + 1.32 * Math.log(length) * lnToLog;
    }

    /**
     * Gives the standard deviation for the magnitude as a function of length
     * (for the previously set or default rake). Note that thier "All" case is
     * applied if rake=Double.NaN
     * 
     * @param length
     *            in km
     * @return standard deviation
     */
    public double getMagStdDev() {
        if (Double.isNaN(rake))
            // apply the "All" case
            return 0.28;
        // else if (( rake <= 45 && rake >= -45 ) || (rake >= 135 && rake <=
        // -135))
        else if ((rake <= 45 && rake >= -45) || (rake >= 135 || rake <= -135))
            // strike slip
            return 0.28;
        else if (rake > 0)
            // thrust/reverse
            return 0.28;
        else
            // normal
            return 0.34;

    }

    /**
     * Computes the median rupture length from magnitude (for the previously set
     * or default rake). Note that thier "All" case is applied if
     * rake=Double.NaN
     * 
     * @param mag
     *            - moment magnitude
     * @return median length in km
     */
    public double getMedianLength(double mag) {
        if (Double.isNaN(rake))
            // their "All" case
            return Math.pow(10.0, -3.22 + 0.69 * mag);
        // else if (( rake <= 45 && rake >= -45 ) || (rake >= 135 && rake <=
        // -135))
        else if ((rake <= 45 && rake >= -45) || (rake >= 135 || rake <= -135))
            // strike slip
            return Math.pow(10.0, -3.55 + 0.74 * mag);
        else if (rake > 0)
            // thrust/reverse
            return Math.pow(10.0, -2.86 + 0.63 * mag);
        else
            // normal
            return Math.pow(10.0, -2.01 + 0.50 * mag);

    }

    /**
     * Computes the standard deviation of log(length) (base-10) from magnitude
     * (for the previously set or default rake)
     * 
     * @param mag
     *            - moment magnitude
     * @param rake
     *            in degrees
     * @return standard deviation
     */
    public double getLengthStdDev() {
        if (Double.isNaN(rake))
            // apply the "All" case
            return 0.22;
        // else if (( rake <= 45 && rake >= -45 ) || (rake >= 135 && rake <=
        // -135))
        else if ((rake <= 45 && rake >= -45) || (rake >= 135 || rake <= -135))
            // strike slip
            return 0.23;
        else if (rake > 0)
            // thrust/reverse
            return 0.20;
        else
            // normal
            return 0.21;

    }

    /**
     * This overides the parent method to allow a value of Double.NaN (which is
     * used to designate the "All" rupture-types option here).
     * 
     * @param rake
     */
    public void setRake(double rake) {
        if (!Double.isNaN(rake))
            FaultUtils.assertValidRake(rake);
        this.rake = rake;
    }

    /*
     * // this was used as a quick test; everything looks good public static
     * void main(String args[]) { WC1994_MagLengthRelationship magRel = new
     * WC1994_MagLengthRelationship();
     * 
     * System.out.println("Length  SS_Mag  R_Mag  N_Mag  All_Mag");
     * System.out.print("1  "); System.out.print(magRel.getMedianMag(1.0,
     * 0.0)+"  "); System.out.print(magRel.getMedianMag(1.0, 90.0)+"  ");
     * System.out.print(magRel.getMedianMag(1.0, -90.0)+"  ");
     * System.out.print(magRel.getMedianMag(1.0, Double.NaN)+"\n");
     * 
     * System.out.print("500  "); System.out.print(magRel.getMedianMag(500,
     * 0.0)+"  "); System.out.print(magRel.getMedianMag(500, 90.0)+"  ");
     * System.out.print(magRel.getMedianMag(500, -90.0)+"  ");
     * System.out.print(magRel.getMedianMag(500, Double.NaN)+"\n");
     * 
     * System.out.print("10000  "); System.out.print(magRel.getMedianMag(1e4,
     * 0.0)+"  "); System.out.print(magRel.getMedianMag(1e4, 90.0)+"  ");
     * System.out.print(magRel.getMedianMag(1e4, -90.0)+"  ");
     * System.out.print(magRel.getMedianMag(1e4, Double.NaN)+"\n");
     * 
     * 
     * System.out.println(" ");
     * System.out.println("Mag  SS_Length R_Length  N_Length  All_Length");
     * System.out.print("4 "); System.out.print(magRel.getMedianLength(4,
     * 0.0)+"  "); System.out.print(magRel.getMedianLength(4, 90.0)+"  ");
     * System.out.print(magRel.getMedianLength(4, -90.0)+"  ");
     * System.out.print(magRel.getMedianLength(4, Double.NaN)+"\n");
     * 
     * System.out.print("6  "); System.out.print(magRel.getMedianLength(6,
     * 0.0)+"  "); System.out.print(magRel.getMedianLength(6, 90.0)+"  ");
     * System.out.print(magRel.getMedianLength(6, -90.0)+"  ");
     * System.out.print(magRel.getMedianLength(6, Double.NaN)+"\n");
     * 
     * System.out.print("8  "); System.out.print(magRel.getMedianLength(8,
     * 0.0)+"  "); System.out.print(magRel.getMedianLength(8, 90.0)+"  ");
     * System.out.print(magRel.getMedianLength(8, -90.0)+"  ");
     * System.out.print(magRel.getMedianLength(8, Double.NaN)+"\n");
     * 
     * System.out.println(" ");
     * System.out.println("Mag_stdDev for  SS_Mag  R_Mag  N_Mag and All_Mag:");
     * System.out.print(magRel.getMagStdDev(0.0)+"  ");
     * System.out.print(magRel.getMagStdDev(90.0)+"  ");
     * System.out.print(magRel.getMagStdDev(-90.0)+"  ");
     * System.out.print(magRel.getMagStdDev(Double.NaN)+"\n");
     * 
     * System.out.println(" ");
     * System.out.println("Length_stdDev for  SS_Mag  R_Mag  N_Mag and All_Mag:"
     * ); System.out.print(magRel.getLengthStdDev(0.0)+"  ");
     * System.out.print(magRel.getLengthStdDev(90.0)+"  ");
     * System.out.print(magRel.getLengthStdDev(-90.0)+"  ");
     * System.out.print(magRel.getLengthStdDev(Double.NaN)+"\n"); }
     */
}
