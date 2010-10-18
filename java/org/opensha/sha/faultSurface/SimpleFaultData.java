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

import java.util.ArrayList;

import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;

// Fix - Needs more comments

/**
 * <b>Title:</b> SimpleFaultData
 * <p>
 * <b>Description:</b> This object contains "simple fault data". This does not
 * check whether the values make sense (e.g., it doesn not check that
 * 0<aveDip<90) because these will get checked in the classes that use this data
 * (and we don't want duplicate these checks).
 * <p>
 * 
 * 
 * @author Sid Hellman, Steven W. Rock, Ned Field
 * @created February 26, 2002
 * @version 1.0
 */

public class SimpleFaultData implements java.io.Serializable {

    /**
	 * 
	 */
    private static final long serialVersionUID = 1L;
    /**
     * Description of the Field
     */
    private double upperSeismogenicDepth;
    private double lowerSeismogenicDepth;
    private double aveDip;
    private double aveDipDir = Double.NaN;
    private FaultTrace faultTrace;

    protected final static String C = "SimpleFaultData";

    public SimpleFaultData() {
    }

    public SimpleFaultData(double aveDip, double lowerSeisDepth,
            double upperSeisDepth, FaultTrace faultTrace) {

        this.aveDip = aveDip;
        this.lowerSeismogenicDepth = lowerSeisDepth;
        this.upperSeismogenicDepth = upperSeisDepth;
        this.faultTrace = faultTrace;

    }

    public SimpleFaultData(double aveDip, double lowerSeisDepth,
            double upperSeisDepth, FaultTrace faultTrace, double aveDipDir) {

        this.aveDip = aveDip;
        this.lowerSeismogenicDepth = lowerSeisDepth;
        this.upperSeismogenicDepth = upperSeisDepth;
        this.faultTrace = faultTrace;
        this.aveDipDir = aveDipDir;

    }

    public void setUpperSeismogenicDepth(double upperSeismogenicDepth) {
        this.upperSeismogenicDepth = upperSeismogenicDepth;
    }

    public double getUpperSeismogenicDepth() {
        return upperSeismogenicDepth;
    }

    public void setLowerSeismogenicDepth(double lowerSeismogenicDepth) {
        this.lowerSeismogenicDepth = lowerSeismogenicDepth;
    }

    public double getLowerSeismogenicDepth() {
        return lowerSeismogenicDepth;
    }

    public void setAveDip(double aveDip) {
        this.aveDip = aveDip;
    }

    public double getAveDip() {
        return aveDip;
    }

    public void setAveDipDir(double aveDipDir) {
        this.aveDipDir = aveDipDir;
    }

    public double getAveDipDir() {
        return aveDipDir;
    }

    public void setFaultTrace(FaultTrace faultTrace) {
        this.faultTrace = faultTrace;
    }

    public FaultTrace getFaultTrace() {
        return faultTrace;
    }

