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

import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.util.FaultUtils;


/**
 * <b>Title:</b>MagScalingRelationship<br>
 *
 * <b>Description:  This is an abstract class that gives the median and standard
 * deviation of magnitude as a function of some scalar value (or the median and
 * standard deviation of the scalar value as a function of magnitude).  The values
 * can also be a function of rake</b>  <p>
 *
 * @author Edward H. Field
 * @version 1.0
 */

public abstract class MagScalingRelationship implements NamedObjectAPI  {

    final static String C = "MagScalingRelationship";

    protected final static double lnToLog = 0.434294;


    /**
     * The rupture rake in degrees.  The default is Double.NaN
     */
    protected double rake = Double.NaN;

    /**
     * Computes the median magnitude from some scalar value (for the previously set or default rake)
     * @return median magnitude
     */
    public abstract double getMedianMag(double scale);

    /**
     * Computes the median magnitude from some scalar value & rupture rake
     * @return median magnitude
     */
    public double getMedianMag(double scale, double rake) {
      setRake(rake);
      return getMedianMag(scale);
    }

    /**
     * This gives the  magnitude standard deviation (for the previously set or default rake)
     * @return median magnitude
     */
    public abstract double getMagStdDev();

    /**
     * This gives the magnitude standard deviation according to the given rake
     * @return median magnitude
     */
    public double getMagStdDev(double rake) {
      setRake(rake);
      return getMagStdDev();
    }

    /**
     * Computes the median scalar value from magnitude (for a previously set or default rake)
     */
    public abstract double getMedianScale(double mag);

    /**
     * Computes the median scalar value from magnitude & rake
     */
    public double getMedianScale(double mag, double rake) {
      setRake(rake);
      return getMedianScale(mag);
    }

    /**
     * Computes the standard deviation of the scalar-value from magnitude (for a
     * previously set or default rake)
     */
    public abstract double getScaleStdDev();

    /**
     * Computes the standard deviation of the scalar-value from rake
     */
    public double getScaleStdDev(double rake) {
      setRake(rake);
      return getScaleStdDev();
    }

    public void setRake(double rake) {
      FaultUtils.assertValidRake(rake);
      this.rake = rake;
    }



    /**
     * Returns the name of the object
     *
     */
    public abstract String getName() ;

}
