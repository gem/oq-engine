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

import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.exceptions.EditableException;

/**
 * <b>Title:</b> ParameterConstraintAPI<p>
 *
 * <b>Description:</b> This is the interface that all
 * constraints must implement. Constraints store such information
 * as if a value is allowed, if the data is editable, i.e. functions
 * that restrict or allow setting new values on parameters.<p>
 *
 * @author     Sid Hellman, Steven W. Rock
 * @created    February 21, 2002
 * @version    1.0
 */

public interface ParameterConstraintAPI<E> extends NamedObjectAPI{

    /**  Every parameter constraint has a name, this function returns that name.  */
    public String getName();

    /**  Every parameter constraint has a name, this function sets that name.  */
    public void setName(String name) throws EditableException ;

    /**
     *  Determine if the new value being set is allowed.
     * @param  obj  Object to check if allowed via constraints.
     * @return      True if the value is allowed.
     */
    public boolean isAllowed( E obj );


    /**
     *  Determines if the value can be edited, i.e. changed once set.
     * @return    The editable value.
     */
    public boolean isEditable();


    /** Disables editing the value once it is set. */
    public void setNonEditable();


    /**
     *  Returns a copy so you can't edit or damage the origial.
     * @return    Exact copy of this object's state.
     */
    public Object clone();

    /** A parameter may or may not allow null values. That permission is set here. */
    public void setNullAllowed(boolean nullAllowed) throws EditableException;
    /** A parameter may or may not allow null values. That permission is checked here. */
    public boolean isNullAllowed();

}
