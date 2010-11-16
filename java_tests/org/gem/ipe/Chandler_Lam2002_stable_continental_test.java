package org.gem.ipe;

import static org.junit.Assert.assertEquals;

import java.io.File;
import java.util.Iterator;
import java.util.List;

import javax.swing.filechooser.FileSystemView;

import org.apache.commons.configuration.Configuration;
import org.apache.commons.configuration.ConfigurationException;
import org.apache.commons.configuration.PropertiesConfiguration;
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
import org.opensha.sha.faultSurface.PointSurface;

public class Chandler_Lam2002_stable_continental_test {

    private Chandler_Lam2002_stable_continental chandler_Lam2002_stable_continental =
            null;
    private Configuration config = null;
    // the current dir is something like "bin", parent is something like
    // "opengem" which contains this:
    private final String testDataDir = "/java_tests/data/";
    private final String testDataFile =
            "ipe_chandler_lam_2002_stable_continental_region.txt";
    private final String token_magnitudes = "magnitudes";
    private final String token_distances = "distances";
    private final String token_magnitude = "m";
    private final String token_distance = "d";
    private final String token_dashSeparator = "-";
    private final String token_dotSeparator = ".";

    private final double tolerance = 1E-8;

    @Before
    public void setUp() {
        chandler_Lam2002_stable_continental =
                new Chandler_Lam2002_stable_continental(
                        new ParameterChangeWarningListener() {
                            @Override
                            public void parameterChangeWarning(
                                    ParameterChangeWarningEvent event) {
                                return;
                            }
                        });
        chandler_Lam2002_stable_continental.setParamDefaults();
    } // setUp()

    @After
    public void tearDown() {
        /*
         * just do this... if any, it will destroy statics, unclosed streams,
         * files ...
         */
        chandler_Lam2002_stable_continental = null;
    } // tearDown()

    /**
     * Helper to retrieve the test data<br>
     * <br>
     * 
     * A configuration object containing the test data. The data is accessible
     * with keys constructed from magnitude and epicentral distance.<br>
     * <br>
     * E.g. v.5.35 is the key for the value computed for magnitude 5 and
     * epicentral distance 35 km<br>
     * 
     * @return Configuration A configuration object
     */
    private Configuration getTestData() {
        if (config == null) {
            FileSystemView fsv = FileSystemView.getFileSystemView();
            File testData =
                    fsv.getChild(fsv.getParentDirectory(new File(".")),
                            testDataDir + testDataFile);
            // File testData =
            // new File(ClassLoader.getSystemResource(testDataFile)
            // .toURI());
            config = new PropertiesConfiguration();
            try {
                ((PropertiesConfiguration) config).load(testData);
            } catch (ConfigurationException e) {
                throw new RuntimeException(e);
            }
        }
        return config;
    } // getTestData()

    private double[] getDoublesFromTestData(String key) {
        List<String> l = null;
        l = getTestData().getList(key);
        double[] doubles = new double[l.size()];
        Iterator<String> iterator = l.iterator();
        int i = 0;
        while (iterator.hasNext()) {
            String m = iterator.next();
            doubles[i] = Double.parseDouble(m);
            ++i;
        } // while
        return doubles;
    } // getDoublesFromTestData()

    @Test
    public void testGetMean() {
        double[] magnitudes = getDoublesFromTestData(token_magnitudes);
        double[] epicentralDistances = getDoublesFromTestData(token_distances);
        // System.out.println("m4 = " + magnitudes[0] + "m3 = " + magnitudes[1]
        // + "m2 = " + magnitudes[2]);
        // System.out.println("d4 = " + epicentralDistances[0] + "d3 = "
        // + epicentralDistances[1] + "d2 = " + epicentralDistances[2]);
        for (int i = 0; i < magnitudes.length; i++) {
            for (int j = 0; j < epicentralDistances.length; j++) {
                double magnitude = magnitudes[i];
                double epicentralDistance = epicentralDistances[j];
                String key =
                        token_magnitude + token_dotSeparator + magnitude
                                + token_dashSeparator + token_distance
                                + token_dotSeparator + epicentralDistance;
                // System.out.println("key = " + key);
                double expected = getTestData().getDouble(key);
                double calculated =
                        chandler_Lam2002_stable_continental.getMean(magnitude,
                                epicentralDistance);
                /*
                 * This tests with a tolerance in percent. The tolerance is
                 * given in percent.
                 */
                double tolerance = 1.0;
                assertEquals(100, (calculated / expected) * 100, tolerance);
            } // for
        } // for

    }

