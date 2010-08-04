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

/**
 * <p>Title: GriddedHypoMagFreqDistAtLocAPI </p>
 *
 * <p>Description: This API constitutes an interface to a number of
 * HypoMagFreqDistAtLoc objects (e.g., for multiple locations, although each
 * location is not necessarily unique).</p>
 *
 * Note : Additiional info needs to be added like binning of Lat, Lon and Depth).
 * @author Nitin Gupta, Vipin Gupta and Edward (Ned) Field
 *
 * @version 1.0
 */
public interface HypoMagFreqDistAtMultLocsAPI {




  /**
   * This gets the HypoMagFreqDistAtLoc for the ith location.
   * @param ithLocation int : Index of the location in the region
   * @return HypoMagFreqDistAtLoc Object.
   *
   * Note : This always gives out yearly Rate.
   */
  public HypoMagFreqDistAtLoc getHypoMagFreqDistAtLoc(int ithLocation);

  public int getNumHypoLocs();

}
