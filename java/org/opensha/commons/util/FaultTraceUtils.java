/**
 * 
 */
package org.opensha.commons.util;

import java.awt.Color;
import java.io.IOException;
import java.util.ArrayList;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;
import org.opensha.commons.geo.LocationVector;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.sha.faultSurface.FaultTrace;
// import org.opensha.sha.gui.controls.PlotColorAndLineTypeSelectorControlPanel;
// import org.opensha.sha.gui.infoTools.GraphiWindowAPI_Impl;
// import org.opensha.sha.gui.infoTools.PlotCurveCharacterstics;

/**
 * <b>Title:</b> EqualLengthSubSectionsTrace
 * <p>
 * 
 * <b>Description:</b> This class provides a number of utilities with respect to
 * fault traces
 * <p>
 * 
 * @author Ned Field and Vipin Gupta
 * @created
 * @version 1.0
 */
public class FaultTraceUtils {

    /**
     * This subdivides the given fault trace into sub-traces that have the
     * length as given (or less). This assumes all fault trace points are at the
     * same depth.
     * 
     * @param faultTrace
     * @param maxSubSectionLen
     *            Maximum length of each subsection
     */
    public static ArrayList<FaultTrace> getEqualLengthSubsectionTraces(
            FaultTrace faultTrace, double maxSubSectionLen) {

        int numSubSections;
        ArrayList<FaultTrace> subSectionTraceList;

        // find the number of sub sections
        double numSubSec = faultTrace.getTraceLength() / maxSubSectionLen;
        if (Math.floor(numSubSec) != numSubSec)
            numSubSections = (int) Math.floor(numSubSec) + 1;
        else
            numSubSections = (int) numSubSec;
        // find the length of each sub section
        double subSecLength = faultTrace.getTraceLength() / numSubSections;
        double distance = 0, distLocs = 0;
        ;
        int numLocs = faultTrace.getNumLocations();
        int index = 0;
        subSectionTraceList = new ArrayList<FaultTrace>();
        Location prevLoc = faultTrace.get(index);
        while (index < numLocs && subSectionTraceList.size() < numSubSections) {
            FaultTrace subSectionTrace =
                    new FaultTrace(faultTrace.getName() + " "
                            + (subSectionTraceList.size() + 1));
            subSectionTraceList.add(subSectionTrace);
            subSectionTrace.add(prevLoc);
            ++index;
            distance = 0;
            while (true && index < faultTrace.getNumLocations()) {
                Location nextLoc = faultTrace.get(index);
                distLocs = LocationUtils.horzDistanceFast(prevLoc, nextLoc);
                distance += distLocs;
                if (distance < subSecLength) { // if sub section length is
                                               // greater than distance, then
                                               // get next point on trace
                    prevLoc = nextLoc;
                    subSectionTrace.add(prevLoc);
                    ++index;
                } else {
                    LocationVector direction =
                            LocationUtils.vector(prevLoc, nextLoc);
                    direction.setHorzDistance(subSecLength
                            - (distance - distLocs));
                    prevLoc = LocationUtils.location(prevLoc, direction);
                    subSectionTrace.add(prevLoc);
                    --index;
                    break;
                }
            }
        }
        return subSectionTraceList;
    }

