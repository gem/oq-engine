package org.opensha.gem.GEM1.calc.gemCommandLineCalculator;

import java.io.BufferedInputStream;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.geo.BorderType;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.Region;
import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.earthquake.griddedForecast.HypoMagFreqDistAtLoc;
import org.opensha.sha.earthquake.griddedForecast.MagFreqDistsForFocalMechs;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMAreaSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMFaultSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMPointSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSubductionFaultSourceData;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

public class InputModelData {

    private ArrayList<GEMSourceData> sourceList;

    // border type for area source definition
    private static BorderType borderType = BorderType.GREAT_CIRCLE;

    // comment line identifier
    private static String comment = "#";

    // key words
    private static String NEW_SOURCE = "newsource";
    private static String AREA_SOURCE = "area";
    private static String POINT_SOURCE = "point";
    private static String FAULT_SOURCE = "fault";
    private static String SUBDUCTION_SOURCE = "subduction";
    private static String GUTENBERG_RICHTER = "gr";

    // for debugging
    private static Boolean D = false;

    // contructor
    public InputModelData(String inputModelFile, double deltaMFD) {

        try {
            sourceList = new ArrayList<GEMSourceData>();

            // common variables
            // source id
            String sourceID = null;
            // source name
            String sourceName = null;
            // tectonic region type
            TectonicRegionType trt = null;

            String sRecord = null;
            StringTokenizer st = null;

            // open file
            File file = new File(inputModelFile);
            FileInputStream oFIS = new FileInputStream(file.getPath());
            BufferedInputStream oBIS = new BufferedInputStream(oFIS);
            BufferedReader oReader =
                    new BufferedReader(new InputStreamReader(oBIS));

            // start reading the file
            sRecord = oReader.readLine();
            while (sRecord != null) {

                // skip comments or empty lines
                while (sRecord.trim().startsWith(comment)
                        || sRecord.replaceAll(" ", "").isEmpty()) {
                    sRecord = oReader.readLine();
                    continue;
                }
                // if keyword newsource is found
                if (sRecord.trim().equalsIgnoreCase(NEW_SOURCE)) {

                    // read source id
                    sRecord = oReader.readLine();
                    while (sRecord.trim().startsWith(comment)
                            || sRecord.replaceAll(" ", "").isEmpty()) {
                        sRecord = oReader.readLine();
                        continue;
                    }
                    sourceID = sRecord.trim();
                    if (D)
                        System.out.println("Source id: " + sourceID);

                    // read source name
                    sRecord = oReader.readLine();
                    while (sRecord.trim().startsWith(comment)
                            || sRecord.replaceAll(" ", "").isEmpty()) {
                        sRecord = oReader.readLine();
                        continue;
                    }
                    sourceName = sRecord.trim();
                    if (D)
                        System.out.println("Source name: " + sourceName);

                    // read tectonic region type
                    sRecord = oReader.readLine();
                    while (sRecord.trim().startsWith(comment)
                            || sRecord.replaceAll(" ", "").isEmpty()) {
                        sRecord = oReader.readLine();
                        continue;
                    }
                    trt = TectonicRegionType.getTypeForName(sRecord.trim());
                    if (D)
                        System.out.println("Tectonic region type: "
                                + trt.toString());

                    // continue reading
                    sRecord = oReader.readLine();
                    while (sRecord.trim().startsWith(comment)
                            || sRecord.replaceAll(" ", "").isEmpty()) {
                        sRecord = oReader.readLine();
                        continue;
                    }

                    // area source definition
                    if (sRecord.trim().equalsIgnoreCase(AREA_SOURCE)) {

                        if (D)
                            System.out.println("Source typology: "
                                    + sRecord.trim());

                        readAreaSourceData(oReader, deltaMFD, sourceID,
                                sourceName, trt);

                    } // end if area

                    // point source definition
                    if (sRecord.trim().equalsIgnoreCase(POINT_SOURCE)) {

                        if (D)
                            System.out.println("Source typology: " + sRecord);

                        readPointSourceData(oReader, deltaMFD, sourceID,
                                sourceName, trt);

                    } // end if point

                    // fault source definition
                    if (sRecord.trim().equalsIgnoreCase(FAULT_SOURCE)) {

                        if (D)
                            System.out.println("Source typology: " + sRecord);

                        readFaultSourceData(oReader, deltaMFD, sourceID,
                                sourceName, trt);

                    } // end if fault

                    // subduction fault source definition
                    if (sRecord.trim().equalsIgnoreCase(SUBDUCTION_SOURCE)) {

                        if (D)
                            System.out.println("Source typology: " + sRecord);

                        readSubductionFaultSourceData(oReader, deltaMFD,
                                sourceID, sourceName, trt);

                    } // end if subduction

                } // end if new source

                // continue reading until next newsource is found or end of file
                // skip comments or empty lines
                while ((sRecord = oReader.readLine()) != null) {
                    if (sRecord.trim().startsWith(comment)
                            || sRecord.replaceAll(" ", "").isEmpty())
                        continue;
                    else if (sRecord.trim().equalsIgnoreCase(NEW_SOURCE))
                        break;
                }

            } // end if sRecord!=null

            oFIS.close();
            oBIS.close();
            oReader.close();
        } catch (FileNotFoundException e) {
            // TODO log4j
            IOException ioe =
                    new IOException(
                            "Source model file not found. Program stops.", e);
            ioe.printStackTrace();
            System.exit(-1);
        } catch (IOException e) {
            // TODO log4j
            IOException ioe =
                    new IOException(
                            "Source model file not found. Program stops.", e);
            ioe.printStackTrace();
            System.exit(-1);
        } // catch
    } // constructor

