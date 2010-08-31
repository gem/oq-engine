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

import org.opensha.commons.param.WarningParameterAPI;

/**
 *  <b>Title:</b> ParameterChangeWarningEvent<p>
 *
 *  <b>Description:</b> This event is thrown when you try to modify a parameter's value
 *  beyond it's recommended value. This event gives the calling class the ability
 *  to either head the warnings or ignore it and update the parameter anyways. <p>
 *
 * @author     Steven W. Rock
 * @created    April 17, 2002
 * @version    1.0
 */

public class ParameterChangeWarningEvent extends EventObject {

    /**
     *  Name of Parameter tried to change.
     */
    private WarningParameterAPI param;

    /**
     *  New value for the Parameter that failed.
     */
    private Object newValue;

    /**
     *  Old value for the Parameter.
     */
    private Object oldValue;


    /**
     *  Constructor for the ParameterChangeWarningEvent object.
     *
     * @param  reference      Object which created this event, i.e. the parametr
     * @param  parameterName  Name of Parameter tried to change.
     * @param  oldValue       Old value for the Parameter
     * @param  badValue       New value for the Parameter that failed
     */
    public ParameterChangeWarningEvent(
            Object reference,
            WarningParameterAPI param,
            Object oldValue,
            Object newValue
             ) {
        super( reference );
        this.param = param;
        this.newValue = newValue;
        this.oldValue = oldValue;
    }


    /**
     *  Gets the name of Parameter that failed a change.
     *
     * @return    Name of Parameter tried to change
     */
    public WarningParameterAPI getWarningParameter() {
        return param;
    }


    /**
     *  Gets the desired new value.
     *
     * @return    new value for the Parameter
     */
    public Object getNewValue() {
        return newValue;
    }


    /**
     *  Gets the old value for the Parameter.
     *
     * @return    Old value for the Parameter
     */
    public Object getOldValue() {
        return oldValue;
    }


    /**
     * Set's the new value ignoring the warning
     */
    public void commitNewChange(){

    }

}
