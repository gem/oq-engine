// package org.opensha.gem.GEM1.calc.gemCommandLineCalculator;
package org.gem.engine;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import java.util.Properties;

import org.apache.commons.configuration.ConfigurationException;
import org.gem.engine.CommandLineCalculator.EqkRuptureDataForMemcache;
import org.gem.engine.hazard.redis.BaseRedisTest;
import org.gem.ipe.PredictionEquationTestHelper;
import org.junit.Test;
import org.opensha.sha.earthquake.EqkRupture;

import com.google.gson.Gson;

public class CommandLineCalculatorTest extends BaseRedisTest {

    private static String peerTestSet1Case5ConfigFile =
            "peerSet1Case5/CalculatorConfig.properties";

    // private static String peerTestSet1Case8aConfigFile =
    // "peerSet1Case8a/CalculatorConfig.properties";

    @Test
    // spike on the java.util.Properties object
    public void twoPropertiesAreEqualWithTheSameParameters() {
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
    public void eqkRuptureSerialisation() throws ConfigurationException {
        CommandLineCalculator clc =
                new CommandLineCalculator(peerTestSet1Case5ConfigFile);
        EqkRuptureDataForMemcache dataToCache =
                clc.new EqkRuptureDataForMemcache();
        EqkRupture rupture = PredictionEquationTestHelper.getElsinoreRupture();
        dataToCache.init(rupture);
        // dataToCache.initTestwise();
        Gson gson = new Gson();
        String expected = "";
        String json = gson.toJson(dataToCache);
        System.out.println("xxr expected = " + expected);
        System.out.println("xxr json = " + json);
        assertTrue("Zampano sais: ", expected.compareTo(json) == 0);
    }

} // class CommandLineCalculatorTest