    private void readAreaSourceData(BufferedReader oReader, double deltaMFD,
            String sourceID, String sourceName, TectonicRegionType trt)
            throws IOException {

        String sRecord = null;
        StringTokenizer st = null;

        // read number of vertices in the polygon boundary
        sRecord = oReader.readLine();
        while (sRecord.trim().startsWith(comment)
                || sRecord.replaceAll(" ", "").isEmpty()) {
            sRecord = oReader.readLine();
            continue;
        }
        int numVert = Integer.parseInt(sRecord.trim());
        if (D)
            System.out.println("Number of polygon vertices: " + numVert);

        // location list containing border coordinates
        LocationList areaBorder = new LocationList();

        // read polygon vertices
        for (int i = 0; i < numVert; i++) {
            sRecord = oReader.readLine();
            while (sRecord.trim().startsWith(comment)
                    || sRecord.replaceAll(" ", "").isEmpty()) {
                sRecord = oReader.readLine();
                continue;
            }
            st = new StringTokenizer(sRecord);
            double lat = Double.parseDouble(st.nextToken());
            double lon = Double.parseDouble(st.nextToken());
            areaBorder.add(new Location(lat, lon));
            if (D)
                System.out.println("Lat: " + lat + ", Lon: " + lon);
        }

        // create region
        Region reg = new Region(areaBorder, borderType);

        // read number of mfd-focal mechanisms pairs
        sRecord = oReader.readLine();
        while (sRecord.trim().startsWith(comment)
                || sRecord.replaceAll(" ", "").isEmpty()) {
            sRecord = oReader.readLine();
            continue;
        }
        st = new StringTokenizer(sRecord.trim());
        int numMfdFm = Integer.parseInt(st.nextToken());

        // magnitude frequency distribution(s)
        IncrementalMagFreqDist[] mfd = new IncrementalMagFreqDist[numMfdFm];

        // focal mechanism(s)
        FocalMechanism[] fm = new FocalMechanism[numMfdFm];

        // loop over mfd-fm pairs
        for (int i = 0; i < numMfdFm; i++) {

            // read mfd specification
            sRecord = oReader.readLine();
            while (sRecord.trim().startsWith(comment)
                    || sRecord.replaceAll(" ", "").isEmpty()) {
                sRecord = oReader.readLine();
                continue;
            }
            // mfd type
            st = new StringTokenizer(sRecord);
            String mfdType = st.nextToken();
            if (mfdType.equalsIgnoreCase(GUTENBERG_RICHTER)) {
                double aVal = Double.parseDouble(st.nextToken());
                double bVal = Double.parseDouble(st.nextToken());
                double mMin = Double.parseDouble(st.nextToken());
                double mMax = Double.parseDouble(st.nextToken());
                if (D)
                    System.out.println("a value: " + aVal + ", b value: "
                            + bVal + ", minimum magnitude: " + mMin
                            + ", maximum magnitude: " + mMax);

                mfd[i] =
                        createGrMfd(aVal, bVal, mMin, mMax, deltaMFD,
                                sourceName);

                if (D)
                    System.out.println(mfd[i]);
            } else {
                System.out.println("Only GR mfd supported!");
                System.out.println("Execution stopped!");
                System.exit(0);
            }

            // read focal mechanism specification
            sRecord = oReader.readLine();
            while (sRecord.trim().startsWith(comment)
                    || sRecord.replaceAll(" ", "").isEmpty()) {
                sRecord = oReader.readLine();
                continue;
            }
            st = new StringTokenizer(sRecord);
            double strike = Double.parseDouble(st.nextToken());
            double dip = Double.parseDouble(st.nextToken());
            double rake = Double.parseDouble(st.nextToken());
            if (D)
                System.out.println("strike: " + strike + ", dip: " + dip
                        + ", rake: " + rake);

            fm[i] = new FocalMechanism(strike, dip, rake);

        } // end loop over mfd-fm

        // instantiate mfd/fm pairs
        MagFreqDistsForFocalMechs magFreqDistForFocalMech =
                new MagFreqDistsForFocalMechs(mfd, fm);

        // read top of rupture distribution
        ArbitrarilyDiscretizedFunc aveRupTopVsMag =
                new ArbitrarilyDiscretizedFunc();
        sRecord = oReader.readLine();
        while (sRecord.trim().startsWith(comment)
                || sRecord.replaceAll(" ", "").isEmpty()) {
            sRecord = oReader.readLine();
            continue;
        }
        // number of values
        st = new StringTokenizer(sRecord);
        int numVal = st.countTokens();
        for (int i = 0; i < numVal / 2; i++) {
            double mag = Double.parseDouble(st.nextToken());
            double depth = Double.parseDouble(st.nextToken());
            aveRupTopVsMag.set(mag, depth);
            if (D)
                System.out.println("Magnitude: " + mag + ", depth: " + depth);
        }

        // read average hypocentral depth
        sRecord = oReader.readLine();
        while (sRecord.trim().startsWith(comment)
                || sRecord.replaceAll(" ", "").isEmpty()) {
            sRecord = oReader.readLine();
            continue;
        }
        double aveHypoDepth = Double.parseDouble(sRecord.trim());
        if (D)
            System.out.println("Average hypocentral depth: " + aveHypoDepth);

        // add to source list
        sourceList.add(new GEMAreaSourceData(sourceID, sourceName, trt, reg,
                magFreqDistForFocalMech, aveRupTopVsMag, aveHypoDepth));

    }

