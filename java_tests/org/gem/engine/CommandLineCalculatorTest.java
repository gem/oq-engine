// package org.opensha.gem.GEM1.calc.gemCommandLineCalculator;
package org.gem.engine;

import static org.junit.Assert.assertTrue;

import java.util.Map;

import org.apache.commons.configuration.ConfigurationException;
import org.gem.engine.CalculatorConfigHelper;
import org.gem.engine.CommandLineCalculator;
import org.gem.engine.CalculatorConfigHelper.CalculationMode;
import org.gem.engine.CalculatorConfigHelper.ConfigItems;
import org.gem.engine.CalculatorConfigHelper.IntensityMeasure;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.opensha.commons.data.Site;

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

    /**
     * Tests the probabilistic event based hazard calc through Monte Carlo logic
     * tree sampling.</br> If this test passes, i.e.</br> - all configurations
     * needed are given in the config file</br> - all needed objects of type
     * org.opensha.commons.param.Parameter are properly instantiated</br> - the
     * application workflow is not interrupted
     * 
     * @throws ConfigurationException
     */
    @Test
    public void testDoProbabilisticEventBasedCalcMonteCarlo()
            throws ConfigurationException {
        CommandLineCalculator clc =
                new CommandLineCalculator("CalculatorConfig.properties");
        String key = CalculatorConfigHelper.ConfigItems.CALCULATION_MODE.name();
        String mode = CalculationMode.MONTE_CARLO.value();
        // String calculationModeFull = CalculationMode.FULL.value();
        clc.setConfigItem(key, mode);
        testDoProbabilisticEventBasedCalc(clc);
    }

    /**
     * Tests the probabilistic event based hazard calc for the full logic tree
     * sampling.</br> If this test passes, i.e.</br> - all configurations needed
     * are given in the config file</br> - all needed objects of type
     * org.opensha.commons.param.Parameter are properly instantiated</br> - the
     * application workflow is not interrupted
     * 
     * @throws ConfigurationException
     */
    @Test
    public void testDoProbabilisticEventBasedCalcFull()
            throws ConfigurationException {
        CommandLineCalculator clc =
                new CommandLineCalculator("CalculatorConfig.properties");
        String key = CalculatorConfigHelper.ConfigItems.CALCULATION_MODE.name();
        String mode = CalculationMode.FULL.value();
        clc.setConfigItem(key, mode);
        testDoProbabilisticEventBasedCalc(clc);
    }

    /**
     * This method does the work for {@link
     * testDoProbabilisticEventBasedCalcMonteCarlo()} and {@link
     * testDoProbabilisticEventBasedCalcFull()}.
     * 
     * @param clc
     *            CommandLineCalculator object configured for either "full"
     *            event based hazard calculation or for the "Monte Carlo"
     *            approach.
     * @throws ConfigurationException
     */
    private void testDoProbabilisticEventBasedCalc(CommandLineCalculator clc)
            throws ConfigurationException {
        Map<Site, Double> result = clc.doCalculationProbabilisticEventBased();
        Object o = null;
        assertTrue(result != null);
        assertTrue(result instanceof Map);
        // assertTrue(result.size() > 0);
        assertTrue(result.size() > 0
                && (o = result.keySet().iterator().next()) instanceof Site);
        assertTrue(result.size() > 0 && result.get(o) instanceof Double);
    } // testDoProbabilisticEventBasedCalcThroughMonteCarloLogicTreeSampling()

} // class CommandLineCalculatorTest
