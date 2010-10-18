package org.gem.engine.hazard.parsers.northernEurasia;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.gem.engine.hazard.parsers.GemFileParser;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.geo.Region;
import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.earthquake.griddedForecast.MagFreqDistsForFocalMechs;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMAreaSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMFaultSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

/**
 * <p>
 * Title: NorthernEurasiaFileReader01
 * </p>
 * </p> This creates an array of source data containing the information parsed
 * from the GSHAP - Northern Eurasia model. The source typologies contained in
 * the original input file are: area sources and fault sources. The
 * seismotectonic regime is not specified (should read more carefully the paper
 * on the Annali di Geofisica) nor the fault mechanism (for this reason and due
 * to the lack of time we set for all the sources a rake value = -90 i.e. we
 * assume that the mechanism is always normal). The description of seismicity is
 * very rough in the original file (usually they use a bin width equal to 0.5
 * units of magnitude). In order to create a discrete MFD with an higher
 * resolution (bins with a smaller width) we calculate the total occurrence rate
 * for mmin < m < max and we derive aGR assuming bGR=1.0.
 * <p>
 * Checks:
 * <ul>
 * <li>Rates read from file
 * </ul>
 * </p>
 * 
 * @author marcop
 * 
 */
public class NorthernEurasiaFileReader01 extends GemFileParser {

    private ArrayList<GEMSourceData> srcList = new ArrayList<GEMSourceData>();
    private static double MWDT = 0.1;
    private static double MMIN = 5.0;
    private static boolean INFO = true;

