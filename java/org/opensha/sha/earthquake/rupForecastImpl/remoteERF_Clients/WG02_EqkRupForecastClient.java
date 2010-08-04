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

import org.opensha.commons.data.TimeSpan;
import org.opensha.sha.earthquake.rupForecastImpl.remote.RegisterRemoteERF_Factory;
import org.opensha.sha.earthquake.rupForecastImpl.remote.RemoteERF_Client;

/**
 * <p>Title: WG02_EqkRupForecastClient </p>
 * <p>Description: This is a client for WG-02 Forecast. It will
 * access ERF from the remote machine </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author Nitin Gupta, Vipin Gupta
 * @version 1.0
 */

public class WG02_EqkRupForecastClient extends RemoteERF_Client {

  public final static String className = "org.opensha.sha.earthquake.rupForecastImpl.WG02.WG02_EqkRupForecast";
  private final static  String remoteRegistrationName = RegisterRemoteERF_Factory.registrationName;
  /**
   * Class default constructor
   * @throws java.rmi.RemoteException
 * @throws NotBoundException 
 * @throws MalformedURLException 
   */
  public WG02_EqkRupForecastClient() throws java.rmi.RemoteException, MalformedURLException, NotBoundException{
    getRemoteERF(className,remoteRegistrationName);
  }



  /**
   * Class constructor that takes in the arguments for the WG-02.
   * @param inputFileStrings
   * @param rupOffset
   * @param gridSpacing
   * @param deltaMag
   * @param backSeisValue
   * @param grTailValue
   * @param name
   * @param timespan
   */
  public WG02_EqkRupForecastClient(ArrayList inputFileStrings, double rupOffset, double gridSpacing,
                             double deltaMag, String backSeisValue, String grTailValue, String name,
    TimeSpan timespan) throws java.rmi.RemoteException{

    //Class array to define the types of arguments that the constructor accepts
    ArrayList paramTypes = new ArrayList();
    paramTypes.add(inputFileStrings.getClass());
    paramTypes.add(Double.TYPE);
    paramTypes.add(Double.TYPE);
    paramTypes.add(Double.TYPE);
    paramTypes.add(backSeisValue.getClass());
    paramTypes.add(grTailValue.getClass());
    paramTypes.add(name.getClass());
    paramTypes.add(timespan.getClass());

    //ArrayList to store the actual vlaue of the objects.
    ArrayList params = new ArrayList();
    params.add(inputFileStrings);
    params.add(new Double(rupOffset));
    params.add(new Double(gridSpacing));
    params.add(new Double(deltaMag));
    params.add(backSeisValue);
    params.add(grTailValue);
    params.add(name);
    params.add(timespan);

    try{
      getRemoteERF(params,paramTypes,className,remoteRegistrationName);
    }catch(Exception e){
      e.printStackTrace();
    }
  }
}
