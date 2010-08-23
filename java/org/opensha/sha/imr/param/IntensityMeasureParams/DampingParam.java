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

package org.opensha.sha.imr.param.IntensityMeasureParams;

import org.opensha.commons.param.DoubleDiscreteConstraint;
import org.opensha.commons.param.DoubleDiscreteParameter;

/**
 * This represents Damping for the Spectral Acceleration parameter (SA_Param).  
 * The constructor requires a list of supported damping levels (in the form of a
 * DoubleDiscreteConstraint).  Once instantiated, this can be added to the
 * SA_Param as an independent parameter.
 * See constructors for info on editability and default values.
 * @author field
 *
 */
public class DampingParam extends DoubleDiscreteParameter {

	public final static String NAME = "SA Damping";
	public final static String UNITS = " % ";
	public final static String INFO = "Oscillator Damping for SA";


	/**
	 * This leaves the parameter non editable
	 * @param dampingConstraint
	 * @param defaultDamping
	 */
	public DampingParam(DoubleDiscreteConstraint dampingConstraint, double defaultDamping) {
		super(NAME, dampingConstraint, UNITS);
		dampingConstraint.setNonEditable();
		this.setInfo(INFO);
		setDefaultValue(defaultDamping);
		setNonEditable();
	}
	
	/**
	 * This sets the default as 5%, and leaves the parameter non-editable
	 * @param dampingConstraint
	 */
	public DampingParam(DoubleDiscreteConstraint dampingConstraint) {this(dampingConstraint, 5.0);}


	/**
	 * This constructor assumes that only 5% damping is supported, and sets this as the default.
	 * The parameter is left non editable.
	 */
	public DampingParam() {
		super(NAME, UNITS);
		double damping = 5;
		DoubleDiscreteConstraint dampingConstraint = new DoubleDiscreteConstraint();
		dampingConstraint.addDouble(damping);
		setValue(damping); // set this hear so current value doesn't cause problems when setting the constraint
		dampingConstraint.setNonEditable();
		setConstraint(dampingConstraint);
		setInfo(INFO);
		setDefaultValue(damping);
		setNonEditable();
	}
}
