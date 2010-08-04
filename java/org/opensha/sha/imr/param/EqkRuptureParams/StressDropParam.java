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
 * RupWidthParam - Down-dip width of rupture.
 * See constructors for info on editability and default values.
 */
public class StressDropParam extends WarningDoubleParameter {

	public final static String NAME = "Stress Drop";
	public final static String UNITS = "bar";
	public final static String INFO = "Rupture Stress Drop";
	public final static Double MIN = new Double(0.0);		// Test
	public final static Double MAX = new Double(1000.0); 	// Test
	// warning values are set in subclasses
	private static double defaultValue = 140.0;

	/**
	 * This sets the default value and warning-constraint limits
	 *  as given, and leaves the parameter as non editable.
	 */
	public StressDropParam(double minWarning, double maxWarning, double defaultWidth) {
		super(NAME, new DoubleConstraint(MIN, MAX));
		getConstraint().setNonEditable();
		DoubleConstraint warn = new DoubleConstraint(minWarning,maxWarning);
		warn.setNonEditable();
		setWarningConstraint(warn);
		setInfo(INFO);
		setDefaultValue(defaultWidth);
		setNonEditable();
	}

	/**
	 * This sets the default value as 140, and applies the given warning-
	 * constraint limits. The parameter is left as non editable.
	 * TODO check the default value
	 */
	public StressDropParam(double minWarning, double maxWarning) { this(minWarning, maxWarning, defaultValue);}

	/**
	 * This sets the default as given.
	 * This is left editable so warning constraints can be added.
	 */
	public StressDropParam(double defaultWidth) {
		super(NAME, new DoubleConstraint(MIN, MAX), UNITS);
		getConstraint().setNonEditable();
	    setInfo(INFO);
	    setDefaultValue(defaultWidth);
	}

	/**
	 * This sets the default as 10.0.
	 * This is left editable so warning constraints can be added.
	 */
	public StressDropParam() {this(defaultValue);}
}
