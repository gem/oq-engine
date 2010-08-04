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

package org.opensha.commons.data.estimate;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;

/**
 * <p>Title: IntegerEstimate.java </p>
 * <p>Description:  This can be used to specify probabilities associated with
 * discrete values from an ArbitrarilyDiscretizedFunction. the discrete Values
 * should be integer values.
 *
 * </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class IntegerEstimate extends DiscreteValueEstimate{
  public final static String NAME  =  "Integer";

  private final static String EST_MSG_X_INTEGER = "All X values should be an integer "+
     " for Integer Estimate";

 /**
  * Constructor - Accepts DiscretizedFunc & an indication of whether it's
  * already normized. It checks that the values(along X Axis) in the function are integers
  * (or withing tolerance of integers)
  *
  * @param func DiscretizedFunc containing the X and Y values
  */
 public IntegerEstimate(ArbitrarilyDiscretizedFunc func, boolean isNormalized) {
   super(func, isNormalized);
   checkValues();

 }



 /**
  * It checks whether values (on X Axis) are indeed integers:
  *
  * @param func ArbitrarilyDiscretizedFunc containing the values and probabilities
  */
 public void checkValues() {
   if(!func.areAllXValuesInteger(this.tol)) throw new InvalidParamValException(EST_MSG_X_INTEGER);
 }

 public String getName() {
   return NAME;
 }


}
