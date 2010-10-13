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

package org.opensha.commons.calc;

import static org.junit.Assert.*;

import org.junit.Test;
import org.opensha.commons.calc.GaussianDistCalc;
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;

/**
 * <p>
 * Title: TestGaussianDistCalc.java
 * </p>
 * <p>
 * Description: Tests the GaussianDistCalc class functions
 * </p>
 * <p>
 * Copyright: Copyright (c) 2002
 * </p>
 * <p>
 * Company:
 * </p>
 * 
 * @author not attributable
 * @version 1.0
 */

public class TestGaussianDistCalc {
    double tolerance = 1e-6;

    public TestGaussianDistCalc() {
    }

    @Test
    public void testGetExceedProbForNonSymmetricTruncation() {
        /**
         * We have two functions in Gaussian Dist Calc: 1. public static double
         * getExceedProb(double standRandVariable, int truncType, double
         * truncLevel) 2. public static double getExceedProb(double
         * standRandVariable, double lowerTruncLevel, double upperTruncLevel) If
         * we provide the same values for lowerTruncLevel and upperTruncLevel in
         * (2), we can check that the values we get is same as we get from (1)
         */
        double upperTruncLevel = 0.5;
        double lowerTruncLevel = -0.5;
        int truncType = 2;
        double truncLevel = 0.5;
        double stdRandVar;
        // check when standRandVariable > truncLevel
        stdRandVar = 1.0;
        double d1 =
                GaussianDistCalc.getExceedProb(stdRandVar, lowerTruncLevel,
                        upperTruncLevel);
        double d2 =
                GaussianDistCalc.getExceedProb(stdRandVar, truncType,
                        truncLevel);
        assertEquals(d1, d2, tolerance);

        // check when standRandVariable < -truncLevel
        stdRandVar = -1.0;
        d1 =
                GaussianDistCalc.getExceedProb(stdRandVar, lowerTruncLevel,
                        upperTruncLevel);
        d2 = GaussianDistCalc.getExceedProb(stdRandVar, truncType, truncLevel);
        assertEquals(d1, d2, tolerance);

        // check when -truncLevel < standRandVariable < truncLevel
        stdRandVar = 0.1;
        d1 =
                GaussianDistCalc.getExceedProb(stdRandVar, lowerTruncLevel,
                        upperTruncLevel);
        d2 = GaussianDistCalc.getExceedProb(stdRandVar, truncType, truncLevel);
        assertEquals(d1, d2, tolerance);

        // exception is thrown if upperTrunclevel<0 or lowerTruncLevel<0
        try {
            GaussianDistCalc.getExceedProb(stdRandVar, -lowerTruncLevel,
                    upperTruncLevel);
            fail("Should not reach here as lower trunc level should be positive");
        } catch (RuntimeException e) {
        }
    }

    @Test
    public void testMiscGetExceedProb() {
        // exception is thrown if truncType == 2 and truncLevel <= 0
        try {
            GaussianDistCalc.getExceedProb(1.0, 2, 0);
            fail("Should not reach here as lower trunc level should be positive");
        } catch (RuntimeException e) {
        }

        // exception is thrown if truncLevel < 0
        try {
            GaussianDistCalc.getExceedProb(1.0, 0, -0.1);
            fail("Should not reach here as lower trunc level should be positive");
        } catch (RuntimeException e) {
        }
        try {
            GaussianDistCalc.getExceedProb(1.0, 1, -0.1);
            fail("Should not reach here as lower trunc level should be positive");
        } catch (RuntimeException e) {
        }
        try {
            GaussianDistCalc.getExceedProb(1.0, 2, -0.1);
            fail("Should not reach here as lower trunc level should be positive");
        } catch (RuntimeException e) {
        }
    }

    @Test
    public void testMiscGetStdRandVar() {
        double exceedProb = 0.2;

        try {
            GaussianDistCalc.getStandRandVar(exceedProb, -0.1, -0.1, tolerance);
            fail("Should not reach here as upper level should be positive");
        } catch (RuntimeException e) {
        }

        try {
            GaussianDistCalc.getStandRandVar(exceedProb, 0., 1., tolerance);
            fail("Should not reach here as lower level should be negative");
        } catch (RuntimeException e) {
        }

        try {
            GaussianDistCalc.getStandRandVar(exceedProb, -1., 1., 0.9e-6);
            fail("Should not reach here as tolerance cannot be < 1e-6");
        } catch (RuntimeException e) {
        }

        try {
            GaussianDistCalc.getStandRandVar(exceedProb, -1., 1., 0.11);
            fail("Should not reach here as tolerance cannot be > 0.1");
        } catch (RuntimeException e) {
        }
    }

