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

package org.opensha.sha.imr.attenRelImpl;

import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;

public class GouletEtAl_2006_AttenRel extends BC_2004_AttenRel {

	
	
   public final static String NAME = "Goulet Et. Al. (2006)";
   public final static String SHORT_NAME = "GouletEtAl2006";
   private static final long serialVersionUID = 1234567890987654364L;

	
  public GouletEtAl_2006_AttenRel(ParameterChangeWarningListener warningListener) {
	  super(warningListener);
  }
  
  /**
   * Returns the Std Dev.
   */
  public double getStdDev(){
	  
	  String stdDevType = stdDevTypeParam.getValue().toString();
	  if (stdDevType.equals(StdDevTypeParam.STD_DEV_TYPE_NONE)) { // "None (zero)"
		  return 0;
	  }
	  updateCoefficients();
	  return getStdDevForGoulet();
  }
  
  
  /**
   * @return    The stdDev value for Goulet (2006) Site Correction Model
   */
  private double getStdDevForGoulet(){
	  double bVal = ((Double)AF_SlopeParam.getValue()).doubleValue();
	  double cVal = ((Double)this.AF_AddRefAccParam.getValue()).doubleValue();
	  double stdDevAF = ((Double)this.AF_StdDevParam.getValue()).doubleValue();
	  double tau = coeffs.tau;
	  as_1997_attenRel.setIntensityMeasure(im);
	  double asRockMean = as_1997_attenRel.getMean();
	  double asRockStdDev = as_1997_attenRel.getStdDev();
//	  double stdDev = Math.pow((bVal*Math.exp(asRockMean))/(Math.exp(asRockMean)+cVal)+1, 2)*
//      (Math.pow(Math.exp(asRockStdDev),2)-Math.pow(tau, 2))+Math.pow(stdDevAF,2)+Math.pow(tau,2);
	  double stdDev = Math.pow((bVal*Math.exp(asRockMean))/(Math.exp(asRockMean)+cVal)+1, 2)*
	                  (Math.pow((asRockStdDev),2))+Math.pow(stdDevAF,2);
//		System.out.println("asRockMean="+asRockMean+"  asRockStdDev="+asRockStdDev+"  StdDev="+stdDev);
//	  return Math.sqrt(stdDev-0.3*0.3);
	  return Math.sqrt(stdDev);
  }

  
  /**
   * get the name of this IMR
   *
   * @returns the name of this IMR
   */
  public String getName() {
    return NAME;
  }

  /**
   * Returns the Short Name of each AttenuationRelationship
   * @return String
   */
  public String getShortName() {
    return SHORT_NAME;
  }
  
}
