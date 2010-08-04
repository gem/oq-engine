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
import org.opensha.commons.data.function.DiscretizedFuncList;
import org.opensha.nshmp.sha.data.calc.FaFvCalc;
import org.opensha.nshmp.util.ui.DataDisplayFormatter;

/**
 * <p>Title: SMSsS1Calculator</p>
 *
 * <p>Description: </p>
 *
 * @author Ned Field,Nitin Gupta and E.V.Leyendecker
 *
 * @version 1.0
 */
public class SMSsS1Calculator {

  /**
   *
   * @param saVals ArbitrarilyDiscretizedFunc
   * @param fa float
   * @param fv float
   * @param siteClass String
   * @return ArbitrarilyDiscretizedFunc
   */
  public ArbitrarilyDiscretizedFunc calculateSMSsS1(ArbitrarilyDiscretizedFunc
      saVals, float fa, float fv, String siteClass) {
    ArbitrarilyDiscretizedFunc function = new ArbitrarilyDiscretizedFunc();
    function.set(saVals.getX(0), fa * saVals.getY(0));
    function.set(saVals.getX(1), fv * saVals.getY(1));
    String title = "Spectral Response Accelerations SMs and SM1";
    String subTitle = "SMs = Fa x Ss and SM1 = Fv x S1";
    String SA = "Sa";
    String text1 = "SMs";
    String text2 = "SM1";
    String info = "";
    info += title + "\n";
    info +=
        DataDisplayFormatter.createSubTitleString(subTitle, siteClass, fa, fv);
    info +=
        DataDisplayFormatter.createFunctionInfoString(function, SA, text1, text2,
        siteClass);
    function.setInfo(info);
    return function;
  }
  
  /**
   * This is the preferred method to compute SMs and SM1 values when the input
   * location is specified via zip code. Previous methods would only calculate
   * the site modified values for the zip code centroid (based on interpolated
   * values of the centroid lat/lng). This method calculates the site modified
   * values for each of the centroid, max and min values. The returned function
   * contains values for the centroid, but the meta information will display
   * values for all three.
   * 
   * @param edition The current data edition. Used to determine which file to
   * read data from.
   * @param region The current geographic region. Not used at this time.
   * @param zipCode The zip code string (5 digits). Note: This value is not
   * verified against the region because this method may only be called after
   * the Ss and S1 values have been computed. Values are validated then, so no
   * need to revalidate now.
   * @param fa The Fa scaling factor for the given siteclass/Ss value.
   * @param fv The Fv scaling factor for the given siteclass/S1 value.
   * @param siteClass The current site class for which to modify the values.
   * @return A function with values representing the site modified values at the
   * zip code centroid, but with meta information displaying all three of the
   * centroid, max, and min values.
   * 
   */
  public ArbitrarilyDiscretizedFunc calculateSMSsS1(String edition,
		  String region, String zipCode, String siteClass) {
	  
	  // This is the "aggregate" function we will return at the end.
	  ArbitrarilyDiscretizedFunc function = new ArbitrarilyDiscretizedFunc();
	  
	  // Use this calculator to get the Ss and S1 values
	  SsS1Calculator calculator = new SsS1Calculator();
	  FaFvCalc fafvcalc = new FaFvCalc();
	  
	  // This is the function holding the Centroid values
	  DiscretizedFuncList funcs = calculator.getSsS1FuncList(edition, region,
			  zipCode);
	  
	  ArbitrarilyDiscretizedFunc funcCen = (ArbitrarilyDiscretizedFunc) 
	  		funcs.get(0);
	  ArbitrarilyDiscretizedFunc funcMax = (ArbitrarilyDiscretizedFunc)
	  		funcs.get(1);
	  ArbitrarilyDiscretizedFunc funcMin = (ArbitrarilyDiscretizedFunc)
		funcs.get(2);
	  
	  ArbitrarilyDiscretizedFunc smCen = new ArbitrarilyDiscretizedFunc();
	  ArbitrarilyDiscretizedFunc smMax = new ArbitrarilyDiscretizedFunc();
	  ArbitrarilyDiscretizedFunc smMin = new ArbitrarilyDiscretizedFunc();
	  
	  String info = "Spectral Response Accelerations SMs and SM1\n";
	  
	  double fa = fafvcalc.getFa(siteClass, funcCen.getY(0));
	  double fv = fafvcalc.getFv(siteClass, funcCen.getY(1));
	  info += "SMs = Fa x Ss and SM1 = Fv x S1\n" + siteClass + "\n";
	  
	  smCen.set(funcCen.getX(0), fa * funcCen.getY(0));
	  smCen.set(funcCen.getX(1), fv * funcCen.getY(1));
	  info += DataDisplayFormatter.createFunctionInfoString(smCen,"Centroid Sa",
			  "SMs, Fa = " + String.format("%4.3f", fa), "SM1, Fv = " + 
				String.format("%4.3f", fv), "");
	  
	  fa = fafvcalc.getFa(siteClass, funcMax.getY(0));
	  fv = fafvcalc.getFv(siteClass, funcMax.getY(1));
	  smMax.set(funcMax.getX(0), fa * funcMax.getY(0));
	  smMax.set(funcMax.getX(1), fv * funcMax.getY(1));
	  info += DataDisplayFormatter.createFunctionInfoString(smMax, "Maximum Sa",
			  "SMs, Fa = " + String.format("%4.3f", fa), "SM1, Fv = " + 
				String.format("%4.3f", fv), "");
	  
	  fa = fafvcalc.getFa(siteClass, funcMin.getY(0));
	  fv = fafvcalc.getFv(siteClass, funcMin.getY(1));
	  smMin.set(funcMin.getX(0), fa * funcMin.getY(0));
	  smMin.set(funcMin.getX(1), fv * funcMin.getY(1));
	  info += DataDisplayFormatter.createFunctionInfoString(smMin, "Minimum Sa",
			  "SMs, Fa = " + String.format("%4.3f", fa), "SM1, Fv = " + 
				String.format("%4.3f", fv), "");
	  
	  function.set(smCen.getX(0), smCen.getY(0));
	  function.set(smCen.getX(1), smCen.getY(1));
	  function.setInfo(info);
	  
	  // Return the aggregate function
	  return function;
  }

}
