// package org.opensha.gem.GEM1.calc.gemCommandLineCalculator;
package org.gem.engine;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import java.util.Properties;

import org.apache.commons.configuration.ConfigurationException;
import org.gem.engine.CommandLineCalculator.EqkRuptureDataForKvs;
import org.gem.engine.hazard.redis.BaseRedisTest;
import org.gem.engine.hazard.redis.Cache;
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
        final int PORT = 6379;
        final int EXPIRE_TIME = 3600;
        final String LOCALHOST = "localhost";
        final String key = "theKeyForRuptureData";
        Cache client;
        client = new Cache(LOCALHOST, PORT);
        client.flush(); // clear the server side cache

        CommandLineCalculator clc =
                new CommandLineCalculator(peerTestSet1Case5ConfigFile);
        EqkRupture rupture = PredictionEquationTestHelper.getElsinoreRupture();
        clc.serializeEqkRuptureToKvs(rupture, key, client);

        EqkRuptureDataForKvs dataToCache =
                clc.new EqkRuptureDataForKvs(rupture);
        Gson gson = new Gson();
        String expected = gson.toJson(dataToCache);
        Object obj = client.get(key);
        String fromKvs = "''";
        if (obj instanceof String) {
            fromKvs = client.get(key).toString();
        }
        System.out.println("xxr eqkRuptureSerialisation() expected = "
                + expected);
        System.out
                .println("xxr eqkRuptureSerialisation() fromKvs = " + fromKvs);
        assertEquals(expected, fromKvs);
        // assertTrue("Zampano says: ", expected.compareTo(json) == 0);
    }

} // class CommandLineCalculatorTest
