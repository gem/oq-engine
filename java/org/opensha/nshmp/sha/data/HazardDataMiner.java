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

package org.opensha.nshmp.sha.data;

import java.net.MalformedURLException;
import java.rmi.Naming;
import java.rmi.NotBoundException;
import java.rmi.RemoteException;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncList;
import org.opensha.nshmp.exceptions.ZipCodeErrorException;
import org.opensha.nshmp.sha.calc.api.HazardDataCalcAPI;
import org.opensha.nshmp.sha.calc.remote.api.RemoteHazardDataCalcFactoryAPI;
import org.opensha.nshmp.util.GlobalConstants;

/**
 * <p>Title: HazardDataMiner</p>
 *
 * <p>Description: This class computes the Ss and S1 based on the location inputs
 * provided by the user in the application.</p>
 *
 * @author Ned Field, Nitin Gupta and E.V.Leyendecker
 * @version 1.0
 */
public class HazardDataMiner implements HazardDataMinerAPI{

  /**
   * Class default constructor
   */
  public HazardDataMiner() {
  }

  private HazardDataCalcAPI getHazardDataCalcObject() throws RemoteException {
    try {
      RemoteHazardDataCalcFactoryAPI remoteDataCalc = (
          RemoteHazardDataCalcFactoryAPI)
          Naming.lookup(GlobalConstants.registrationName);
      HazardDataCalcAPI calc = remoteDataCalc.getRemoteHazardDataCalc();
      return calc;
    }
    catch (MalformedURLException e) {
      e.printStackTrace();
    }
    catch (NotBoundException ee) {
      ee.printStackTrace();
    }
    return null;
  }

  /**
   *
   * @param hazardCurveFunction ArbitrarilyDiscretizedFunc
   * @param fex double Frequency of exceedance = 1/ReturnPd
   * @param expTime double
   * @return double
   */
  public double getExceedProb(
      double fex, double expTime) throws RemoteException {

    HazardDataCalcAPI calc = getHazardDataCalcObject();
    return calc.computeExceedProb(fex, expTime);
  }

  /**
   *
   * @param exceedProb double
   * @param expTime double
   * @return double
   */
  public double getReturnPeriod(double exceedProb, double expTime) throws
      RemoteException {
    HazardDataCalcAPI calc = getHazardDataCalcObject();
    return calc.computeReturnPeriod(exceedProb, expTime);
  }

  /**
   * Gets the Basic Hazard Curve using the Lat and Lon
   * @param geographicRegion String
   * @param dataEdition String
   * @param lat double
   * @param lon double
   * @return ArbitrarilyDiscretizedFunc
   */
  public ArbitrarilyDiscretizedFunc getBasicHazardcurve(String geographicRegion,
      String dataEdition, double lat, double lon,
      String hazCurveType) throws RemoteException {

    HazardDataCalcAPI calc = getHazardDataCalcObject();
    return calc.computeHazardCurve(geographicRegion, dataEdition, lat, lon,
                                   hazCurveType);
  }

  /**
   * Gets the Basic Hazard Curve using the Lat and Lon
   * @param geographicRegion String
   * @param dataEdition String
   * @param zipCode String
   * @return DiscretizedFuncList
   * @throws ZipCodeErrorException
   */
  public ArbitrarilyDiscretizedFunc getBasicHazardcurve(String geographicRegion,
      String dataEdition, String zipCode,
      String hazCurveType) throws
      ZipCodeErrorException, RemoteException {

    HazardDataCalcAPI calc = getHazardDataCalcObject();
    return calc.computeHazardCurve(geographicRegion, dataEdition, zipCode,
                                   hazCurveType);
  }

  /**
   * Gets the Ss and S1 when location is provided using the Lat and Lon
   * @param geographicRegion String
   * @param dataEdition String
   * @param lat double
   * @param lon double
   * @return ArbitrarilyDiscretizedFunc
   */
  public ArbitrarilyDiscretizedFunc getSsS1(String geographicRegion,
                                            String dataEdition, double lat,
                                            double lon) throws RemoteException {

    HazardDataCalcAPI calc = getHazardDataCalcObject();
    return calc.computeSsS1(geographicRegion, dataEdition, lat, lon);
  }

