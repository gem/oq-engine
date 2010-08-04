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

import java.io.IOException;
import java.rmi.RemoteException;
import java.rmi.server.UnicastRemoteObject;
import java.util.ArrayList;
import java.util.ListIterator;

import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.Region;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.sha.earthquake.ERF_EpistemicList;

/**
 * <p>Title: RemoteERF_ListImpl</p>
 * <p>Description: This class provides the handle to remotely existing ERF List.</p>
 * @author : Ned Field, Nitin Gupta and Vipin Gupta
 * @created Aug 05,2004
 * @version 1.0
 */

public class RemoteERF_ListImpl
    extends UnicastRemoteObject implements
    RemoteERF_ListAPI{

  private ERF_EpistemicList erfList = null;
  private static final boolean D = false;
  private ArrayList listenerList = new ArrayList();

  /**
   * creates the EqkRupForecast object based on received className
   *
   * @param className
   * @throws java.rmi.RemoteException
   * @throws IOException
   */
  public RemoteERF_ListImpl(String className) throws java.rmi.RemoteException,
      IOException {
    erfList = (ERF_EpistemicList) org.opensha.commons.util.ClassUtils.
        createNoArgConstructorClassInstance(className);
   }

  /**
   * get the number of Eqk Rup Forecasts in this list
   * @return : number of eqk rup forecasts in this list
   */
  public int getNumERFs() {
    return erfList.getNumERFs();
  }


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
  public boolean setParameter(String name, Object value) throws
      RemoteException {
    return erfList.setParameter(name, value);
  }

  /**
   * get the ERF in the list with the specified index
   * @param index : index of Eqk rup forecast to return
   * @return
   */
  public RemoteEqkRupForecastAPI getRemoteERF(int index) {
    return erfList.getRemoteERF(index);
  }

  /**
   * get the weight of the ERF at the specified index
   * @param index : index of ERF
   * @return : relative weight of ERF
   */
  public double getERF_RelativeWeight(int index) {
    return erfList.getERF_RelativeWeight(index);
  }

  /**
   * Return the vector containing the Double values with
   * relative weights for each ERF
   * @return : ArrayList of Double values
   */
  public ArrayList getRelativeWeightsList() {
    return erfList.getRelativeWeightsList();
  }

  /**
   * return the list of adjustable params
   * @return
   */
  public ListIterator getAdjustableParamsIterator() {
    return erfList.getAdjustableParamsIterator();
  }

  /**
   * get the name of this class
   * @return
   */
  public String getName() {
    return erfList.getName();
  }

  /**
   * Checks whether this location lies wothin the applicable region of this ERF list
   * @param loc : Location to check
   */
  public boolean isLocWithinApplicableRegion(Location loc) {
    return true;
  }

  /* (non-Javadoc)
   * @see org.opensha.sha.earthquake.rupForecastImpl.Frankel02.ERFFrankel02Server#updateForecast()
   */
  public void updateForecast() throws
      RemoteException {
    erfList.updateForecast();
  }

  /**
   * Get the region for which this forecast is applicable
   * @return : Geographic region object specifying the applicable region of forecast
   */
  public Region getApplicableRegion() {
    return erfList.getApplicableRegion();
  }

  /**
   * This method sets the time-span field.
   * @param time
   */
  public void setTimeSpan(TimeSpan time) {
    erfList.setTimeSpan(time);
  }

  /**
   *
   * @returns the adjustable ParameterList for the ERF
   */
  public ParameterList getAdjustableParameterList() {
    return erfList.getAdjustableParameterList();
  }

  /**
   * get the timespan
   *
   * @return : TimeSpan
   */
  public TimeSpan getTimeSpan() {
    return erfList.getTimeSpan();
  }

  /**
   * sets the value for the parameter change flag
   * @param flag
   */
  public void setParameterChangeFlag(boolean flag) {
    erfList.setParameterChangeFlag(flag);
  }

  /**
   *
   * @param paramName
   * @returns the Parameter from the parameter list with param name.
   */
  public ParameterAPI getParameter(String paramName) throws RemoteException {
    // TODO Auto-generated method stub
    return erfList.getParameter(paramName);
  }


  /**
   * Update the forecast and save it in serialized mode into a file
   * @return
   */
  public String saveForecast() throws
      RemoteException {
    String urlPrefix = "http://gravity.usc.edu/";
    String parentDir = "/opt/install/apache-tomcat-5.5.20/webapps/";
    String subDir = "OpenSHA/HazardMapDatasets/savedERFs/";
    String fileName = System.currentTimeMillis() + ".javaobject";
    try {
		org.opensha.commons.util.FileUtils.saveObjectInFile(parentDir + subDir + fileName,
		                                            erfList);
	} catch (IOException e) {
		// TODO Auto-generated catch block
		e.printStackTrace();
	}
    return parentDir + subDir + fileName;
  }

}
