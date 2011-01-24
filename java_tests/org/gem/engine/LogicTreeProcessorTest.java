package org.gem.engine;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import java.util.Properties;

import org.apache.commons.configuration.ConfigurationException;
import org.gem.engine.LogicTreeProcessor.EqkRuptureDataForNrml;
import org.gem.engine.hazard.redis.BaseRedisTest;
import org.gem.engine.hazard.redis.Cache;
import org.gem.ipe.PredictionEquationTestHelper;
import org.junit.Test;
import org.opensha.commons.geo.Location;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;

import com.google.gson.Gson;

public class LogicTreeProcessorTest extends BaseRedisTest {

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

        LogicTreeProcessor calc1 = new LogicTreeProcessor(config1);
        LogicTreeProcessor calc2 = new LogicTreeProcessor(config1);
        LogicTreeProcessor calc3 = new LogicTreeProcessor(config2);

        assertTrue(calc1.equals(calc2));
        assertFalse(calc1.equals(calc3));
    }

    /**
     * Tests if lon, lat, depth of a gridded surface of a EqkRupture has
     * correctly been extracted to a data object ("EqkRuptureDataForKvs") so
     * that the content of the json string (generated with gson) will be
     * correct.<br>
     * 
     * @throws ConfigurationException
     */
    @Test
    public void eqkRuptureKvsData() throws ConfigurationException {
        LogicTreeProcessor clc =
                new LogicTreeProcessor(peerTestSet1Case5ConfigFile);
        /*
         * Not to big test data:
         */
        EqkRupture rupture = PredictionEquationTestHelper.getElsinoreRupture();
        EqkRuptureDataForNrml dataFromEqkRuptureNeededForNrml =
                clc.new EqkRuptureDataForNrml(rupture);
        EvenlyGriddedSurfaceAPI grid = rupture.getRuptureSurface();
        int numberOfColumns = grid.getNumCols();
        int numberOfRows = grid.getNumRows();
        double[] lonGrid = dataFromEqkRuptureNeededForNrml.getLonGrid();
        double[] latGrid = dataFromEqkRuptureNeededForNrml.getLatGrid();
        double[] depthGrid = dataFromEqkRuptureNeededForNrml.getDepthGrid();
        for (int row = 0; row < numberOfRows; row++) {
            for (int col = 0; col < numberOfColumns; col++) {
                Location l = grid.get(row, col);
                int indexOfFlatArray = (row) * numberOfColumns + (col);
                assertEquals(lonGrid[indexOfFlatArray], l.getLongitude(), 0.0);
                assertEquals(latGrid[indexOfFlatArray], l.getLatitude(), 0.0);
                assertEquals(depthGrid[indexOfFlatArray], l.getDepth(), 0.0);
            } // for columns
        } // for rows
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

        LogicTreeProcessor clc =
                new LogicTreeProcessor(peerTestSet1Case5ConfigFile);
        EqkRupture rupture = PredictionEquationTestHelper.getElsinoreRupture();
        clc.serializeEqkRuptureToKvs(rupture, key, client);

        EqkRuptureDataForNrml dataToCache =
                clc.new EqkRuptureDataForNrml(rupture);
        Gson gson = new Gson();
        String expected = gson.toJson(dataToCache);
        Object obj = client.get(key);
        String fromKvs = "''";
        if (obj instanceof String) {
            fromKvs = client.get(key).toString();
        }
        /*
         * debug - if you want to have a look, print it to the console:
         */
        // System.out.println("eqkRuptureSerialisation() expected = "
        // + expected);
        // System.out
        // .println("eqkRuptureSerialisation() fromKvs = " + fromKvs);
        assertEquals(expected, fromKvs);
    }

} // class LogicTreeProcessorTest
