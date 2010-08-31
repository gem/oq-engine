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

import org.opensha.commons.geo.Location;
import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.magdist.IncrementalMagFreqDist;

/**
 * <p>Title: HypoMagFreqDistAtLoc</p>
 *
 * <p>Description: This allows user to store a set of MagFreqDists and associate focal mechanims for a given
 * location.</p>
 *
 * @author Nitin Gupta
 * @version 1.0
 */
public class HypoMagFreqDistAtLoc extends MagFreqDistsForFocalMechs implements java.io.Serializable{

  private Location location;

  /**
   * Class Constructor.
   * In this case the no focalMechanisms are specified.
   * @param magDist IncrementalMagFreqDist[] list of MagFreqDist for the given location.
   * @param loc Location
   */
  public HypoMagFreqDistAtLoc(IncrementalMagFreqDist[] magDist, Location loc) {
	  super(magDist);
	  location = loc;
  }
  
  
  /**
   * Class Constructor.
   * This is for passing in a single magFreqDist (don't have to create an array) and no focal mechanism.
   * @param magDist IncrementalMagFreqDist MagFreqDist for the given location.
   * @param loc Location
   */
  public HypoMagFreqDistAtLoc(IncrementalMagFreqDist magDist, Location loc) {
	  super(magDist);
	  location = loc;
  }

  /**
   * Class constructor.
   * This constructor allows user to give a list of focalMechanisms for a given location.
   * @param magDist IncrementalMagFreqDist[] list of magFreqDist, same as number of focal mechanisms.
   * @param loc Location Location
   * @param focalMechanism FocalMechanism[] list of focal mechanism for a given location.
   *
   */
  public HypoMagFreqDistAtLoc(IncrementalMagFreqDist[] magDist, Location loc,
                              FocalMechanism[] focalMechanism) {
	  super(magDist, focalMechanism);
	  location = loc;
  }

  /**
   * Class constructor.
   * This constructor allows user to give a single magDist and focalMechanism for a given location.
   * @param magDist IncrementalMagFreqDist
   * @param loc Location Location
   * @param focalMechanism FocalMechanism
   *
   */
  public HypoMagFreqDistAtLoc(IncrementalMagFreqDist magDist, Location loc, FocalMechanism focalMech) {
	  super(magDist,focalMech);
	  location = loc;
  }

  /**
   * Returns the Location at which MagFreqDist(s) is calculated.
   * @return Location
   */
  public Location getLocation() {
    return location;
  }
  

}
