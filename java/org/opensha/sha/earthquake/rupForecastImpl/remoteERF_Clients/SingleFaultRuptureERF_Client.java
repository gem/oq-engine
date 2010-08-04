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

import java.net.MalformedURLException;
import java.rmi.NotBoundException;
import java.util.ArrayList;

import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.earthquake.rupForecastImpl.remote.RegisterRemoteERF_Factory;
import org.opensha.sha.earthquake.rupForecastImpl.remote.RemoteERF_Client;

/**
 * <p>Title: SingleFaultRuptureERF_Client </p>
 * <p>Description: This is a client for Single Fault Rupture ERF.
 * It will access ERF from the remote machine </p>
 * @author Nitin Gupta, Vipin Gupta
 * @version 1.0
 */

public class SingleFaultRuptureERF_Client extends RemoteERF_Client{

  private final static  String className = "org.opensha.sha.earthquake.rupForecastImpl.SingleFaultRuptureERF";
  private final static  String remoteRegistrationName = RegisterRemoteERF_Factory.registrationName;

  public SingleFaultRuptureERF_Client() throws java.rmi.RemoteException, MalformedURLException, NotBoundException{

    getRemoteERF(className,remoteRegistrationName);
  }

  /**
   * Constructor for this source
   */
  public SingleFaultRuptureERF_Client(EqkRupture eqkRupture, double prob)
    throws java.rmi.RemoteException{
    //Class array to define the types of arguments that the constructor accepts
    ArrayList paramTypes = new ArrayList();
    paramTypes.add(eqkRupture.getClass());
    paramTypes.add(Double.TYPE);

    //ArrayList to store the actual vlaue of the objects.
    ArrayList params = new ArrayList();
    params.add(eqkRupture);
    params.add(new Double(prob));

    try{
      getRemoteERF(params,paramTypes,className,remoteRegistrationName);
    }catch(Exception e){
      e.printStackTrace();
    }
  }

}
