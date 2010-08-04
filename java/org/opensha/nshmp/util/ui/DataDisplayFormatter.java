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

package org.opensha.nshmp.util.ui;

import java.text.DecimalFormat;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncList;

/**
 * <p>Title: DataDisplayFormatter</p>
 *
 * <p>Description: This class formats the data to be displayed in the application.</p>
 *
 * @author Ned Field,Nitin Gupta , E.V.Leyendecker
 *
 * @version 1.0
 */
public final class DataDisplayFormatter {

  private static DecimalFormat periodFormat = new DecimalFormat("0.0#");
  private static DecimalFormat saValFormat = new DecimalFormat("0.000");
  private static DecimalFormat annualExceedanceFormat = new DecimalFormat(
      "0.000E00#");

  /**
   * Creates the SubTitle info String
   * @param subtitle String
   * @param siteClass String
   * @param fa float
   * @param fv float
   * @return String
   */
  public static String createSubTitleString(String subtitle, String siteClass,
                                            float fa,
                                            float fv) {
    String dataInfo = "";
    dataInfo += subtitle + "\n";
    dataInfo += siteClass + " - " + " Fa = " + fa +
        " ,Fv = " + fv + "\n";
    return dataInfo;
  }

  /**
   * Formats the data to be displayed. This is used for output of the
   * build code analysis options for Ss S1 and SMs and SDs values.
   * 
   * @param function ArbitrarilyDiscretizedFunc
   * @param saString String
   * @param text1 String : First text to be displayed
   * @param text2 String : Second Text to be displayed
   * @param siteClass String
   * @return String
   */
  public static String createFunctionInfoString(ArbitrarilyDiscretizedFunc
                                                function,
                                                String saString, String text1,
                                                String text2, String siteClass) {
    String dataInfo = "";
		dataInfo += "\n" + pad("Period", 2) + pad(saString,2) + "\n";
		dataInfo += colPad("(sec)","Period",2) + colPad("(g)", saString, 2) + "\n";

		String meta = "(" + text1;
		if ( siteClass != null && !"".equals(siteClass)) {
			meta += ", " + siteClass;
		}
		meta += ")\n";
		
		dataInfo += colPad(periodFormat.format(function.getX(0)),"Period",2) +
			colPad(saValFormat.format(function.getY(0)),saString,2) + meta;
		
		meta = "(" + text2;
		if ( siteClass != null && !"".equals(siteClass)) {
			meta += ", " + siteClass;
		}
		meta += ")\n";
		
		dataInfo += colPad(periodFormat.format(function.getX(1)),"Period",2) +
			colPad(saValFormat.format(function.getY(1)),saString,2) + meta;
  
		return dataInfo;
  }
  
  public static String createFunctionInfoString(ArbitrarilyDiscretizedFunc func,
		  String saText, String SsText, String S1Text, String siteClass, 
		  boolean flag){
	  
	  StringBuffer info = new StringBuffer("\n");
	  
	  // CRs and CR1
	  info.append(pad("Period", 2) + pad("CR", 2) + "\n");
	  info.append(colPad("(sec)","Period", 2) + "\n");
	  info.append(colPad(periodFormat.format(func.getX(0)), "Period", 2) +
			  colPad(saValFormat.format(func.getY(6)), "CR", 2) + " (CRs)\n");
	  info.append(colPad(periodFormat.format(func.getX(1)), "Period", 2) +
			  colPad(saValFormat.format(func.getY(7)), "CR", 2) + " (CRs)\n\n");

	  // Column headers
	  info.append(pad("Period", 2) + pad(saText, 2) + "\n");
	  // Column units
	  info.append(colPad("(sec)","Period",2)+colPad("(g)",saText,2)+"\n");
	  
	  // SsUH, S1UH
	  info.append(colPad(periodFormat.format(func.getX(0)), "Period", 2) +
			  colPad(saValFormat.format(func.getY(2)), saText, 2) +" (SsUH)\n");
	  info.append(colPad(periodFormat.format(func.getX(1)), "Period", 2) +
			  colPad(saValFormat.format(func.getY(3)), saText,2)+" (S1UH)\n\n");
	  
	  // SsD, S1D
	  info.append(colPad(periodFormat.format(func.getX(0)), "Period", 2) +
			  colPad(saValFormat.format(func.getY(4)), saText, 2) + " (SsD)\n");
	  info.append(colPad(periodFormat.format(func.getX(1)), "Period", 2) +
			  colPad(saValFormat.format(func.getY(5)), saText, 2)+" (S1D)\n\n");
	  
	  // Ss and S1
	  info.append(colPad(periodFormat.format(func.getX(0)), "Period", 2) +
			  colPad(saValFormat.format(func.getY(0)), saText, 2) + " (Ss)\n");
	  info.append(colPad(periodFormat.format(func.getX(1)), "Period", 2) +
			  colPad(saValFormat.format(func.getY(1)), saText, 2) + " (S1)\n");
	  
	  // Return the information
	  return info.toString();
  }

