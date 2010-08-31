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

package org.opensha.commons.calc.magScalingRelations;



/**
 * <b>Title:</b>MagLengthRelationship<br>
 *
 * <b>Description:</b>  This is an abstract class that gives the median and standard
 * deviation of magnitude as a function of length (km) or visa versa.  The
 * values can also be a function of rake.  Note that the standard deviation for length
 * as a function of mag is given for natural-log(length) not length.  <p>
 *
 * @author Edward H. Field
 * @version 1.0
 */

public abstract class MagLengthRelationship extends MagScalingRelationship {

    final static String C = "MagLengthRelationship";

    /**
     * Computes the median magnitude from rupture length (for the previously set or default rake)
     * @param length in km
     * @return median magnitude
     */
    public abstract double getMedianMag(double length);

    /**
     * Computes the median magnitude from rupture length & rake
     * @param length in km
     * @param rake in degrees
     * @return median magnitude
     */
    public double getMedianMag(double length, double rake) {
      setRake(rake);
      return getMedianMag(length);
    }

    /**
     * Gives the standard deviation for the magnitude as a function of length
     *  (for the previously set or default rake)
     * @param length in km
     * @return standard deviation
     */
    public abstract double getMagStdDev();

    /**
     * Gives the standard deviation for the magnitude as a function of length & rake
     * @param length in km
     * @param rake in degrees
     * @return standard deviation
     */
    public double getMagStdDev(double rake) {
      setRake(rake);
      return getMagStdDev();
    }

    /**
     * Computes the median rupture length from magnitude (for the previously set
     * or default rake)
     * @param mag - moment magnitude
     * @return median length in km
     */
    public abstract double getMedianLength(double mag);

    /**
     * Computes the median rupture length from magnitude & rake
     * @param mag - moment magnitude
     * @param rake in degrees
     * @return median length in km
     */
    public double getMedianLength(double mag, double rake) {
      setRake(rake);
      return getMedianLength(mag);
    }

    /**
     * Computes the standard deviation of log(length) (base-10) from magnitude
     *  (for the previously set or default rake)
     * @param mag - moment magnitude
     * @param rake in degrees
     * @return standard deviation
     */
    public abstract double getLengthStdDev();

    /**
     * Computes the standard deviation of log(length) (base-10) from magnitude & rake
     * @param mag - moment magnitude
     * @param rake in degrees
     * @return standard deviation
     */
    public double getLengthStdDev(double rake) {
      setRake(rake);
      return getLengthStdDev();
    }

    /**
     * over-ride parent method to call getMedainLength(mag) here
     */
    public double getMedianScale(double mag) {
      return getMedianLength(mag);
    }

    /**
     * over-ride parent method to call getLengthStdDev(mag) here
     */
    public double getScaleStdDev() {
      return getLengthStdDev();
    }

}
