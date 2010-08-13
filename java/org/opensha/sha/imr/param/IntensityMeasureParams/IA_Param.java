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

import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.WarningDoubleParameter;

/**
 * This constitutes the natural-log Arias Intensity intensity measure
 * parameter.  
 * See constructors for info on editability and default values.
 * @author goulet (aug 2009) - modified based on PGA_Param from field
 *
 */
public class IA_Param extends WarningDoubleParameter {

    public final static String NAME = "IA"; 
    public final static String UNITS = "m/s"; 
    public final static String INFO = "Arias Intensity"; 
    public final static Double MIN = new Double(Double.MIN_VALUE); 
    public final static Double MAX = new Double(Double.MAX_VALUE); 
    public final static Double DEFAULT_WARN_MIN = new Double(Double.MIN_VALUE); 
    public final static Double DEFAULT_WARN_MAX = new Double(Double.MAX_VALUE); 


	/**
	 * This uses the supplied warning constraint and default (both in natural-log space).
	 * The parameter is left as non editable
	 * @param warningConstraint
	 * @param defaultPGA
	 */
	public IA_Param(DoubleConstraint warningConstraint, double defaultIA) {
		super(NAME, new DoubleConstraint(MIN, MAX), UNITS);
		getConstraint().setNonEditable();
	    this.setInfo(INFO);
	    setWarningConstraint(warningConstraint);
	    setDefaultValue(defaultIA);
	    setNonEditable();
	}
	
	/**
	 * This uses the DEFAULT_WARN_MIN and DEFAULT_WARN_MAX fields to set the
	 * warning constraint, and sets the default as Math.log(1.0) (the natural
	 * log of 1.0).
	 * The parameter is left as non editable
	 */
	public IA_Param() {
		super(NAME, new DoubleConstraint(MIN, MAX), UNITS);
		getConstraint().setNonEditable();
	    setInfo(INFO);
	    DoubleConstraint warn2 = new DoubleConstraint(DEFAULT_WARN_MIN, DEFAULT_WARN_MAX);
	    warn2.setNonEditable();
	    setWarningConstraint(warn2);
	    setDefaultValue(Math.log(1.0));
	    setNonEditable();
	}
}
