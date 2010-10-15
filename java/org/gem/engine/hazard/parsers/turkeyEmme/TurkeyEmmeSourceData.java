package org.gem.engine.hazard.parsers.turkeyEmme;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;

import org.gem.engine.hazard.parsers.GemFileParser;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMAreaSourceData;

import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.geo.Region;
import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.earthquake.griddedForecast.MagFreqDistsForFocalMechs;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMFaultSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

/**
 * <p>
 * <b>Title:</b> Turkey ERF
 * <p>
 * 
 * <p>
 * <b>Description:</b> This class implements an ERF using the information parsed
 * from the files that Koeri made available within the EMME project.
 * </p>
 * 
 * @author M. Pagani
 * @version 1.0
 * @created November, 2009
 * 
 */

public class TurkeyEmmeSourceData extends GemFileParser {

    private boolean useAreas = false;
    private boolean useFaults = true;
    private static boolean INFO = true;

    /**
     * ERF constructor
     * 
     * @param sourceData
     * @param zoneGeom
     */
    public TurkeyEmmeSourceData(TurkeyReadSourceData sourceData,
            TurkeyReadGMLFileSourceZones zoneGeom, TurkeyReadGMLFileFaults flt) {

        // Array list with all source data parsed
        ArrayList<GEMSourceData> srcList = new ArrayList<GEMSourceData>();
        // MAGNITUDE minimum and maximum rounded values
        double mMin, mMax;
        // MAGNITUDE number of intervals
        int mNum;
        // MAGNITUDE magnitude width
        double mWdt = 0.1;
        // Parameters of the GR relationship
        double aGR, bGR;
        // Cumulative total rate
        double totCumRate;
        //
        TectonicRegionType trtype = null;
        // Fault dip, rake
        double dip = 90.0, rake = 0.0;

        // Flag controlling the use of faults in the calculations
        if (flt != null) {
            useFaults = true;
        }
        // Flag controlling the use of area sources in the calculations
        if (zoneGeom != null) {
            useAreas = true;
        }

        // AREA sources
        if (useAreas) {
            Iterator<LocationList> iter = zoneGeom.getCoords().iterator();
            int srcCnt = 0;
            while (iter.hasNext()) {

                // Info
                if (INFO)
                    System.out.printf("Source: %d (name: %s)\n", srcCnt,
                            zoneGeom.getName().get(srcCnt));

                // Get Source code
                String code = zoneGeom.getCode().get(srcCnt);

                // Round magnitude interval extremes
                mMax = Math.ceil(sourceData.mMax.get(code) / mWdt) * mWdt;
                mMin = Math.floor(sourceData.mMin.get(code) / mWdt) * mWdt;

                // GR parameters
                aGR = sourceData.aGR.get(code);
                bGR = sourceData.bGR.get(code);

                // Compute the number of magnitude intervals
                mNum = (int) Math.round((mMax - mMin) / mWdt);
                if (INFO) {
                    System.out.printf(
                            "   mMin............................: %-5.2f \n",
                            mMin);
                    System.out.printf(
                            "   mMax............................: %-5.2f \n",
                            mMax);
                    System.out.printf(
                            "   aGR.............................: %-5.2f \n",
                            aGR);
                    System.out.printf(
                            "   bGR.............................: %-5.2f \n",
                            bGR);
                }

                // Compute the total cumulative rate
                totCumRate =
                        Math.pow(10, aGR - bGR * mMin)
                                - Math.pow(10, aGR - bGR * mMax);
                // mNum = (int) Math.round((mMax-mMin)/mWdt+1);
                mNum =
                        (int) Math
                                .round(((mMax - mWdt / 2) - (mMin + mWdt / 2))
                                        / mWdt + 1);
                if (INFO)
                    System.out.printf("   Tot Cum Rate.: %10.8f [ev/yr]\n",
                            totCumRate);

                // Parameters: bGR, Total occurrence rate, mMin, mMax, Number of
                // M extremes
                GutenbergRichterMagFreqDist distGR =
                        new GutenbergRichterMagFreqDist(bGR, totCumRate, mMin
                                + mWdt / 2, mMax - mWdt / 2, mNum);

                if (INFO) {
                    for (int i = 0; i < distGR.getNum(); i++) {
                        System.out.printf("   mag %5.2f rte: %6.2f\n",
                                distGR.getX(i), distGR.getY(i));
                    }
                }

                // Create a list with the values for the top of rupture
                ArbitrarilyDiscretizedFunc topRupDist =
                        new ArbitrarilyDiscretizedFunc();
                double dm = (mMax - mMin + mWdt) / (mNum + 1);
                double tmpM = mMin + mWdt / 2;
                // NOTE: we assume top of rupture == 0 for all the magnitude
                // (THIS IS A VERY
                // STRONG ASSUMPION keep at the moment)
                for (int i = 0; i < mNum; i++) {
                    topRupDist.set(tmpM, 0.0);
                    tmpM += dm;
                }

                // Create a MFD array
                IncrementalMagFreqDist[] mfdArr = new IncrementalMagFreqDist[1];
                mfdArr[0] = distGR;

                // Get a source geometry (i.e. a LocationList) and create the
                // evenly gridded region
                LocationList locl = iter.next();
                Region rgg = new Region(locl, null);

                // ArrayList of mfds and focal mechanisms

                FocalMechanism[] focMechArr = new FocalMechanism[1];
                focMechArr[0] = new FocalMechanism(90, 90, 45);

                // Create Area source data container
                MagFreqDistsForFocalMechs mfdffm =
                        new MagFreqDistsForFocalMechs(mfdArr, focMechArr);

                // public GEMAreaSourceData(String id, String name,
                // TectonicRegionType tectReg,
                // Region reg, MagFreqDistsForFocalMechs magfreqDistFocMech,
                // ArbitrarilyDiscretizedFunc aveRupTopVsMag, double
                // aveHypoDepth){

                GEMAreaSourceData asrc =
                        new GEMAreaSourceData(zoneGeom.getCode().get(srcCnt),
                                zoneGeom.getCode().get(srcCnt),
                                TectonicRegionType.ACTIVE_SHALLOW, rgg, mfdffm,
                                topRupDist, 5.0);

                // Update the GEMInputToERF object
                srcList.add(asrc);

                // Update counter
                srcCnt++;
            }

            if (INFO) {
                System.out.printf("   Area sources added .............: %d \n",
                        srcCnt);
            }
        }

        if (useFaults) {
            // System.out.println(flt.getCoords().size()+" "+flt.getCode().size());

            // FAULT sources
            Iterator<LocationList> iterF = flt.getCoords().iterator();
            int cntF = 0;
            while (iterF.hasNext()) {

                // Get Source code
                String code = flt.getCode().get(cntF);

                // Info
                System.out.printf("Source (%d - %s)", cntF + 1, code);
                System.out.println("        " + flt.getName().get(cntF));

                // Get a source geometry (i.e. a LocationList) and create the
                // fault trace
                LocationList locl = iterF.next();
                FaultTrace fltTr = new FaultTrace(flt.getName().get(cntF));
                Iterator<Location> iii = locl.iterator();
                while (iii.hasNext()) {
                    Location loc = iii.next();
                    fltTr.add(loc);
                }

                // GR distribution
                if (sourceData.mMax.containsKey(code)) {
                    mMax = Math.ceil(sourceData.mMax.get(code) / mWdt) * mWdt;
                } else {
                    System.out.println("Missing bGR for the Source " + code);
                    cntF++;
                    continue;
                }
                mMin = Math.floor(sourceData.mMin.get(code) / mWdt) * mWdt;

                // Calculate the number of magnitude intervals
                mNum = (int) Math.round((mMax - mMin) / mWdt + 1);

                // Parameters of the GR relationship
                aGR = sourceData.aGR.get(code);
                bGR = sourceData.bGR.get(code);

                // Calculate the total cumulative rate
                double cumTotRate =
                        Math.pow(10, aGR - bGR * mMin)
                                - Math.pow(10, aGR - bGR * mMax);

                if (INFO) {
                    System.out.printf(
                            "   mMin............................: %-5.2f \n",
                            mMin);
                    System.out.printf(
                            "   mMax............................: %-5.2f \n",
                            mMax);
                    System.out.printf(
                            "   aGR.............................: %-5.2f \n",
                            aGR);
                    System.out.printf(
                            "   bGR.............................: %-5.2f \n",
                            bGR);
                }

                // Parameters: bGR, Total occurrence rate, mMin, mMax, Number of
                // M extremes
                GutenbergRichterMagFreqDist magfrq =
                        new GutenbergRichterMagFreqDist(bGR, cumTotRate, mMin,
                                mMax, mNum);

                // NOTE by now we assume values of dip and rake ... they're
                // undefined
                dip = 90.0;
                rake = 45.0;

                // Create a GEM fault source
                GEMFaultSourceData fsrc =
                        new GEMFaultSourceData(flt.getCode().get(cntF), flt
                                .getName().get(cntF),
                                TectonicRegionType.ACTIVE_SHALLOW, magfrq,
                                fltTr, dip, rake, 10.0, 0.0, true);

                // Update the GEMInputToERF object
                srcList.add(fsrc);

                // Increment the fault counter
                cntF++;

            }
        } // Use faults

        // Array list with all source data parsed
        ArrayList<GEMSourceData> finalList = new ArrayList<GEMSourceData>();

        // Post-processing faults - Divide the seismicity over the segments
        HashMap<String, Double> faultSystemLenght =
                new HashMap<String, Double>();
        for (GEMSourceData src : srcList) {
            if (src instanceof GEMFaultSourceData) {
                GEMFaultSourceData fault = (GEMFaultSourceData) src;
                if (faultSystemLenght.containsKey(fault.getID())) {
                    faultSystemLenght.put(src.getID(),
                            faultSystemLenght.get(src.getID())
                                    + fault.getTrace().getTraceLength());
                } else {
                    faultSystemLenght.put(src.getID(), fault.getTrace()
                            .getTraceLength());
                }
            }
        }

        // Scaling occurrence rates depending on the length of the segment
        int idx = 0;
        for (GEMSourceData src : srcList) {
            if (src instanceof GEMFaultSourceData) {
                GEMFaultSourceData fault = (GEMFaultSourceData) src;
                double ratio =
                        fault.getTrace().getTraceLength()
                                / faultSystemLenght.get(fault.getID());
                System.out.printf(" %s %-40s ratio %5.2f\n", fault.getID(),
                        fault.getName(), ratio);
                IncrementalMagFreqDist mfd = fault.getMfd();
                mfd.scaleToTotalMomentRate(mfd.getTotalMomentRate() * ratio);

                // fault.setMfd(mfd);
                // srcList.set(idx,fault);

                finalList.add(new GEMFaultSourceData(fault.getID(), fault
                        .getName(), fault.getTectReg(), mfd, fault.getTrace(),
                        fault.getDip(), fault.getRake(), fault
                                .getSeismDepthLow(), fault.getSeismDepthUpp(),
                        true));

            } else {
                finalList.add(src);
            }
            idx++;
        }

        //
        this.setList(finalList);

    }
}
