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

package org.opensha.sha.imr.param.OtherParams;

import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.StringParameter;

/**
 * Component Parameter, reserved for representing the component of shaking
 * (in 3D space). The constraint must be provided in the constructor, and the
 * "COMPONENT_*" strings here represent common options that can be used in creating 
 *  the constraint (although other unique options can be added as well).
 *  See constructors for info on editability and default values.
 */

public class ComponentParam extends StringParameter {

	public final static String NAME = "Component";
	public final static String INFO = "Component of shaking";

	// Options for constraint:
	public final static String COMPONENT_AVE_HORZ = "Average Horizontal";
	public final static String COMPONENT_GMRotI50 = "Average Horizontal (GMRotI50)";
	public final static String COMPONENT_RANDOM_HORZ = "Random Horizontal";
	public final static String COMPONENT_GREATER_OF_TWO_HORZ = "Greater of Two Horz.";
	public final static String COMPONENT_VERT = "Vertical";

	/**
	 * The parameter is set as non editable after creation
	 * @param options
	 * @param defaultValue
	 */
	public ComponentParam(StringConstraint options, String defaultValue) {
		super(NAME, options);
	    setInfo(INFO);
	    setDefaultValue(defaultValue);
	    setNonEditable();
	}
}
