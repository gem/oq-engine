package org.gem.calc;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

import org.apache.commons.math.ArgumentOutsideDomainException;

import static org.junit.Assert.*;
import org.junit.Test;
import org.opensha.commons.data.DataPoint2D;
import org.opensha.commons.data.function.DiscretizedFuncAPI;

import static org.gem.calc.UHSCalculator.initHazCurve;
import static org.gem.calc.UHSCalculator.interpolatePoe;

public class UHSCalculatorTest
{

    /**
     * Test hazard curve initialization.
     */
    @Test
    public void testInitHazCurve()
    {
        Double[] imls = { 0.005, 0.007, 0.0098, 0.0137, 0.0192, 0.0269, 0.0376,
                0.0527, 0.0738, 0.103, 0.145, 0.203, 0.284, 0.397, 0.556,
                0.778, 1.09, 1.52, 2.13 };

        DiscretizedFuncAPI hc = initHazCurve(imls);

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

        assertArrayEquals(imls, hcImls.toArray(new Double[hcImls.size()]));
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
}
