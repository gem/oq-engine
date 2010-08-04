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


import org.opensha.sha.earthquake.EqkRupForecastAPI;
/**
 * <p>Title: GriddedHypoMagFreqDistForecastWrappedERF</p>
 *
 * <p>Description: This class wraps any Earthquake Rupture Forecast into a
 * GriddedHypoMagFreqDistForecast.</p>
 *
 * @author Nitin Gupta
 * @since Sept 16, 2005
 * @version 1.0
 */
public class GriddedHypoMagFreqDistForecastWrappedERF
    extends GriddedHypoMagFreqDistForecast {

  //ERF Object
  private EqkRupForecastAPI eqkRupForecast;

  /**
   * Class constructor that accepts the EqkRupForecast as the argument.
   * @param eqkRupforecast EqkRupForecastAPI
   */
  public GriddedHypoMagFreqDistForecastWrappedERF(EqkRupForecastAPI eqkRupForecast) {
    this.eqkRupForecast = eqkRupForecast;
  }

  /**
   * If any parameter has been changed then update the forecast.
   */
  public void updateForecast() {
    if (parameterChangeFlag) {
      eqkRupForecast.updateForecast();
    }
  }

  /**
   * gets the Hypocenter Mag.
   *
   * @param ithLocation int : Index of the location in the region
   * @return HypoMagFreqDistAtLoc Object using which user can retrieve the
   *   Magnitude Frequency Distribution.
   * @todo Implement this
   *   org.opensha.sha.earthquake.GriddedHypoMagFreqDistAtLocAPI method
   */
  public HypoMagFreqDistAtLoc getHypoMagFreqDistAtLoc(int ithLocation) {
    return null;
  }




}
