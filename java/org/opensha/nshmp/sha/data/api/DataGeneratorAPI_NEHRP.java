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

package org.opensha.nshmp.sha.data.api;

import java.rmi.RemoteException;
import java.util.ArrayList;

import org.opensha.commons.geo.Location;
import org.opensha.nshmp.exceptions.ZipCodeErrorException;

/**
 * <p>Title: DataGeneratorAPI_NEHRP</p>
 *
 * <p>Description: this interface provides the minimum functionality that a
 * DataGenerator classes must provide. </p>
 * @author : Ned Field, Nitin Gupta and E.V.Leyendecker
 * @version 1.0
 */
public interface DataGeneratorAPI_NEHRP {

  /**
   * Removes all the calculated data.
   */
  public void clearData();

  /**
   * Clears the lat/lon/zip values
	*/
  public void setNoLocation();

  /**
   * Returns the Data and all the metadata associated with it in a String.
   * @return String
   */
  public String getDataInfo();

  /**
   * Gets the data for SsS1 in case Territory.
   * Territory is when user is not allowed to enter any zip code or Lat-Lon
   * for the location or if it is GAUM and TAUTILLA.
   */
  public void calculateSsS1() throws RemoteException;

  /**
   * Gets the data for SsS1 in case region specified is not a Territory and user
   * specifies Lat-Lon for the location.
   */
  public void calculateSsS1(double lat, double lon) throws RemoteException;

  /**
   * Gets the data for SsS1 in case region specified is not a Territory and user
   * specifies zip code for the location.
   */
  public void calculateSsS1(String zipCode) throws ZipCodeErrorException,
      RemoteException;

  /**
   * Gets the data for SsS1 for each location in the list of <code>locations</code>.
   * If any given location is not valid for the current region, an error message is
   * displayed and the output displays "Out of Region" information.  Output is
   * directed to the specified <code>outFile</code> Excel file.
   * @param locations A list of locations to calculate SsS1 at.
   * @param outFile The Excel file to output the information.
   */
  public void calculateSsS1(ArrayList<Location> locations, String outFile);
  
  /**
   * Sets the selected site class
   * @param siteClass String
   */
  public void setSiteClass(String siteClass);

  /**
   * Returns the site class
   * @return String
   */
  public String getSelectedSiteClass();

  /**
   * Returns the list of functions for plotting.
   * @param isMapSpectrumFunctionNeeded boolean true if user has clicked the map spectrum button
   * @param isSDSpectrumFunctionNeeded boolean true if user has clicked the SD spectrum button
   * @param isSMSpectrumFunctionNeeded boolean true if user has clicked the SM spectrum button
   * @return ArrayList
   */
  public ArrayList getFunctionsToPlotForSA(boolean
                                           isMapSpectrumFunctionNeeded,
                                           boolean isSDSpectrumFunctionNeeded,
                                           boolean isSMSpectrumFunctionNeeded);

  /**
   * Returns the SA at .2sec
   * @return double
   */
  public double getSs();

  /**
   * Returns the SA at 1 sec
   * @return double
   */
  public double getSa();

  /**
   *
   */
  public void calculateSMSsS1() throws RemoteException;
  
  /**
   * 
   * @param edition
   * @param region
   * @param zipCode
   * @param siteClass
   * @throws RemoteException
   */
  public void calculateSMSsS1(String edition, String region,
		  String zipCode, String siteClass) throws RemoteException;

  /**
   *
   */
  public void calculatedSDSsS1() throws RemoteException;

  /**
   * 
   * @param edition
   * @param region
   * @param zipCode
   * @param siteClass
   * @throws RemoteException
   */
  public void calculateSDSsS1(String edition, String region,
		  String zipCode, String siteClass) throws RemoteException;
  
  /**
   * 
   * @param locations
   * @param conditions
   * @param outfile
   */
  public void calculateSMsSm1SDsSD1(ArrayList<Location> locations, 
  		ArrayList<String> conditions, String outfile);
  
  /**
   *
   */
  public void calculateMapSpectrum() throws RemoteException;

  /**
   *
   */
  public void calculateSMSpectrum() throws RemoteException;

  /**
   *
   */
  public void calculateSDSpectrum() throws RemoteException;

  /**
   * Sets the selected geographic region.
   * @param region String
   */
  public void setRegion(String region);

  /**
   * Sets the selected data edition.
   * @param edition String
   */
  public void setEdition(String edition);

  /**
   * Sets the Fa value.
   * @param fa double
   */
  public void setFa(float fa);

  /**
   * Sets the Fv value.
   * @param fv double
   */
  public void setFv(float fv);

  /**
   * Sets the Spectra type
   * @param spectraType String
   */
  public void setSpectraType(String spectraType);

  /**
   * Computes the Map Spectrum(s) for the batch file.
   * @param locations
   * @param outfile
   */
  public void calculateMapSpectrum(ArrayList<Location> locations, String outfile);
  
  /**
   * Computes the SM Spectrum(s) for the batch file.
   * @param locations
   * @param conditions
   * @param outfile
   */
  public void calculateSMSpectrum(ArrayList<Location> locations,
		ArrayList<String> conditions, String outfile);

  /**
   * Computes the SD Spectrum(s) for the batch file.
   * @param locations
   * @param conditions
   * @param outfile
   */
  public void calculateSDSpectrum(ArrayList<Location> locations,
		ArrayList<String> conditions, String outfile);


}
