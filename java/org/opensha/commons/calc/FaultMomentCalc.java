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

package org.opensha.commons.calc;

/**
 * <p>Title: FaultMomentCalc </p>
 * <p>Description: This is a utility to calculate moment (in SI units: Newton-Meters) for
 * given fault information</p>
 *
 * @author Ned Field
 * @created    Dec 2, 2002
 * @version 1.0
 */

public final class FaultMomentCalc {
	
public final static double SHEAR_MODULUS = 3.0e10;

 /**
  * This function calculates the moment (SI units) for the given fault area and average slip,
  * assuming a shear modulus of 3e10 N-m.  Note that this also computes moment rate
  * if slip rate is given rather than slip.
  * @param area: the fault area (in square Meters)
  * @param slip: the ave slip (in Meters)
  * @returns Moment (in Newton-Meters) or moment rate if slip-rate given.
  */
  public static double getMoment(double area, double slip) {
    return SHEAR_MODULUS*slip*area;
  }
  
  /**
   * This function calculates slip for a given fault area and moment, assuming a shear modulus of 3e10 N-m.
   * This also calculates slip rate if moment rate is given
   * 
   * @param area: the fault area (in square Meters)
   * @param moment:(in Newton-Meters) or moment rate 
   * @returns Slip (in meters) or slip rate if moment-rate is given
   */
  public static double getSlip(double area, double moment) {
	  return moment/(area*SHEAR_MODULUS);
  }

}