  /**
   *
   * @param geographicRegion String
   * @param dataEdition String
   * @param lat double
   * @param lon double
   * @param selectedSpectraType String
   * @return ArbitrarilyDiscretizedFunc
   */
  public ArbitrarilyDiscretizedFunc getSsS1(String geographicRegion,
                                            String dataEdition, double lat,
                                            double lon,
                                            String selectedSpectraType) throws
      RemoteException {

    HazardDataCalcAPI calc = getHazardDataCalcObject();
    return calc.computeSsS1(geographicRegion, dataEdition, lat, lon,
                            selectedSpectraType);
  }

  /**
   *
   * @param geographicRegion String
   * @param dataEdition String
   * @param lat double
   * @param lon double
   * @param selectedSpectraType String
   * @return DiscretizedFuncList
   */
  public DiscretizedFuncList getSA(String geographicRegion,
                                   String dataEdition, double lat,
                                   double lon, String selectedSpectraType) throws
      RemoteException {

    HazardDataCalcAPI calc = getHazardDataCalcObject();
    return calc.computeSA(geographicRegion, dataEdition, lat, lon,
                          selectedSpectraType);
  }

  /**
   * Gets the Ss and S1 when location is provided using the zipCode
   * @param geographicRegion String
   * @param dataEdition String
   * @param zipCode String
   * @return DiscretizedFuncList
   * @throws ZipCodeErrorException
   */
  public DiscretizedFuncList getSA(String geographicRegion,
                                   String dataEdition, String zipCode,
                                   String spectraType) throws
      ZipCodeErrorException, RemoteException {

    HazardDataCalcAPI calc = getHazardDataCalcObject();
    return calc.computeSA(geographicRegion, dataEdition, zipCode, spectraType);
  }

  /**
   * Gets the Ss and S1 when location is provided using the zipCode
   * @param geographicRegion String
   * @param dataEdition String
   * @param zipCode String
   * @return DiscretizedFuncList
   * @throws ZipCodeErrorException
   */
  public ArbitrarilyDiscretizedFunc getSsS1(String geographicRegion,
                                            String dataEdition, String zipCode,
                                            String spectraType) throws
      ZipCodeErrorException, RemoteException {

    HazardDataCalcAPI calc = getHazardDataCalcObject();
    return calc.computeSsS1(geographicRegion, dataEdition, zipCode, spectraType);
  }

  /**
   * Gets the Ss and S1 when location is provided using the zipCode
   * @param geographicRegion String
   * @param dataEdition String
   * @param zipCode String
   * @return DiscretizedFuncList
   * @throws ZipCodeErrorException
   */
  public ArbitrarilyDiscretizedFunc getSsS1(String geographicRegion,
                                            String dataEdition, String zipCode) throws
      ZipCodeErrorException, RemoteException {

    HazardDataCalcAPI calc = getHazardDataCalcObject();
    return calc.computeSsS1(geographicRegion, dataEdition, zipCode);
  }

  /**
   * Gets the Ss and S1 when geographic region provided is  a territory.
   * @param geographicRegion String
   * @return ArbitrarilyDiscretizedFunc
   */
  public ArbitrarilyDiscretizedFunc getSsS1(String geographicRegion) throws
      RemoteException {

    HazardDataCalcAPI calc = getHazardDataCalcObject();
    return calc.computeSsS1(geographicRegion);
  }

  /**
   *
   * @param func ArbitrarilyDiscretizedFunc
   * @param fa double
   * @param fv double
   * @return ArbitrarilyDiscretizedFunc
   */
  public ArbitrarilyDiscretizedFunc getSDSsS1(ArbitrarilyDiscretizedFunc func,
                                              float fa, float fv,
                                              String siteClass) throws
      RemoteException {
    HazardDataCalcAPI calc = getHazardDataCalcObject();
    return calc.computeSDSsS1(func, fa, fv, siteClass);
  }
  