    private void readPointSourceData(BufferedReader oReader, double deltaMFD,
            String sourceID, String sourceName, TectonicRegionType trt)
            throws IOException {

        String sRecord = null;
        StringTokenizer st = null;

        // read source location
        sRecord = oReader.readLine();
        while (sRecord.trim().startsWith(comment)
                || sRecord.replaceAll(" ", "").isEmpty()) {
            sRecord = oReader.readLine();
            continue;
        }
        st = new StringTokenizer(sRecord);
        double lat = Double.parseDouble(st.nextToken());
        double lon = Double.parseDouble(st.nextToken());
        Location loc = new Location(lat, lon);
        if (D)
            System.out.println("Location coordinates: " + loc.getLatitude()
                    + ", " + loc.getLongitude());

        // read number of mfd-focal mechanisms pairs
        sRecord = oReader.readLine();
        while (sRecord.trim().startsWith(comment)
                || sRecord.replaceAll(" ", "").isEmpty()) {
            sRecord = oReader.readLine();
            continue;
        }
        st = new StringTokenizer(sRecord.trim());
        int numMfdFm = Integer.parseInt(st.nextToken());

        // magnitude frequency distribution(s)
        IncrementalMagFreqDist[] mfd = new IncrementalMagFreqDist[numMfdFm];

        // focal mechanism(s)
        FocalMechanism[] fm = new FocalMechanism[numMfdFm];

        // loop over mfd-fm pairs
        for (int i = 0; i < numMfdFm; i++) {

            // read mfd specification
            sRecord = oReader.readLine();
            while (sRecord.trim().startsWith(comment)
                    || sRecord.replaceAll(" ", "").isEmpty()) {
                sRecord = oReader.readLine();
                continue;
            }
            // mfd type
            st = new StringTokenizer(sRecord);
            String mfdType = st.nextToken();
            if (mfdType.equalsIgnoreCase(GUTENBERG_RICHTER)) {
                double aVal = Double.parseDouble(st.nextToken());
                double bVal = Double.parseDouble(st.nextToken());
                double mMin = Double.parseDouble(st.nextToken());
                double mMax = Double.parseDouble(st.nextToken());
                if (D)
                    System.out.println("a value: " + aVal + ", b value: "
                            + bVal + ", minimum magnitude: " + mMin
                            + ", maximum magnitude: " + mMax);

                mfd[i] =
                        createGrMfd(aVal, bVal, mMin, mMax, deltaMFD,
                                sourceName);

                if (D)
                    System.out.println(mfd[i]);
            } else {
                System.out.println("Only GR mfd supported!");
                System.out.println("Execution stopped!");
                System.exit(0);
            }

            // read focal mechanism specification
            sRecord = oReader.readLine();
            while (sRecord.trim().startsWith(comment)
                    || sRecord.replaceAll(" ", "").isEmpty()) {
                sRecord = oReader.readLine();
                continue;
            }
            st = new StringTokenizer(sRecord);
            double strike = Double.parseDouble(st.nextToken());
            double dip = Double.parseDouble(st.nextToken());
            double rake = Double.parseDouble(st.nextToken());
            if (D)
                System.out.println("strike: " + strike + ", dip: " + dip
                        + ", rake: " + rake);

            fm[i] = new FocalMechanism(strike, dip, rake);

        } // end loop over mfd-fm

        HypoMagFreqDistAtLoc mfdAtLoc = new HypoMagFreqDistAtLoc(mfd, loc, fm);

        // read top of rupture distribution
        ArbitrarilyDiscretizedFunc aveRupTopVsMag =
                new ArbitrarilyDiscretizedFunc();
        sRecord = oReader.readLine();
        while (sRecord.trim().startsWith(comment)
                || sRecord.replaceAll(" ", "").isEmpty()) {
            sRecord = oReader.readLine();
            continue;
        }
        // number of values
        st = new StringTokenizer(sRecord);
        int numVal = st.countTokens();
        for (int i = 0; i < numVal / 2; i++) {
            double mag = Double.parseDouble(st.nextToken());
            double depth = Double.parseDouble(st.nextToken());
            aveRupTopVsMag.set(mag, depth);
            if (D)
                System.out.println("Magnitude: " + mag + ", depth: " + depth);
        }

        // read average hypocentral depth
        sRecord = oReader.readLine();
        while (sRecord.trim().startsWith(comment)
                || sRecord.replaceAll(" ", "").isEmpty()) {
            sRecord = oReader.readLine();
            continue;
        }
        double aveHypoDepth = Double.parseDouble(sRecord.trim());
        if (D)
            System.out.println("Average hypocentral depth: " + aveHypoDepth);

        // add to source list
        sourceList.add(new GEMPointSourceData(sourceID, sourceName, trt,
                mfdAtLoc, aveRupTopVsMag, aveHypoDepth));

    }

