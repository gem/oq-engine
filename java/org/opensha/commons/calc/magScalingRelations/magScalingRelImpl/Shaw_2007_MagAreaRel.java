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

/**
 * <b>Title:</b>Shaw_2007_MagAreaRel<br>
 *
 * <b>Description:</b>  .<p>
 *
 * @author Edward H. Field
 * @version 1.0
 */

public class Shaw_2007_MagAreaRel extends MagAreaRelationship {

    final static String C = "Shaw_2007_MagAreaRel";
    public final static String NAME = "Shaw (2007)";

    /**
     * Computes the median magnitude from rupture area.
     * @param area in km
     * @return median magnitude
     */
    public double getMedianMag(double area){
    	double alpha=6;
    	double h=15;
    	double numer= Math.max(1,Math.sqrt(area/(h*h)));
    	double denom= (1 + Math.max(1,(area/(alpha*h*h))))/2;
    	return  3.98 + Math.log(area)*lnToLog + 0.667*Math.log(numer/denom)*lnToLog;
    }

    /**
     * Gives the standard deviation for magnitude
     * @return standard deviation
     */
    public double getMagStdDev(){ return Double.NaN;}

    /**
     * Computes the median rupture area from magnitude
     * @param mag - moment magnitude
     * @return median area in km
     */
    public double getMedianArea(double mag){
          return Double.NaN;
   }

    /**
     * This returns NaN because the value is not available
     * @return standard deviation
     */
    public double getAreaStdDev() {return  Double.NaN;}

    /**
     * Returns the name of the object
     *
     */
    public String getName() {
      return NAME;
    }
}

