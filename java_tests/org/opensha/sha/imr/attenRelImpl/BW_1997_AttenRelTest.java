package org.opensha.sha.imr.attenRelImpl;

import static org.junit.Assert.assertEquals;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.opensha.commons.data.Site;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.imr.param.PropagationEffectParams.WarningDoublePropagationEffectParameter;

import junit.framework.TestCase;

public class BW_1997_AttenRelTest extends TestCase {
    private BW_1997_AttenRel bw_1997_AttenRel;

    @Before
    public void setUp() {
        /*
         * The ParameterChangeWarningListener is a nuisance and a dummy. Other
         * tests implement the interface just to be able to create the
         * prediction equation class. That can not be the way either!
         */
        bw_1997_AttenRel =
                new BW_1997_AttenRel(new ParameterChangeWarningListener() {
                    @Override
                    public void parameterChangeWarning(
                            ParameterChangeWarningEvent event) {
                        return;
                    }
                });
    } // setUp()

    @After
    public void tearDown() {
        // just do this... if any, it will destroy statics, unclosed streams,
        // files ...
        bw_1997_AttenRel = null;
    } // tearDown()

    @Test
    public void testGetMean() {
        int[] magnitudes = { 5, 6, 7, 8, 9 };
        int[] epicentralDistances =
                { 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 30, 40, 50, 60, 70, 80,
                        90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190,
                        200 };
        // one array of doubles per magnitue (i.e. 5, 6, 7, 8, 9)
        // these are the results provided by Damiano's spread sheet
        double[][] results =
                {
                        { 9.52, 8.56, 8, 7.6, 7.29, 7.04, 6.82, 6.64, 6.48,
                                6.33, 5.37, 4.81, 4.41, 4.1, 3.85, 3.63, 3.45,
                                3.29, 3.14, 3.01, 2.89, 2.78, 2.67, 2.58, 2.49,
                                2.4, 2.33, 2.25, 2.18 },
                        { 10.69, 9.73, 9.17, 8.77, 8.46, 8.21, 7.99, 7.81,
                                7.65, 7.5, 6.54, 5.98, 5.58, 5.27, 5.02, 4.8,
                                4.62, 4.46, 4.31, 4.18, 4.06, 3.95, 3.84, 3.75,
                                3.66, 3.57, 3.5, 3.42, 3.35 },
                        { 11.86, 10.9, 10.34, 9.94, 9.63, 9.38, 9.16, 8.98,
                                8.82, 8.67, 7.71, 7.15, 6.75, 6.44, 6.19, 5.97,
                                5.79, 5.63, 5.48, 5.35, 5.23, 5.12, 5.01, 4.92,
                                4.83, 4.74, 4.67, 4.59, 4.52 },
                        { 13.03, 12.07, 11.51, 11.11, 10.8, 10.55, 10.33,
                                10.15, 9.99, 9.84, 8.88, 8.32, 7.92, 7.61,
                                7.36, 7.14, 6.96, 6.8, 6.65, 6.52, 6.4, 6.29,
                                6.18, 6.09, 6, 5.91, 5.84, 5.76, 5.69 },
                        { 14.2, 13.24, 12.68, 12.28, 11.97, 11.72, 11.5, 11.32,
                                11.16, 11.01, 10.05, 9.49, 9.09, 8.78, 8.53,
                                8.31, 8.13, 7.97, 7.82, 7.69, 7.57, 7.46, 7.35,
                                7.26, 7.17, 7.08, 7.01, 6.93, 6.86 } }; // double[][]
        for (int i = 0; i < magnitudes.length; i++) {
            for (int j = 0; j < epicentralDistances.length; j++) {
                int magnitude = magnitudes[i];
                int epicentralDistance = epicentralDistances[j];
                double expected = results[i][j];
                // tolerance in percent
                double tolerance = 1.0;
                double calculated =
                        bw_1997_AttenRel.getMean(magnitude, epicentralDistance);
                /*
                 * This would be a test with an absolute tolerance -> not good.
                 */
                // assertEquals("mag = " + magnitude
                // + " distance = " + epicentralDistance
                // + " expected result = " + expected,
                // expected, bw_1997_AttenRel
                // .getMean(magnitude, epicentralDistance), 0.1);
                /*
                 * This tests with a tolerance in percent.
                 */
                assertEquals(100, (calculated / expected) * 100, tolerance);
            } // for
        } // for
    } // testGetMean

    public void testStdDev() {
        assertEquals(
                "The standard deviation of this intensity prediction equation is zero.",
                0.0, bw_1997_AttenRel.getStdDev());
    } // testStdDev()

    /**
     * This tests the OpenSHA parameter mechanism of</br> (</br>
     * org.opensha.sha.imr.param.
     * PropagationEffectParams.WarningDoublePropagationEffectParameter</br>
     * )</br> respectively (</br> org.opensha.commons.param.Parameter</br>
     * )</br>
     * 
     * In the OpenSHA program flow the parameters are set to the
     * AttenuationRelation subclasses when a ParameterChangeEvent is fired. E.g.
     * here, this happens with the call
     * bw_1997_AttenRel.setEqkRupture(eqkRupture).
     */
    public void testParameterClasses() {
        double mag = 5.0;
        double aveRake = 0.0;
        Location hypo = new Location(0.0, 0.0, 5.0);
        Location location = new Location(0.0, 0.1, 0.0);
        EqkRupture eqkRupture =
                PredictionEquationTestHelper.getPointEqkRupture(mag, hypo,
                        aveRake);
        double epicentralDistance = LocationUtils.horzDistance(hypo, location);
        /*
         * This is what we want to test: The following call triggers a call
         * chain that finally calls
         * WarningDoublePropagationEffectParameter.setValue(), which then fires
         * a ParameterChangeEvent which sets the parameters correctly in the
         * attenuation relation equation (e.g. class BW_1997_AttenRel).
         */
        bw_1997_AttenRel.setSite(new Site(location));
        /*
         * dito
         */
        bw_1997_AttenRel.setEqkRupture(eqkRupture);
        /*
         * These are the equation's results if if parameters are set by the
         * parameter change event:
         */
        double meanParameterListener = bw_1997_AttenRel.getMean();
        double stdDevParameterListener = bw_1997_AttenRel.getStdDev();
        /*
         * These are the results of the directly called calculation method(s):
         */
        double meanDirect = bw_1997_AttenRel.getMean(mag, epicentralDistance);
        double stdDevDirect = bw_1997_AttenRel.getStdDev();
        /*
         * If the results match, we take that as a proof that parameters have
         * been been properly set by the ParameterChangeEvent mechanism.
         * 
         * They should be exactly equal, do not specify a tolerance to the
         * assertion methods (as done in other tests).
         */
        assertEquals(meanParameterListener, meanDirect);
        assertEquals(stdDevParameterListener, stdDevDirect);
    }

} // class TestCase
