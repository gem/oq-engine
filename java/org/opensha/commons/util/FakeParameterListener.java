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

package org.opensha.commons.util;

import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeFailEvent;
import org.opensha.commons.param.event.ParameterChangeFailListener;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;

/**
 * This is simply a class that implements all of the ParameterChangeListeners, without 
 * actually doing anything. It is most useful when instantiating AttenuationRelationship
 * objects when you don't care about about ParameterChange events, especially for quick
 * tests.
 * 
 * @author kevin
 *
 */
public class FakeParameterListener implements ParameterChangeFailListener,
		ParameterChangeListener, ParameterChangeWarningListener {

	public void parameterChangeFailed(ParameterChangeFailEvent event) {
		// do nothing

	}

	public void parameterChange(ParameterChangeEvent event) {
		// do nothing

	}

	public void parameterChangeWarning(ParameterChangeWarningEvent event) {
		// do nothing
	}

}
