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

package org.opensha.sha.imr.param.SiteParams;

import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.StringParameter;

/**
 *  Vs flag Parameter - indicates whether vs was measured or inferred/estimated,
 *  or as other categories if the user provides them.
 *  See constructors for info on editability and default values.
 */

public class Vs30_TypeParam extends StringParameter {

	public final static String NAME = "Vs30 Type";
	public final static String INFO = "Indicates how Vs30 was obtained";
	// Options for constraint:
	public final static String VS30_TYPE_MEASURED = "Measured";
	public final static String VS30_TYPE_INFERRED = "Inferred";

	/**
	 * This provides maximum flexibility in terms of setting the options 
	 * and the default.  The parameter is left as non editable.
	 */
	public Vs30_TypeParam(StringConstraint options, String defaultValue) {
		super(NAME, options);
	    this.setInfo(INFO);
	    setDefaultValue(defaultValue);
	    setNonEditable();
	}
	
	/**
	 * This sets the options as given in the fields here, and sets the default
	 * as VS30_TYPE_INFERRED.  Thge parameter is left as non editable.
	 */
	public Vs30_TypeParam() {
		super(NAME);
		StringConstraint options = new StringConstraint();
		options.addString(VS30_TYPE_MEASURED);
		options.addString(VS30_TYPE_INFERRED);
		options.setNonEditable();
		setValue(VS30_TYPE_INFERRED); // need to do this so next line succeeds
		setConstraint(options);
	    setInfo(INFO);
	    setDefaultValue(VS30_TYPE_INFERRED);
	    setNonEditable();
	}
}
