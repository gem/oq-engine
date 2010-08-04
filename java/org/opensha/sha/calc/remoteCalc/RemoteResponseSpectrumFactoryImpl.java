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

import java.rmi.server.UnicastRemoteObject;

import org.opensha.sha.calc.SpectrumCalculator;
import org.opensha.sha.calc.SpectrumCalculatorAPI;

/**
 * <p>Title: RemoteResponseSpectrumFactoryImpl</p>
 * <p>Description: This class returns the instance of the server based Spectrum Calculator
 * to the application. This is the RMI based interface, so when a server based
 * instance is returned to the application it calls the methods of the calculator
 * in the same manner as it would call the Spectrum Calulator on its own machine.</p>
 * @author : Ned (Edward) Field , Nitin Gupta and Vipin Gupta
 * @version 1.0
 */

public class RemoteResponseSpectrumFactoryImpl extends UnicastRemoteObject
    implements RemoteResponseSpectrumFactoryAPI{

  public RemoteResponseSpectrumFactoryImpl() throws java.rmi.RemoteException {
  }

  /**
   * Get the reference to the instance of the HazardCurveCalculator
   * @return
   * @throws java.rmi.RemoteException
   */
  public SpectrumCalculatorAPI getRemoteResponseSpectrumCalculator() throws java.rmi.RemoteException{
    try{
      SpectrumCalculatorAPI spectrum = new SpectrumCalculator();
      return spectrum;
    }catch(Exception e){
      e.printStackTrace();
    }
    return null;
  }
}
