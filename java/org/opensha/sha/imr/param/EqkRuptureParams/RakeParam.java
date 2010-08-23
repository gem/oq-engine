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
import org.opensha.commons.param.DoubleParameter;

/**
 * Rake Parameter, reserved for representing the average rake of the earthquake
 * rupture.
 * See constructors for info on editability and default values.
 */
public class RakeParam extends DoubleParameter {

	public final static String NAME = "Rake";
	public final static String UNITS = "degrees";
	public final static String INFO = "Average rake of earthquake rupture";
	protected final static Double MIN = new Double( -180);
	protected final static Double MAX = new Double(180);

	/**
	 * This sets the default as given  
	 * This also leaves the parameter as non editable.
	 */
	public RakeParam(double defaultRake) {
		super(NAME, new DoubleConstraint(MIN, MAX), UNITS);
		getConstraint().setNonEditable();
	    setInfo(INFO);
	    setDefaultValue(defaultRake);
	    setNonEditable();
	}

	/**
	 * This sets the default as 0.0  
	 * This also leaves the parameter as non editable.
	 */
	public RakeParam() {this(0.0);}

}