    @Test
    public void testGetStdRandVarForNonSymmetricTruncation() {
        /**
         * We have two functions in Gaussian Dist Calc: 1. public static double
         * getStandRandVar(double exceedProb, int truncType, double truncLevel,
         * double tolerance) 2. public static double getStandRandVar(double
         * exceedProb, double lowerTruncLevel, double upperTruncLevel, double
         * tolerance) If we provide the same values for lowerTruncLevel and
         * upperTruncLevel in (2), we can check that the values we get is same
         * as we get from (1)
         */
        double upperTruncLevel = 0.5;
        double lowerTruncLevel = -0.5;
        int truncType = 2;
        double truncLevel = 0.5;
        double prob;

        // if( exceedProb <= 0.5 && exceedProb > 0.0 )
        prob = 0.2;
        double d1 =
                GaussianDistCalc.getStandRandVar(prob, lowerTruncLevel,
                        upperTruncLevel, tolerance);
        double d2 =
                GaussianDistCalc.getStdRndVariable(prob, truncType, truncLevel,
                        tolerance);
        assertEquals(d1, d2, tolerance);

        // if ( exceedProb > 0.5 && exceedProb < 1.0 )
        prob = 0.7;
        d1 =
                GaussianDistCalc.getStandRandVar(prob, lowerTruncLevel,
                        upperTruncLevel, tolerance);
        d2 =
                GaussianDistCalc.getStdRndVariable(prob, truncType, truncLevel,
                        tolerance);
        assertEquals(d1, d2, tolerance);

        // if (exceedProb == 0.0)
        prob = 0.0;
        d1 =
                GaussianDistCalc.getStandRandVar(prob, lowerTruncLevel,
                        upperTruncLevel, tolerance);
        d2 =
                GaussianDistCalc.getStdRndVariable(prob, truncType, truncLevel,
                        tolerance);
        assertEquals(d1, d2, tolerance);

        // if (exceedProb == 1.0)
        prob = 1.0;
        d1 =
                GaussianDistCalc.getStandRandVar(prob, lowerTruncLevel,
                        upperTruncLevel, tolerance);
        d2 =
                GaussianDistCalc.getStdRndVariable(prob, truncType, truncLevel,
                        tolerance);
        assertEquals(d1, d2, tolerance);

        // if (exceedProb < 0) or (exceedProb > 1)
        prob = -0.7;
        try {
            d1 =
                    GaussianDistCalc.getStandRandVar(prob, lowerTruncLevel,
                            upperTruncLevel, tolerance);
            fail("should not reach here as probability is negative");
        } catch (RuntimeException e) {
        }

    }