    /**
     * Get a single combined simpleFaultData from multiple SimpleFaultData
     * 
     * @param simpleFaultDataList
     * @return
     */
    public static SimpleFaultData getCombinedSimpleFaultData(
            ArrayList<SimpleFaultData> simpleFaultDataList) {
        if (simpleFaultDataList.size() == 1) {
            return simpleFaultDataList.get(0);
        }
        // correctly order the first fault section
        FaultTrace faultTrace1 = simpleFaultDataList.get(0).getFaultTrace();
        FaultTrace faultTrace2 = simpleFaultDataList.get(1).getFaultTrace();
        double minDist = Double.MAX_VALUE, distance;
        boolean reverse = false;
        ArrayList<Integer> reversedIndices = new ArrayList<Integer>();
        distance =
                LocationUtils.horzDistance(faultTrace1.get(0),
                        faultTrace2.get(0));
        if (distance < minDist) {
            minDist = distance;
            reverse = true;
        }
        distance =
                LocationUtils.horzDistance(faultTrace1.get(0),
                        faultTrace2.get(faultTrace2.getNumLocations() - 1));
        if (distance < minDist) {
            minDist = distance;
            reverse = true;
        }
        distance =
                LocationUtils.horzDistance(
                        faultTrace1.get(faultTrace1.getNumLocations() - 1),
                        faultTrace2.get(0));
        if (distance < minDist) {
            minDist = distance;
            reverse = false;
        }
        distance =
                LocationUtils.horzDistance(
                        faultTrace1.get(faultTrace1.getNumLocations() - 1),
                        faultTrace2.get(faultTrace2.getNumLocations() - 1));
        if (distance < minDist) {
            minDist = distance;
            reverse = false;
        }
        if (reverse) {
            reversedIndices.add(0);
            faultTrace1.reverse();
            if (simpleFaultDataList.get(0).getAveDip() != 90)
                simpleFaultDataList.get(0).setAveDip(
                        -simpleFaultDataList.get(0).getAveDip());
        }

        // Calculate Upper Seis Depth, Lower Seis Depth and Dip
        double combinedDip = 0, combinedUpperSeisDepth = 0, totArea = 0, totLength =
                0;
        FaultTrace combinedFaultTrace =
                new FaultTrace("Combined Fault Sections");
        int num = simpleFaultDataList.size();

        for (int i = 0; i < num; ++i) {
            FaultTrace faultTrace = simpleFaultDataList.get(i).getFaultTrace();
            int numLocations = faultTrace.getNumLocations();
            if (i > 0) { // check the ordering of point in this fault trace
                FaultTrace prevFaultTrace =
                        simpleFaultDataList.get(i - 1).getFaultTrace();
                Location lastLoc =
                        prevFaultTrace
                                .get(prevFaultTrace.getNumLocations() - 1);
                double distance1 =
                        LocationUtils.horzDistance(lastLoc, faultTrace.get(0));
                double distance2 =
                        LocationUtils.horzDistance(lastLoc, faultTrace
                                .get(faultTrace.getNumLocations() - 1));
                if (distance2 < distance1) { // reverse this fault trace
                    faultTrace.reverse();
                    reversedIndices.add(i);
                    if (simpleFaultDataList.get(i).getAveDip() != 90)
                        simpleFaultDataList.get(i).setAveDip(
                                -simpleFaultDataList.get(i).getAveDip());
                }
                // remove any loc that is within 1km of its neighbor
                // as per Ned's email on Feb 7, 2007 at 5:53 AM
                if (distance2 > 1 && distance1 > 1)
                    combinedFaultTrace.add(faultTrace.get(0).clone());
                // add the fault Trace locations to combined trace
                for (int locIndex = 1; locIndex < numLocations; ++locIndex)
                    combinedFaultTrace.add(faultTrace.get(locIndex).clone());

            } else { // if this is first fault section, add all points in fault
                     // trace
            // add the fault Trace locations to combined trace
                for (int locIndex = 0; locIndex < numLocations; ++locIndex)
                    combinedFaultTrace.add(faultTrace.get(locIndex).clone());
            }

            double length = faultTrace.getTraceLength();
            double dip = simpleFaultDataList.get(i).getAveDip();
            double area =
                    Math.abs(length
                            * (simpleFaultDataList.get(i)
                                    .getLowerSeismogenicDepth() - simpleFaultDataList
                                    .get(i).getUpperSeismogenicDepth())
                            / Math.sin(dip * Math.PI / 180));
            totLength += length;
            totArea += area;
            combinedUpperSeisDepth +=
                    (area * simpleFaultDataList.get(i)
                            .getUpperSeismogenicDepth());
            if (dip > 0)
                combinedDip += (area * dip);
            else
                combinedDip += (area * (dip + 180));
            // System.out.println(dip+","+area+","+combinedDip+","+totArea);
        }

        // Revert back the fault traces that were reversed
        for (int i = 0; i < reversedIndices.size(); ++i) {
            int index = reversedIndices.get(i);
            simpleFaultDataList.get(index).getFaultTrace().reverse();
            if (simpleFaultDataList.get(index).getAveDip() != 90)
                simpleFaultDataList.get(index).setAveDip(
                        -simpleFaultDataList.get(index).getAveDip());
        }

        double dip = combinedDip / totArea;

        // double tolerance = 1e-6;
        // if(dip-90 < tolerance) dip=90;
        // if Dip<0, reverse the trace points to follow Aki and Richards
        // convention
        if (dip > 90) {
            dip = (180 - dip);
            combinedFaultTrace.reverse();
        }

        // System.out.println(dip);

        SimpleFaultData simpleFaultData = new SimpleFaultData();
        simpleFaultData.setAveDip(dip);
        double upperSeismogenicDepth = combinedUpperSeisDepth / totArea;
        simpleFaultData.setUpperSeismogenicDepth(upperSeismogenicDepth);

        for (int i = 0; i < combinedFaultTrace.getNumLocations(); ++i) {
            // combinedFaultTrace.getLocationAt(i).setDepth(
            // simpleFaultData.getUpperSeismogenicDepth());
            // replace trace Locations with depth corrected values
            Location old = combinedFaultTrace.get(i);
            Location loc =
                    new Location(old.getLatitude(), old.getLongitude(),
                            upperSeismogenicDepth);
            combinedFaultTrace.set(i, loc);
        }
        simpleFaultData.setLowerSeismogenicDepth((totArea / totLength)
                * Math.sin(dip * Math.PI / 180) + upperSeismogenicDepth);
        // System.out.println(simpleFaultData.getLowerSeismogenicDepth());
        simpleFaultData.setFaultTrace(combinedFaultTrace);
        return simpleFaultData;

    }

    private final static String TAB = "  ";

    public String toString() {

        StringBuffer b = new StringBuffer(C);
        b.append('\n');
        b.append(TAB + "Ave. Dip = " + aveDip);
        b.append(TAB + "Upper Seismogenic Depth = " + upperSeismogenicDepth);
        b.append(TAB + "Lower Seismogenic Depth = " + lowerSeismogenicDepth);
        b.append(TAB + "Fault Trace = " + faultTrace.toString());
        return b.toString();

    }

    /**
     * Clones the SimpleFaultData. Please note that FaultTrace is not completely
     * cloned
     */
    public SimpleFaultData clone() {
        SimpleFaultData simpleFaultData = new SimpleFaultData();
        simpleFaultData.setUpperSeismogenicDepth(upperSeismogenicDepth);
        simpleFaultData.setLowerSeismogenicDepth(lowerSeismogenicDepth);
        simpleFaultData.setAveDip(aveDip);
        simpleFaultData.setFaultTrace(faultTrace);
        return simpleFaultData;
    }

}
