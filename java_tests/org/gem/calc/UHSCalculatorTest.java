package org.gem.calc;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

import static org.junit.Assert.*;
import org.junit.Test;
import org.opensha.commons.data.DataPoint2D;
import org.opensha.commons.data.function.DiscretizedFuncAPI;

import static org.gem.calc.UHSCalculator.initHazCurves;

public class UHSCalculatorTest {

    /**
     * Test for proper hazard curve initialization.
     */
    @Test
    public void testInitHazCurves() {
        Double[] periods = {0.025, 0.45, 2.5};
        Double[] imls = {
                0.005, 0.007, 0.0098, 0.0137, 0.0192, 0.0269,
                0.0376, 0.0527, 0.0738, 0.103, 0.145, 0.203,
                0.284, 0.397, 0.556, 0.778, 1.09, 1.52, 2.13};

        Map<Double, DiscretizedFuncAPI> hazCurveMap = initHazCurves(periods, imls);
        
        // should be 1 hazard curve per period
        assertEquals(periods.length, hazCurveMap.values().size());

        for (double p : periods) {
            DiscretizedFuncAPI hc = hazCurveMap.get(p);
            assertNotNull(hc);

            List<Double> hcImls = new ArrayList<Double>();
            Iterator<DataPoint2D> iter = hc.getPointsIterator();

            if (!iter.hasNext()) {
                fail("Hazard Curve has no points.");
            }

            while (iter.hasNext()) {
                DataPoint2D dp = iter.next();
                // Y-values should be initialized to 1.0 by default
                assertEquals(1.0, dp.getY(), 0.0);

                hcImls.add(dp.getX());
            }

            assertArrayEquals(imls, hcImls.toArray(new Double[hcImls.size()]));
        }
    }
}
