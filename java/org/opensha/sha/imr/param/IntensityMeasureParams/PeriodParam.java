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

/**
 * This represents Period for the Spectral Acceleration parameter (SA_Param).  
 * The constructor requires a list of supported periods (in the form of a
 * DoubleDiscreteConstraint).  Once instantiated, this can be added to the
 * SA_Param as an independent parameter.
 * See constructors for info on editability and default values.
 * @author field
 *
 */
public class PeriodParam extends DoubleDiscreteParameter {

	public final static String NAME = "SA Period";
	public final static String UNITS = "sec";
	public final static String INFO = "Oscillator Period for SA";

	/**
	 * This is the most general constructor
	 * @param peroidList - desired constraints
	 * @param defaultPeriod - desired default value
	 * @param leaveEditable - whether or not to leave editable
	 */
	public PeriodParam(DoubleDiscreteConstraint peroidList, double defaultPeriod, boolean leaveEditable) {
		super(NAME, peroidList, UNITS);
		peroidList.setNonEditable();
		this.setInfo(INFO);
		setDefaultValue(defaultPeriod);
		if(!leaveEditable) setNonEditable();
	}
	
	/**
	 * This sets the default as 1.0 and leaves the parameter non editable
	 * @param peroidList
	 */
	public PeriodParam(DoubleDiscreteConstraint peroidList) { this(peroidList,1.0,false);}
	
	/**
	 * Helper method to quickly get the supported periods.
	 * 
	 * @return
	 */
	public ArrayList<Double> getSupportedPeriods() {
		DoubleDiscreteConstraint constr = (DoubleDiscreteConstraint) getConstraint();
		ArrayList<Double> periods = constr.getAllowedDoubles();
		return periods;
	}
	
	/**
	 * This assumes the list is always in order (is this correct?)
	 * @return
	 */
	public double getMinPeriod() {
		ArrayList<Double> periods = getSupportedPeriods();
		return periods.get(0);
	}
	
	/**
	 * This assumes the list is always in order (is this correct?)
	 * @return
	 */
	public double getMaxPeriod() {
		ArrayList<Double> periods = getSupportedPeriods();
		return periods.get(periods.size()-1);
	}
	
	public double[] getPeriods() {
		ArrayList<Double> periods = getSupportedPeriods();
		double[] pers = new double[periods.size()];
		for(int i=0;i<periods.size();i++)
			pers[i] = periods.get(i).doubleValue();
		return pers;
	}


}
