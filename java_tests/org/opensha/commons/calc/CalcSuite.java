package org.opensha.commons.calc;

import org.junit.runner.RunWith;
import org.junit.runners.Suite;
import org.opensha.commons.geo.LocationUtilsTest;

@RunWith(Suite.class)
@Suite.SuiteClasses({ LocationUtilsTest.class, TestGaussianDistCalc.class,
        TestMomentMagCalc.class })
public class CalcSuite {

    public static void main(String args[]) {
        org.junit.runner.JUnitCore.runClasses(CalcSuite.class);
    }
}
