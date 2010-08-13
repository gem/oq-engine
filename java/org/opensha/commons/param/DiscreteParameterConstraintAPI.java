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

package org.opensha.commons.param;

import java.util.ArrayList;
import java.util.ListIterator;

/**
 * <b>Title:</b> DiscreteParameterConstraintAPI<p>
 *
 * <b>Description:</b> This interface must be implemented by all parameters
 * that wish to restrict allowed values to a definite set. These values are
 * typically presented in a GUI with a picklist.<p>
 *
 * @author Steven W. Rock
 * @version 1.0
 */

public interface DiscreteParameterConstraintAPI<E> extends ParameterConstraintAPI<E> {

    /** Returns cloned vector of allowed values, unable to modify original values. */
    public ArrayList getAllowedValues();

    /**  Returns Iterator over allowed values, able to modify original. */
    public ListIterator listIterator();

    /** Returns the number of allowed values in the list */
    public int size();
}
