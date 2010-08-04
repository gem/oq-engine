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

import java.text.DecimalFormat;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncList;
import org.opensha.commons.geo.Location;
import org.opensha.nshmp.exceptions.ZipCodeErrorException;
import org.opensha.nshmp.sha.data.SiteInterpolation;
import org.opensha.nshmp.sha.io.DataFileNameSelectorForUHS;
import org.opensha.nshmp.sha.io.UHS_Record;
import org.opensha.nshmp.util.GlobalConstants;
import org.opensha.nshmp.util.LocationUtil;
import org.opensha.nshmp.util.ZipCodeToLatLonConvertor;
import org.opensha.nshmp.util.ui.DataDisplayFormatter;

/**
 * <p>Title: UHS_SACalculator</p>
 *
 * <p>Description: Computes the values for the Ss and S1 for the given location or
 * territory in USA.</p>
 * @author  Ned Field, Nitin Gupta , E.V.Leyendecker
 * @version 1.0
 */
public class UHS_SACalculator {

  //grid spacing in file
  protected float gridSpacing;

  /**
   * Some static String for the data printing
   */
  protected static final String SA_TITLE =
      "Uniform Hazard Spectrum (UHS) for ";

  private static final String BC_BOUNDARY_STRING = "B/C Boundary";

  protected DecimalFormat latLonFormat = new DecimalFormat("0.0000##");

  private static final String PGA_Metadata_String =
      "UHS values of PGA, Ss, and S1 for ";

  /*
   * Computes the Std Displacement function using the SA function.
   */
  private ArbitrarilyDiscretizedFunc calcSDTFunction(ArbitrarilyDiscretizedFunc
      saFunction) {
    StdDisplacementCalc calc = new StdDisplacementCalc();
    ArbitrarilyDiscretizedFunc sdTFunction = calc.getStdDisplacement(saFunction);
    return sdTFunction;
  }

  /*
   *
   * @param geographicRegion String
   * @param dataEdition String
   * @param saFunction ArbitrarilyDiscretizedFunc
   * @return ArbitrarilyDiscretizedFunc
   */
  private ArbitrarilyDiscretizedFunc createPGAValues(String geographicRegion,
      String dataEdition,
      ArbitrarilyDiscretizedFunc saFunction) {
    ArbitrarilyDiscretizedFunc pgaFunction = new ArbitrarilyDiscretizedFunc();
    if (dataEdition.equals(GlobalConstants.data_1996) ||
        dataEdition.equals(GlobalConstants.data_2002)) {

      //number of Periods in this case is 7
      //T0,PGA
      pgaFunction.set(saFunction.get(0));
      //Ts,Ss
      pgaFunction.set(saFunction.get(2));
      //T1,S1
      pgaFunction.set(saFunction.get(5));
    }
    else if (dataEdition.equals(GlobalConstants.data_1998)) {
      //number of periods in this are 4
      //T0,PGA
      pgaFunction.set(saFunction.get(0));
      //Ts,Ss
      pgaFunction.set(saFunction.get(1));
      //T1,S1
      pgaFunction.set(saFunction.get(3));

    }
    else {
      //number of periods in this are 3
      //T0,PGA
      pgaFunction.set(saFunction.get(0));
      //Ts,Ss
      pgaFunction.set(saFunction.get(1));
      //T1,S1
      pgaFunction.set(saFunction.get(2));
    }
    pgaFunction.setName(GlobalConstants.UHS_PGA_FUNC_NAME);
    return pgaFunction;
  }

