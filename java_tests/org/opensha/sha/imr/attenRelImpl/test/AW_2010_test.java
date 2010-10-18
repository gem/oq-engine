/**
 * AW_2010_test
 * 
 * Description: This program tests that correct values are calculated by the
 * AW_2010_AttenRel Class. A tolerance level of 1E-8 is provided. Run as JUnit
 * test.
 * 
 * Input: Excel spreadsheet prepared by D. Monelli converted to CSV text file in
 * 2 possible formats: (1) For Finite Ruptures: in AW2010FINITE.TXT (Format:
 * ruptureDistance, MMI(Mw=5), MMI(Mw=6), MMI(Mw=7), MMI(Mw=8), Sigma) (2) For
 * Point Ruptures: in AW2010POINT.TXT (Format: hypocentralDistance, MMI(Mw=5),
 * MMI(Mw=6), MMI(Mw=7), Sigma)
 * 
 * Please refer to the following files (added): - AW_2010_AttenRel.java (in
 * org.opensha.sha.imr.attenRelImpl) - MMI_Param.java (in
 * org.opensha.sha.imr.param.IntensityMeasureParams) -
 * DistanceHypoParameter.java (in
 * org.opensha.sha.imr.param.PropagationEffectParams)
 * 
 * And the following files (modified): - AttenuationRelationship.java (in
 * org.opensha.sha.imr)
 * 
 * @authors Aurea Moemke, Damiano Monelli
 * @created 22 September 2010
 * @version 1.0
 * 
 */

package org.opensha.sha.imr.attenRelImpl.test;

import static org.junit.Assert.assertEquals;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.io.LineNumberReader;
import java.util.Scanner;
import java.util.StringTokenizer;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;

import org.opensha.commons.data.Site;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.faultSurface.PointSurface;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;
import org.opensha.sha.imr.attenRelImpl.AW_2010_AttenRel;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceRupParameter;

public class AW_2010_test implements ParameterChangeWarningListener {

    private AW_2010_AttenRel aw_2010_AttenRel = null;

    private static String inputFilePath = "/java_tests/data/";
    private static String inputFileNameFinite = "AW2010FINITE.TXT";
    private static String inputFileNamePoint = "AW2010POINT.TXT";

    private static double tolerance = 1E-8;

    @Before
    public void setUp() {
        aw_2010_AttenRel = new AW_2010_AttenRel(this);
        aw_2010_AttenRel.setParamDefaults();
    }

    @After
    public void tearDown() {
        aw_2010_AttenRel = null;
    }

    /**
     * This test validates the getMean(m,r) and getStdDev(r) methods for point
     * ruptures against a verification table obtained using an Excel spreadsheet
     */
    @Test
    public void pointRuptureEquation() {
        boolean isFiniteRupture = false;
        File dir1 = new File(".");
        String dirPath = null;
        try {
            dirPath = dir1.getCanonicalPath();
        } catch (Exception e) {
            e.printStackTrace();
        }
        File inFile = new File(dirPath + inputFilePath + inputFileNamePoint);
        int numlines = countFileLines(inFile);
        doTest(isFiniteRupture, tolerance, numlines, inFile);
    }

    /**
     * This test validates the getMean(m,r) and getStdDev(r) methods for finite
     * ruptures against a verification table obtained using an Excel spreadsheet
     */
    @Test
    public void finiteRuptureEquation() {
        boolean isFiniteRupture = true;
        File dir1 = new File(".");
        String dirPath = null;
        try {
            dirPath = dir1.getCanonicalPath();
        } catch (Exception e) {
            e.printStackTrace();
        }
        File inFile = new File(dirPath + inputFilePath + inputFileNameFinite);
        int numlines = countFileLines(inFile);
        doTest(isFiniteRupture, tolerance, numlines, inFile);
    }