    private void readFaultSourceData(BufferedReader oReader, double deltaMFD,
            String sourceID, String sourceName, TectonicRegionType trt)
            throws IOException {

        String sRecord = null;
        StringTokenizer st = null;

        // read number of points in fault trace
        sRecord = oReader.readLine();
        while (sRecord.trim().startsWith(comment)
                || sRecord.replaceAll(" ", "").isEmpty()) {
            sRecord = oReader.readLine();
            continue;
        }
        int numPoint = Integer.parseInt(sRecord.trim());
        if (D)
            System.out.println("Number of fault trace points: " + numPoint);

        // read fault trace coordinates
        FaultTrace trace = new FaultTrace(sourceName);
        for (int i = 0; i < numPoint; i++) {
            sRecord = oReader.readLine();
            while (sRecord.trim().startsWith(comment)
                    || sRecord.replaceAll(" ", "").isEmpty()) {
                sRecord = oReader.readLine();
                continue;
            }
            st = new StringTokenizer(sRecord);
            double lat = Double.parseDouble(st.nextToken());
            double lon = Double.parseDouble(st.nextToken());
            trace.add(new Location(lat, lon));
            if (D)
                System.out.println("Lat: " + lat + ", Lon: " + lon);
        }

        // read fault dip
        sRecord = oReader.readLine();
        while (sRecord.trim().startsWith(comment)
                || sRecord.replaceAll(" ", "").isEmpty()) {
            sRecord = oReader.readLine();
            continue;
        }
        double dip = Double.parseDouble(sRecord.trim());
        if (D)
            System.out.println("Dip: " + dip);

        // read fault rake
        sRecord = oReader.readLine();
        while (sRecord.trim().startsWith(comment)
                || sRecord.replaceAll(" ", "").isEmpty()) {
            sRecord = oReader.readLine();
            continue;
        }
        double rake = Double.parseDouble(sRecord.trim());
        if (D)
            System.out.println("Rake: " + rake);

        // read top depth
        sRecord = oReader.readLine();
        while (sRecord.trim().startsWith(comment)
                || sRecord.replaceAll(" ", "").isEmpty()) {
            sRecord = oReader.readLine();
            continue;
        }
        double topDepth = Double.parseDouble(sRecord.trim());
        if (D)
            System.out.println("Top depth: " + topDepth);

        // read bottom depth
        sRecord = oReader.readLine();
        while (sRecord.trim().startsWith(comment)
                || sRecord.replaceAll(" ", "").isEmpty()) {
            sRecord = oReader.readLine();
            continue;
        }
        double bottomDepth = Double.parseDouble(sRecord.trim());
        if (D)
            System.out.println("Bottom depth: " + bottomDepth);

        // read magnitude frequency distribution
        IncrementalMagFreqDist mfd = null;
        Boolean floatRuptureFlag = null;
        sRecord = oReader.readLine();
        while (sRecord.trim().startsWith(comment)
                || sRecord.replaceAll(" ", "").isEmpty()) {
            sRecord = oReader.readLine();
            continue;
        }
        // mfd type
        st = new StringTokenizer(sRecord);
        String mfdType = st.nextToken();
        if (mfdType.equalsIgnoreCase(GUTENBERG_RICHTER)) {

            floatRuptureFlag = true;

            double aVal = Double.parseDouble(st.nextToken());
            double bVal = Double.parseDouble(st.nextToken());
            double mMin = Double.parseDouble(st.nextToken());
            double mMax = Double.parseDouble(st.nextToken());
            if (D)
                System.out.println("a value: " + aVal + ", b value: " + bVal
                        + ", minimum magnitude: " + mMin
                        + ", maximum magnitude: " + mMax);

            mfd = createGrMfd(aVal, bVal, mMin, mMax, deltaMFD, sourceName);

            if (D)
                System.out.println(mfd);
        } else {
            System.out.println("Only GR mfd supported!");
            System.out.println("Execution stopped!");
            System.exit(0);
        }

        // add to source list
        sourceList.add(new GEMFaultSourceData(sourceID, sourceName, trt, mfd,
                trace, dip, rake, bottomDepth, topDepth, floatRuptureFlag));

    }

