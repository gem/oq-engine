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

package org.opensha.sha.imr.event;

import java.util.EventListener;

/**
 *  <b>Title:</b> ScalarIMRChangeListener<p>
 *
 *  <b>Description:</b> The change listener receives change events whenever a new
 *  Attenuation Relationship is selected, such as from an IMR Gui Bean.<p>
 *
 * @author     Kevin Milner
 * @created    February 27 2009
 * @version    1.0
 */

public interface ScalarIMRChangeListener extends EventListener {
    /**
     *  Function that must be implemented by all Listeners for
     *  AttenuationRelationshipChangeEvents.
     *
     * @param  event  The Event which triggered this function call
     */
    public void imrChange( ScalarIMRChangeEvent event );
}
