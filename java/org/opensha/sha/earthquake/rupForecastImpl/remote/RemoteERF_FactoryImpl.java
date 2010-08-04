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

import java.rmi.server.UnicastRemoteObject;
import java.util.ArrayList;


/**
 * <p>Title: RemoteERF_FactoryImpl.java </p>
 * <p>Description: This class generates a new ERF remote object and passes its
 * reference back to the calling client </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author Nitin Gupta, Vipin Gupta
 * @version 1.0
 */

public class RemoteERF_FactoryImpl extends UnicastRemoteObject
    implements RemoteERF_FactoryAPI {


  public RemoteERF_FactoryImpl() throws java.rmi.RemoteException  { }

  /**
   * Retun the Remote ERF reference back to the calling client
   * @return Remote ERF
   * @throws java.rmi.RemoteException
   */
  public RemoteEqkRupForecastAPI getRemoteERF(String className) throws java.rmi.RemoteException {
    try {
       RemoteEqkRupForecastAPI erfServer = new RemoteEqkRupForecast_Impl(className);
       return erfServer;
    }catch(Exception e) { e.printStackTrace();}
    return null;
  }


  /**
   * Retun the Remote ERF reference back to the calling client.
   * @param params : Passes the arguments for creating the class constructor.
   * @param className: class name of the ERF
   * @return
   * @throws java.rmi.RemoteException
   */
  public RemoteEqkRupForecastAPI getRemoteERF(ArrayList params,ArrayList paramTypes,String className) throws java.rmi.RemoteException {
    try {
      RemoteEqkRupForecastAPI erfServer = new RemoteEqkRupForecast_Impl(params,paramTypes,className);
      return erfServer;
      }catch(Exception e) { e.printStackTrace();}
      return null;
  }
}


