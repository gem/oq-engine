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

package org.opensha.sha.imr.param.EqkRuptureParams;

import org.opensha.commons.param.BooleanParameter;

/**
 * Aftershock parameter, indicates whether or not an event is an aftershock.
 * See constructors for info on editability and default values.
 */
public class AftershockParam extends BooleanParameter {

	public final static String NAME = "Aftershock";
	public final static String INFO = "Indicates whether earthquake is an aftershock";

	/**
	 * This constructor sets the default value as "false".
	 * This also makes the parameter non editable.
	 */
	public AftershockParam(boolean defaultValue) {
		super(NAME);
	    setInfo(INFO);
	    setDefaultValue(defaultValue);
	    setNonEditable();
	}
	/**
	 * This constructor sets the default value as "false".  
	 * This also makes the parameter non editable.
	 */
	public AftershockParam() { this(false); }



}
