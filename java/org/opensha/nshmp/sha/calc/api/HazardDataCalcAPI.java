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

package org.opensha.nshmp.sha.calc.api;

import java.rmi.Remote;
import java.rmi.RemoteException;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncList;
import org.opensha.nshmp.exceptions.ZipCodeErrorException;

/**
 * <p>Title: HazardDataCalcAPI</p>
 *
 * <p>Description: This interface defines functions that HazardDataCalc muct provide
 * for Hazard Data calculations.
 * It extends Remote as any class implementing this interface can provide a server
 * implemenation of all the functionality.</p>
 * @author Ned Field, Nitin Gupta and Vipin Gupta
 *
 * @version 1.0
 */
public interface HazardDataCalcAPI
    extends Remote {

  /**
   *
   * @param hazardCurveFunction ArbitrarilyDiscretizedFunc
   * @param fex double Frequency of exceedance = 1/ReturnPd
   * @param expTime double
   * @return double
   */
  public double computeExceedProb(double fex, double expTime) throws
      RemoteException;

  /**
   *
   * @param exceedProb double
   * @param expTime double
   * @return double
   */
  public double computeReturnPeriod(double exceedProb, double expTime) throws
      RemoteException;

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
      double longitude, String hazCurveType) throws RemoteException;

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
      RemoteException;

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
      RemoteException;

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
      RemoteException;

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
      RemoteException;

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
                                       String zipCode,
                                       String spectraType) throws
      ZipCodeErrorException, RemoteException;

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
      ZipCodeErrorException, RemoteException;

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
      ZipCodeErrorException, RemoteException;

  /**
   *
   * @param selectedRegion String
   * @return ArbitrarilyDiscretizedFunc
   */
  public ArbitrarilyDiscretizedFunc computeSsS1(String selectedRegion) throws
      RemoteException;

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
      RemoteException;

  public ArbitrarilyDiscretizedFunc computeSMSsS1(String edition, String region,
		  String zipCode, String siteClass) throws RemoteException;
  
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
      RemoteException;
  
  /**
   * 
   * @param edition
   * @param region
   * @param zipCode
   * @param siteClass
   * @return
   * @throws RemoteException
   */
  public ArbitrarilyDiscretizedFunc computeSDSsS1(String edition, String region,
		  String zipCode, String siteClass) throws RemoteException;

  /**
   *
   * @param function ArbitrarilyDiscretizedFunc
   * @param fa float
   * @param fv float
   * @return DiscretizedFuncList
   */
  public DiscretizedFuncList computeMapSpectrum(ArbitrarilyDiscretizedFunc
                                                function) throws
      RemoteException;

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
      RemoteException;

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
      RemoteException;

  /**
   *
   * @param function ArbitrarilyDiscretizedFunc
   * @return DiscretizedFuncList
   */
  public DiscretizedFuncList computeApproxUHSpectrum(ArbitrarilyDiscretizedFunc
      function) throws RemoteException;

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
      RemoteException;

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
      RemoteException;

}
