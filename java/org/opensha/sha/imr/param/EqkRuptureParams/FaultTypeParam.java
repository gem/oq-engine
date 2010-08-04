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

import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.StringParameter;

/**
 * FaulltTypeParam, a StringParameter for representing different
 * styles of faulting.  The options are not specified here because
 * nomenclature generally differs among subclasses.  The default must
 * also be specified in the constructor.
 * See constructors for info on editability and default values.
 */

public class FaultTypeParam extends StringParameter {

	public final static String NAME = "Fault Type";
	public final static String INFO = "Style of faulting";

	/**
	 * This sets the parameter as non-editable
	 * @param options
	 * @param defaultValue
	 */
	public FaultTypeParam(StringConstraint options, String defaultValue) {
		super(NAME, options);
	    setInfo(INFO);
	    setDefaultValue(defaultValue);
	    this.setNonEditable();
	}
}
