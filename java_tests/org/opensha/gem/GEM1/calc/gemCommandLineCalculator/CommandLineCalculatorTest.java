// package org.opensha.gem.GEM1.calc.gemCommandLineCalculator;
package org.opensha.gem.GEM1.calc.gemCommandLineCalculator;

import org.apache.commons.configuration.ConfigurationException;
import org.junit.Test;

public class CommandLineCalculatorTest {

    /**
     * The calculator does not yet run if it is give to calculate for an
     * intensity measure type "MMI". This tests veryfies that. It is expected to
     * fail.
     * 
     * @throws ConfigurationException
     */
    @Test(expected = IllegalArgumentException.class)
    public void testCalculatorConfig() throws ConfigurationException {
        /*
         * (state at 2010-10-07): This lets the test fail as expected
         * (2010-10-07)
         */
        final String intensityMeasureTypeToTest = "MMI";
        /*
         * (state at 2010-10-07): This would let the test end successfull
         */
        // final String intensityMeasureTypeToTest = "PGA";
        CommandLineCalculator clc =
                new CommandLineCalculator("CalculatorConfig.properties");
        clc.setConfigItem(
                CalculatorConfigHelper.ConfigItems.INTENSITY_MEASURE_TYPE
                        .name(), intensityMeasureTypeToTest);
        clc.doCalculation();
    } // testCalculatorConfig()

} // class CommandLineCalculatorTest
