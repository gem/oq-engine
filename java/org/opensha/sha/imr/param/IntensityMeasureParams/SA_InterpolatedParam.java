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
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.WarningDoubleParameter;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodInterpolatedParam;

/**
 * This constitutes is for the natural-log Spectral Acceleration intensity
 * measure parameter. It requires being given a PeriodParam and DampingParam, as
 * these are the parameters that SA depends upon. See constructors for info on
 * editability and default values.
 * 
 * @author field
 * 
 */
public class SA_InterpolatedParam extends WarningDoubleParameter {

    public final static String NAME = "SA Interpolated";
    public final static String UNITS = "g";
    public final static String INFO = "Response Spectral Acceleration";
    protected final static Double MIN = new Double(Math.log(Double.MIN_VALUE));
    protected final static Double MAX = new Double(Double.MAX_VALUE);
    protected final static Double DEFAULT_WARN_MIN = new Double(
            Math.log(Double.MIN_VALUE));
    protected final static Double DEFAULT_WARN_MAX = new Double(Math.log(3.0));

    /**
     * This uses the DEFAULT_WARN_MIN and DEFAULT_WARN_MAX fields to set the
     * warning constraint, and sets the default as Math.log(0.5) (the natural
     * log of 0.5). The parameter is left as non editable
     */
    public SA_InterpolatedParam(PeriodInterpolatedParam periodInterpPeram,
            DampingParam dampingParam) {
        super(NAME, new DoubleConstraint(MIN, MAX), UNITS);
        getConstraint().setNonEditable();
        this.setInfo(INFO);
        DoubleConstraint warn2 =
                new DoubleConstraint(DEFAULT_WARN_MIN, DEFAULT_WARN_MAX);
        warn2.setNonEditable();
        setWarningConstraint(warn2);
        addIndependentParameter(periodInterpPeram);
        addIndependentParameter(dampingParam);
        setDefaultValue(0.5);
        setNonEditable();
    }

    /**
     * Helper method to quickly get the period param
     * 
     * @return
     */
    public PeriodInterpolatedParam getPeriodInterpolatedParam() {
        return (PeriodInterpolatedParam) this
                .getIndependentParameter(PeriodInterpolatedParam.NAME);
    }

    /**
     * Helper method to quickly get the damping param
     * 
     * @return
     */
    public DampingParam getDampingParam() {
        return (DampingParam) this.getIndependentParameter(DampingParam.NAME);
    }

    public static void
            setPeriodInSA_Param(ParameterAPI<?> param, double period) {
        SA_Param saParam = (SA_Param) param;
        saParam.getPeriodParam().setValue(period);
    }

}