    /**
     * This resamples the trace into num subsections of equal length (final
     * number of points in trace is num+1). However, note that these subsections
     * of are equal length on the original trace, and that the final subsections
     * will be less than that if there is curvature in the original between the
     * points (e.g., corners getting cut).
     * 
     * @param trace
     * @param num
     *            - number of subsections
     * @return
     */
    public static FaultTrace resampleTrace(FaultTrace trace, int num) {
        double resampInt = trace.getTraceLength() / num;
        FaultTrace resampTrace = new FaultTrace("resampled " + trace.getName());
        resampTrace.add(trace.get(0)); // add the first location
        double remainingLength = resampInt;
        Location lastLoc = trace.get(0);
        int NextLocIndex = 1;
        while (NextLocIndex < trace.size()) {
            Location nextLoc = trace.get(NextLocIndex);
            double length = LocationUtils.linearDistanceFast(lastLoc, nextLoc);
            if (length > remainingLength) {
                // set the point
                LocationVector dir = LocationUtils.vector(lastLoc, nextLoc);
                dir.setHorzDistance(dir.getHorzDistance() * remainingLength
                        / length);
                dir.setVertDistance(dir.getVertDistance() * remainingLength
                        / length);
                Location loc = LocationUtils.location(lastLoc, dir);
                resampTrace.add(loc);
                lastLoc = loc;
                remainingLength = resampInt;
                // Next location stays the same
            } else {
                lastLoc = nextLoc;
                NextLocIndex += 1;
                remainingLength -= length;
            }
        }

        // make sure we got the last one (might be missed because of numerical
        // precision issues?)
        double dist =
                LocationUtils.linearDistanceFast(trace.get(trace.size() - 1),
                        resampTrace.get(resampTrace.size() - 1));
        if (dist > resampInt / 2)
            resampTrace.add(trace.get(trace.size() - 1));

        /* Debugging Stuff **************** */
        /*
         * // write out each to check System.out.println("RESAMPLED"); for(int
         * i=0; i<resampTrace.size(); i++) { Location l =
         * resampTrace.getLocationAt(i);
         * System.out.println(l.getLatitude()+"\t"+
         * l.getLongitude()+"\t"+l.getDepth()); }
         * 
         * System.out.println("ORIGINAL"); for(int i=0; i<trace.size(); i++) {
         * Location l = trace.getLocationAt(i);
         * System.out.println(l.getLatitude(
         * )+"\t"+l.getLongitude()+"\t"+l.getDepth()); }
         * 
         * // write out each to check
         * System.out.println("target resampInt="+resampInt+"\tnum sect="+num);
         * System.out.println("RESAMPLED"); double ave=0, min=Double.MAX_VALUE,
         * max=Double.MIN_VALUE; for(int i=1; i<resampTrace.size(); i++) {
         * double d =
         * LocationUtils.getTotalDistance(resampTrace.getLocationAt(i-1),
         * resampTrace.getLocationAt(i)); ave +=d; if(d<min) min=d; if(d>max)
         * max=d; } ave /= resampTrace.size()-1;
         * System.out.println("ave="+ave+"\tmin="
         * +min+"\tmax="+max+"\tnum pts="+resampTrace.size());
         * 
         * 
         * System.out.println("ORIGINAL"); ave=0; min=Double.MAX_VALUE;
         * max=Double.MIN_VALUE; for(int i=1; i<trace.size(); i++) { double d =
         * LocationUtils.getTotalDistance(trace.getLocationAt(i-1),
         * trace.getLocationAt(i)); ave +=d; if(d<min) min=d; if(d>max) max=d; }
         * ave /= trace.size()-1;
         * System.out.println("ave="+ave+"\tmin="+min+"\tmax="
         * +max+"\tnum pts="+trace.size());
         * 
         * /* End of debugging stuff *******************
         */

        return resampTrace;
    }

    /**
     * This is a quick plot of the traces
     * 
     * @param traces
     */
    public static void plotTraces(ArrayList<FaultTrace> traces) {
        throw new RuntimeException(
                "This doesn't work because our functions will reorder x-axis values to monotonically increase (and remove duplicates - someone should fix this)");
        /*
         * ArrayList funcs = new ArrayList(); for(int t=0; t<traces.size();t++)
         * { FaultTrace trace = traces.get(t); ArbitrarilyDiscretizedFunc
         * traceFunc = new ArbitrarilyDiscretizedFunc(); for(int
         * i=0;i<trace.size();i++) { Location loc= trace.getLocationAt(i);
         * traceFunc.set(loc.getLongitude(), loc.getLatitude()); }
         * traceFunc.setName(trace.getName()); funcs.add(traceFunc); }
         * GraphiWindowAPI_Impl graph = new GraphiWindowAPI_Impl(funcs, "");
         * ArrayList<PlotCurveCharacterstics> plotChars = new
         * ArrayList<PlotCurveCharacterstics>(); /* plotChars.add(new
         * PlotCurveCharacterstics
         * (PlotColorAndLineTypeSelectorControlPanel.FILLED_CIRCLES,
         * Color.BLACK, 4)); plotChars.add(new
         * PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel
         * .SOLID_LINE, Color.BLUE, 2)); plotChars.add(new
         * PlotCurveCharacterstics
         * (PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE, Color.BLUE,
         * 1)); plotChars.add(new
         * PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel
         * .SOLID_LINE, Color.BLUE, 1)); graph.setPlottingFeatures(plotChars);
         * graph.setX_AxisLabel("Longitude"); graph.setY_AxisLabel("Latitude");
         * graph.setTickLabelFontSize(12);
         * graph.setAxisAndTickLabelFontSize(14); /* // to save files if(dirName
         * != null) { String filename = ROOT_PATH+dirName+"/slipRates"; try {
         * graph.saveAsPDF(filename+".pdf"); graph.saveAsPNG(filename+".png"); }
         * catch (IOException e) { // TODO Auto-generated catch block
         * e.printStackTrace(); } }
         */

    }

}
