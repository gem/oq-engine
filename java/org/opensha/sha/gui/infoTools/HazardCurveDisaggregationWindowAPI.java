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

package org.opensha.sha.gui.infoTools;

/**
 * <p>Title: HazardCurveDisaggregationWindowAPI</p>
 *
 * <p>Description: This allows the main application to listen to the events
 * that occur on the HazardCurve Disaggregation window.</p>
 *
 * @author Nitin Gupta, Vipin Gupta, Ned Field
 * @since Nov 28, 2005
 * @version 1.0
 */
public interface HazardCurveDisaggregationWindowAPI {

    /**
     * Returns the Sorted Sources Disaggregation list based on
     * @return String
     */
    public String getSourceDisaggregationInfo();

    /**
     * Returns the Disaggregation plot image webaddr.
     * @return String
     */
    public String getDisaggregationPlot();

    //gets the Parameters info as HTML for which Disaggregation generated.
    public String getMapParametersInfoAsHTML();

}