    public NorthernEurasiaFileReader01(BufferedReader fileRead)
            throws IOException {

        NorthernEurasiaSourceData tmpsrc;
        String line;
        int nnodes = 0;
        int end1, end2;

        // Variables
        double lat = -99999;
        double lon = -99999;
        double rte = -99999;
        double mindep = -99999;
        double maxdep = -99999;
        double mag = -99999;
        double dip01 = 0.0;
        double dip02 = 0.0;

        String latstr = null;
        String lonstr = null;
        String srcLab = null;
        String magstr = null;
        String rtestr = null;
        String mindepstr = null;
        String maxdepstr = null;
        String sigstr = null;
        String azmstr = null;
        String dip01str = null;
        String dip01sigstr = null;
        String dip02str = null;
        String dip02sigstr = null;
        String lenstr = null;
        String type = null;

        LocationList locLst = null;

        // Matchers
        Matcher matcher01;

        // Patterns
        Pattern LABEL = Pattern.compile("^7\\.RU\\.(D|L)\\.(\\d+)");

        // Initialize counters
        int cnt = 0;
        int areaSrc = 0;
        int faultSrc = 0;

        BufferedWriter out =
                new BufferedWriter(new FileWriter("/tmp/neaParsing.log"));

        try {

            locLst = new LocationList();
            ArrayList<Double> magArr = new ArrayList<Double>();
            ArrayList<Double> rteArr = new ArrayList<Double>();
            ArrayList<Double> minDepArr = new ArrayList<Double>();
            ArrayList<Double> maxDepArr = new ArrayList<Double>();
            HashMap<Double, Integer> magHm = new HashMap<Double, Integer>();

            // Reading file content
            while (fileRead.ready()) {

                // Read lines
                String line1 = fileRead.readLine();
                String line2 = fileRead.readLine();

                // Check the type of source
                matcher01 = LABEL.matcher(line1);
                if (matcher01.find()) {
                    System.out.println(line1);

                    // Store the the information already read for the "old"
                    // source
                    if (cnt > 0 && rteArr.size() > 0
                            && Collections.max(magArr) > MMIN) {

                        System.out.printf("   %4d sum %4d - %s\n", cnt, areaSrc
                                + faultSrc, srcLab);
                        out.write(String.format("   %4d sum %4d - %s\n", cnt,
                                areaSrc + faultSrc, srcLab));
                        // if (Math.abs(cnt-(areaSrc+faultSrc)) > 2)
                        // System.exit(0);

                        // Sorting magnitudes
                        for (int i = 0; i < magArr.size(); i++) {
                            for (int j = i; j < magArr.size(); j++) {
                                if (magArr.get(j) < magArr.get(i)) {
                                    Collections.swap(magArr, i, j);
                                    Collections.swap(rteArr, i, j);
                                }
                            }
                        }

                        // Defining min and max magnitudes
                        double mmax = 0, mmin = 0, magWdt = 0.5;
                        if (magArr.size() > 2) {
                            magWdt =
                                    magArr.get(magArr.size() - 1)
                                            - magArr.get(magArr.size() - 2);
                            mmax = magArr.get(magArr.size() - 1) + magWdt / 2;
                            mmax = Math.ceil((mmax - mmax / 2e2) / MWDT) * MWDT;
                            mmin =
                                    magArr.get(0)
                                            - ((magArr.get(1) - magArr.get(0)) / 2.0);
                        } else if (magArr.size() == 2) {
                            magWdt = magArr.get(1) - magArr.get(0);
                            mmax =
                                    Math.ceil((magArr.get(1) + 0.25) / MWDT)
                                            * MWDT;
                            mmin = magArr.get(0) - 0.25;
                        } else {
                            mmax =
                                    Math.ceil((magArr.get(0) + 0.25) / MWDT)
                                            * MWDT;
                            mmin =
                                    Math.floor((magArr.get(0) - 0.25) / MWDT)
                                            * MWDT;
                        }
                        IncrementalMagFreqDist mfdtmp = null;

                        // Creating fault source
                        if (type.contentEquals("A")) {

                            int num = (int) Math.round((mmax - MMIN) / MWDT);
                            mfdtmp =
                                    new IncrementalMagFreqDist(MMIN + MWDT / 2,
                                            num, MWDT);

                            // Sum seismicity occurrence rates
                            double rteTot = 0.0;
                            for (int i = 0; i < rteArr.size(); i++) {
                                rteTot += rteArr.get(i);
                            }
                            out.write(String.format(
                                    "Total number of occurrences: %6.4e\n",
                                    rteTot));

                            // Redistribute the seismicity using a
                            // double-truncated GR
                            double bGR = -1.0;
                            double den =
                                    Math.pow(10, bGR * mmin)
                                            - Math.pow(10, bGR * mmax);
                            double aGR = Math.log10(rteTot / (den));

                            // Set the seismicity
                            for (int j = 0; j < mfdtmp.getNum(); j++) {
                                double tmp =
                                        Math.pow(
                                                10,
                                                aGR
                                                        + bGR
                                                        * (mfdtmp.getX(j) - MWDT / 2))
                                                - Math.pow(
                                                        10,
                                                        aGR
                                                                + bGR
                                                                * (mfdtmp
                                                                        .getX(j) + MWDT / 2));
                                mfdtmp.set(j, tmp);
                            }

                            for (int j = 0; j < mfdtmp.getNum(); j++) {
                                if (mfdtmp.getY(j) < 1e-10)
                                    mfdtmp.set(j, mfdtmp.getY(j + 1));
                                out.write(String.format(" %3d %6.2f %6.2e \n",
                                        j, mfdtmp.getX(j), mfdtmp.getY(j)));
                            }

                        } else if (type.contentEquals("F")) {

                            int num = (int) Math.round((mmax - mmin) / MWDT);
                            mfdtmp =
                                    new IncrementalMagFreqDist(mmin + MWDT / 2,
                                            num, MWDT);

                            // Sum seismicity occurrence rates
                            double rteTot = 0.0;
                            for (int i = 0; i < rteArr.size(); i++) {
                                rteTot += rteArr.get(i);
                            }
                            out.write(String.format(
                                    "Total number of occurrences: %6.4e\n",
                                    rteTot));

                            // Redistribute the seismicity using a
                            // double-truncated GR
                            double bGR = -1.0;
                            double den =
                                    Math.pow(10, bGR * mmin)
                                            - Math.pow(10, bGR * mmax);
                            double aGR = Math.log10(rteTot / (den));

                            // Set the seismicity
                            for (int j = 0; j < mfdtmp.getNum(); j++) {
                                double tmp =
                                        Math.pow(
                                                10,
                                                aGR
                                                        + bGR
                                                        * (mfdtmp.getX(j) - MWDT / 2))
                                                - Math.pow(
                                                        10,
                                                        aGR
                                                                + bGR
                                                                * (mfdtmp
                                                                        .getX(j) + MWDT / 2));
                                mfdtmp.set(j, tmp);
                            }

                            for (int j = 0; j < mfdtmp.getNum(); j++) {
                                if (mfdtmp.getY(j) < 1e-10)
                                    mfdtmp.set(j, mfdtmp.getY(j + 1));
                                out.write(String.format(" %3d %6.2f %6.2e \n",
                                        j, mfdtmp.getX(j), mfdtmp.getY(j)));
                            }

                        } else {
                            throw new RuntimeException("unknown option");
                        }

                        // Creating area source
                        if (type.contentEquals("A")) {

                            // Instantiate the region
                            Region reg = new Region(locLst, null);

                            IncrementalMagFreqDist mfdtmp01;
                            if (dip01str.matches("\\d+\\.*\\d*")
                                    && dip02str.matches("\\d+\\.*\\d*")) {
                                mfdtmp.scaleToTotalMomentRate(mfdtmp
                                        .getTotalMomentRate() / 2);
                                mfdtmp01 = mfdtmp.deepClone();
                            }

                            // MFD for focal mechanism
                            FocalMechanism fm = new FocalMechanism();
                            IncrementalMagFreqDist[] arrMfd =
                                    new IncrementalMagFreqDist[1];
                            arrMfd[0] = mfdtmp;

                            FocalMechanism[] arrFm = new FocalMechanism[1];
                            arrFm[0] = fm;
                            MagFreqDistsForFocalMechs mfdffm =
                                    new MagFreqDistsForFocalMechs(arrMfd, arrFm);

                            // Top of rupture
                            ArbitrarilyDiscretizedFunc depTopRup =
                                    new ArbitrarilyDiscretizedFunc();
                            double depMin = 5.0;
                            if (minDepArr.size() > 0)
                                depMin = Collections.min(minDepArr);
                            if (minDepArr.size() == magArr.size()) {
                                for (int i = 0; i < minDepArr.size(); i++) {
                                }
                            } else {
                                depTopRup.set(MMIN, depMin);
                            }

                            // Shallow active tectonic sources
                            GEMAreaSourceData src =
                                    new GEMAreaSourceData(String.format("%d",
                                            areaSrc), srcLab,
                                            TectonicRegionType.ACTIVE_SHALLOW,
                                            reg, mfdffm, depTopRup, depMin);
                            srcList.add(src);
                            areaSrc++;
                        } else if (type.contentEquals("F")) {
                            // Creating fault source

                            // Defines the values of the minimum and maximum
                            // depths
                            double depMin = 5.0;
                            if (minDepArr.size() > 0)
                                depMin = Collections.min(minDepArr);
                            double depMax = 20.0;
                            if (maxDepArr.size() > 0)
                                depMax = Collections.max(maxDepArr);
                            if (depMin == depMax)
                                depMax = depMin + 15.0;

                            // Updates the depths of point describing the trace
                            int idx = 0;
                            LocationList locLstnew = locLst.clone();
                            for (Location loc : locLst) {
                                locLstnew.add(
                                        idx,
                                        new Location(loc.getLatitude(), loc
                                                .getLongitude(), depMin));
                                idx++;
                            }

                            // Create the fault trace
                            FaultTrace fltTrc = new FaultTrace(srcLab);
                            fltTrc.addAll(locLst);

                            // Define the dip of the fault
                            dip01 = 90.0;
                            if (dip01str.matches("\\d+\\.*\\d*"))
                                dip01 = Double.valueOf(dip01str).doubleValue();

                            // Reverse the fault trace for dip angles greater
                            // then 90
                            if (dip01 > 90) {
                                dip01 = 180 - dip01;
                                fltTrc.reverse();
                            }

                            if (depMax < depMin) {
                                System.out.println(depMax + " < " + depMin);
                                throw new RuntimeException(
                                        "Max depth is lower then dep min");
                            }

                            // Adding the source to the faultList
                            GEMFaultSourceData src =
                                    new GEMFaultSourceData(String.format("%d",
                                            faultSrc), srcLab,
                                            TectonicRegionType.ACTIVE_SHALLOW,
                                            mfdtmp, fltTrc, // Fault trace
                                            dip01, // Dip
                                            -90.0, // Rake
                                            depMax, // Depth low
                                            depMin, // Depth Upp
                                            true);
                            srcList.add(src);
                            faultSrc++;

                        } else {
                            throw new RuntimeException(
                                    "Unrecognized source type");
                        }

                    }

                    // Create source label
                    if (line1.length() >= 7)
                        srcLab = (line1.subSequence(0, 8)).toString().trim();
                    if (line2.length() >= 7)
                        srcLab =
                                srcLab
                                        + (line2.subSequence(0, 8)).toString()
                                                .trim();

                    // Initialize data containers
                    locLst = new LocationList();
                    magArr = new ArrayList<Double>();
                    rteArr = new ArrayList<Double>();
                    minDepArr = new ArrayList<Double>();
                    maxDepArr = new ArrayList<Double>();
                    magHm = new HashMap<Double, Integer>();

                    // Process label
                    String srctype = matcher01.group(1);
                    if (srctype.contentEquals("D")) {
                        cnt++;
                        type = "A";
                    } else if (srctype.contentEquals("L")) {
                        cnt++;
                        type = "F";
                    }

                }

                // Latitude
                if (line1.length() >= 13)
                    latstr = (line1.subSequence(9, 13)).toString().trim();
                if (line2.length() >= 13)
                    latstr =
                            latstr
                                    + (line2.subSequence(9, 13)).toString()
                                            .trim();
                // Longitude
                if (line1.length() >= 19)
                    lonstr = (line1.subSequence(14, 19)).toString().trim();
                if (line2.length() >= 19)
                    lonstr =
                            lonstr
                                    + (line2.subSequence(14, 19)).toString()
                                            .trim();
                // Magnitude MLH
                if (line1.length() >= 22)
                    magstr = (line1.subSequence(20, 22)).toString().trim();
                if (line2.length() >= 22)
                    magstr =
                            magstr
                                    + (line2.subSequence(20, 22)).toString()
                                            .trim();
                // Annual rate of events
                if (line1.length() >= 31)
                    rtestr = (line1.subSequence(23, 31)).toString().trim();
                if (line2.length() >= 31)
                    rtestr =
                            rtestr
                                    + (line2.subSequence(23, 31)).toString()
                                            .trim();
                // Minimum depth
                if (line1.length() >= 36)
                    mindepstr = (line1.subSequence(33, 36)).toString().trim();
                if (line2.length() >= 36)
                    mindepstr =
                            mindepstr
                                    + (line2.subSequence(33, 36)).toString()
                                            .trim();
                // Maximum depth
                if (line1.length() >= 40)
                    maxdepstr = (line1.subSequence(37, 40)).toString().trim();
                if (line2.length() >= 40)
                    maxdepstr =
                            maxdepstr
                                    + (line2.subSequence(37, 40)).toString()
                                            .trim();
                // Sigma
                // TODO check this variable
                if (line1.length() >= 41)
                    sigstr = (line1.subSequence(41, 41)).toString().trim();
                if (line2.length() >= 41)
                    sigstr =
                            sigstr
                                    + (line2.subSequence(41, 41)).toString()
                                            .trim();
                // Azimuth
                if (line1.length() >= 46)
                    azmstr = (line1.subSequence(42, 46)).toString().trim();
                if (line2.length() >= 46)
                    azmstr =
                            azmstr
                                    + (line2.subSequence(42, 46)).toString()
                                            .trim();
                // Dip 1st value
                end1 = 51;
                end2 = 51;
                if (line1.length() < end1)
                    end1 = line1.length();
                if (line2.length() < end2)
                    end2 = line2.length();
                if (line1.length() >= 47)
                    dip01str = (line1.subSequence(47, end1)).toString().trim();
                if (line2.length() >= 47)
                    dip01str =
                            dip01str
                                    + (line2.subSequence(47, end2)).toString()
                                            .trim();
                // Dip 1st value sigma
                end1 = 55;
                if (line1.length() < end1)
                    end1 = line1.length();
                end2 = 55;
                if (line2.length() < end2)
                    end2 = line2.length();
                if (line1.length() >= 55)
                    dip01sigstr =
                            (line1.subSequence(52, end1)).toString().trim();
                if (line2.length() >= 55)
                    dip01sigstr =
                            dip01sigstr
                                    + (line2.subSequence(52, end2)).toString()
                                            .trim();
                // Dip 2nd value
                end1 = 60;
                if (line1.length() < end1)
                    end1 = line1.length();
                end2 = 60;
                if (line2.length() < end2)
                    end2 = line2.length();
                if (line1.length() >= 56)
                    dip02str = (line1.subSequence(56, end1)).toString().trim();
                if (line2.length() >= 56)
                    dip02str =
                            dip02str
                                    + (line2.subSequence(56, end2)).toString()
                                            .trim();

                // if (line2.length() >= 56)
                // System.out.println("==>"+line2.subSequence(56,end2)+"<==");

                // Dip 2nd value sigma
                end1 = 64;
                if (line1.length() < end1)
                    end1 = line1.length();
                end2 = 64;
                if (line2.length() < end2)
                    end2 = line2.length();
                if (line1.length() >= 60)
                    dip02sigstr =
                            (line1.subSequence(60, end1)).toString().trim();
                if (line2.length() >= 60)
                    dip02sigstr =
                            dip02sigstr
                                    + (line2.subSequence(60, end2)).toString()
                                            .trim();

                // if (line2.length() >= 60)
                // System.out.println("-->"+line2.subSequence(60,end2)+"<--");
                // System.out.println("azim:"+azmstr+" dip1:"+dip01str+
                // " dipsig1:"+dip01sigstr+" dip2:"+dip02str+" dipsig2:"+dip02sigstr);
                //
                // Lineament length
                if (line1.length() >= 65)
                    lenstr = (line1.subSequence(63, 65)).toString().trim();
                if (line2.length() >= 65)
                    lenstr =
                            lenstr
                                    + (line2.subSequence(63, 65)).toString()
                                            .trim(); // Lineament length

                latstr = latstr.replace(",", ".");
                if (latstr.matches("\\d+\\.*\\d*"))
                    lat = Double.valueOf(latstr).doubleValue();
                lonstr = lonstr.replace(",", ".");
                if (lonstr.matches("\\d+\\.*\\d*"))
                    lon = Double.valueOf(lonstr).doubleValue();
                magstr = magstr.replace(",", ".");
                if (magstr.matches("\\d+\\.*\\d*"))
                    mag = Double.valueOf(magstr).doubleValue();
                rtestr = rtestr.replace(",", ".");
                if (rtestr.matches("\\d+\\.*\\d*"))
                    rte = Double.valueOf(rtestr).doubleValue();
                mindepstr = mindepstr.replace(",", ".");
                if (mindepstr.matches("\\d+\\.*\\d*"))
                    mindep = Double.valueOf(mindepstr).doubleValue();
                maxdepstr = maxdepstr.replace(",", ".");
                if (maxdepstr.matches("\\d+\\.*\\d*"))
                    maxdep = Double.valueOf(maxdepstr).doubleValue();
                dip01str = dip01str.replace(",", ".");
                dip01 = 90.0; // This is the default
                if (dip01str.matches("\\d+\\.*\\d*"))
                    dip01 = Double.valueOf(dip01str).doubleValue();
                dip02str = dip01str.replace(",", ".");
                dip02 = 180.0; // This is the default
                if (dip02str.matches("\\d+\\.*\\d*"))
                    dip02 = Double.valueOf(dip02str).doubleValue();

                // Save info: longitude and latitude
                if (latstr.matches("\\d+\\.*\\d*")
                        && lonstr.matches("\\d+\\.*\\d*")) {
                    if (lon > 180)
                        lon = 360 - lon;
                    locLst.add(new Location(lat, lon));
                }

                // Save info: magnitude and rates
                if (rtestr.matches("\\d+\\.*\\d*")
                        && magstr.matches("\\d+\\.*\\d*")) {
                    if (!magHm.containsKey(mag)) {
                        rteArr.add(rte);
                        magArr.add(mag);
                        magHm.put(mag, 1);
                    }
                }

                // Save info: depths
                if (mindepstr.matches("\\d+\\.*\\d*"))
                    maxDepArr.add(mindep);
                if (maxdepstr.matches("\\d+\\.*\\d*"))
                    maxDepArr.add(maxdep);

            }
            System.out.println("Number of sources " + cnt);

        } finally {
            fileRead.close();
        }

        this.setList(srcList);

    }

}