  /**
   * Formats the data to be displayed. This is used for output of
   * the hazard curves analysis option.
   * @param function ArbitrarilyDiscretizedFunc
   * @param saString String
   * @param text1 String : First text to be displayed
   * @param text2 String : Second Text to be displayed
   * @param siteClass String
   * @return String
   */
  public static String createFunctionInfoString_HazardCurves(
      ArbitrarilyDiscretizedFunc
      function,
      String xAxisString, String yAxisString,
      String xAxisUnits, String yAxisUnits,
      String text) {
    String dataInfo = "";
		dataInfo += text + "\n" + pad(xAxisString, 2) + pad(yAxisString, 2) + "\n" +
			colPad("(" + xAxisUnits + ")", xAxisString, 2) + 
			colPad("(" + yAxisUnits + ")", yAxisString, 2) + "\n";

		for (int i = 0; i < function.getNum(); ++i) {
			dataInfo += colPad(saValFormat.format(function.getX(i)),xAxisString,2) +
				colPad(annualExceedanceFormat.format(function.getY(i)),yAxisString,2) +
				"\n";
	  }	
    return dataInfo;
  }

  /**
   * Formats the data to be displayed. This is called when computing
   * spectrum for the building code analysis options.
   * @param functions DiscretizedFuncList
   * @param siteClass String
   * @return String
   */
  public static String createFunctionInfoString(DiscretizedFuncList
                                                functionList, String siteClass) {
    String dataInfo = "";
		dataInfo += "\n" + colPad("Period", 6, 2) + colPad("Sa", 6, 2) +
			colPad("Sd", 6, 2) + "\n";
		dataInfo += colPad("(sec)", 6, 2) + colPad("(g)", 6, 2) +
			colPad("(inches)", 6, 2) + "\n";

    ArbitrarilyDiscretizedFunc function1 = (ArbitrarilyDiscretizedFunc)
        functionList.get(1);
    ArbitrarilyDiscretizedFunc function2 = (ArbitrarilyDiscretizedFunc)
        functionList.get(0);
		for (int i = 0; i < function1.getNum(); ++i) {
			dataInfo += colPad(saValFormat.format(function1.getX(i)),"Period",2) +
				colPad(saValFormat.format(function1.getY(i)), 6, 2) +
				colPad(saValFormat.format(function2.getY(i)), 6, 2) + "\n";
    }

    return dataInfo;
  }

  /**
   * Creates the info string for the 2009 function spectra.
   * @param funcs
   * @param siteClass
   * @param flag
   * @return
   */
  public static String createFunctionInfoString(DiscretizedFuncList funcs,
		  String siteClass, boolean flag) {
	  StringBuffer info = new StringBuffer("\n");
	  info.append(colPad("Period", 6, 2) + colPad("Sa", 6, 2) + "\n");
	  info.append(colPad("(sec)", 6, 2) + colPad("(g)", 6, 2) + "\n");
	  ArbitrarilyDiscretizedFunc func=(ArbitrarilyDiscretizedFunc) funcs.get(1);
	  int num = func.getNum();
	  for (int i = 0; i < num; ++i) {
		  info.append(colPad(saValFormat.format(func.getX(i)), "Period", 2) +
				  colPad(saValFormat.format(func.getY(i)), 6, 2) + "\n");
	  }
	  return info.toString();
  }
  
	public static String center(String str, int width) {
		int strLen = str.length();
		if (strLen >= width ) return str;
	
		String result = str;
		int dif = width - strLen;
		dif = dif / 2;
		for(int i = 0; i < dif; ++i) {
			result = " " + result;
		}
		while(result.length() < width) {
			result = result + " ";
		}
		return result;
	}

  public static String pad(String str, int padding) {
		int width = str.length() + (2*padding);
		return center(str, width);
	}

	public static String colPad(String str, String heading, int padding) {
		int width = heading.length();
		width += (2*padding);
		return center(str, width);
	}

	public static String colPad(String str, int headWidth, int padding) {
		int width = headWidth + (2*padding);
		return center(str, width);
	}
}
