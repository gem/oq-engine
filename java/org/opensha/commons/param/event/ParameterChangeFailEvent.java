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

package org.opensha.commons.param.event;

import java.util.EventObject;

/**
 *  <b>Title:</b> ParameterChangeFailEvent<p>
 *
 *  <b>Description:</b> Any time a Parameter value thows a ConstraintException,
 *  this event is triggered and recieved by all listeners<p>

 *
 * @author     Steven W. Rock
 * @created    February 21, 2002
 * @version    1.0
 */

public class ParameterChangeFailEvent extends EventObject {

    /** Name of Parameter tried to change. */
    private String parameterName;

    /** New invalid value for the Parameter that failed. */
    private Object badValue;

    /** Old value for the Parameter. */
    private Object oldValue;


    /**
     *  Constructor for the ParameterChangeFailEvent object.
     *
     * @param  reference      Object which created this event
     * @param  parameterName  Name of Parameter tried to change.
     * @param  oldValue       Old value for the Parameter
     * @param  badValue       New value for the Parameter that failed
     */
    public ParameterChangeFailEvent(
            Object reference,
            String parameterName,
            Object oldValue,
            Object badValue
             ) {
        super( reference );
        this.parameterName = parameterName;
        this.badValue = badValue;
        this.oldValue = oldValue;
    }


    /**
     *  Gets the name of Parameter that failed a change.
     * @return    Name of Parameter tried to change
     */
    public String getParameterName() { return parameterName; }


    /**
     *  Gets the failed value.
     * @return    Failed value for the Parameter
     */
    public Object getBadValue() { return badValue; }


    /**
     *  Gets the old value for the Parameter.
     * @return    Old value for the Parameter
     */
    public Object getOldValue() {
        return oldValue;
    }

}
