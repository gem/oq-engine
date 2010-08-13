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

package org.opensha.sha.imr.param.PropagationEffectParams;

import org.opensha.commons.data.Site;
import org.opensha.sha.earthquake.EqkRupture;

/**
* <p>Title: PropagationEffectParameterAPI</p>
* <p>Description: Interface that PropagationEffect
* Parameters must implement. </p>
*
* Propagation Effect Parameters are a specific subclass
* of parameters that deal with earthquake probability
* variables. Their defining characteristics are that
* they take two independent variables, a Site and ProbEqkRupture
* and then can calculate their own value. Their use is distinct
* from regular parameters in that setValue() is typically
* not called. That is the only way to set standard
* parameters. <p>
*
* This API defines several gatValue() functions that take
* different combinations of Site and ProbEqkRupture that
* will make this parameter recalculate itself, returning the
* new value. <p>
*
* @author Steven W. Rock
* @version 1.0
*/
public interface PropagationEffectParameterAPI {


     /** Sets the independent variables (Site and eqkRupture) then calculates and returns the value */
    public Object getValue(EqkRupture eqkRupture, Site site);

    /** Sets the site and recalculates the value. The ProbEqkRupture must have already been set */
    public Object getValue(Site site);

    /** Sets the EqkRupture and recalculates the value. The Site must have already been set */
    public Object getValue(EqkRupture eqkRupture);

    /** Sets the independent variables (Site and EqkRupture) then calculates the value */
    public void setValue(EqkRupture eqkRupture, Site site);

    /** The EqkRupture and Site must have already been set */
    public Object getValue();

    /** Sets the Site and the value is recalculated */
    public void setSite(Site site);
    /** Returns the Site that set this value */
    public Site getSite();

    /** Sets the EqkRupture associated with this Parameter, and the value is recalculated */
    public void setEqkRupture(EqkRupture eqkRupture);
    /** Returns the EqkRupture that set this value */
    public EqkRupture getEqkRupture();

    /**
     * Standard Java function. Creates a copy of this class instance
     * so originaly can not be modified
     */
    public Object clone();


}
