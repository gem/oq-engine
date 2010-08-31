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

package org.opensha.sha.imr.param.PropagationEffectParams;

import org.opensha.commons.param.BooleanParameter;

/**
 * HangingWallFlagParam parameter - indicates whether a site is 
 * on the hanging wall of a rupture surface.  Exact definition and setting 
 * of value must be handled in the implementing class.
 * See constructors for info on editability and default values.
 */
public class HangingWallFlagParam extends BooleanParameter {

	public final static String NAME = "Site on Hanging Wall";
	public final static String INFO = "Indicates whether the site is on the hanging wall";

	/**
	 * This sets the default value as given, and leaves the parameter
	 * non editable.
	 * @param defaultValue
	 */
	public HangingWallFlagParam(boolean defaultValue) {
		super(NAME);
		setInfo(INFO);
		setDefaultValue(defaultValue);
	}
	
	/**
	 * This sets the default value as "false", and leaves the parameter
	 * non editable.
	 * @param defaultValue
	 */
	public HangingWallFlagParam() {this(false);}

}
