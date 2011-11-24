package org.gem.calc;

import static org.gem.calc.DisaggregationTestHelper.makeHazardCurve;
import static org.gem.calc.CalcUtils.getGMV;
import static org.junit.Assert.*;

import org.junit.Test;
import org.opensha.commons.data.function.DiscretizedFuncAPI;

public class CalcUtilsTest
{

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

        DiscretizedFuncAPI hazardCurve = makeHazardCurve();

        double delta = 0.00000009;
        // boundary tests:
        assertEquals(minIml, getGMV(hazardCurve, highPoe), delta);
        assertEquals(maxIml, getGMV(hazardCurve, lowPoe), delta);

        // interpolation test:
        assertEquals(imlForPoe0_5, getGMV(hazardCurve, 0.5), delta);
    }

}
