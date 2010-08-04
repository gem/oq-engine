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

package org.opensha.sha.earthquake.rupForecastImpl.remoteERF_Clients;


import org.opensha.sha.earthquake.rupForecastImpl.remote.RegisterRemoteERF_ListFactory;
import org.opensha.sha.earthquake.rupForecastImpl.remote.RemoteERF_ListClient;


/**
 * <p>Title: PEER_LogicTreeERF_ListClient</p>
 * <p>Description: This class provides the access to the server side PEER_LogicTree
 * ERF List. It creates the objects of the PEER_NonPlanarFaultForecast on the server.</p>
 * @author : Ned Field, Nitin Gupta and Vipin Gupta
 * @created Sept 28,2004
 * @version 1.0
 */

public class PEER_LogicTreeERF_ListClient extends RemoteERF_ListClient{

  public PEER_LogicTreeERF_ListClient() throws java.rmi.RemoteException{
    String className = "org.opensha.sha.earthquake.rupForecastImpl.PEER_TestCases.PEER_LogicTreeServerBasedERF_List";
    String remoteRegistrationName = RegisterRemoteERF_ListFactory.registrationName;
    getRemoteERF_List(className,remoteRegistrationName);
  }

}
