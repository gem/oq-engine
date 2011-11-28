package org.gem.calc;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Iterator;
import java.util.List;

import static org.junit.Assert.*;

import org.junit.Test;
import org.opensha.commons.data.DataPoint2D;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.geo.BorderType;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.imr.param.SiteParams.Vs30_TypeParam.Vs30Type;

import static org.gem.calc.UHSCalculator.initHazCurve;
import static org.gem.calc.UHSCalculator.interpolatePoe;
import static org.gem.calc.CalcTestHelper.IMLS;
import static org.gem.calc.CalcTestHelper.LOG_IMLS;
import static org.gem.calc.CalcTestHelper.makeTestERF;
import static org.gem.calc.CalcTestHelper.makeTestImrMap;
import static org.gem.calc.CalcTestHelper.makeTestSite;
import static org.gem.calc.CalcUtils.InputValidationException;

public class UHSCalculatorTest
{

    public static final Double[] PERIODS = {0.025, 0.45, 2.5};
    public static final Double[] POES = {0.1, 0.02};
    public static final double MAX_DISTANCE = 200.0;
    public static final double AREA_SRC_DISCRETIZATION = 0.1;
    public static final int NUM_MFD_PTS = 40;
    public static final BorderType BORDER_TYPE = BorderType.GREAT_CIRCLE;
    /**
     * Expected UHS curve for PoE = 0.1
     */
    public static final Double[] UHS_CURVE_POE_0_1 = {0.2774217067746703, 0.32675005743942004, 0.05309858927852786};
    /**
     * Expected UHS curve for PoE = 0.02
     */
    public static final Double[] UHS_CURVE_POE_0_02 = {0.5667404129191248, 0.6185688023781438, 0.11843417899553109};

    public static final Double[] UNSORTED_ARRAY = {-0.1, 0.1, 0.0};
    public static final Double [] IMLS_SHORT = {Math.log(0.005), Math.log(0.007)};
    private static final EqkRupForecastAPI ERF = makeTestERF(AREA_SRC_DISCRETIZATION, NUM_MFD_PTS, BORDER_TYPE);

    private static List<Double[]> expectedUHSResults()
    {
        List<Double[]> results = new ArrayList<Double[]>();
        results.add(UHS_CURVE_POE_0_1);
        results.add(UHS_CURVE_POE_0_02);
        return results;
    }

    /**
     * Test hazard curve initialization.
     */
    @Test
    public void testInitHazCurve()
    {
        DiscretizedFuncAPI hc = initHazCurve(IMLS);

        List<Double> hcImls = new ArrayList<Double>();
        Iterator<DataPoint2D> iter = hc.getPointsIterator();
        if (!iter.hasNext())
        {
            fail("Hazard Curve has no points.");
        }
        while (iter.hasNext())
        {
            DataPoint2D dp = iter.next();
            // Y-values should be initialized to 1.0 by default
            assertEquals(1.0, dp.getY(), 0.0);

            hcImls.add(dp.getX());
        }

        assertArrayEquals(IMLS, hcImls.toArray(new Double[hcImls.size()]));
    }

    /**
     * Test the super-basic linear interpolation.
     */
    @Test
    public void testInterpolatePoe() {
        double period1, period2, poe1, poe2;

        period1 = 0.0;
        period2 = 0.5;
        poe1 = 0.0;
        poe2 = 1.0;

        assertEquals(0.5, interpolatePoe(period1, period2, poe1, poe2, 0.25), 0.0);
    }

    @Test(expected=InputValidationException.class)
    public void testConstructorNullPoEs()
    {
        new UHSCalculator(new Double[1], null, new Double[2], ERF, null, 0.0);
    }

    @Test(expected=InputValidationException.class)
    public void testConstructorNullPeriods()
    {
        new UHSCalculator(null, new Double[1], new Double[2], ERF, null, 0.0);
    }

    @Test(expected=InputValidationException.class)
    public void testConstructorNullImls()
    {
        new UHSCalculator(new Double[1], new Double[1], null, ERF, null, 0.0);
    }

