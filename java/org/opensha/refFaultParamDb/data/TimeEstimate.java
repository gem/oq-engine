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

package org.opensha.refFaultParamDb.data;
import org.opensha.commons.data.estimate.Estimate;
/**
 * <p>Title: TimeEstimate.java </p>
 * <p>Description: Allows the user to specify a time estimate. This estimate
 * can be a start time estimate or an end time estimate in a time span.</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class TimeEstimate extends TimeAPI {
  private Estimate estimate;
  private String era=AD;
  private boolean isKa; // whether ka is selected or user is providing calendar year estimate
  private int zeroYear;

  public TimeEstimate() {
  }

  public String toString() {
    return "Time Estimate=("+estimate.toString()+")\n"+
        "Era="+era+"\n"+
        "Is Ka="+isKa+"\n"+
        "Zero Year ="+zeroYear+"\n"+
        super.toString();
  }

  public void setForKaUnits(Estimate estimate, int zeroYear) {
    this.zeroYear = zeroYear;
    this.estimate = estimate;
    isKa = true;
  }

  public void setForCalendarYear(Estimate estimate, String era) {
    this.estimate = estimate;
    this.era = era;
    isKa = false;
  }

  public boolean isKaSelected() {
    return isKa;
  }

  public String getEra() {
    return era;
  }

  public Estimate getEstimate() {
    return estimate;
  }

  public int getZeroYear() {
    return zeroYear;
  }
}
