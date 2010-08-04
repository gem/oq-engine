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

package org.opensha.sha.earthquake.rupForecastImpl.remote;


import java.rmi.Remote;
import java.rmi.RemoteException;

import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.Region;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterList;

/**
 * <p>Title: RemoteERF_API</p>
 * <p>Description: This defines the interface for the Remote ERF_LIST and
 * Remote EqkRupForecast classes. Both Remote ERF_List and Remote EqkRupForcast
 * classes implements this interface.It is the parent interface that both Remote
 * ERF_List and Remote EqkRupForecast have to implement.
 * This interface is needed so that common functions for both list and single forecast
 * can go in this interface. In the application one does not have care if it is a list
 * or single ERF because it will call the respective methods of the classes automatically
 * based on who soever object was created</p>
 * @author : Nitin Gupta
 * @created Sept 30, 2004
 * @version 1.0
 */

public interface RemoteERF_API  extends Remote{


  /**
   * This method updates the forecast according to the currently specified
   * parameters.  Call this once before looping over the getRupture() or
   * getSource() methods to ensure a fresh forecast.  This approach was chosen
   * over checking whether parameters have changed during each getRupture() etc.
   * method call because a user might inadvertently change a parameter value in
   * the middle of the loop.  This approach is also faster.
   * @return
   */
   public void updateForecast() throws RemoteException ;

   /**
    * Loops over all the adjustable parameters and set parameter with the given
    * name to the given value.
    * First checks if the parameter is contained within the ERF adjustable parameter
    * list or TimeSpan adjustable parameters list. If not then return false.
    * @param name String Name of the Adjustable Parameter
    * @param value Object Parameeter Value
    * @return boolean boolean to see if it was successful in setting the parameter
    * value.
    */
   public boolean setParameter(String name, Object value) throws RemoteException;


   /**
    * save the forecast in a file
    * @throws RemoteException
    */
   public String saveForecast() throws RemoteException ;

  /**
   * Return the name for this class
   *
   * @return : return the name for this class
   */
   public String getName() throws RemoteException;

   /**
    * This method sets the time-span field
    * @param time
    */
   public void setTimeSpan(TimeSpan time) throws RemoteException;


   /**
    * This method gets the time-span field
    */
   public TimeSpan getTimeSpan() throws RemoteException;


   /**
    * This function finds whether a particular location lies in applicable
    * region of the forecast
    *
    * @param loc : location
    * @return: True if this location is within forecast's applicable region, else false
    */
   public boolean isLocWithinApplicableRegion(Location loc) throws RemoteException;


   /**
    * Get the region for which this forecast is applicable
    * @return : Geographic region object specifying the applicable region of forecast
    */
   public Region getApplicableRegion() throws RemoteException;

   /**
    * Gets the Adjustable parameter list for the ERF
    * @return
    */
   public ParameterList getAdjustableParameterList() throws RemoteException;

   /**
    *
    * @param paramName
    * @returns the Parameter from the parameter list with param name.
    */
   public ParameterAPI getParameter(String paramName) throws RemoteException;


}
