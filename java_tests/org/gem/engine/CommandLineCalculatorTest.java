// package org.opensha.gem.GEM1.calc.gemCommandLineCalculator;
package org.gem.engine;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import java.io.IOException;
import java.util.Map;
import java.util.Properties;

import org.apache.commons.configuration.ConfigurationException;
import org.gem.engine.CalculatorConfigHelper.CalculationMode;
import org.gem.engine.CalculatorConfigHelper.ConfigItems;
import org.gem.engine.CalculatorConfigHelper.IntensityMeasure;
import org.gem.engine.hazard.memcached.BaseMemcachedTest;
import org.gem.engine.hazard.memcached.Cache;
import org.junit.Test;
import org.opensha.commons.data.Site;

import com.google.gson.Gson;

public class CommandLineCalculatorTest extends BaseMemcachedTest {

    /**
     * The calculator does not yet run if it is give to calculate for an
     * intensity measure type "MMI". This tests veryfies that. It is expected to
     * fail.
     * 
     * @throws ConfigurationException
     * @throws IOException
     */
    @Test(expected = IllegalArgumentException.class)
    public void testCalculatorConfig() throws ConfigurationException,
            IOException {

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
     * @throws IOException
     */
    @Test
    public void testDoProbabilisticEventBasedCalcMonteCarlo()
            throws ConfigurationException, IOException {
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
     * @throws IOException
     */
    @Test
    public void testDoProbabilisticEventBasedCalcFull()
            throws ConfigurationException, IOException {
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
     * @throws IOException
     */
    private void testDoProbabilisticEventBasedCalc(CommandLineCalculator clc)
            throws ConfigurationException, IOException {
        Map<Site, Double> result = clc.doCalculationProbabilisticEventBased();
        Object o = null;
        assertTrue(result != null);
        assertTrue(result instanceof Map);
        // assertTrue(result.size() > 0);
        assertTrue(result.size() > 0
                && (o = result.keySet().iterator().next()) instanceof Site);
        assertTrue(result.size() > 0 && result.get(o) instanceof Double);
    } // testDoProbabilisticEventBasedCalcThroughMonteCarloLogicTreeSampling()

    @Test
    // spike on the java.util.Properties object
            public
            void twoPropertiesAreEqualWithTheSameParameters() {
        Properties config1 = new Properties();
        config1.setProperty("KEY", "VALUE");

        Properties config2 = new Properties();
        config2.setProperty("KEY", "VALUE");

        Properties config3 = new Properties();
        config3.setProperty("ANOTHER_KEY", "ANOTHER_VALUE");

        Properties config4 = new Properties();
        config4.setProperty("KEY", "VALUE");
        config4.setProperty("ANOTHER_KEY", "ANOTHER_VALUE");

        assertTrue(config1.equals(config2));
        assertFalse(config1.equals(config3));
        assertFalse(config1.equals(config4));
        assertFalse(config3.equals(config4));
    }

    @Test
    public void twoCalculatorsAreEqualWithTheSameConfig() {
        Properties config1 = new Properties();
        config1.setProperty("KEY", "VALUE");

        Properties config2 = new Properties();
        config2.setProperty("ANOTHER_KEY", "ANOTHER_VALUE");

        CommandLineCalculator calc1 = new CommandLineCalculator(config1);
        CommandLineCalculator calc2 = new CommandLineCalculator(config1);
        CommandLineCalculator calc3 = new CommandLineCalculator(config2);

        assertTrue(calc1.equals(calc2));
        assertFalse(calc1.equals(calc3));
    }

    @Test
    public void supportsConfigurationReadingFromCache() {
        Properties config = new Properties();
        config.setProperty("KEY", "VALUE");
        config.setProperty("ANOTHER_KEY", "ANOTHER_VALUE");

        client.set("KEY", EXPIRE_TIME, new Gson().toJson(config));

        assertEquals(new CommandLineCalculator(config),
                new CommandLineCalculator(new Cache(LOCALHOST, PORT), "KEY"));
    }
} // class CommandLineCalculatorTest