    /**
     * This test compares the results of the getMean() and getStdDev() methods
     * when setting a Site and a point EqkRupture object with the results of the
     * get getMeanForPointRup(m,r) method when passing directly the magnitude
     * and hypocentral distance values. This test is meant to validate if the
     * Site and EqkRupture parameters are passed correctly to the
     * AttenuationRelationship object and correct distinction is done between
     * point and finite rupture. The average rake is not needed by the IPE but
     * is used to define the EqkRupture object. In the test, the Site is defined
     * on the same latitude as the hypocenter but shifted 0.1 degrees East.
     * 
     */
    @Test
    public void pointEqkRupture() {

        double mag = 5.0;
        double aveRake = 0.0;
        Location hypo = new Location(0.0, 0.0, 5.0);
        Site site = new Site(new Location(0.0, 0.1, 0.0));
        EqkRupture rup = getPointEqkRupture(mag, hypo, aveRake);
        double hypoDist =
                Math.sqrt(Math.pow(
                        LocationUtils.horzDistance(hypo, site.getLocation()), 2)
                        + Math.pow(
                                LocationUtils.vertDistance(hypo,
                                        site.getLocation()), 2));
        aw_2010_AttenRel.setSite(site);
        aw_2010_AttenRel.setEqkRupture(rup);

        double meanMMI = aw_2010_AttenRel.getMean();
        double std = aw_2010_AttenRel.getStdDev();

        double meanMMI_pointRupture =
                aw_2010_AttenRel.getMeanForPointRup(mag, hypoDist);
        double std_pointRupture =
                aw_2010_AttenRel.getStdDevForPointRup(hypoDist);

        assertEquals(meanMMI_pointRupture, meanMMI, tolerance);
        assertEquals(std_pointRupture, std, tolerance);
    }

    /**
     * This test compares the results of the getMean() and getStdDev() methods
     * when setting a Site and a finite EqkRupture object with the results of
     * the getMeanForFiniteRup(m,r) method when passing directly the magnitude
     * and closest distance to rupture values. This test is meant to validate if
     * the Site and EqkRupture parameters are passed correctly to the
     * AttenuationRelationship object and correct distinction is done between
     * point and finite rupture. For this test, the defined finite rupture is
     * data taken from the Elsinore fault (USGS California model:
     * aFault_aPriori_D2.1.in). The average rake is not needed by the IPE but is
     * used to define the EqkRupture object. The Site is defined on the same
     * latitude as the hypocenter but shifted 0.1 degrees East.
     */
    @Test
    public void finiteEqkRupture() {

        double aveDip = 90.0;
        double lowerSeisDepth = 13.0;
        double upperSeisDepth = 0.0;
        FaultTrace trace = new FaultTrace("Elsinore;GI");
        trace.add(new Location(33.82890, -117.59000));
        trace.add(new Location(33.81290, -117.54800));
        trace.add(new Location(33.74509, -117.46332));
        trace.add(new Location(33.73183, -117.44568));
        trace.add(new Location(33.71851, -117.42415));
        trace.add(new Location(33.70453, -117.40265));
        trace.add(new Location(33.68522, -117.37270));
        trace.add(new Location(33.62646, -117.27443));
        double gridSpacing = 1.0;

        double mag = 6.889;
        double aveRake = 0.0;
        Location hypo = new Location(33.73183, -117.44568);
        Site site = new Site(new Location(33.8, -117.6, 0.0));
        EqkRupture rup =
                getFiniteEqkRupture(aveDip, lowerSeisDepth, upperSeisDepth,
                        trace, gridSpacing, mag, hypo, aveRake);
        aw_2010_AttenRel.setSite(site);
        aw_2010_AttenRel.setEqkRupture(rup);

        double meanMMI = aw_2010_AttenRel.getMean();
        double std = aw_2010_AttenRel.getStdDev();
        double rRup =
                (Double) aw_2010_AttenRel.getParameter(
                        DistanceRupParameter.NAME).getValue();
        double meanMMI_finiteRupture =
                aw_2010_AttenRel.getMeanForFiniteRup(mag, rRup);
        double std_finiteRupture = aw_2010_AttenRel.getStdDevForFiniteRup(rRup);

        assertEquals(meanMMI_finiteRupture, meanMMI, tolerance);
        assertEquals(std_finiteRupture, std, tolerance);
    }

