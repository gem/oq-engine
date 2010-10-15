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

import java.util.ListIterator;

import org.opensha.commons.data.Container2DAPI;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;

/**
 * <b>Title:</b> GriddedSurfaceAPI
 * <p>
 * <b>Description:</b>
 * 
 * The GriddedSurfaceAPI represents a geographical surface of Location objects
 * slicing through or on the surface of the earth. Recall that a Container2DAPI
 * represents a collection of Objects in a matrix, or grid, accessed by row and
 * column inedexes. All GriddedSurfaces do is to constrain the object at each
 * grid point to be a Location object. There are also methods for getting info
 * about the surface (e.g., ave dip, ave strike, etc.).
 * <p>
 * 
 * There are no constraints on what locations are put where, but the presumption
 * is that the the grid of locations map out the surface . it is also presumed
 * that the zeroeth row represent the top edge (or trace).
 * <p>
 * 
 * @author
 * @created
 * @version 1.0
 */
public interface GriddedSurfaceAPI extends Container2DAPI<Location> {

    /** Returns the average dip of the surface. */
    public double getAveDip() throws UnsupportedOperationException;;

    /** Returns the average strike of the surface. */
    public double getAveStrike() throws UnsupportedOperationException;

    /**
     * Put all the locations of this surface into a location list
     * 
     * @return
     */
    public LocationList getLocationList();

    /** Common debug string that most Java classes implement */
    public String toString();

    /**
     * get a list of locations that constitutes the perimeter (forst row, last
     * col, last row, and first col)
     */
    public LocationList getSurfacePerimeterLocsList();

    /**
     * Returns the Metadata for the surface
     * 
     * @return String
     */
    public String getSurfaceMetadata();

    /**
     * This returns the total length of the surface
     * 
     * @return double
     */
    public double getSurfaceLength();

    /**
     * This returns the surface width (down dip)
     * 
     * @return double
     */
    public double getSurfaceWidth();

    /**
     * Method to get location...same as get(row, column)
     * 
     * @param row
     * @param column
     * @return
     */
    public Location getLocation(int row, int column);

    /**
     * Method to set location...same as set(row, column, loc)
     * 
     * @param row
     * @param column
     * @param loc
     */
    public void setLocation(int row, int column, Location loc);

    /**
     * Returns listiterator()
     * 
     * @return
     */
    public ListIterator<Location> getLocationsIterator();

}
