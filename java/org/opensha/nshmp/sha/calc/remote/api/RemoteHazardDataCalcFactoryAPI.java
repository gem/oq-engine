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

package org.opensha.nshmp.sha.calc.remote.api;

import java.rmi.Remote;

import org.opensha.nshmp.sha.calc.api.HazardDataCalcAPI;

/**
 * <p>Title: RemoteHazardDataCalcFactoryAPI</p>
 *
 * <p>Description: This class gets the new instance of the
 * Remote Hazard Data Calc to the user.</p>
 *
 * @author Ned Field, Nitin Gupta , E.V.Leyendecker
 * @version 1.0
 */
public interface RemoteHazardDataCalcFactoryAPI
    extends Remote {

  /**
   * Get the reference to the instance of the HazardDataCalc
   * @return
   * @throws java.rmi.RemoteException
   */
  public HazardDataCalcAPI getRemoteHazardDataCalc() throws java.rmi.
      RemoteException;

}
