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

import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.WarningDoubleParameter;

/**
 * Magnitude parameter, reserved for representing moment magnitude.
 * The warning constraint must be created and added after instantiation.
 * See constructors for info on editability and default values.
 */
public class MagParam extends WarningDoubleParameter {

	public final static String NAME = "Magnitude";
	public final static String INFO = "Earthquake Moment Magnatude";
	protected final static Double MIN = new Double(0);
	protected final static Double MAX = new Double(10);
	// warning values are set in subclasses
	
	/**
	 * This sets the default value and warning-constraint limits
	 *  as given, and leaves the parameter as non editable.
	 */
	public MagParam(double minWarning, double maxWarning, double defaultMag) {
		super(NAME, new DoubleConstraint(MIN, MAX));
		getConstraint().setNonEditable();
		DoubleConstraint warn = new DoubleConstraint(minWarning, maxWarning);
		warn.setNonEditable();
		setWarningConstraint(warn);
	    setInfo(INFO);
	    setDefaultValue(defaultMag);
	    setNonEditable();
	    
	}

	/**
	 * This sets the default value as 5.5, and applies the given warning-
	 * constraint limits. The parameter is left as non editable.
	 */
	public MagParam(double minWarning, double maxWarning) { this(minWarning, maxWarning, 5.5);}

	/**
	 * This sets the default value as given.  No warning limits are set, so
	 * this is left editable so warning constraints can be added.
	 */
	public MagParam(double defaultMag) {
		super(NAME, new DoubleConstraint(MIN, MAX));
		getConstraint().setNonEditable();
	    setInfo(INFO);
	    setDefaultValue(defaultMag);
	}

	/**
	 * This sets the default value as 5.5.  No warning limits are set, so
	 * this is left editable so warning constraints can be added.
	 */
	public MagParam() { this(5.5);}
	
	
}
