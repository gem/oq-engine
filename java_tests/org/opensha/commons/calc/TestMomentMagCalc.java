package org.opensha.commons.calc;

import static org.junit.Assert.*;

import org.junit.Before;
import org.junit.Test;
import org.opensha.commons.util.DataUtils;

public class TestMomentMagCalc {

    @Before
    public void setUp() throws Exception {
    }

    @Test
    public void testGetMoment() {
        for (double moment = 1e10; moment < 1e30; moment *= 5) {
            double mag = MomentMagCalc.getMag(moment);
            double calcMoment = MomentMagCalc.getMoment(mag);
            double pDiff = DataUtils.getPercentDiff(calcMoment, moment);
            assertTrue(pDiff < 0.000001);
        }
    }

    @Test
    /**
     * This just checks against the formula I got from wikipedia
     */
    public void testGetMag() {
        for (double moment = 1e10; moment < 1e30; moment *= 5) {
            double calcMag = MomentMagCalc.getMag(moment);
            double mag = (2. / 3.) * StrictMath.log10(moment * 1e7) - 10.7;
            System.out.println("MAG: " + mag);
            assertEquals(mag, calcMag, 0.0001);
        }
        // fail("Not yet implemented");
    }

}
