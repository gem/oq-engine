package org.gem.engine.hazard.parsers.northernEurasia;

import java.io.BufferedReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.gem.engine.hazard.parsers.GemFileParser;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.magdist.IncrementalMagFreqDist;

public class NorthernEurasiaFileReader extends GemFileParser {

    private ArrayList<GEMSourceData> srcList = new ArrayList<GEMSourceData>();
    private static double MWDT = 0.1;
    private static double MMIN = 5.0;
    private static boolean INFO = true;

    public NorthernEurasiaFileReader(BufferedReader fileRead)
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

        // Initialize counter
        int cnt = 0;

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

                    // Store the the information already read for the "old"
                    // source
                    if (cnt > 0 && rteArr.size() > 0
                            && Collections.max(magArr) > MMIN) {

                        // Sorting magnitudes
                        for (int i = 0; i < magArr.size(); i++) {
                            for (int j = i; j < magArr.size(); j++) {
                                if (magArr.get(j) < magArr.get(i)) {
                                    Collections.swap(magArr, i, j);
                                    Collections.swap(rteArr, i, j);
                                }
                            }
                        }

                        // // Determining magnitude width
                        // double magWdt = 0;
                        // for (int i=1; i < magArr.size(); i++){
                        // if (i == 1) {
                        // magWdt = magArr.get(i) - magArr.get(i-1);
                        // System.out.printf("%5.2f %5.2f\n",magArr.get(i-1),magArr.get(i));
                        // } else if (magWdt-(magArr.get(i) - magArr.get(i-1)) >
                        // 1e-2){
                        // double dff = magArr.get(i) - magArr.get(i-1);
                        // System.out.println("prev:"+magWdt+" new:"+dff);
                        // System.exit(0);
                        // } else {
                        // //
                        // }
                        // }

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
                        System.out.printf(
                                "Mmin %5.2f Mmax %5.2f Mwdt: %5.2f\n", mmin,
                                mmax, magWdt);

                        int num = (int) Math.round((mmax - MMIN) / MWDT);
                        IncrementalMagFreqDist mfdtmp =
                                new IncrementalMagFreqDist(MMIN + MWDT / 2,
                                        num, MWDT);
                        System.out.printf("Number of intervals: %d\n", num);

                        int cov = 0;
                        for (int i = 1; i < magArr.size(); i++) {

                            // Compute the differences
                            double dffLo = 0.0;
                            double dffUp = 0.0;
                            if (i == 1 | i == magArr.size() - 1) {
                                magWdt = magArr.get(i) - magArr.get(i - 1);
                                dffLo = magWdt / 2.0;
                                dffUp = magWdt / 2.0;
                            } else {
                                dffLo = (magArr.get(i) - magArr.get(i - 1)) / 2;
                                dffUp = (magArr.get(i + 1) - magArr.get(i)) / 2;
                            }
                            System.out.printf("dffLo %5.2f sffUp %5.2f\n",
                                    dffLo, dffUp);

                            // Iterate over the final mfd
                            for (int j = 0; j < mfdtmp.getNum(); j++) {

                                if (mfdtmp.getX(j) >= (magArr.get(i) - dffLo - dffLo / 5.0)
                                        && mfdtmp.getX(j) < (magArr.get(i)
                                                + dffUp + dffUp / 5.0)) {

                                    double rate =
                                            rteArr.get(i) / (dffLo + dffUp)
                                                    * MWDT;
                                    mfdtmp.set(j, rate);
                                    cov += 1;
                                    System.out.printf(
                                            " %5.2f < %5.2f < %5.2f ",
                                            magArr.get(i) - dffLo,
                                            mfdtmp.getX(j), magArr.get(i)
                                                    + dffUp);
                                    System.out.printf(" rate: %6.3e (idx: %d)",
                                            mfdtmp.getY(j), j);
                                    System.out.printf("\n ");
                                }
                                // else if (i == 1 && mfdtmp.getX(j) <
                                // (magArr.get(i)+dffUp+dffUp/5.0)){
                                // System.out.println("CORRECTION");
                                // mfdtmp.set(j,rteArr.get(i)/(dffLo+dffUp)*MWDT);
                                // }
                            }

                        }
                        System.out
                                .println("cov:" + cov + "/" + mfdtmp.getNum());

                        if (magArr.size() == 0) {
                            System.out
                                    .println("This source has no magnitudes defined");
                            System.exit(1);
                        }

                        System.out.println("Number of mag-rte couples: "
                                + magHm.keySet().size());
                        for (double db : magHm.keySet()) {
                            System.out.printf("  %5.2f\n", db);
                        }

                        boolean stop = false;
                        System.out.println("M max: " + mmax);
                        for (int j = mfdtmp.getNum() - 1; j >= 0; j--) {
                            if (mfdtmp.getY(j) < 1e-10)
                                mfdtmp.set(j, mfdtmp.getY(j + 1));
                            System.out.printf(" %3d %6.2f %6.2e \n", j,
                                    mfdtmp.getX(j), mfdtmp.getY(j));
                            if (Double.isNaN(mfdtmp.getY(j))) {
                                stop = true;
                            }
                        }
                        if (stop)
                            System.exit(0);

                        // Creating area source
                        if (type.contentEquals("A")) {

                            // Adding the source to the areaList
                            // srcList.add(gemsrc);
                        }

                        // Creating fault source
                        if (type.contentEquals("F")) {

                            // Adding the source to the faultList
                            // srcList.add(gemsrc);

                        }

                    }

                    System.out.println("");
                    System.out.println("");
                    System.out.println(line1);
                    System.out.println(line2);

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
                        // System.out.println("+++"+srctype+" DOMAIN");
                        cnt++;
                        type = "A";
                    } else if (srctype.contentEquals("L")) {
                        // System.out.println("+++"+srctype+" LINEAMENT");
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

                // Save info: longitude and latitude
                if (latstr.matches("\\d+\\.*\\d*")
                        && lonstr.matches("\\d+\\.*\\d*")) {
                    if (lon > 180)
                        lon = 360 - lon;
                    locLst.add(new Location(lat, lon));
                    System.out.println("++++" + lat + " " + lon + " " + rte
                            + " " + mag + " " + mindep + " " + maxdep);
                }

                // Save info: magnitude and rates
                if (rtestr.matches("\\d+\\.*\\d*")
                        && magstr.matches("\\d+\\.*\\d*")) {
                    if (!magHm.containsKey(mag)) {
                        rteArr.add(rte);
                        magArr.add(mag);
                        magHm.put(mag, 1);
                        System.out.println("++++            " + rte + " " + mag
                                + " " + mindep + " " + maxdep);
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

    }

}
