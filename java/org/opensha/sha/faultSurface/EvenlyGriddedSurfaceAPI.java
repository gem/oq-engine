/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with the Southern California
 * Earthquake Center (SCEC, http://www.scec.org) at the University of Southern
 * California and the UnitedStates Geological Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not
 * use this file except in compliance with the License. You may obtain a copy of
 * the License at
 * 
 * http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations under
 * the License.
 ******************************************************************************/

package org.opensha.sha.faultSurface;

/**
 * <b>Title:</b> EvenlyGriddedSurfaceAPI
 * <p>
 * <b>Description:</b>
 * 
 * This extends GriddedSurfaceAPI assuming the locations are in some way evenly
 * spaced.
 * <p>
 * 
 * @author
 * @created
 * @version 1.0
 */
public interface EvenlyGriddedSurfaceAPI extends GriddedSurfaceAPI {

    /**
     * returns the grid spacing along strike
     * 
     * @return
     */
    public double getGridSpacingAlongStrike();

    /**
     * returns the grid spacing down dip
     * 
     * @return
     */
    public double getGridSpacingDownDip();

    /**
     * this tells whether along strike and down dip grip
     * 
     * @return
     */
    public Boolean isGridSpacingSame();

    /**
     * This returns the total length of the surface in km
     * 
     * @return double
     */
    public double getSurfaceLength();

    /**
     * This returns the surface width (down dip) in km
     * 
     * @return double
     */
    public double getSurfaceWidth();

    /**
     * This returns the surface area in km-sq
     * 
     * @return double
     */
    public double getSurfaceArea();

}
