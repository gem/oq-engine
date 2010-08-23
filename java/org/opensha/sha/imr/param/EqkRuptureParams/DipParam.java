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
 * Dip Parameter, for representing the average dip of the earthquake rupture.
 * See constructors for info on editability and default values.
 */
public class DipParam extends WarningDoubleParameter {

	public final static String NAME = "Dip";
	public final static String UNITS = "degrees";
	public final static String INFO = "Average dip of earthquake rupture";
	protected final static Double MIN = new Double(0);
	protected final static Double MAX = new Double(90);

	/**
	 * This sets the default value and warning-constraint limits
	 *  as given, and leaves the parameter as non editable.
	 */
	public DipParam(double minWarning, double maxWarning, double defaultDip) {
		super(NAME, new DoubleConstraint(MIN, MAX));
		getConstraint().setNonEditable();
		DoubleConstraint warn = new DoubleConstraint(minWarning,maxWarning);
		warn.setNonEditable();
		setWarningConstraint(warn);
		setInfo(INFO);
		setDefaultValue(defaultDip);
		setNonEditable();
	}

	/**
	 * This sets the default value as 90, and applies the given warning-
	 * constraint limits. The parameter is left as non editable.
	 */
	public DipParam(double minWarning, double maxWarning) { this(minWarning, maxWarning, 90);}

	/**
	 * This sets the default dip as given and and leaves it 
	 * editable so one can set the warning constraint.
	 */
	public DipParam(double dipDefault) {
		super(NAME, new DoubleConstraint(MIN, MAX), UNITS);
		getConstraint().setNonEditable();
		setInfo(INFO);
		setDefaultValue(dipDefault);
	}

	/**
	 * This sets the default dip as 90 degrees, and and leaves it 
	 * editable so one can set the warning constraint.
	 */
	public DipParam() { this(90.0); }

}
