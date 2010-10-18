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

package org.opensha.sha.imr.param.IntensityMeasureParams;

import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.WarningDoubleParameter;

/**
 * This constitutes the MMI intensity measure parameter. See constructors for
 * info on editability and default values.
 * 
 * @author Damiano Monelli
 * @created 22 September 2010
 * @version 1.0
 * 
 */
public class MMI_Param extends WarningDoubleParameter {

    /**
	 * 
	 */
    private static final long serialVersionUID = 1L;
    public final static String NAME = "MMI";
    public final static String UNITS = "degree";
    public final static String INFO = "Modified Mercalli Intensity";
    public final static Double MIN = new Double(1.0);
    public final static Double MAX = new Double(12.0);
    public final static Double DEFAULT = new Double(5.0);
    public final static Double DEFAULT_WARN_MIN = new Double(1.0);
    public final static Double DEFAULT_WARN_MAX = new Double(12.0);

    /**
     * This uses the supplied warning constraint and default. The parameter is
     * left as non editable
     * 
     * @param warningConstraint
     * @param defaultMMI
     */
    public MMI_Param(DoubleConstraint warningConstraint, double defaultMMI) {
        super(NAME, new DoubleConstraint(MIN, MAX), UNITS);
        getConstraint().setNonEditable();
        this.setInfo(INFO);
        setWarningConstraint(warningConstraint);
        setDefaultValue(defaultMMI);
        setNonEditable();
    }

    /**
     * This uses the DEFAULT_WARN_MIN and DEFAULT_WARN_MAX fields to set the
     * warning constraint, and sets the default value The parameter is left as
     * non editable
     */
    public MMI_Param() {
        super(NAME, new DoubleConstraint(MIN, MAX), UNITS);
        getConstraint().setNonEditable();
        setInfo(INFO);
        DoubleConstraint warn2 =
                new DoubleConstraint(DEFAULT_WARN_MIN, DEFAULT_WARN_MAX);
        warn2.setNonEditable();
        setWarningConstraint(warn2);
        setDefaultValue(DEFAULT);
        setNonEditable();
    }

}
