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

package org.opensha.commons.data;

import java.util.Comparator;

import org.opensha.commons.exceptions.InvalidRangeException;

/**
 *  <b>Title:</b> DataPoint2DComparatorAPI<p>
 *
 *  <b>Description:</b> This interface must be implemented by all comparators of
 *  DataPoint2D. The comparator uses a tolerance to specify when two values are
 *  within tolerance of each other, they are equal<p>
 *
 * @author     Steven W. Rock
 * @created    February 20, 2002
 * @see        DataPoint2D
 * @version    1.0
 */

public interface DataPoint2DComparatorAPI extends Comparator {

    /**
     *  Tolerance indicates the distance two values can be apart, but still
     *  considered equal. This function sets the tolerance.
     *
     * @param  newTolerance               The new tolerance value
     * @exception  InvalidRangeException  Is Thrown if the tolarance is negative
     */
    public void setTolerance( double newTolerance ) throws InvalidRangeException;


    /**
     *  Tolerance indicates the distance two values can be apart, but still
     *  considered equal. This function returns the tolerance.
     *
     * @return    The tolerance value
     */
    public double getTolerance();

}
