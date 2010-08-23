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

package org.opensha.sha.imr.param.OtherParams;

import org.opensha.commons.param.DoubleParameter;

/**
 * SigmaTruncLevelParam, a DoubleParameter that represents where truncation occurs
 * on the Gaussian distribution (in units of standard deviation, relative to the mean).
 * See constructors for info on editability and default values.

 */

public class SigmaTruncLevelParam extends DoubleParameter {

	public final static String NAME = "Truncation Level";
	public final static String UNITS = "Std Dev";
	public final static String INFO = "The number of standard deviations, from the mean, where truncation occurs";
	public final static Double DEFAULT = new Double(2.0);
	public final static Double MIN = new Double(Double.MIN_VALUE);
	public final static Double MAX = new Double(Double.MAX_VALUE);

	/**
	 * This constructor sets the default as given, and leaves the
	 * parameter non-editable
	 */
	public SigmaTruncLevelParam(double defaultTruncLevel) {
		super(NAME, MIN, MAX, UNITS);
		setInfo(INFO);
		setDefaultValue(defaultTruncLevel);
		setNonEditable();
		setValueAsDefault();
	}

	/**
	 * This constructor sets the default as 2.0, and leaves the
	 * parameter non-editable
	 */
	public SigmaTruncLevelParam() {this(2.0); }

}