    private void readSubductionFaultSourceData(BufferedReader oReader,
            double deltaMFD, String sourceID, String sourceName,
            TectonicRegionType trt) throws IOException {

        String sRecord = null;
        StringTokenizer st = null;

        // read number of points in top fault trace
        sRecord = oReader.readLine();
        while (sRecord.trim().startsWith(comment)
                || sRecord.replaceAll(" ", "").isEmpty()) {
            sRecord = oReader.readLine();
            continue;
        }
        int numPointTop = Integer.parseInt(sRecord.trim());
        if (D)
            System.out.println("Number of top trace points: " + numPointTop);

        // read top fault trace coordinates
        FaultTrace topTrace = new FaultTrace(sourceName);
        for (int i = 0; i < numPointTop; i++) {
            sRecord = oReader.readLine();
            while (sRecord.trim().startsWith(comment)
                    || sRecord.replaceAll(" ", "").isEmpty()) {
                sRecord = oReader.readLine();
                continue;
            }
            st = new StringTokenizer(sRecord);
            double lat = Double.parseDouble(st.nextToken());
            double lon = Double.parseDouble(st.nextToken());
            double depth = Double.parseDouble(st.nextToken());
            topTrace.add(new Location(lat, lon, depth));
            if (D)
                System.out.println("Lat: " + lat + ", Lon: " + lon
                        + ", depth: " + depth);
        }

        // read number of points in bottom fault trace
        sRecord = oReader.readLine();
        while (sRecord.trim().startsWith(comment)
                || sRecord.replaceAll(" ", "").isEmpty()) {
            sRecord = oReader.readLine();
            continue;
        }
        int numPointBottom = Integer.parseInt(sRecord.trim());
        if (D)
            System.out.println("Number of bottom trace points: "
                    + numPointBottom);

        // read bottom fault trace coordinates
        FaultTrace bottomTrace = new FaultTrace(sourceName);
        for (int i = 0; i < numPointBottom; i++) {
            sRecord = oReader.readLine();
            while (sRecord.trim().startsWith(comment)
                    || sRecord.replaceAll(" ", "").isEmpty()) {
                sRecord = oReader.readLine();
                continue;
            }
            st = new StringTokenizer(sRecord);
            double lat = Double.parseDouble(st.nextToken());
            double lon = Double.parseDouble(st.nextToken());
            double depth = Double.parseDouble(st.nextToken());
            bottomTrace.add(new Location(lat, lon, depth));
            if (D)
                System.out.println("Lat: " + lat + ", Lon: " + lon
                        + ", depth: " + depth);
        }

        // read fault rake
        sRecord = oReader.readLine();
        while (sRecord.trim().startsWith(comment)
                || sRecord.replaceAll(" ", "").isEmpty()) {
            sRecord = oReader.readLine();
            continue;
        }
        double rake = Double.parseDouble(sRecord.trim());
        if (D)
            System.out.println("Rake: " + rake);

        // read magnitude frequency distribution
        IncrementalMagFreqDist mfd = null;
        Boolean floatRuptureFlag = null;
        sRecord = oReader.readLine();
        while (sRecord.trim().startsWith(comment)
                || sRecord.replaceAll(" ", "").isEmpty()) {
            sRecord = oReader.readLine();
            continue;
        }
        // mfd type
        st = new StringTokenizer(sRecord);
        String mfdType = st.nextToken();
        if (mfdType.equalsIgnoreCase(GUTENBERG_RICHTER)) {

            floatRuptureFlag = true;

            double aVal = Double.parseDouble(st.nextToken());
            double bVal = Double.parseDouble(st.nextToken());
            double mMin = Double.parseDouble(st.nextToken());
            double mMax = Double.parseDouble(st.nextToken());
            if (D)
                System.out.println("a value: " + aVal + ", b value: " + bVal
                        + ", minimum magnitude: " + mMin
                        + ", maximum magnitude: " + mMax);

            mfd = createGrMfd(aVal, bVal, mMin, mMax, deltaMFD, sourceName);

            if (D)
                System.out.println(mfd);
        } else {
            System.out.println("Only GR mfd supported!");
            System.out.println("Execution stopped!");
            System.exit(0);
        }

        // add to source list
        sourceList.add(new GEMSubductionFaultSourceData(sourceID, sourceName,
                trt, topTrace, bottomTrace, rake, mfd, floatRuptureFlag));

    }

