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

package org.opensha.commons.util;

import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.DoubleDiscreteConstraint;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterConstraintAPI;
import org.opensha.commons.param.WarningParameterAPI;

/**
 * <b>Title:</b>ParamUtils<p>
 *
 * <b>Description:</b>Generic functions used in handling parameters, basically
 * verifying the class type of a Parameter. Recall that all Parameters implement
 * the ParameterAPI. Because of this they are passed around functions as ParameterAPI.
 * In some cases you need to know more specifically the class type in  order to access
 * the special functions of these subclasses. This utility class verifies the class type
 * so you can cast to the right type without throwing errors.
 *
 * @author Steven W. Rock
 * @version 1.0
 */

public class ParamUtils {

    /**
     * Returns true if the ParameterAPI is a DoubleParameter or DoubleDiscreteParameter.
     * This allows you to get and set the value as a Double.
     * @param           The parameter to verify
     * @return          boolean true if is either parameter type, else false
     */
    public static boolean isDoubleOrDoubleDiscreteConstraint(ParameterAPI param) {
        if( isDoubleConstraint(param) || isDoubleDiscreteConstraint(param) ) return true;
        else return false;
    }

    /**
     * Returns true if the ParameterAPI contained constraint is a DoubleConstraint.
     * @param           The parameter to verify
     * @return          boolean true if constraint is DOubleConstraint, false otherwise.
     */
    public static boolean isDoubleConstraint(ParameterAPI param) {
        ParameterConstraintAPI constraint = param.getConstraint();
        if ( constraint instanceof DoubleConstraint ) return true;
        else return false;
    }

    /**
     * Returns true if the ParameterAPI contained constraint is a DoubleDiscreteConstraint.
     * @param           The parameter to verify
     * @return          boolean if is either parameter type
     */
    public static boolean isDoubleDiscreteConstraint(ParameterAPI param) {
        ParameterConstraintAPI constraint = param.getConstraint();
        if ( constraint instanceof DoubleDiscreteConstraint ) return true;
        else return false;
    }

    /**
     * Returns true if the ParameterAPI is an instance of WarningParameterAPI
     * @param           The parameter to verify
     * @return          boolean if is either parameter type
     */
    public static boolean isWarningParameterAPI(ParameterAPI param) {
        if ( param instanceof WarningParameterAPI ) return true;
        else return false;
    }

}
