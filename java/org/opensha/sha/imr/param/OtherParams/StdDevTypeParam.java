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

import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.StringParameter;

/**
 * StdDevTypeParam represents the various types of standard deviations that an IMR might 
 * support  The constraint must be provided in the constructor, and the "STD_DEV_TYPE_*" 
 * strings here represent common options that can be used in creating the constraint 
 * (although other unique options can be added as well).
 * "InterEvent" is the event to event variability, "Intra-Event" is the variability 
 * within an event, and "Total" (the most common) is the other two two added in quadrature.
 * Other options should be self explanatory. 
 *  See constructors for info on editability and default values.
 */

public class StdDevTypeParam extends StringParameter {

	
	public final static String NAME = "Std Dev Type";
	// No units for this one
	public final static String INFO = "Type of Standard Deviation";
	
	// Options
	public final static String STD_DEV_TYPE_TOTAL = "Total";
	public final static String STD_DEV_TYPE_INTER = "Inter-Event";
	public final static String STD_DEV_TYPE_INTRA = "Intra-Event";
	public final static String STD_DEV_TYPE_NONE = "None (zero)";
	public final static String STD_DEV_TYPE_TOTAL_MAG_DEP = "Total (Mag Dependent)";
	public final static String STD_DEV_TYPE_TOTAL_PGA_DEP = "Total (PGA Dependent)";
	public final static String STD_DEV_TYPE_INTRA_MAG_DEP = "Intra-Event (Mag Dependent)";

//	public String DEFAULT = STD_DEV_TYPE_TOTAL;

	/**
	 * This sets the default as STD_DEV_TYPE_TOTAL (and will throw and 
	 * exception if that value is not in the options list).
	 * The parameter is set as non editable after creation.
	 * 
	 * @param options
	 */
	public StdDevTypeParam(StringConstraint options) {
		super(NAME, options);
	    setInfo(INFO);
	    setDefaultValue(STD_DEV_TYPE_TOTAL);
	    setNonEditable();
	}
	/**
	 * This one allows you to set the default (overriding how its set in the other constructor).
	 * The parameter is set as non editable after creation.
	 * @param options
	 */
	public StdDevTypeParam(StringConstraint options, String defaultValue) {
		super(NAME, options);
	    setInfo(INFO);
	    setDefaultValue(defaultValue);
	    setNonEditable();
	}
}