    protected static EvenlyDiscretizedFunc getTestCDFVals() {
        EvenlyDiscretizedFunc func = new EvenlyDiscretizedFunc(-7.5, 151, 0.1);
        func.setTolerance(0.00001);

        func.set(-7.500, 0.00000000000003);
        func.set(-7.400, 0.00000000000007);
        func.set(-7.300, 0.00000000000014);
        func.set(-7.200, 0.00000000000030);
        func.set(-7.100, 0.00000000000063);
        func.set(-7.000, 0.00000000000129);
        func.set(-6.900, 0.00000000000262);
        func.set(-6.800, 0.00000000000526);
        func.set(-6.700, 0.00000000001048);
        func.set(-6.600, 0.00000000002067);
        func.set(-6.500, 0.00000000004036);
        func.set(-6.400, 0.00000000007805);
        func.set(-6.300, 0.00000000014947);
        func.set(-6.200, 0.00000000028347);
        func.set(-6.100, 0.00000000053238);
        func.set(-6.000, 0.00000000099012);
        func.set(-5.900, 0.00000000182358);
        func.set(-5.800, 0.00000000332605);
        func.set(-5.700, 0.00000000600765);
        func.set(-5.600, 0.00000001074622);
        func.set(-5.500, 0.00000001903640);
        func.set(-5.400, 0.00000003339612);
        func.set(-5.300, 0.00000005802207);
        func.set(-5.200, 0.00000009983440);
        func.set(-5.100, 0.00000017012231);
        func.set(-5.000, 0.00000028710500);
        func.set(-4.900, 0.00000047986955);
        func.set(-4.800, 0.00000079435267);
        func.set(-4.700, 0.00000130231565);
        func.set(-4.600, 0.00000211464338);
        func.set(-4.500, 0.00000340080306);
        func.set(-4.400, 0.00000541695305);
        func.set(-4.300, 0.00000854602119);
        func.set(-4.200, 0.00001335409733);
        func.set(-4.100, 0.00002066871577);
        func.set(-4.000, 0.00003168603461);
        func.set(-3.900, 0.00004811551887);
        func.set(-3.800, 0.00007237243427);
        func.set(-3.700, 0.00010783014541);
        func.set(-3.600, 0.00015914571377);
        func.set(-3.500, 0.00023267337367);
        func.set(-3.400, 0.00033698082293);
        func.set(-3.300, 0.00048348253664);
        func.set(-3.200, 0.00068720208079);
        func.set(-3.100, 0.00096767123560);
        func.set(-3.000, 0.00134996722324);
        func.set(-2.900, 0.00186588014039);
        func.set(-2.800, 0.00255519064153);
        func.set(-2.700, 0.00346702305311);
        func.set(-2.600, 0.00466122178265);
        func.set(-2.500, 0.00620967985875);
        func.set(-2.400, 0.00819752886943);
        func.set(-2.300, 0.01072408105972);
        func.set(-2.200, 0.01390339890832);
        func.set(-2.100, 0.01786435741803);
        func.set(-2.000, 0.02275006203619);
        func.set(-1.900, 0.02871649286457);
        func.set(-1.800, 0.03593026551383);
        func.set(-1.700, 0.04456543178248);
        func.set(-1.600, 0.05479928945388);
        func.set(-1.500, 0.06680722879345);
        func.set(-1.400, 0.08075671125630);
        func.set(-1.300, 0.09680054949574);
        func.set(-1.200, 0.11506973171771);
        func.set(-1.100, 0.13566610150762);
        func.set(-1.000, 0.15865525975900);
        func.set(-0.900, 0.18406009173192);
        func.set(-0.800, 0.21185533393828);
        func.set(-0.700, 0.24196357848479);
        func.set(-0.600, 0.27425306493856);
        func.set(-0.500, 0.30853753263572);
        func.set(-0.400, 0.34457830341314);
        func.set(-0.300, 0.38208864252738);
        func.set(-0.200, 0.42074031283329);
        func.set(-0.100, 0.46017210446634);
        func.set(0.000, 0.50000000000000);
        func.set(0.100, 0.53982789553366);
        func.set(0.200, 0.57925968716672);
        func.set(0.300, 0.61791135747262);
        func.set(0.400, 0.65542169658687);
        func.set(0.500, 0.69146246736428);
        func.set(0.600, 0.72574693506144);
        func.set(0.700, 0.75803642151521);
        func.set(0.800, 0.78814466606172);
        func.set(0.900, 0.81593990826808);
        func.set(1.000, 0.84134474024100);
        func.set(1.100, 0.86433389849238);
        func.set(1.200, 0.88493026828229);
        func.set(1.300, 0.90319945050426);
        func.set(1.400, 0.91924328874370);
        func.set(1.500, 0.93319277120655);
        func.set(1.600, 0.94520071054612);
        func.set(1.700, 0.95543456821752);
        func.set(1.800, 0.96406973448618);
        func.set(1.900, 0.97128350713543);
        func.set(2.000, 0.97724993796381);
        func.set(2.100, 0.98213564258197);
        func.set(2.200, 0.98609660109168);
        func.set(2.300, 0.98927591894028);
        func.set(2.400, 0.99180247113057);
        func.set(2.500, 0.99379032014125);
        func.set(2.600, 0.99533877821735);
        func.set(2.700, 0.99653297694689);
        func.set(2.800, 0.99744480935848);
        func.set(2.900, 0.99813411985961);
        func.set(3.000, 0.99865003277676);
        func.set(3.100, 0.99903232876440);
        func.set(3.200, 0.99931279791921);
        func.set(3.300, 0.99951651746336);
        func.set(3.400, 0.99966301917707);
        func.set(3.500, 0.99976732662633);
        func.set(3.600, 0.99984085428623);
        func.set(3.700, 0.99989216985459);
        func.set(3.800, 0.99992762756573);
        func.set(3.900, 0.99995188448114);
        func.set(4.000, 0.99996831396539);
        func.set(4.100, 0.99997933128423);
        func.set(4.200, 0.99998664590267);
        func.set(4.300, 0.99999145397881);
        func.set(4.400, 0.99999458304695);
        func.set(4.500, 0.99999659919694);
        func.set(4.600, 0.99999788535662);
        func.set(4.700, 0.99999869768435);
        func.set(4.800, 0.99999920564733);
        func.set(4.900, 0.99999952013045);
        func.set(5.000, 0.99999971289500);
        func.set(5.100, 0.99999982987769);
        func.set(5.200, 0.99999990016560);
        func.set(5.300, 0.99999994197793);
        func.set(5.400, 0.99999996660388);
        func.set(5.500, 0.99999998096360);
        func.set(5.600, 0.99999998925378);
        func.set(5.700, 0.99999999399235);
        func.set(5.800, 0.99999999667395);
        func.set(5.900, 0.99999999817642);
        func.set(6.000, 0.99999999900988);
        func.set(6.100, 0.99999999946763);
        func.set(6.200, 0.99999999971653);
        func.set(6.300, 0.99999999985053);
        func.set(6.400, 0.99999999992195);
        func.set(6.500, 0.99999999995964);
        func.set(6.600, 0.99999999997934);
        func.set(6.700, 0.99999999998952);
        func.set(6.800, 0.99999999999474);
        func.set(6.900, 0.99999999999738);
        func.set(7.000, 0.99999999999871);
        func.set(7.100, 0.99999999999937);
        func.set(7.200, 0.99999999999970);
        func.set(7.300, 0.99999999999986);
        func.set(7.400, 0.99999999999993);
        func.set(7.500, 0.99999999999997);

        return func;
    }