    @Test(expected=InputValidationException.class)
    public void testConstructorPeriodsTooShort()
    {
        new UHSCalculator(new Double[0], new Double[1], IMLS_SHORT, ERF, null, 0.0);
    }

    @Test(expected=InputValidationException.class)
    public void testConstructorPoEsTooShort()
    {
        new UHSCalculator(new Double[1], new Double[0], IMLS_SHORT, ERF, null, 0.0);
    }

    @Test(expected=InputValidationException.class)
    public void testConstructorImlsTooShort()
    {
        new UHSCalculator(new Double[1], new Double[1], new Double[1], ERF, null, 0.0);
    }

    @Test(expected=InputValidationException.class)
    public void testConstructorUnsortedPeriods()
    {
        new UHSCalculator(UNSORTED_ARRAY, new Double[1], new Double[1], ERF, null, 0.0);
    }

    @Test(expected=InputValidationException.class)
    public void testConstructorUnsortedPoEs()
    {
        new UHSCalculator(new Double[1], UNSORTED_ARRAY, new Double[1], ERF, null, 0.0);
    }

    @Test(expected=InputValidationException.class)
    public void testConstructorUnsortedImls()
    {
        new UHSCalculator(new Double[1], new Double[1], UNSORTED_ARRAY, ERF, null, 0.0);
    }

    @Test(expected=RuntimeException.class)
    public void testConstructorNonPoissonianErf()
    {
        new UHSCalculator(new Double[1], new Double[1], IMLS_SHORT,
                          new NonPoissonianERF(), null, 0.0);
    }

    /**
     * Test the full UHS computation.
     */
    @Test
    public void testComputeUHS()
    {
        UHSCalculator uhsCalc = new UHSCalculator(
                PERIODS, POES, LOG_IMLS.toArray(new Double[LOG_IMLS.size()]),
                ERF, makeTestImrMap(), MAX_DISTANCE);

        List<Double[]> expected = expectedUHSResults();
        List<Double[]> actual = uhsCalc.computeUHS(makeTestSite());

        assertEquals(expected.size(), actual.size());
        for (int i = 0; i < expected.size(); i++)
        {
            assertTrue(Arrays.equals(expected.get(i), actual.get(i)));
        }
    }

    /**
     * Test the full UHS computation using the more 'primitive'
     * function.
     */
    @Test
    public void testComputeUHS2()
    {
        UHSCalculator uhsCalc = new UHSCalculator(
                PERIODS, POES, LOG_IMLS.toArray(new Double[LOG_IMLS.size()]),
                ERF, makeTestImrMap(), MAX_DISTANCE);

        List<Double[]> expected = expectedUHSResults();

        String vs30Type = Vs30Type.Measured.toString();
        double lat, lon, vs30Value, depthTo1pt0KMPS, depthTo2pt5KMPS;
        lat = 0.0;
        lon = 0.0;
        vs30Value = 760.0;
        depthTo1pt0KMPS = 100.0;
        depthTo2pt5KMPS = 1.0;

        List<Double[]> actual = uhsCalc.computeUHS(
                lat, lon, vs30Type, vs30Value,
                depthTo1pt0KMPS, depthTo2pt5KMPS);

        assertEquals(expected.size(), actual.size());
        for (int i = 0; i < expected.size(); i++)
        {
            assertTrue(Arrays.equals(expected.get(i), actual.get(i)));
        }
    }

    @Test(expected=InputValidationException.class)
    public void testComputeUHSThrowsOnInvalidVs30Type()
    {
        UHSCalculator uhsCalc = new UHSCalculator(
                PERIODS, POES, LOG_IMLS.toArray(new Double[LOG_IMLS.size()]),
                ERF, makeTestImrMap(), MAX_DISTANCE);

        // vs30Type is case-sensitive
        uhsCalc.computeUHS(0, 0, "measured", 0, 0, 0);
    }
}
