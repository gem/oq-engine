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

package org.opensha.sha.earthquake;

import java.io.Serializable;

/**
 * <p>
 * Title: FocalMechanism
 * </p>
 * 
 * <p>
 * Description: This class allows to set the Focal Mechanism
 * </p>
 * 
 * @author Nitin Gupta
 * @version 1.0
 */
public class FocalMechanism implements Serializable {

    /**
	 * 
	 */
    private static final long serialVersionUID = 1L;

    private double strike, dip, rake;

    /**
     * Class default constructor
     */
    public FocalMechanism() {
    }

    /**
     * 
     * @param strike
     *            double
     * @param dip
     *            double
     * @param rake
     *            double
     */
    public FocalMechanism(double strike, double dip, double rake) {
        this.strike = strike;
        this.rake = rake;
        this.dip = dip;
    }

    public double getDip() {
        return dip;
    }

    public double getRake() {
        return rake;
    }

    public double getStrike() {
        return strike;
    }

    public void setDip(double dip) {
        this.dip = dip;
    }

    public void setRake(double rake) {
        this.rake = rake;
    }

    public void setStrike(double strike) {
        this.strike = strike;
    }

    public void setFocalMechanism(double dip, double rake, double strike) {
        this.dip = dip;
        this.rake = rake;
        this.strike = strike;
    }

    public FocalMechanism copy() {
        return new FocalMechanism(strike, dip, rake);
    }

}
