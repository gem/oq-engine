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

import java.util.ArrayList;

import org.opensha.commons.param.DoubleDiscreteConstraint;
import org.opensha.commons.param.DoubleDiscreteParameter;
import org.opensha.commons.param.DoubleParameter;

/**
 * This represents continuous Period for the Spectral Acceleration parameter (SA_InterpolatedParam).  
 * @author field
 *
 */
public class PeriodInterpolatedParam extends DoubleParameter {

	public final static String NAME = "SA Interpolated Period";
	public final static String UNITS = "sec";
	public final static String INFO = "Continous oscillator period for interpolated SA";

	/**
	 * This is the most general constructor
	 * @param minPeroid - minimum value
	 * @param maxPeroid - maximum value
	 * @param defaultPeriod - desired default value
	 * @param leaveEditable - whether or not to leave editable
	 */
	public PeriodInterpolatedParam(double minPeriod, double maxPeriod, double defaultPeriod, boolean leaveEditable) {
		super(NAME, minPeriod, maxPeriod, UNITS);
		this.setInfo(INFO);
		setDefaultValue(defaultPeriod);
		if(!leaveEditable) setNonEditable();
	}
	
}
