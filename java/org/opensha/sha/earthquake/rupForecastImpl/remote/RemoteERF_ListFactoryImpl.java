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

/**
 * <p>Title: RemoteERF_ListFactoryImpl </p>
 * <p>Description: This class generates a new ERF List remote object and passes its
 * reference back to the calling client. </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author Nitin Gupta, Vipin Gupta
 * @version 1.0
 */

public class RemoteERF_ListFactoryImpl extends UnicastRemoteObject
    implements RemoteERF_ListFactoryAPI {


  public RemoteERF_ListFactoryImpl() throws java.rmi.RemoteException  { }

  /**
   * Return the Remote ERF List reference back to the calling client
   * @return Remote ERF List
   * @throws java.rmi.RemoteException
   */
  public RemoteERF_ListAPI getRemoteERF_List(String className) throws java.rmi.RemoteException {
    try {
       RemoteERF_ListAPI erfServer = new RemoteERF_ListImpl(className);
       return erfServer;
    }catch(Exception e) { e.printStackTrace();}
    return null;
  }
}
