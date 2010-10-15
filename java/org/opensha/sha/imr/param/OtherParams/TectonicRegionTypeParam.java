/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with the Southern California
 * Earthquake Center (SCEC, http://www.scec.org) at the University of Southern
 * California and the UnitedStates Geological Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not
 * use this file except in compliance with the License. You may obtain a copy of
 * the License at
 * 
 * http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations under
 * the License.
 ******************************************************************************/

package org.opensha.sha.imr.param.OtherParams;

import java.util.ArrayList;

import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.StringParameter;
import org.opensha.sha.util.TectonicRegionType;

/**
 * This Tectonic Region Type Param is a string representation of our
 * TectonicRegionType enum (located in org.opensha.sha.util). The options to be
 * supported in any given instance are supplied via the string constraint
 * supplied in the constructor. However, no options other than what's defined by
 * the TectonicRegionType enum are allowed. See constructors for info on
 * editability and default values. Note that this is not in the EqkRuptureParams
 * directory because it will not be set from information in and EqkRupture
 * object (the latter does not carry this info).
 */

public class TectonicRegionTypeParam extends StringParameter {

    /**
	 * 
	 */
    private static final long serialVersionUID = 1L;

    public final static String NAME = "Tectonic Region";
    public final static String INFO =
            "Applicable Tectonic Region(s) - not strictly enforced";

    /**
     * This no-argument constructor defaults to only Active Shallow Crust, and
     * sets the parameter as non editable.
     */
    public TectonicRegionTypeParam() {
        super(NAME);
        StringConstraint options = new StringConstraint();
        options.addString(TectonicRegionType.ACTIVE_SHALLOW.toString());
        setConstraint(options);
        setInfo(INFO);
        setDefaultValue(TectonicRegionType.ACTIVE_SHALLOW.toString());
        setNonEditable();
    }

    /**
     * This constructor will throw an exception if the options contain a
     * non-allowed type (as represented by the TYPE_* fields here). The
     * parameter is set as non editable after creation
     * 
     * @param options
     * @param defaultValue
     */
    public TectonicRegionTypeParam(StringConstraint options, String defaultValue) {
        super(NAME, options);
        // check that options are supported
        ArrayList<String> strings = options.getAllowedStrings();
        for (int i = 0; i < strings.size(); i++)
            if (!TectonicRegionType.isValidType((String) strings.get(i)))
                throw new RuntimeException(
                        "Constraint type not supported by TectonicRegionTypeParam");
        setInfo(INFO);
        setDefaultValue(defaultValue);
        setNonEditable();
    }

    /**
     * This checks whether a type is potentially supported by this class
     * (whether an instance could support it, as opposed to whether an instance
     * does support it (the latter being controlled by the string constraint).
     * 
     * @param option
     * @return boolean
     */
    public static boolean isTypePotentiallySupported(String option) {
        return TectonicRegionType.isValidType(option);
    }

}