    private GutenbergRichterMagFreqDist createGrMfd(double aVal, double bVal,
            double mMin, double mMax, double deltaMFD, String sourceName) {

        GutenbergRichterMagFreqDist mfd = null;

        // round mMin and mMax with respect to delta bin
        mMin = Math.round(mMin / deltaMFD) * deltaMFD;
        mMax = Math.round(mMax / deltaMFD) * deltaMFD;

        if (mMax < mMin) {
            System.out.println("Minimum magnitude for source " + sourceName
                    + " is less then mMax");
            System.out.println("Check the source input file.");
            System.out.println("Execution stopped.");
            System.exit(0);
        }

        // compute total cumulative rate between minimum and maximum magnitude
        double totCumRate =
                Math.pow(10, aVal - bVal * mMin)
                        - Math.pow(10, aVal - bVal * mMax);

        if (mMax != mMin) {
            // shift to bin center
            mMin = mMin + deltaMFD / 2;
            mMax = mMax - deltaMFD / 2;
        }

        // number of magnitude values in the mfd
        int numVal = (int) Math.round(((mMax - mMin) / deltaMFD + 1));

        mfd =
                new GutenbergRichterMagFreqDist(bVal, totCumRate, mMin, mMax,
                        numVal);

        return mfd;
    }

    public ArrayList<GEMSourceData> getSourceList() {
        return sourceList;
    }

    // for testing
    public static void main(String[] args) throws IOException {

        InputModelData data =
                new InputModelData(
                        "/Users/damianomonelli/Projects/opengem/data/src_model1.dat",
                        0.1);

    }

}
