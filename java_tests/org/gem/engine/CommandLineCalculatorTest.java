// package org.opensha.gem.GEM1.calc.gemCommandLineCalculator;
package org.gem.engine;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.Properties;
import java.util.StringTokenizer;

import org.apache.commons.configuration.ConfigurationException;
import org.gem.engine.CalculatorConfigHelper.CalculationMode;
import org.gem.engine.CalculatorConfigHelper.ConfigItems;
import org.gem.engine.CalculatorConfigHelper.IntensityMeasure;
import org.gem.engine.hazard.memcached.BaseMemcachedTest;
import org.gem.engine.hazard.memcached.Cache;
import org.junit.Test;
import org.opensha.commons.data.Site;
import org.opensha.commons.geo.Location;
import org.opensha.sha.earthquake.EqkRupture;

import com.google.gson.Gson;

public class CommandLineCalculatorTest extends BaseMemcachedTest {

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
                new CommandLineCalculator(
                        "peerSet1Case5/CalculatorConfig.properties");
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
                new CommandLineCalculator(
                        "peerSet1Case5/CalculatorConfig.properties");
        String key = CalculatorConfigHelper.ConfigItems.CALCULATION_MODE.name();
        String mode = CalculationMode.MONTE_CARLO.value();
        clc.setConfigItem(key, mode);
        key =
                CalculatorConfigHelper.ConfigItems.NUMBER_OF_SEISMICITY_HISTORIES
                        .name();
        clc.setConfigItem(key, Integer.toString(10));
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
                new CommandLineCalculator(
                        "peerSet1Case5/CalculatorConfig.properties");
        String key = CalculatorConfigHelper.ConfigItems.CALCULATION_MODE.name();
        String mode = CalculationMode.FULL.value();
        clc.setConfigItem(key, mode);
        key =
                CalculatorConfigHelper.ConfigItems.NUMBER_OF_SEISMICITY_HISTORIES
                        .name();
        clc.setConfigItem(key, Integer.toString(10));
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
        Map<Integer, Map<String, Map<EqkRupture, Map<Site, Double>>>> result =
                clc.doCalculationProbabilisticEventBased();
        Object o = null;
        assertTrue(result != null);
        assertTrue(result instanceof Map);
        assertTrue(result.size() > 0);
        // assertTrue(result.size() > 0
        // && (o = result.get(o).keySet().iterator().next()) instanceof Site);
        // assertTrue(result.size() > 0 && result.get(o) instanceof String);
    } // testDoProbabilisticEventBasedCalcThroughMonteCarloLogicTreeSampling()

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
    public void supportsConfigurationReadingFromCache() {
        Properties config = new Properties();
        config.setProperty("KEY", "VALUE");
        config.setProperty("ANOTHER_KEY", "ANOTHER_VALUE");

        client.set("KEY", EXPIRE_TIME, new Gson().toJson(config));

        assertEquals(new CommandLineCalculator(config),
                new CommandLineCalculator(new Cache(LOCALHOST, PORT), "KEY"));
    }

    /**
     * Implements PEER test set 1 case 5 (single, planar, vertical fault, with
     * floating ruptures following GR truncated magnitude frequency
     * distribution) using classical PSHA approach.
     * 
     * @throws ConfigurationException
     */
    @Test
    public void peerSet1Case5ClassicalPSHA() throws ConfigurationException {
        double tolerance = 1e-3;
        CommandLineCalculator clc =
                new CommandLineCalculator(
                        "peerSet1Case5/CalculatorConfig.properties");
        clc.doCalculation();
        Map<Location, double[]> computedResults = readComputedResults();

        Map<Location, double[]> expectedResults =
                getHandResultsPeerTestSet1Case5();
        compareResults(computedResults, expectedResults, tolerance);

        expectedResults = getMeanResultsPeerTestSet1Case5();
        compareResults(computedResults, expectedResults, tolerance);

    }

    /**
     * Implements PEER test set 1 case 5 (single, planar, vertical fault, with
     * floating ruptures following GR truncated magnitude frequency
     * distribution) using stochastic event set approach
     * 
     * @throws ConfigurationException
     */
    @Test
    public void peerSet1Case5StochasticEventSet() throws ConfigurationException {
        double tolerance = 1e-2;
        int numberSeismicityHistories = 50000;
        CommandLineCalculator clc =
                new CommandLineCalculator(
                        "peerSet1Case5/CalculatorConfig.properties");
        Map<Integer, Map<String, Map<EqkRupture, Map<Site, Double>>>> groundMotionFields =
                clc.doCalculationProbabilisticEventBased();
        Map<Location, double[]> calculatedResults = setUpCalculatedResultsMap();
        double[] imlList =
                new double[] { 0.001, 0.01, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3,
                        0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.7, 0.8 };
        computeHazardCurves(numberSeismicityHistories, groundMotionFields,
                calculatedResults, imlList);

        Map<Location, double[]> expectedResults =
                getHandResultsPeerTestSet1Case5();
        compareResults(calculatedResults, expectedResults, tolerance);

        expectedResults = getMeanResultsPeerTestSet1Case5();
        compareResults(calculatedResults, expectedResults, tolerance);
    }

    private void computeHazardCurves(
            int numberSeismicityHistories,
            Map<Integer, Map<String, Map<EqkRupture, Map<Site, Double>>>> groundMotionFields,
            Map<Location, double[]> calculatedResults, double[] imlList) {
        for (Integer i : groundMotionFields.keySet())
            for (String label : groundMotionFields.get(i).keySet())
                for (EqkRupture rup : groundMotionFields.get(i).get(label)
                        .keySet())
                    for (Site site : groundMotionFields.get(i).get(label).get(
                            rup).keySet()) {
                        Location loc = site.getLocation();
                        double groundMotionValue =
                                Math.exp(groundMotionFields.get(i).get(label)
                                        .get(rup).get(site));
                        for (int j = 0; j < imlList.length; j++)
                            if (groundMotionValue > imlList[j])
                                calculatedResults.get(loc)[j] =
                                        calculatedResults.get(loc)[j] + 1;
                    }
        for (Location loc : calculatedResults.keySet()) {
            for (int j = 0; j < imlList.length; j++)
                calculatedResults.get(loc)[j] =
                        calculatedResults.get(loc)[j]
                                / numberSeismicityHistories;
        }
    }

    private Map<Location, double[]> setUpCalculatedResultsMap() {
        Map<Location, double[]> calculatedResults =
                new HashMap<Location, double[]>();
        calculatedResults.put(new Location(38.113, -122.000), new double[] {
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                0.0, 0.0, 0.0, 0.0 });
        calculatedResults.put(new Location(38.113, -122.114), new double[] {
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                0.0, 0.0, 0.0, 0.0 });
        calculatedResults.put(new Location(38.111, -122.570), new double[] {
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                0.0, 0.0, 0.0, 0.0 });
        calculatedResults.put(new Location(38.000, -122.000), new double[] {
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                0.0, 0.0, 0.0, 0.0 });
        calculatedResults.put(new Location(37.910, -122.000), new double[] {
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                0.0, 0.0, 0.0, 0.0 });
        calculatedResults.put(new Location(38.225, -122.000), new double[] {
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                0.0, 0.0, 0.0, 0.0 });
        calculatedResults.put(new Location(38.113, -121.886), new double[] {
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                0.0, 0.0, 0.0, 0.0 });
        return calculatedResults;
    }

    private void compareResults(Map<Location, double[]> computedResults,
            Map<Location, double[]> expectedResults, double tolerance) {
        for (Location loc : expectedResults.keySet()) {
            for (int i = 0; i < expectedResults.get(loc).length; i++) {
                assertEquals(expectedResults.get(loc)[i], computedResults
                        .get(loc)[i], tolerance);
            }
        }
    }

    private Map<Location, double[]> readComputedResults() {
        Map<Location, double[]> computedResults =
                new HashMap<Location, double[]>();
        File results = new File("build/individualHazardCurves.dat");
        FileReader fReader = null;
        try {
            fReader = new FileReader(results.getAbsolutePath());
            BufferedReader reader = new BufferedReader(fReader);
            String line = reader.readLine();
            StringTokenizer st = null;
            Location loc = null;
            double lon = Double.NaN;
            double lat = Double.NaN;
            double[] probEx = null;
            while ((line = reader.readLine()) != null) {
                st = new StringTokenizer(line);
                probEx = new double[st.countTokens() - 2];
                lon = Double.valueOf(st.nextToken());
                lat = Double.valueOf(st.nextToken());
                loc = new Location(lat, lon);
                int indexToken = 0;
                while (st.hasMoreTokens()) {
                    probEx[indexToken] = Double.valueOf(st.nextToken());
                    indexToken = indexToken + 1;
                }
                computedResults.put(loc, probEx);
            }
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        }
        return computedResults;
    }

    /**
     * returns hand-computed results for Sites 4, 5, and 6 for test set 1 case 5
     * 
     * @return
     */
    private Map<Location, double[]> getHandResultsPeerTestSet1Case5() {
        Map<Location, double[]> handResults = new HashMap<Location, double[]>();
        Location loc = new Location(38.000, -122.000);
        double[] probEx =
                new double[] { 3.99E-02, 3.99E-02, 3.98E-02, 2.99E-02,
                        2.00E-02, 1.30E-02, 8.58E-03, 5.72E-03, 3.88E-03,
                        2.69E-03, 1.91E-03, 1.37E-03, 9.74E-04, 6.75E-04,
                        2.52E-04, 0.00E+00 };
        handResults.put(loc, probEx);
        loc = new Location(37.910, -122.000);
        probEx =
                new double[] { 3.99E-02, 3.99E-02, 3.14E-02, 1.21E-02,
                        4.41E-03, 1.89E-03, 7.53E-04, 1.25E-04, 0.00E+00,
                        0.00E+00, 0.00E+00, 0.00E+00, 0.00E+00, 0.00E+00,
                        0.00E+00, 0.00E+00 };
        handResults.put(loc, probEx);
        loc = new Location(38.225, -122.000);
        probEx =
                new double[] { 3.99E-02, 3.99E-02, 3.98E-02, 2.99E-02,
                        2.00E-02, 1.30E-02, 8.58E-03, 5.72E-03, 3.88E-03,
                        2.69E-03, 1.91E-03, 1.37E-03, 9.74E-04, 6.75E-04,
                        2.52E-04, 0.00E+00 };
        handResults.put(loc, probEx);
        return handResults;
    }

    /**
     * returns mean results for sites 1, 2, 3, and 7 for test set 1 case 5
     * 
     * @return
     */
    private Map<Location, double[]> getMeanResultsPeerTestSet1Case5() {

        Map<Location, double[]> meanResults = new HashMap<Location, double[]>();

        Location loc = new Location(38.113, -122.000);
        double[] probEx =
                new double[] { 4.00E-02, 4.00E-02, 4.00E-02, 3.99E-02,
                        3.46E-02, 2.57E-02, 1.89E-02, 1.37E-02, 9.88E-03,
                        6.93E-03, 4.84E-03, 3.36E-03, 2.34E-03, 1.52E-03,
                        5.12E-04 };
        meanResults.put(loc, probEx);

        loc = new Location(38.113, -122.114);
        probEx =
                new double[] { 4.00E-02, 4.00E-02, 4.00E-02, 3.31E-02,
                        1.22E-02, 4.85E-03, 1.76E-03, 2.40E-04 };
        meanResults.put(loc, probEx);

        loc = new Location(38.111, -122.570);
        probEx = new double[] { 4.00E-2, 4.00E-2 };
        meanResults.put(loc, probEx);

        loc = new Location(38.113, -121.886);
        probEx =
                new double[] { 4.00E-02, 4.00E-02, 4.00E-02, 3.31E-02,
                        1.22E-02, 4.85E-03, 1.76E-03, 2.40E-04 };
        meanResults.put(loc, probEx);
        return meanResults;
    }

} // class CommandLineCalculatorTest
