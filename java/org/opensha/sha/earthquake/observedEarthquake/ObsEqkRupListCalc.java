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

package org.opensha.sha.earthquake.observedEarthquake;

import java.util.Collections;

import org.opensha.sha.earthquake.EqkRuptureMagComparator;
import org.opensha.sha.magdist.IncrementalMagFreqDist;

/**
 * <p>Title: ObsEqkRupListCalc</p>
 *
 * <p>Description: This class provides users with capability to operate on
 * Observed Eqk Rupture list. all the functions defined in this class are static,
 * so user does not have to create the object of the class to call the method.
 * </p>
 *
 * @author Nitin Gupta
 * @version 1.0
 */
public class ObsEqkRupListCalc {

    /**
     * Returns the Mean Mag for the given list of Events.
     * @param obsEqkEvents ObsEqkRupList list of Observed Events
     * @return double meean Magnitude
     */
    public static double getMeanMag(ObsEqkRupList obsEqkEvents){
    int size = obsEqkEvents.size();
    double mag =0;
    for(int i=0;i<size;++i)
      mag += obsEqkEvents.getObsEqkRuptureAt(i).getMag();
    return (mag/size);
  }

  /**
   * Returns the minimum magnitude for the observed Eqk Rupture events.
   * @param obsEqkEvents ObsEqkRupList list of observed eqk events
   * @return double min-mag
   */
  public static double getMinMag(ObsEqkRupList obsEqkEvents) {
    Double minMag = (Double)Collections.min(obsEqkEvents.getObsEqkRupEventList(),new EqkRuptureMagComparator());
    return minMag.doubleValue();
  }


  /**
   * Returns the maximum magnitude for the observed Eqk Rupture events.
   * @param obsEqkEvents ObsEqkRupList list of observed eqk events
   * @return double max-mag
   */
  public static double getMaxMag(ObsEqkRupList obsEqkEvents) {
    Double maxMag = (Double)Collections.max(obsEqkEvents.getObsEqkRupEventList(),new EqkRuptureMagComparator());
    return maxMag.doubleValue();
  }

  /**
   * Returns the difference in origin time of Observed Eqk events in chronological
   * order. Difference is in the millisec.
   * @param obsEqkEvents ObsEqkRupList Observed Eqk Event List
   * @return long[] returns the long array of difference in time between all
   * the observed events after ordering them based on their origin time.
   *
   * Note : Returns array of long  which is the differnce in the origin time
   * of 2 events after they are converted to milliseconds.
   */
  public static long[] getInterEventTimes(ObsEqkRupList obsEqkEvents) {

    obsEqkEvents.sortObsEqkRupListByOriginTime();
    int size = obsEqkEvents.size();
    long[] interEventTimes = new long[size-1];

    for(int i=0;i<size -1;++i){
      long time = obsEqkEvents.getObsEqkRuptureAt(i+1).getOriginTime().getTimeInMillis() -
          obsEqkEvents.getObsEqkRuptureAt(i).getOriginTime().getTimeInMillis();
      interEventTimes[i] = time;
    }

    return interEventTimes;
  }

  public static IncrementalMagFreqDist getMagFreqDist(ObsEqkRupList obsEqkEvents) {
    return null;
  }

  public static IncrementalMagFreqDist getMagNumDist(ObsEqkRupList obsEqkEvents) {
    return null;
  }











}
