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

package org.opensha.sha.earthquake.griddedForecast;

import org.opensha.commons.geo.GriddedRegion;
import org.opensha.sha.earthquake.observedEarthquake.ObsEqkRupList;
import org.opensha.sha.earthquake.observedEarthquake.ObsEqkRupture;


/**
 * <p>Title: AfterShockHypoMagFreqDistForecast</p>
 *
 * <p>Description: This class represents a poissonian aftershock hypocenter
 * forecast.
 *
 * The indexing over HypMagFreqDistAtLoc objects is exactly the same as the
 * EvenlyGriddedGeographicRegionAPI afterShockZone.</p>
 *
 * @author Nitin Gupta, Vipin Gupta and Edward (Ned) Field
 * @version 1.0
 */
public abstract class AfterShockHypoMagFreqDistForecast
    extends GriddedHypoMagFreqDistForecast {


  protected ObsEqkRupture mainShock;
  protected ObsEqkRupList afterShocks;

  /**
   * Class no-arg constructor
   */
  public AfterShockHypoMagFreqDistForecast() {
  }


  /**
   * Gets the Aftershock list for the forecast model.
   * @return ObsEqkRupList
   */
  public ObsEqkRupList getAfterShocks() {
    return afterShocks;
  }

  /**
   * Allows the user to set the AfterShockZone as EvelyGriddedGeographicRegion.
   * @return EvenlyGriddedGeographicRegionAPI AfterShockZone.
   */
  public GriddedRegion getAfterShockZone() {
    return getRegion();
  }

  /**
   * Returns the main shock
   * @return ObsEqkRupture
   */
  public ObsEqkRupture getMainShock() {
    return mainShock;
  }

  /**
   * Sets the list of ObsEqkRuptures for the given AfterShockHypoMagFreqDistForecast.
   * @param afterShocks ObsEqkRupList
   */
  public void setAfterShocks(ObsEqkRupList aftershockList) {
	//SortAftershocks_Calc afterShockCalc = new   SortAftershocks_Calc();
    //afterShocks = afterShockCalc.selectAfterShocksToNewMainshock_Calc();
	  afterShocks = aftershockList;
  }

  /**
   * addToAftershockList
   */
  public void addToAftershockList(ObsEqkRupture newAftershock) {
    afterShocks.addObsEqkEvent(newAftershock);
  }



  /**
   * Sets the mainshock event for the given forecast model.
   * @param mainShock ObsEqkRupture
   */
  public void setMainShock(ObsEqkRupture mainShock) {
    this.mainShock = mainShock;
  }
}
