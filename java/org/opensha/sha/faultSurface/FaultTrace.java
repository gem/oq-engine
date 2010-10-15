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

package org.opensha.sha.faultSurface;

import java.util.Iterator;

import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.commons.util.FaultTraceUtils;

// Fix - Needs more comments

/**
 * <b>Title:</b> FaultTrace
 * <p>
 * 
 * <b>Description:</b> This simply contains a vector (or array) of Location
 * objects representing the top trace of a fault (with non-zero depth if it
 * buried).
 * <p>
 * 
 * @author Sid Hellman, Steven W. Rock
 * @created February 26, 2002
 * @version 1.0
 */

public class FaultTrace extends LocationList implements NamedObjectAPI {

    /**
	 * 
	 */
    private static final long serialVersionUID = 1L;
    /**
     * Fault name field
     */
    private String faultName;

    public FaultTrace(String faultName) {
        super();
        this.faultName = faultName;

    }

    public void setName(String faultName) {
        this.faultName = faultName;
    }

    public String getName() {
        return faultName;
    }

    public int getNumLocations() {
        return size();
    }

    /**
     * This returns the total fault-trace length in km
     * 
     * @return
     */
    public double getTraceLength() {
        double totLength = 0;
        Iterator<Location> it = iterator();
        Location lastLoc = it.next();
        Location loc = null;
        while (it.hasNext()) {
            loc = it.next();
            totLength += LocationUtils.horzDistance(lastLoc, loc);
            lastLoc = loc;
        }
        return totLength;
    }

    /**
     * This returns the average strike (weight average by length)
     * 
     * @return
     */
    public double getAveStrike() {
        double totLength = 0, length = 0;
        Iterator<Location> it = iterator();
        Location lastLoc = it.next();
        Location loc = null;
        double aveStrike = 0;
        while (it.hasNext()) {
            loc = it.next();
            length = LocationUtils.horzDistance(lastLoc, loc);
            aveStrike += LocationUtils.azimuth(lastLoc, loc) * length;
            totLength += length;
            lastLoc = loc;
        }
        throw new RuntimeException(
                "This needs to be fixed for case where aximuths that cross the north direction (e.g., values of 10 & 350 average to 180");
        // return aveStrike/totLength;
    }

    /**
     * This returns the strike direction (between -180 and 180 degrees) defined
     * by the first and last points only
     * 
     * @return
     */
    public double getStrikeDirection() {
        return LocationUtils.azimuth(get(0), get(size() - 1));
    }

    /**
     * This returns the change in strike direction in going from this trace to
     * the one passed in (input_trace_azimuth-this_azimuth), where this accounts
     * the change in sign for azimuths at 180 degrees. The output is between
     * -180 and 180 degress).
     * 
     * @return
     */
    public double getStrikeDirectionDifference(FaultTrace trace) {
        double diff = trace.getStrikeDirection() - this.getStrikeDirection();
        if (diff > 180)
            return diff - 360;
        else if (diff < -180)
            return diff + 360;
        else
            return diff;
    }

    /*
     * Calculates minimum distance of this faultTrace from the user provided
     * fault trace, where the latter is resampled at discrInterval (km) for
     * computing distances. Returns the distance in km.
     * 
     * @param faultTrace FaultTrace from where distance needs to be calculated
     * 
     * @param discrInterval resampling interval (km)
     */
    public double getMinDistance(FaultTrace faultTrace, double discrInterval) {
        // calculate the minimum fault trace distance
        double minFaultTraceDist = Double.POSITIVE_INFINITY;
        double dist;
        int num = (int) (faultTrace.getTraceLength() / discrInterval) + 1;
        FaultTrace discrFaultTrace =
                FaultTraceUtils.resampleTrace(faultTrace, num);
        for (int i = 0; i < discrFaultTrace.getNumLocations(); ++i) {
            dist = minDistToLine(discrFaultTrace.get(i));
            if (dist < minFaultTraceDist)
                minFaultTraceDist = dist;
        }
        return minFaultTraceDist;
    }

    private final static String TAB = "  ";

    public String toString() {

        StringBuffer b = new StringBuffer("FaultTrace");
        b.append('\n');
        b.append(TAB + "Name = " + faultName);

        b.append(super.toString());
        return b.toString();

    }

    public FaultTrace clone() {
        FaultTrace trace = new FaultTrace(this.getName());
        for (Location loc : this) {
            trace.add(loc);
        }
        return trace;
    }

}