    /**
     * This test compares the results of the getMean() and getStdDev() methods
     * when setting a Site and a EqkRupture object with the results of the get
     * getMeanForPointRup(m,r) and getTotalStdDevForPointRup(r) methods when
     * passing directly the magnitude and hypocentral distance values. This test
     * is meant to validate if the Site and EqkRupture parameters are passed
     * correctly to the AttenuationRelationship object and correct distinction
     * is done between point and finite rupture. The average rake is not needed
     * by the IPE but is used to define the EqkRupture object. In the test, the
     * Site is defined on the same latitude as the hypocenter but shifted 0.1
     * degrees East.
     * 
     */
    @Test
    public void testGetMeanWhenSettingSiteAndRupture() {
        // create a site and a rupture and their epicentral distance
        double magnitude = 5.0;
        double aveRake = 0.0;
        Location hypo = new Location(0.0, 0.0, 5.0);
        Site site = new Site(new Location(0.0, 0.1, 0.0));
        EqkRupture rup = getPointEqkRupture(magnitude, hypo, aveRake);
        double epicentralDistance =
                LocationUtils.horzDistance(hypo, site.getLocation());
        // Setting site and rupture should propagate the epicentral distance and
        // the magnitude.
        chandler_Lam2002_stable_continental.setSite(site);
        chandler_Lam2002_stable_continental.setEqkRupture(rup);
        double meanDistanceFromSiteMagnitudeFromRupture =
                chandler_Lam2002_stable_continental.getMean();
        double standardDeviationFromParameterApi =
                chandler_Lam2002_stable_continental.getStdDev();
        double meanDirect =
                chandler_Lam2002_stable_continental.getMean(magnitude,
                        epicentralDistance);
        double standardDeviationDirect =
                chandler_Lam2002_stable_continental.getStdDev();
        assertEquals(meanDistanceFromSiteMagnitudeFromRupture, meanDirect,
                tolerance);
        assertEquals(standardDeviationFromParameterApi,
                standardDeviationDirect, 0.0);
    }

    /**
     * This test checks that the Chandler_Lam2002_stable_continental object
     * throws a warning exception when a magnitude value < 3.3 is passed. In
     * this test, the point source is defined with magnitude 3.2 (too low). The
     * average rake is not needed by the IPE but is used to define the
     * EqkRupture object. Hypocenter coordinates are lat, lon, depth in km.
     * 
     */
    @Test(expected = org.opensha.commons.exceptions.WarningException.class)
    public void magnitudeValueTooSmall() {
        double mag = 3.2;
        double aveRake = 0.0;
        Location hypo = new Location(0.0, 0.0, 5.0);
        EqkRupture rup = getPointEqkRupture(mag, hypo, aveRake);
        chandler_Lam2002_stable_continental.setEqkRupture(rup);
    }

    /**
     * This test checks that the Chandler_Lam2002_stable_continental object
     * throws a warning exception when a magnitude value > 8 is passed. In this
     * test, the point source is defined with magnitude 8.1 (too high). The
     * average rake is not needed by the IPE but is used to define the
     * EqkRupture object. Hypocenter coordinates are lat, lon, depth in km.
     */
    @Test(expected = org.opensha.commons.exceptions.WarningException.class)
    public void magnitudeValueTooLarge() {
        double mag = 8.1;
        double aveRake = 0.0;
        Location hypo = new Location(0.0, 0.0, 5.0);
        EqkRupture rup = getPointEqkRupture(mag, hypo, aveRake);
        chandler_Lam2002_stable_continental.setEqkRupture(rup);
    }

    /**
     * Check if the method setValue() in the classes DistanceEpicentralParameter
     * and DistanceHypoParameter behave in the same way... The question is if
     * they both throw an InvalidRangeException when necessary. It may not be
     * thrown for DistanceEpicentralParameter.setValue()
     * 
     * --> In the method calcValueFromSiteAndEqkRup in
     * DistanceEpicentralParameter, the distance value is set using the
     * setValueIgnoreWarning method while in DistanceHypoParameter the distance
     * is set using setValue (and this gives an exception if the distance is
     * outside the allowed range). So probably it is correct when using
     * DistanceEpicentralParameter.setValue() an exception is *not* thrown
     * 
     * This test checks that the Chandler_Lam2002_stable_continental object
     * throws a warning exception when a closest distance to rupture > 300 km is
     * passed.
     */
    // @Test(expected = org.opensha.commons.exceptions.WarningException.class)
    // public void closestDistanceToRuptureTooLarge() {
    // double mag = 7.9;
    // double aveRake = 0.0;
    // Location hypo = new Location(0.0, 0.0, 5.0);
    // EqkRupture rup = getPointEqkRupture(mag, hypo, aveRake);
    // // to far away:
    // Site site = new Site(new Location(90.0, 90.0, 0.0));
    // chandler_Lam2002_stable_continental.setEqkRupture(rup);
    // chandler_Lam2002_stable_continental.setSite(site);
    // }

    /*
     * Creates an EqkRupture object for a point source.
     */
    private EqkRupture getPointEqkRupture(double mag, Location hypo,
            double aveRake) {
        EvenlyGriddedSurfaceAPI rupSurf = new PointSurface(hypo);
        EqkRupture rup = new EqkRupture(mag, aveRake, rupSurf, hypo);
        return rup;
    }

} // class Chandler_Lam2002_stable_continental_test