    /**
     * This test checks that the AW_2010_AttenRel object throws a warning
     * exception when a magnitude value < 5 is passed. In this test, the point
     * source is defined with magnitude 4.0 (too low). The average rake is not
     * needed by the IPE but is used to define the EqkRupture object. Hypocenter
     * coordinates are lat, lon, depth in km.
     * 
     */
    @Test(expected = org.opensha.commons.exceptions.WarningException.class)
    public void magnitudeValueTooSmall() {
        double mag = 4.0;
        double aveRake = 0.0;
        Location hypo = new Location(0.0, 0.0, 5.0);
        EqkRupture rup = getPointEqkRupture(mag, hypo, aveRake);
        aw_2010_AttenRel.setEqkRupture(rup);
    }

    /**
     * This test checks that the AW_2010_AttenRel object throws a warning
     * exception when a magnitude value > 8 is passed. In this test, the point
     * source is defined with magnitude 9.0 (too high). The average rake is not
     * needed by the IPE but is used to define the EqkRupture object. Hypocenter
     * coordinates are lat, lon, depth in km.
     */
    @Test(expected = org.opensha.commons.exceptions.WarningException.class)
    public void magnitudeValueTooLarge() {
        double mag = 9.0;
        double aveRake = 0.0;
        Location hypo = new Location(0.0, 0.0, 5.0);
        EqkRupture rup = getPointEqkRupture(mag, hypo, aveRake);
        aw_2010_AttenRel.setEqkRupture(rup);
    }

    /**
     * This test checks that the AW_2010_AttenRel object throws a warning
     * exception when a hypocentral distance > 300 km is passed. The point
     * source is defined with magnitude 5 (acceptable value). The average rake
     * is not needed by the IPE but is used to define the EqkRupture object.
     * Hypocenter coordinates are lat, lon, depth in km. The Site is defined on
     * the same latitude as the hypocenter but shifted 4 degrees East.
     */
    @Test(expected = org.opensha.commons.exceptions.WarningException.class)
    public void hypocentralDistanceTooLarge() {
        double mag = 5.0;
        double aveRake = 0.0;
        Location hypo = new Location(0.0, 0.0, 5.0);
        Site site = new Site(new Location(0.0, 4., 0.0));
        EqkRupture rup = getPointEqkRupture(mag, hypo, aveRake);
        aw_2010_AttenRel.setSite(site);
        aw_2010_AttenRel.setEqkRupture(rup);
    }

    /**
     * This test checks that the AW_2010_AttenRel object throws a warning
     * exception when a closest distance to rupture > 300 km is passed. For this
     * test, the defined finite rupture is data taken from the Elsinore fault
     * (USGS California model: aFault_aPriori_D2.1.in). The Site is defined at
     * the intersection of the equator and Greenwich meridian (should be enough
     * far from California).
     */
    @Test(expected = org.opensha.commons.exceptions.WarningException.class)
    public void closestDistanceToRuptureTooLarge() {
        double aveDip = 90.0;
        double lowerSeisDepth = 13.0;
        double upperSeisDepth = 0.0;
        FaultTrace trace = new FaultTrace("Elsinore;GI");
        trace.add(new Location(33.82890, -117.59000));
        trace.add(new Location(33.81290, -117.54800));
        trace.add(new Location(33.74509, -117.46332));
        trace.add(new Location(33.73183, -117.44568));
        trace.add(new Location(33.71851, -117.42415));
        trace.add(new Location(33.70453, -117.40265));
        trace.add(new Location(33.68522, -117.37270));
        trace.add(new Location(33.62646, -117.27443));
        double gridSpacing = 1.0;
        double mag = 6.889;
        double aveRake = 0.0;
        Location hypo = new Location(33.73183, -117.44568);
        Site site = new Site(new Location(0.0, 0.0, 0.0));
        EqkRupture rup =
                getFiniteEqkRupture(aveDip, lowerSeisDepth, upperSeisDepth,
                        trace, gridSpacing, mag, hypo, aveRake);
        aw_2010_AttenRel.setSite(site);
        aw_2010_AttenRel.setEqkRupture(rup);
    }

