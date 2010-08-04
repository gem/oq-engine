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
 * <b>Title:</b>MagAreaRelationship<br>
 *
 * <b>Description:</b>  This is an abstract class that gives the median and standard
 * deviation of magnitude as a function of area (km-squared) or visa versa.  The
 * values can also be a function of rake.  Note that the standard deviation for area
 * as a function of mag is given for natural-log(area) not area.  <p>
 *
 * @author Edward H. Field
 * @version 1.0
 */

public abstract class MagAreaRelationship extends MagScalingRelationship {

    final static String C = "MagAreaRelationship";

    /**
     * Computes the median magnitude from rupture area
     * @param area in km-squared
     * @return median magnitude
     */
    public abstract double getMedianMag(double area);

    /**
     * Computes the median magnitude from rupture area & rake
     * @param area in km-squared
     * @param rake in degrees
     * @return median magnitude
     */
    public double getMedianMag(double area, double rake) {
      setRake(rake);
      return getMedianMag(area);
    }

    /**
     * Gives the standard deviation for the magnitude as a function of area (for
     * the previously set or default rake)
     * @param area in km-squared
     * @return standard deviation
     */
    public abstract double getMagStdDev();

    /**
     * Gives the standard deviation for the magnitude as a function of area & rake
     * @param area in km-squared
     * @param rake in degrees
     * @return standard deviation
     */
    public double getMagStdDev(double rake) {
      setRake(rake);
      return getMagStdDev();
    }

    /**
     * Computes the median rupture area from magnitude (for the previously set or default rake)
     * @param mag - moment magnitude
     * @return median area in km-squared
     */
    public abstract double getMedianArea(double mag);

    /**
     * Computes the median rupture area from magnitude & rake
     * @param mag - moment magnitude
     * @param rake in degrees
     * @return median area in km-squared
     */
    public double getMedianArea(double mag, double rake) {
      setRake(rake);
      return getMedianArea(mag);
    }

    /**
     * Computes the standard deviation of log(area) (base-10) from magnitude
     * (for the previously set or default rake)
     * @param mag - moment magnitude
     * @param rake in degrees
     * @return standard deviation
     */
    public abstract double getAreaStdDev();

    /**
     * Computes the standard deviation of log(area) (base-10) from magnitude & rake
     * @param mag - moment magnitude
     * @param rake in degrees
     * @return standard deviation
     */
    public double getAreaStdDev(double rake) {
      setRake(rake);
      return getAreaStdDev();
    }

    /**
     * over-ride parent method to call getMedainArea(mag) here
     */
    public double getMedianScale(double mag) {
      return getMedianArea(mag);
    }

    /**
     * over-ride parent method to call getAreaStdDev() here
     */
    public double getScaleStdDev() {
      return getAreaStdDev();
    }

}
