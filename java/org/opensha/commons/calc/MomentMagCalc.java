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
 * <p>Title: MomentMagCalc </p>
 * <p>Description: This is a utility to calculate moment (in SI units: Newton-Meters) for a given magnitude or vice versa</p>
 *
 * @author Vipin Gupta
 * @created    August 7, 2002
 * @version 1.0
 */

public final class MomentMagCalc {

 /**
  * This function calculates the moment for the given magnitude
  * @param mag: Magnitude
  * @returns Moment in Newton-Meters
  */
 public static double getMoment(double mag) {
    return (Math.pow(10,1.5*mag+9.05));
 }

 /**
  * This function calculates the magnitude for the given moment
  * @param moment : Moment in Newton-Meters
  * @returns magnitude for the given moment
  */
 public static double getMag(double moment) {
   return (Math.log(moment)/Math.log(10)-9.05)/1.5;
 }

}