    /*
     * Counts lines in input file (not including first line).
     */
    private int countFileLines(File testFile) {
        int count = 0;
        try {
            if (testFile.exists()) {
                FileReader fr = new FileReader(testFile);
                LineNumberReader ln = new LineNumberReader(fr);
                while (ln.readLine() != null) {
                    count++;
                }
                ln.close();
            } else {
                System.out.println("File does not exist!");
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
        return count - 1;
    }

    /*
     * Parses an ascii file into arrays for testing. Ascii file format is as
     * follows: closest distance to rupture(for finite ruptures)/ hypocentral
     * distance (for point ruptures), mmi for mag 5, mmi for mag 6, mmi for mag
     * 7, mmi for mag 8 (only for finite ruptures) and sigma.
     */
    private void loadTestData(File testFile, int numMags, double rRup[],
            double vals[][], double sigma[]) {
        Scanner scanner = null;
        try {
            scanner = new Scanner(testFile);
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        }
        String lineContent = scanner.nextLine();
        int i = 0;
        StringTokenizer st;
        while (scanner.hasNextLine()) {
            lineContent = scanner.nextLine();
            st = new StringTokenizer(lineContent, ",");
            rRup[i] = Double.parseDouble(st.nextToken());
            for (int j = 0; j < numMags + 1; j++) {
                if (j < numMags) {
                    vals[i][j] = Double.parseDouble(st.nextToken());
                } else {
                    sigma[i] = Double.parseDouble(st.nextToken());
                }
            }
            i++;
        }
        scanner.close();
    }

    /*
     * Checks if computed values are same as expected values. Different methods
     * are called for Finite Ruptures and Point Ruptures. Note that for finite
     * ruptures, 4 values are given for magnitudes 5,6,7,8. For point ruptures,
     * only 3 values are given corresponding to magnitudes 5, 6, 7.
     */
    private void doTest(boolean isFiniteRupture, double tolerance,
            int numlines, File inFile) {
        int[] mw = { 5, 6, 7, 8 };
        int numMags = 0;
        if (isFiniteRupture)
            numMags = 4;
        else
            numMags = 3;
        double[] r = new double[numlines];
        double[] sigma = new double[numlines];
        double[][] results;
        results = new double[numlines][];
        for (int i = 0; i < r.length; i++) {
            r[i] = 0.0;
            sigma[i] = 0.0;
            results[i] = new double[numMags + 1];
            for (int j = 0; j < numMags + 1; j++) {
                results[i][j] = 0.0;
            }
        }

        loadTestData(inFile, numMags, r, results, sigma);

        double expectedmean, computedmean;
        double expectedstddev, computedstddev;
        for (int i = 0; i < r.length; i++) {
            for (int j = 0; j < numMags; j++) {
                expectedmean = results[i][j];
                expectedstddev = sigma[i];
                if (isFiniteRupture) {
                    computedmean =
                            aw_2010_AttenRel.getMeanForFiniteRup(mw[j], r[i]);
                    computedstddev =
                            aw_2010_AttenRel.getStdDevForFiniteRup(r[i]);
                } else {
                    computedmean =
                            aw_2010_AttenRel.getMeanForPointRup(mw[j], r[i]);
                    computedstddev =
                            aw_2010_AttenRel.getStdDevForPointRup(r[i]);
                }
                assertEquals(expectedmean, computedmean, tolerance);
                assertEquals(expectedstddev, computedstddev, tolerance);
            }
        }
    }

    /*
     * Creates an EqkRupture object for a point source.
     */
    private EqkRupture getPointEqkRupture(double mag, Location hypo,
            double aveRake) {
        EvenlyGriddedSurfaceAPI rupSurf = new PointSurface(hypo);
        EqkRupture rup = new EqkRupture(mag, aveRake, rupSurf, hypo);
        return rup;
    }

    /*
     * Creates an EqkRupture object for a finite source.
     */
    private EqkRupture getFiniteEqkRupture(double aveDip,
            double lowerSeisDepth, double upperSeisDepth,
            FaultTrace faultTrace, double gridSpacing, double mag,
            Location hypo, double aveRake) {
        StirlingGriddedSurface rupSurf =
                new StirlingGriddedSurface(faultTrace, aveDip, upperSeisDepth,
                        lowerSeisDepth, gridSpacing);
        EqkRupture rup = new EqkRupture(mag, aveRake, rupSurf, hypo);
        return rup;
    }

    public void parameterChangeWarning(ParameterChangeWarningEvent event) {
    }

}
