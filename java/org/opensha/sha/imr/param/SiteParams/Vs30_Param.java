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

import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.WarningDoubleParameter;

/**
 * Vs30 Parameter, reserved for representing the average shear-wave velocity
 * in the upper 30 meters of a site (a commonly used parameter).  The warning 
 * constraint must be created and added when instantiated.
 * See constructors for info on editability and default values.
 */
public class Vs30_Param extends WarningDoubleParameter {

	public final static String NAME = "Vs30";
	public final static String UNITS = "m/sec";
	public final static String INFO = "The average shear-wave velocity between 0 and 30-meters depth";
//	public final static Double DEFAULT = new Double("760");
	protected final static Double MIN = new Double(0.0);
	protected final static Double MAX = new Double(5000.0);

	/**
	 * This constructor sets the default value as given and leaves the param editable so
	 * the warning constraint can be added.
	 */
	public Vs30_Param(double defaultValue) {
		super(NAME, new DoubleConstraint(MIN, MAX), UNITS);
		getConstraint().setNonEditable();
	    this.setInfo(INFO);
	    setDefaultValue(defaultValue);
	}

	/**
	 * This constructor sets the default value as 760 m/sec and leaves the param editable so
	 * the warning constraint can be added.
	 */
	public Vs30_Param() {this(760);}

	/**
	 * This constructor sets the default and warning constraint as given, 
	 * and sets everything as non-editable.
	 * @param warnMin
	 * @param warnMax
	 */
	public Vs30_Param(double defaultValue, double warnMin, double warnMax) {
		super(NAME, new DoubleConstraint(MIN, MAX), UNITS);
		getConstraint().setNonEditable();
	    setInfo(INFO);
	    setDefaultValue(defaultValue);
	    DoubleConstraint warn = new DoubleConstraint(warnMin, warnMax);
	    setWarningConstraint(warn);
	    warn.setNonEditable();
	    setNonEditable();
	}
	
	/**
	 * This constructor sets the default as 760 m/sec, the warning constraint 
	 *  as given, and sets everything as non-editable.
	 * @param warnMin
	 * @param warnMax
	 */
	public Vs30_Param(double warnMin, double warnMax) {this(760.0,warnMin, warnMax);}


}
