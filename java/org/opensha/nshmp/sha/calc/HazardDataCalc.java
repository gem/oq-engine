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

import java.rmi.RemoteException;
import java.rmi.server.UnicastRemoteObject;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncList;
import org.opensha.nshmp.exceptions.ZipCodeErrorException;
import org.opensha.nshmp.sha.calc.api.HazardDataCalcAPI;

/**
 * <p>Title: HazardDataCalc</p>
 *
 * <p>Description: This class computes the Hazard Data.</p>
 * @author : Ned Field, Nitin Gupta and E.V.Leyendecker
 *
 * @version 1.0
 */
public class HazardDataCalc
    extends UnicastRemoteObject implements HazardDataCalcAPI {

  public HazardDataCalc() throws RemoteException { }

  /**
   *
   * @param fex double Frequency of exceedance = 1/ReturnPd
   * @param expTime double
   * @return double
   */
  public double computeExceedProb(
      double fex, double expTime) throws RemoteException {
    SingleValueHazardCurveCalculator calc = new
        SingleValueHazardCurveCalculator();
    return calc.calculateProbExceed(fex, expTime);

  }

  /**
   *
   * @param exceedProb double
   * @param expTime double
   * @return double
   */
  public double computeReturnPeriod(double exceedProb, double expTime) throws
      RemoteException {
    SingleValueHazardCurveCalculator calc = new
        SingleValueHazardCurveCalculator();
    return calc.calculateReturnPeriod(exceedProb, expTime);
  }

  /**
   *
   * @param selectedRegion String
   * @param selectedEdition String
   * @param latitude double
   * @param longitude double
   * @return ArbitrarilyDiscretizedFunc
   */
  public ArbitrarilyDiscretizedFunc computeHazardCurve(String selectedRegion,
      String selectedEdition,
      double latitude,
      double longitude, String hazCurveType) throws RemoteException {

    HazardCurveCalculator calc = new HazardCurveCalculator();
    return calc.getBasicHazardCurve(selectedRegion, selectedEdition, latitude,
                                    longitude, hazCurveType);
  }

  /**
   *
   * @param selectedRegion String
   * @param selectedEdition String
   * @param zipCode String
   * @return ArbitrarilyDiscretizedFunc
   * @throws ZipCodeErrorException
   */
  public ArbitrarilyDiscretizedFunc computeHazardCurve(String selectedRegion,
      String selectedEdition,
      String zipCode, String hazCurveType) throws ZipCodeErrorException,
      RemoteException {
    HazardCurveCalculator calc = new HazardCurveCalculator();
    return calc.getBasicHazardCurve(selectedRegion, selectedEdition, zipCode,
                                    hazCurveType);
  }

  /**
   *
   * @param selectedRegion String
   * @param selectedEdition String
   * @param latitude double
   * @param longitude double
   * @return ArbitrarilyDiscretizedFunc
   */
  public ArbitrarilyDiscretizedFunc computeSsS1(String selectedRegion,
                                                String selectedEdition,
                                                double latitude,
                                                double longitude) throws
      RemoteException {
    SsS1Calculator ssS1Calc = new SsS1Calculator();
    return ssS1Calc.getSsS1(selectedRegion, selectedEdition, latitude,
                            longitude);
  }

  /**
   *
   * @param selectedRegion String
   * @param selectedEdition String
   * @param latitude double
   * @param longitude double
   * @return ArbitrarilyDiscretizedFunc
   */
  public ArbitrarilyDiscretizedFunc computeSsS1(String selectedRegion,
                                                String selectedEdition,
                                                double latitude,
                                                double longitude,
                                                String spectraType) throws
      RemoteException {
    SsS1Calculator ssS1Calc = new SsS1Calculator();
    return ssS1Calc.getSsS1(selectedRegion, selectedEdition, latitude,
                            longitude, spectraType);
  }

  /**
   * Used for getting the SA values for the UHS
   * @param selectedRegion String
   * @param selectedEdition String
   * @param latitude double
   * @param longitude double
   * @param spectraType String
   * @return DiscretizedFuncList
   */
  public DiscretizedFuncList computeSA(String selectedRegion,
                                       String selectedEdition,
                                       double latitude,
                                       double longitude,
                                       String spectraType) throws
      RemoteException {
    UHS_SACalculator saCalc = new UHS_SACalculator();
    return saCalc.getSA(selectedRegion, selectedEdition, latitude,
                        longitude, spectraType);
  }

  /**
   * Used for getting the SA values for the UHS
   * @param selectedRegion String
   * @param selectedEdition String
   * @param zipCode The 5 character zip code of interest
   * @param spectraType String
   * @return DiscretizedFuncList
   */
  public DiscretizedFuncList computeSA(String selectedRegion,
                                       String selectedEdition,
                                       String zipCode,
                                       String spectraType) throws
      ZipCodeErrorException, RemoteException {
    UHS_SACalculator saCalc = new UHS_SACalculator();
    return saCalc.getSA(selectedRegion, selectedEdition, zipCode, spectraType);
  }

  /**
   *
   * @param selectedRegion String
   * @param selectedEdition String
   * @param zipCode String
   * @return DiscretizedFuncList
   * @throws ZipCodeErrorException
   */
  public ArbitrarilyDiscretizedFunc computeSsS1(String selectedRegion,
                                                String selectedEdition,
                                                String zipCode) throws
      ZipCodeErrorException, RemoteException {
    SsS1Calculator ssS1Calc = new SsS1Calculator();
    return ssS1Calc.getSsS1(selectedRegion, selectedEdition, zipCode);
  }

  /**
   *
   * @param selectedRegion String
   * @param selectedEdition String
   * @param zipCode String
   * @return DiscretizedFuncList
   * @throws ZipCodeErrorException
   */
  public ArbitrarilyDiscretizedFunc computeSsS1(String selectedRegion,
                                                String selectedEdition,
                                                String zipCode,
                                                String spectraType) throws
      ZipCodeErrorException, RemoteException {
    SsS1Calculator ssS1Calc = new SsS1Calculator();
    return ssS1Calc.getSsS1(selectedRegion, selectedEdition, zipCode,
                            spectraType);
  }

  /**
   *
   * @param selectedRegion String
   * @return ArbitrarilyDiscretizedFunc
   */
  public ArbitrarilyDiscretizedFunc computeSsS1(String selectedRegion) throws
      RemoteException {
    SsS1Calculator ssS1Calc = new SsS1Calculator();
    return ssS1Calc.getSsS1ForTerritory(selectedRegion);
  }

  /**
   *
   * @param function ArbitrarilyDiscretizedFunc
   * @param fa float
   * @param fv float
   * @return ArbitrarilyDiscretizedFunc
   */
  public ArbitrarilyDiscretizedFunc computeSMSsS1(ArbitrarilyDiscretizedFunc
                                                  function,
                                                  float fa, float fv,
                                                  String siteClass) throws
      RemoteException {

    SMSsS1Calculator calc = new SMSsS1Calculator();
    return calc.calculateSMSsS1(function, fa, fv, siteClass);
  }
  
  public ArbitrarilyDiscretizedFunc computeSMSsS1(String edition, String region,
		  String zipCode, String siteClass) throws 
		  RemoteException {
	  SMSsS1Calculator calc = new SMSsS1Calculator();
	  return calc.calculateSMSsS1(edition, region, zipCode, siteClass);
  }
  
  /**
   *
   * @param function ArbitrarilyDiscretizedFunc
   * @param fa float
   * @param fv float
   * @return ArbitrarilyDiscretizedFunc
   */
  public ArbitrarilyDiscretizedFunc computeSDSsS1(ArbitrarilyDiscretizedFunc
                                                  function,
                                                  float fa, float fv,
                                                  String siteClass) throws
      RemoteException {
    SDSsS1Calculator calc = new SDSsS1Calculator();
    return calc.calculateSDSsS1(function, fa, fv, siteClass);
  }

  public ArbitrarilyDiscretizedFunc computeSDSsS1(String edition, String region,
		  String zipCode, String siteClass) throws RemoteException {
	  SDSsS1Calculator calc = new SDSsS1Calculator();
	  return calc.calculateSDSsS1(edition, region, zipCode, siteClass);
  }
  /**
   *
   * @param function ArbitrarilyDiscretizedFunc
   * @return DiscretizedFuncList
   */
  public DiscretizedFuncList computeMapSpectrum(ArbitrarilyDiscretizedFunc
                                                function) throws
      RemoteException {

    SpectrumCalculator calc = new SpectrumCalculator();
    return calc.calculateMapSpectrum(function);
  }

  /**
   *
   * @param function ArbitrarilyDiscretizedFunc
   * @param fa float
   * @param fv float
   * @return DiscretizedFuncList
   */
  public DiscretizedFuncList computeSMSpectrum(ArbitrarilyDiscretizedFunc
                                               function, float fa, float fv,
                                               String siteClass, String edition) throws
      RemoteException {

    SpectrumCalculator calc = new SpectrumCalculator();
    return calc.calculateSMSpectrum(function, fa, fv, siteClass, edition);
  }

  /**
   *
   * @param function ArbitrarilyDiscretizedFunc
   * @param fa float
   * @param fv float
   * @return DiscretizedFuncList
   */
  public DiscretizedFuncList computeSDSpectrum(ArbitrarilyDiscretizedFunc
                                               function, float fa, float fv,
                                               String siteClass, String edition) throws
      RemoteException {

    SpectrumCalculator calc = new SpectrumCalculator();
    return calc.calculateSDSpectrum(function, fa, fv, siteClass, edition);
  }

  /**
   *
   * @param function ArbitrarilyDiscretizedFunc
   * @return DiscretizedFuncList
   */
  public DiscretizedFuncList computeApproxUHSpectrum(ArbitrarilyDiscretizedFunc
      function) throws RemoteException {

    UHS_SpectrumCalculator calc = new UHS_SpectrumCalculator();
    return calc.calculateApproxUHSSpectrum(function);
  }

  /**
   *
   * @param function ArbitrarilyDiscretizedFunc
   * @param fa float
   * @param fv float
   * @return DiscretizedFuncList
   */
  public DiscretizedFuncList computeSM_UHSpectrum(ArbitrarilyDiscretizedFunc
                                                  function, float fa, float fv,
                                                  String siteClass) throws
      RemoteException {

    UHS_SpectrumCalculator calc = new UHS_SpectrumCalculator();
    return calc.calculateSMS_UHSpectrum(function, fa, fv, siteClass);
  }

  /**
   *
   * @param function ArbitrarilyDiscretizedFunc
   * @param fa float
   * @param fv float
   * @return DiscretizedFuncList
   */
  public DiscretizedFuncList computeSD_UHSpectrum(ArbitrarilyDiscretizedFunc
                                                  function, float fa, float fv,
                                                  String siteClass) throws
      RemoteException {

    UHS_SpectrumCalculator calc = new UHS_SpectrumCalculator();
    return calc.calculateSD_UHSpectrum(function, fa, fv, siteClass);
  }

}

