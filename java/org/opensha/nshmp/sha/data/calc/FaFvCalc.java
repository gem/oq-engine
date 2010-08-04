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

package org.opensha.nshmp.sha.data.calc;

import org.opensha.nshmp.util.GlobalConstants;
import org.opensha.nshmp.util.Interpolation;



/**
 * <p>Title: FaFvCalc</p>
 *
 * <p>Description: This class calculates the Fa and Fv values based on
 * Ss (SA at 0.1sec) and S1 (SA at 1.0sec) respectively, and selected site coefficient.</p>
 * @author Ned Field, Nitin Gupta and E.V.Leyendecker
 * @version 1.0
 */
public class FaFvCalc {

  /**
   * Calculates Fa based on site class and SA at 0.1sec value (Ss Value)
   * @param siteClassVal String
   * @param sValue double
   * @return double
   */
  public double getFa(String siteClassVal, double sValue) {
    return getFaFv(siteClassVal, GlobalConstants.faData,
                   GlobalConstants.faColumnNames, sValue);
  }

  /**
   * Calculates Fv based on site class and SA at 1.0sec value (S1 Value)
   * @param siteClassVal String
   * @param s1Value double
   * @return double
   */
  public double getFv(String siteClassVal, double s1Value) {
    return getFaFv(siteClassVal, GlobalConstants.fvData,
                   GlobalConstants.fvColumnNames, s1Value);
  }

  /*
   * Calculate the Fa and Fv based on what user has requested
   * @param siteClassVal String
   * @param data Object[][] : Fa or Fv array
   * @param columnNames String[]
   * @param sValue double
   * @return double
   */
  private double getFaFv(String siteClassVal, Object[][] data,
                         String[] columnNames, double sValue) {
    char siteClass = siteClassVal.charAt(siteClassVal.length() - 1);
    int rowNumber;

    int length = data.length;
    // get the row number
    rowNumber = -1;
    //iterating over all the rows to get the row number which is based on the site class
    for (int i = 0; i < length; ++i) {
      char val = ( (String) data[i][0]).charAt(0);
      if (val == siteClass) {
        rowNumber = i;
        break;
      }
    }

    //get the column number
    int columnNumber = -1;
    length = columnNames.length;

    /**
     * This finds the column number based on Sa value.It checks between which 2 columns
     * does the SA value lies. If column number is 1 then no interpolation is
     * required else interpolate between the column number one got to previous column.
     * starting the index from 1 as first element in the columns names array is
     * constant "Site Class".
     */
    for (int j = 1; j < columnNames.length; ++j) {
      String columnName = columnNames[j];
      double colVal = getValueFromString(columnName);
      if (Double.isNaN(colVal)) {
        continue;
      }
      // found the columnNumber
      if (sValue <= colVal) {
        columnNumber = j;
        break;
      }
    }

    if (columnNumber == -1) {
      return Double.parseDouble( (String) data[rowNumber][columnNames.length -
                                1]);
    }
    else if (columnNumber == 1) {
      return Double.parseDouble( (String) data[rowNumber][columnNumber]);
    }
    else {
      String y2String = (String) data[rowNumber][columnNumber];
      String y1String = (String) data[rowNumber][columnNumber - 1];
      double y2 = Double.parseDouble(y2String);

      double x2 = getValueFromString(columnNames[columnNumber]);
      double y1 = Double.parseDouble(y1String);
      double x1 = getValueFromString(columnNames[columnNumber - 1]);
      return Interpolation.getInterpolatedY(x1, x2, y1, y2, sValue);
    }
  }

  /*
   * Getting the S value from the column name.
   * @param columnName String
   * @return double
   */
  private double getValueFromString(String columnName) {
    int index = -1;
    int indexForEqual = columnName.indexOf("=");
    for (int k = indexForEqual; k < columnName.length(); ++k) {
      if ( (columnName.charAt(k) >= '0' && columnName.charAt(k) <= '9') ||
          columnName.charAt(k) == '.') {
        index = k;
        break;
      }
    }
    if (index >= columnName.length() || index < 0) {
      return Double.NaN;
    }
    else {
      return Double.parseDouble(columnName.substring(index));
    }

  }

}
