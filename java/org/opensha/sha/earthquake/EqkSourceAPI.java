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

package org.opensha.sha.earthquake;

import java.util.ArrayList;
import java.util.Iterator;

import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.geo.LocationList;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.util.TectonicRegionType;

/**
 * <p>
 * Title: EqkSourceAPI
 * </p>
 * <p>
 * Description: THis interface is for getting rupture information about each
 * earhquake source
 * </p>
 * 
 * @author Nitin Gupta & Vipin Gupta
 * @date Aug 27 20002
 * @version 1.0
 */

public interface EqkSourceAPI extends NamedObjectAPI {

    /**
     * Get the iterator over all ruptures
     * 
     * @return Iterator on vector for all ruptures
     */
    public Iterator getRupturesIterator();

    /**
     * Get the number of ruptures for this source
     * 
     * @return returns an integer value specifying the number of ruptures for
     *         this source
     */
    public int getNumRuptures();

    /**
     * Get the ith rupture for this source This is a handle(or reference) to
     * existing class variable. If this function is called again, then output
     * from previous function call will not remain valid because of passing by
     * reference. It is a secret, fast but dangerous method
     * 
     * @param i
     *            ith rupture
     */
    public ProbEqkRupture getRupture(int nRupture);

    /**
     * this function can be used if a clone is wanted instead of handle to class
     * variable Subsequent calls to this function will not affect the result got
     * previously. This is in contrast with the getRupture(int i) function
     * 
     * @param i
     * @return
     */
    public ProbEqkRupture getRuptureClone(int nRupture);

    /**
     * Returns the ArrayList consisting of all ruptures for this source all the
     * objects are cloned. so this vector can be saved by the user
     * 
     * @return ArrayList consisting of
     */
    public ArrayList getRuptureList();

    /**
     * It returns a list of all the locations which make up the surface for this
     * source.
     * 
     * @return LocationList - List of all the locations which constitute the
     *         surface of this source
     */
    public LocationList getAllSourceLocs();

    /**
     * This gives the entire surface of the source
     * 
     * @return
     */
    public EvenlyGriddedSurfaceAPI getSourceSurface();

    /**
     * This identifies the type of tectonic region the source is associate with.
     * This should return one of the TYPE_* variables defined in the class
     * org.opensha.sha.imr.param.OtherParams.TectonicRegionTypeParam;
     */
    public TectonicRegionType getTectonicRegionType();

}
