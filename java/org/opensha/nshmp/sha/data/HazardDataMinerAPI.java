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

import java.rmi.RemoteException;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncList;
import org.opensha.nshmp.exceptions.ZipCodeErrorException;

/**
 * <p>Title: HazardDataMinerAPI.java </p>
 * <p>Description: This interface is implemented by the classes which connect
 * to server to get calculation results from the server. One of the class
 * connects to the RMI while the other connects with the servlet.</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public interface HazardDataMinerAPI {

  /**
   *
   * @param hazardCurveFunction ArbitrarilyDiscretizedFunc
   * @param fex double Frequency of exceedance = 1/ReturnPd
   * @param expTime double
   * @return double
   */
  public double getExceedProb(double fex, double expTime) throws RemoteException ;

  /**
   *
   * @param exceedProb double
   * @param expTime double
   * @return double
   */
  public double getReturnPeriod(double exceedProb, double expTime) throws
      RemoteException ;

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
      String hazCurveType) throws RemoteException ;

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
      ZipCodeErrorException, RemoteException ;

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
                                            double lon) throws RemoteException ;

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
      RemoteException ;

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
      RemoteException;

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
      ZipCodeErrorException, RemoteException ;

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
      ZipCodeErrorException, RemoteException ;

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
      ZipCodeErrorException, RemoteException ;

  /**
   * Gets the Ss and S1 when geographic region provided is  a territory.
   * @param geographicRegion String
   * @return ArbitrarilyDiscretizedFunc
   */
  public ArbitrarilyDiscretizedFunc getSsS1(String geographicRegion) throws
      RemoteException ;

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
      RemoteException ;

  public ArbitrarilyDiscretizedFunc getSDSsS1(String edition, String region,
		  String zipCode, String siteClass) throws
		  RemoteException;
  
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
      RemoteException ;
  
  public ArbitrarilyDiscretizedFunc getSMSsS1(String edition, String region,
		  String zipCode, String siteClass) throws
		  RemoteException;

  /**
   *
   * @param func ArbitrarilyDiscretizedFunc
   * @param fa double
   * @param fv double
   * @return DiscretizedFuncList
   */
  public DiscretizedFuncList getSMSpectrum(ArbitrarilyDiscretizedFunc func,
                                           float fa, float fv, String siteClass, String edition) throws
      RemoteException ;

  /**
   *
   * @param func ArbitrarilyDiscretizedFunc
   * @param fa double
   * @param fv double
   * @return DiscretizedFuncList
   */
  public DiscretizedFuncList getSDSpectrum(ArbitrarilyDiscretizedFunc func,
                                           float fa, float fv, String siteClass, String edition) throws
      RemoteException;

  /**
   *
   * @param func ArbitrarilyDiscretizedFunc
   * @return DiscretizedFuncList
   */
  public DiscretizedFuncList getMapSpectrum(ArbitrarilyDiscretizedFunc func) throws
      RemoteException ;

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
      RemoteException ;

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
      RemoteException ;

  /**
   *
   * @param func ArbitrarilyDiscretizedFunc
   * @return DiscretizedFuncList
   */
  public DiscretizedFuncList getApprox_UHSpectrum(ArbitrarilyDiscretizedFunc
                                                  func) throws RemoteException ;



}
