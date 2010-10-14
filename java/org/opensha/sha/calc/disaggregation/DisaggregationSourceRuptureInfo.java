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

package org.opensha.sha.calc.disaggregation;

import org.opensha.sha.earthquake.ProbEqkSource;

/**
 * <p>
 * Title: DisaggregationSourceInfo
 * </p>
 * 
 * <p>
 * Description: Stores the Source info. required for Disaggregation.
 * </p>
 * 
 * @author
 * @version 1.0
 */
public class DisaggregationSourceRuptureInfo {

    private String name;
    private double rate;
    private double eventRate;
    private double mag;
    private double distance;
    private int id;
    private ProbEqkSource source;

    public DisaggregationSourceRuptureInfo(String name, double rate, int id,
            ProbEqkSource source) {

        this.name = name;
        this.rate = rate;
        this.id = id;
        this.source = source;
    }

    public DisaggregationSourceRuptureInfo(String name, double eventRate,
            double rate, int id, double mag, double distance,
            ProbEqkSource source) {
        this.name = name;
        this.rate = rate;
        this.id = id;
        this.eventRate = eventRate;
        this.mag = mag;
        this.distance = distance;
        this.source = source;
    }

    public DisaggregationSourceRuptureInfo(String name, double eventRate,
            double rate, int id, ProbEqkSource source) {

        this.name = name;
        this.rate = rate;
        this.id = id;
        this.eventRate = eventRate;
        this.source = source;
    }

    public int getId() {
        return id;
    }

    public double getRate() {
        return rate;
    }

    public String getName() {
        return name;
    }

    public double getEventRate() {
        return eventRate;
    }

    public double getMag() {
        return mag;
    }

    public double getDistance() {
        return distance;
    }

    public ProbEqkSource getSource() {
        return source;
    }
}
