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

package org.opensha.nshmp.sha.calc;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;

/**
 * <p>Title: StdDisplacementCalc</p>
 *
 * <p>Description: Calculates the Standard displacement using the SA value function.</p>
 * @author Ned Field, Nitin Gupta and E.V.Leyendecker
 * @version 1.0
 */
public class StdDisplacementCalc {

  /**
   * Calculates the Std Displacement function Vs Period using the Sa Values.
   * @param saFunction ArbitrarilyDiscretizedFunc Sa Values function
   * where X values are the Periods and Y are the SA vals
   * @return ArbitrarilyDiscretizedFunc
   */
  public ArbitrarilyDiscretizedFunc getStdDisplacement(
      ArbitrarilyDiscretizedFunc saFunction) {

    ArbitrarilyDiscretizedFunc sdTFunction = new ArbitrarilyDiscretizedFunc();

    int numPoints = saFunction.getNum();
    for (int i = 0; i < numPoints; ++i) {
      double tempPeriod = Math.pow(saFunction.getX(i), 2.0);
      double sdVal = 9.77 * saFunction.getY(i) * tempPeriod;
      sdTFunction.set(saFunction.getX(i), sdVal);
    }
    return sdTFunction;
  }

}