  /**
   *
   * @param latitude double
   * @param longitude double
   * @return ArbitrarilyDiscretizedFunc
   */
  public DiscretizedFuncList getSA(String selectedRegion,
                                   String selectedEdition,
                                   double latitude, double longitude,
                                   String spectraType) {

    UHS_Record record = new UHS_Record();
    DataFileNameSelectorForUHS dataFileSelector = new
        DataFileNameSelectorForUHS();
    String fileName = dataFileSelector.getFileName(selectedRegion,
        selectedEdition, latitude,
        longitude, spectraType);
    SiteInterpolation siteSaVals = new SiteInterpolation();
    ArbitrarilyDiscretizedFunc function = siteSaVals.getPeriodValuesForLocation(
        fileName, record,
        latitude, longitude);
    function.setName(GlobalConstants.UNIFORM_HAZARD_SPECTRUM_NAME + " of " +
                     GlobalConstants.SA_Vs_T_GRAPH_NAME);
    ArbitrarilyDiscretizedFunc sdTFunction = calcSDTFunction(function);
    gridSpacing = (float) siteSaVals.getGridSpacing();

    DiscretizedFuncList funcList = new DiscretizedFuncList();
    funcList.add(sdTFunction);
    funcList.add(function);
    funcList.add(createPGAValues(selectedRegion, selectedEdition, function));
    funcList.setInfo(setInfo(funcList, latitude, longitude, spectraType));
    return funcList;
  }

  private String setInfo(DiscretizedFuncList funcList,
                         double latitude, double longitude, String spectraType) {
    //set the info for the function being added
    String info = "";
    info += SA_TITLE + spectraType + "\n\n";

    info += "Latitude = " + latLonFormat.format(latitude) + "\n";
    info += "Longitude = " + latLonFormat.format(longitude) + "\n";
    info += BC_BOUNDARY_STRING + "\n";

    info += "Data are based on a " + gridSpacing + " deg grid spacing";
    info +=
        DataDisplayFormatter.createFunctionInfoString(funcList,
        GlobalConstants.SITE_CLASS_B);
    //adding the info for the PGA function
    //info +=
      //  getPGAInfo( (ArbitrarilyDiscretizedFunc) funcList.get(2), spectraType);

    return info;
  }

  /*
   * Ading the PGA info to the Metadata
   * @param pgaFunction ArbitrarilyDiscretizedFunc
   * @param spectraType String
   * @return String
   */
  private String getPGAInfo(ArbitrarilyDiscretizedFunc pgaFunction,
                            String spectraType) {
    String info = "\n";
    info += PGA_Metadata_String + spectraType + "\n";
    info += BC_BOUNDARY_STRING + "\n";
    info += "Data are based on a " + gridSpacing + " deg grid spacing";
    info +=
        DataDisplayFormatter.createFunctionInfoString_HazardCurves(pgaFunction,
        "Period", "Sa", GlobalConstants.PERIOD_UNITS,
        GlobalConstants.SA_UNITS, "");
    return info;
  }

  private String setInfoForZipCode(DiscretizedFuncList funcList, String zipCode,
                                   double lat, double lon, String spectraType) {
    //adding the info for each function
    //set the info for the function being added
    String info = "";
    info += SA_TITLE + spectraType + "\n\n";

    info += "Zip Code - " + zipCode + "\n";
    info += "Zip Code Latitude = " + latLonFormat.format(lat) + "\n";
    info += "Zip Code Longitude = " + latLonFormat.format(lon) + "\n";
    info += BC_BOUNDARY_STRING + "\n";

    info += "Data are based on a " + gridSpacing + " deg grid spacing";
    info +=
        DataDisplayFormatter.createFunctionInfoString(funcList,
        GlobalConstants.SITE_CLASS_B);
    //adding the info for the PGA function
    //info +=
      //  getPGAInfo( (ArbitrarilyDiscretizedFunc) funcList.get(2), spectraType);
    return info;

  }

  /**
   *
   * @param zipCode
   * @return
   */
  public DiscretizedFuncList getSA(String selectedRegion,
                                   String selectedEdition,
                                   String zipCode, String spectraType) throws
      ZipCodeErrorException {
    Location loc = ZipCodeToLatLonConvertor.getLocationForZipCode(zipCode);
    LocationUtil.checkZipCodeValidity(loc, selectedRegion);
    double lat = loc.getLatitude();
    double lon = loc.getLongitude();
    //getting the SA Period values for the lat lon for the selected Zip code.
    DiscretizedFuncList funcList = getSA(selectedRegion,
                                         selectedEdition, lat, lon, spectraType);
    funcList.setInfo(setInfoForZipCode(funcList, zipCode, lat, lon, spectraType));
    return funcList;
  }

}
