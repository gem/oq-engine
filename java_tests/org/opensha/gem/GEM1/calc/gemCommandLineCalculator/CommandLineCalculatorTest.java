// package org.opensha.gem.GEM1.calc.gemCommandLineCalculator;
package org.opensha.gem.GEM1.calc.gemCommandLineCalculator;

import static org.junit.Assert.assertTrue;

import java.util.Map;

import org.apache.commons.configuration.ConfigurationException;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.opensha.commons.data.Site;
import org.opensha.gem.GEM1.calc.gemCommandLineCalculator.CalculatorConfigHelper.CalculationMode;
import org.opensha.gem.GEM1.calc.gemCommandLineCalculator.CalculatorConfigHelper.ConfigItems;
import org.opensha.gem.GEM1.calc.gemCommandLineCalculator.CalculatorConfigHelper.IntensityMeasure;

public class CommandLineCalculatorTest {

    /**
     * Do this before every test method:
     */
    @Before
    public void setUp() {
    }

    /**
     * Do this after every test method:
     */
    @After
    public void tearDown() {
    }

    /**
     * Looks for the config file only in the class path, no where else. Looks
     * for a file called "CalculatorConfig.properties".
     */
    private String searchForConfigFile() {
        final String fileName = "CalculatorConfig.properties";
        final String classPathProperty = System.getProperty("java.class.path");
        final String userDirProperty = System.getProperty("user.dir");
        final String javaHomeProperty = System.getProperty("java.home");
        System.out.println(classPathProperty);
        System.out.println(userDirProperty);
        System.out.println(javaHomeProperty);
        return classPathProperty;
    }

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
        // final String intensityMeasureTypeToTest = "MMI";
        final String intensityMeasureTypeToTest = IntensityMeasure.MMI.type();
        /*
         * 
         * (state at 2010-10-07): This would let the test end successfully.
         */
        // final String intensityMeasureTypeToTest =
        // IntensityMeasure.PGA.type();
        CommandLineCalculator clc =
                new CommandLineCalculator("CalculatorConfig.properties");
        clc.setConfigItem(ConfigItems.INTENSITY_MEASURE_TYPE.name(),
                intensityMeasureTypeToTest);
        clc.doCalculation();
    } // testCalculatorConfig()

    @Test
    public void testDoProbabilisticEventBasedCalcThroughMonteCarloLogicTreeSampling()
            throws ConfigurationException {
        searchForConfigFile();
        Map<Site, Double> result = null;
        CommandLineCalculator clc =
                new CommandLineCalculator("CalculatorConfig.properties");
        String key = CalculatorConfigHelper.ConfigItems.CALCULATION_MODE.name();
        String value = CalculationMode.MONTE_CARLO.value();
        // String calculationModeFull = CalculationMode.FULL.value();
        clc.setConfigItem(key, value);
        result = clc.doCalculationProbabilisticEventBased();
        Object o = null;
        assertTrue(result != null);
        assertTrue(result instanceof Map);
        assertTrue(result.size() > 0);
        assertTrue((o = result.keySet().iterator().next()) instanceof Site);
        assertTrue(result.get(o) instanceof Double);
    } // testDoProbabilisticEventBasedCalcThroughMonteCarloLogicTreeSampling()

    // @Test
    // public void testDoProbabilisticEventBasedCalcForAllLogicTreeEndBranches()
    // {
    // Map<Site, Double>
    // }
} // class CommandLineCalculatorTest
