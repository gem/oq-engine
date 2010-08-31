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
 * <b>Title:</b>HanksBakun2002_MagAreaRel<br>
 *
 * <b>Description:</b>  This implements the "Hanks & Bakun (2002) Mag-Area Rel.",
 * published in the Bulletin of the Seismological Society of America
 * (Vol. 92, No. 5, pp. 1841�1846, June 2002).
 * The equation is Mag=3.98+log10(Area) if Area less than or equal to 537, or 
 * Mag=3.07+(4/3)log10(Area) if Area greater than 537.<p>
 *
 * @author Edward H. Field
 * @version 1.0
 */

public class HanksBakun2002_MagAreaRel extends MagAreaRelationship {

    final static String C = "HanksBakun2002_MagAreaRel";
    public final static String NAME = "Hanks & Bakun (2002)";
    
    final static double mag_cut = 3.98 + Math.log(537)*lnToLog;

    /**
     * Computes the median magnitude from rupture area.
     * @param area in km
     * @return median magnitude
     */
    public  double getMedianMag(double area){
    		if(area <= 537)
    			return  3.98 + Math.log(area)*lnToLog;
    		else 
    			return  3.07 + (4.0/3.0)*Math.log(area)*lnToLog;
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
    		if (mag <= mag_cut)
    			return Math.pow(10.0,mag-3.98);
    		else
    			return Math.pow(10.0,3*(mag-3.07)/4);
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

