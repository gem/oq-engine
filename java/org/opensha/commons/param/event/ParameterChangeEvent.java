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

import org.opensha.commons.param.ParameterAPI;

/**
 *  <b>Title:</b> ParameterChangeEvent<p>
 *
 *  <b>Description:</b> Any time a Parameter value is changed via the GUI editor
 *  JPanel, this event is triggered and recieved by all listeners<p>
 *
 * @author     Steven W. Rock
 * @created    February 21, 2002
 * @version    1.0
 */

public class ParameterChangeEvent extends EventObject {

    /** Name of Parameter being changed. */
    private String parameterName;

    /** New value for the Parameter. */
    private Object newValue;

    /** Old value for the Parameter. */
    private Object oldValue;


    /**
     * Constructor for the ParameterChangeEvent object.
     *
     * @param  reference      Object which created this event
     * @param  parameterName  Name of Parameter being changed
     * @param  oldValue       Old value for the Parameter
     * @param  newValue       New value for the Parameter
     */
    public ParameterChangeEvent(
            Object reference,
            String parameterName,
            Object oldValue,
            Object newValue
             ) {
        super( reference );
        this.parameterName = parameterName;
        this.newValue = newValue;
        this.oldValue = oldValue;
    }


    /**
     *  Gets the name of Parameter being changed.
     *
     * @return    Name of Parameter being changed
     */
    public String getParameterName() {
        return parameterName;
    }


    /**
     *  Gets the new value for the Parameter.
     *
     * @return    New value for the Parameter
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
     * Returns the Parameter Object that caused the Event to be fired.
     * @return ParameterAPI
     */
    public ParameterAPI getParameter(){
      return (ParameterAPI)this.getSource();
    }

}
