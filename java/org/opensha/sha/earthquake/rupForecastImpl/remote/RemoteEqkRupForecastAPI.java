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

import java.rmi.RemoteException;
import java.util.ArrayList;

import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;



/**
 *
 * <p>Title: RemoteEqkRupForecastAPI</p>
 * <p>Description: This class provides the interface to the Remotely existing
 * ERF's.</p>
 * @author : Nitin Gupta and Vipin Gupta
 * @version 1.0
 */
public interface RemoteEqkRupForecastAPI extends RemoteERF_API {


  /**
   *
   * @returns the total number os sources
   */
  public int getNumSources() throws RemoteException;

  /**
   *
   * @returns the sourceList
   */
  public ArrayList getSourceList() throws RemoteException;

  /**
   * Return the earhthquake source at index i.   Note that this returns a
   * pointer to the source held internally, so that if any parameters
   * are changed, and this method is called again, the source obtained
   * by any previous call to this method will no longer be valid.
   *
   * @param iSource : index of the desired source (only "0" allowed here).
   *
   * @return Returns the ProbEqkSource at index i
   *
   */
  public ProbEqkSource getSource(int iSource) throws RemoteException;



  /**
   * Return the earthquake source at index i. This methos DOES NOT return the
   * reference to the class variable. So, when you call this method again,
   * result from previous method call is still valid. This behavior is in contrast
   * with the behavior of method getSource(int i)
   *
   * @param iSource : index of the source needed
   *
   * @return Returns the ProbEqkSource at index i
   *
   * FIX:FIX :: This function has not been implemented yet. Have to give a thought on that
   *
   */
  public ProbEqkSource getSourceClone(int iSource) throws RemoteException;




  /**
   *
   * @param iSource
   * @returns the number of ruptures for the ithSource
   */
  public int getNumRuptures(int iSource) throws RemoteException;



  /**
   *
   * @param iSource
   * @param nRupture
   * @returns the ProbEqkRupture object for the ithSource and nth rupture
   */
  public ProbEqkRupture getRupture(int iSource,int nRupture) throws RemoteException;

  /**
   * Get the ith rupture of the source. this method DOES NOT return reference
   * to the object. So, when you call this method again, result from previous
   * method call is valid. This behavior is in contrast with
   * getRupture(int source, int i) method
   *
   * @param source
   * @param i
   * @return
   */
  public ProbEqkRupture getRuptureClone(int iSource, int nRupture) throws RemoteException;


}