  public ArbitrarilyDiscretizedFunc getSDSsS1(String edition, String region,
		  String zipCode, String siteClass) throws
		  RemoteException {
	  HazardDataCalcAPI calc = getHazardDataCalcObject();
	  return calc.computeSMSsS1(edition, region, zipCode, siteClass);
  }
  
  /**
   *
   * @param func ArbitrarilyDiscretizedFunc
   * @param fa double
   * @param fv double
   * @return ArbitrarilyDiscretizedFunc
   */
  public ArbitrarilyDiscretizedFunc getSMSsS1(ArbitrarilyDiscretizedFunc func,
                                              float fa, float fv,
                                              String siteClass) throws
      RemoteException {
    HazardDataCalcAPI calc = getHazardDataCalcObject();
    return calc.computeSMSsS1(func, fa, fv, siteClass);
  }

  public ArbitrarilyDiscretizedFunc getSMSsS1(String edition, String region,
		  String zipCode, String siteClass) throws
		  RemoteException {
	  HazardDataCalcAPI calc = getHazardDataCalcObject();
	  return calc.computeSMSsS1(edition, region, zipCode, siteClass);
  }
  /**
   *
   * @param func ArbitrarilyDiscretizedFunc
   * @param fa double
   * @param fv double
   * @return DiscretizedFuncList
   */
  public DiscretizedFuncList getSMSpectrum(ArbitrarilyDiscretizedFunc func,
                                           float fa, float fv, String siteClass, String edition) throws
      RemoteException {
    HazardDataCalcAPI calc = getHazardDataCalcObject();
    return calc.computeSMSpectrum(func, fa, fv, siteClass, edition);
  }

  /**
   *
   * @param func ArbitrarilyDiscretizedFunc
   * @param fa double
   * @param fv double
   * @return DiscretizedFuncList
   */
  public DiscretizedFuncList getSDSpectrum(ArbitrarilyDiscretizedFunc func,
                                           float fa, float fv, String siteClass, String edition) throws
      RemoteException {
    HazardDataCalcAPI calc = getHazardDataCalcObject();
    return calc.computeSDSpectrum(func, fa, fv, siteClass, edition);
  }

  /**
   *
   * @param func ArbitrarilyDiscretizedFunc
   * @return DiscretizedFuncList
   */
  public DiscretizedFuncList getMapSpectrum(ArbitrarilyDiscretizedFunc func) throws
      RemoteException {
    HazardDataCalcAPI calc = getHazardDataCalcObject();
    return calc.computeMapSpectrum(func);
  }

  /**
   *
   * @param func ArbitrarilyDiscretizedFunc
   * @param fa double
   * @param fv double
   * @return DiscretizedFuncList
   */
  public DiscretizedFuncList getSM_UHSpectrum(ArbitrarilyDiscretizedFunc func,
                                              float fa, float fv,
                                              String siteClass) throws
      RemoteException {
    HazardDataCalcAPI calc = getHazardDataCalcObject();
    return calc.computeSM_UHSpectrum(func, fa, fv, siteClass);
  }

  /**
   *
   * @param func ArbitrarilyDiscretizedFunc
   * @param fa double
   * @param fv double
   * @return DiscretizedFuncList
   */
  public DiscretizedFuncList getSD_UHSpectrum(ArbitrarilyDiscretizedFunc func,
                                              float fa, float fv,
                                              String siteClass) throws
      RemoteException {
    HazardDataCalcAPI calc = getHazardDataCalcObject();
    return calc.computeSD_UHSpectrum(func, fa, fv, siteClass);
  }

  /**
   *
   * @param func ArbitrarilyDiscretizedFunc
   * @return DiscretizedFuncList
   */
  public DiscretizedFuncList getApprox_UHSpectrum(ArbitrarilyDiscretizedFunc
                                                  func) throws RemoteException {
    HazardDataCalcAPI calc = getHazardDataCalcObject();
    return calc.computeApproxUHSpectrum(func);
  }

}
