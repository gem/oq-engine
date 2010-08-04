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

package org.opensha.sha.calc.remoteCalc;

import java.net.MalformedURLException;
import java.rmi.Naming;
import java.rmi.NotBoundException;
import java.rmi.RemoteException;

import org.opensha.sha.calc.disaggregation.DisaggregationCalculator;
import org.opensha.sha.calc.disaggregation.DisaggregationCalculatorAPI;

/**
 * <p>Title: RemoteDisaggregationCalcClient</p>
 * <p>Description: This class establishes the remote RMI to the server based
 * Hazard Curve Calculation.</p>
 * @author : Ned (Edward) Field, Nitin Gupta and Vipin Gupta
 * @version 1.0
 */

public class RemoteDisaggregationCalcClient {

  /**
   * Get the reference to the remote Disaggregation calc Factory
   */
  public DisaggregationCalculatorAPI getRemoteDisaggregationCalc() {
    try {
      RemoteDisaggregationCalcFactoryAPI remoteDisaggregationCalcFactory= (RemoteDisaggregationCalcFactoryAPI)
          Naming.lookup(RegisterRemoteDisaggregationCalcFactory.registrationName);
      return remoteDisaggregationCalcFactory.getRemoteDisaggregationCalculator();
    }
    catch (NotBoundException n) {
      try{
        return new DisaggregationCalculator();
      }catch(RemoteException e){
        e.printStackTrace();
      }
    }
    catch (MalformedURLException m) {
      try{
        return new DisaggregationCalculator();
      }catch(RemoteException e){
        e.printStackTrace();
      }
    }
    catch(java.rmi.UnknownHostException r){
      try{
        return new DisaggregationCalculator();
      }catch(RemoteException e){
        e.printStackTrace();
      }
    }
    catch (java.rmi.UnmarshalException u) {
      u.printStackTrace();
    }
    catch (RemoteException r) {
      r.printStackTrace();
    }
    return null;
  }

}