    /**
     * This compares the rusults of getCDF between +/- 7.5 SRVs with those
     * computed using Excel (the NORSDIST function). The difference is 0.3 % at
     * SRV=-4, and grows to 364 % (a factor of 3.64) at SRV=-7.5. The difference
     * is negligible for all positive CRVs (up to at least 7.5). Norm Abrahamson
     * says this is good enough for seismic hazard calculations.
     */
    @Test
    public void testGetCDF() {
        // first put Excel results into a faunction
        EvenlyDiscretizedFunc func = getTestCDFVals();

        for (int i = 0; i < func.getNum(); ++i) {

            double srv = func.getX(i);
            double prob = func.getY(i);
            double prob_computed = GaussianDistCalc.getCDF(srv);

            double ratio = prob_computed / prob;
            double rDiff = Math.abs(ratio - 1.0);

            System.out.println("SRV = " + (float) srv + "; Computed Prob = "
                    + prob_computed + ";  Ratio = " + prob_computed / prob);

            checkRatio(srv, Integer.MIN_VALUE, ratio, 3.64);
            checkRatio(srv, -4, ratio, 1.0035);
            if (srv == 0)
                assertEquals("Should be equal at srv == 0", prob,
                        prob_computed, 0.0);
            checkRDiff(srv, 0, rDiff, 0.000001);
        }
    }

    private static void checkRDiff(double srv, double srvMin, double rDiff,
            double maxRatio) {
        if (srv > srvMin) {
            assertTrue("Ratio of computed to actual prob should be less than "
                    + maxRatio + " for SRV > " + srvMin, rDiff < maxRatio);
        }
    }

    private static void checkRatio(double srv, double srvMin, double ratio,
            double maxRatio) {
        if (srv > srvMin) {
            assertTrue("Ratio of computed to actual prob should be less than "
                    + maxRatio + " for SRV > " + srvMin, ratio < maxRatio);
        }
    }

}
