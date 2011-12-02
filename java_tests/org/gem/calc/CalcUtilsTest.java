package org.gem.calc;

import static org.gem.calc.CalcTestHelper.makeHazardCurve;
import static org.gem.calc.CalcUtils.getGMV;
import static org.gem.calc.CalcUtils.assertPoissonian;
import static org.gem.calc.CalcUtils.assertVs30TypeIsValid;
import static org.junit.Assert.*;

import org.gem.calc.CalcUtils.InputValidationException;
import org.junit.Test;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.geo.BorderType;

import static org.gem.calc.CalcTestHelper.LOG_IMLS;
import static org.gem.calc.CalcTestHelper.makeTestERF;

public class CalcUtilsTest
{

    public static final double AREA_SRC_DISCRETIZATION = 0.01;
    public static final int NUM_MFD_PTS = 41;
    public static final BorderType BORDER_TYPE = BorderType.MERCATOR_LINEAR;

    @Test
    public void testGetGMV()
    {
        // technically, this is an invalid PoE value
        // we're just using this to test boundary behavior of getGMV
        // (since the highest PoE on this test curve is 1.0--the max valid value)
        Double highPoe = 1.1;
        // slightly lower than the lowest PoE in the test curve
        Double lowPoe = 1.1075602E-6;

        Double minIml = -5.298317366548036;  // log(0.005)
        Double maxIml = 0.7561219797213337;  // log(2.13)
        // expected interpolated value for poe = 0.5
        Double imlForPoe0_5 = -2.298526833020888;

        DiscretizedFuncAPI hazardCurve = makeHazardCurve(LOG_IMLS, 0.01, makeTestERF(0.01, 41, BorderType.MERCATOR_LINEAR));

        double delta = 0.00000009;
        // boundary tests:
        assertEquals(minIml, getGMV(hazardCurve, highPoe), delta);
        assertEquals(maxIml, getGMV(hazardCurve, lowPoe), delta);

        // interpolation test:
        assertEquals(imlForPoe0_5, getGMV(hazardCurve, 0.5), delta);
    }

    @Test
    public void testAssertPoissonian()
    {
        // This should succeed without any errors.
        assertPoissonian(makeTestERF(AREA_SRC_DISCRETIZATION, NUM_MFD_PTS, BORDER_TYPE));
    }

    @Test(expected=RuntimeException.class)
    public void testAssertPoissonianBadData()
    {
        assertPoissonian(new NonPoissonianERF());
    }

    @Test
    public void testAssertVs30TypeIsValid()
    {
        // These should succeed without any errors
        assertVs30TypeIsValid("Measured");
        assertVs30TypeIsValid("Inferred");
    }

    @Test(expected=InputValidationException.class)
    public void testAssertVs30TypeIsValidThrows()
    {
        // The vs30 type is case sensitive;
        // "measured" is not in the VS30  type enum.
        assertVs30TypeIsValid("measured");
    }
}
