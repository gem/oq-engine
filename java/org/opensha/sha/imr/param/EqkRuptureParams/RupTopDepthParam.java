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
 * RupTopDepth parameter - Depth to top of rupture.
 * See constructors for info on editability and default values.
 */
public class RupTopDepthParam extends WarningDoubleParameter {

	public final static String NAME = "Rupture Top Depth";
	public final static String UNITS = "km";
	public final static String INFO = "The depth to the shallowest point on the earthquake rupture surface";
	protected final static Double MIN = new Double(0);
	protected final static Double MAX = new Double(30);
	// warning values are set in subclasses
	
	
	/**
	 * This sets the default value and warning-constraint limits
	 *  as given, and leaves the parameter as non editable.
	 */
	public RupTopDepthParam(double minWarning, double maxWarning, double defaultDepth) {
		super(NAME, new DoubleConstraint(MIN, MAX));
		getConstraint().setNonEditable();
		DoubleConstraint warn = new DoubleConstraint(minWarning,maxWarning);
		warn.setNonEditable();
		setWarningConstraint(warn);
		setInfo(INFO);
		setDefaultValue(defaultDepth);
		setNonEditable();
	}

	/**
	 * This sets the default value as 0.0, and applies the given warning-
	 * constraint limits. The parameter is left as non editable.
	 */
	public RupTopDepthParam(double minWarning, double maxWarning) { this(minWarning, maxWarning, 0.0);}
	
	/**
	 * This sets the default as given
	 * This is left editable so warning constraints can be added.
	 */
	public RupTopDepthParam(double defaultDepth) {
		super(NAME, new DoubleConstraint(MIN, MAX), UNITS);
		getConstraint().setNonEditable();
	    setInfo(INFO);
	    setDefaultValue(defaultDepth);
	}

	/**
	 * This sets the default as 0.0
	 * This is left editable so warning constraints can be added.
	 */
	public RupTopDepthParam() { this(0.0); }

}
