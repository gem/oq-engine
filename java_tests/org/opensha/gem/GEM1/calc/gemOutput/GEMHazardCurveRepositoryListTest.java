package org.opensha.gem.GEM1.calc.gemOutput;

import static org.junit.Assert.assertEquals;

import java.net.InetSocketAddress;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import net.spy.memcached.MemcachedClient;

import org.gem.engine.hazard.memcached.Cache;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.opensha.commons.data.Site;
import org.opensha.commons.geo.Location;

import com.google.gson.Gson;

public class GEMHazardCurveRepositoryListTest {

    private static final int PORT = 11211;
    private static final String LOCALHOST = "localhost";
    private static final Double TOLERANCE = 1e-10;

    private MemcachedClient client;
    private GEMHazardCurveRepositoryList model;

    @Before
    public void setUp() throws Exception {
        client = new MemcachedClient(new InetSocketAddress(LOCALHOST, PORT));
        client.flush(); // clear the server side cache

        // sample model
        model = new GEMHazardCurveRepositoryList();

        ArrayList<Site> sites = new ArrayList<Site>();
        sites.add(new Site(new Location(37.5000, -122.5000)));

        ArrayList<Double> groundMotionLevels = new ArrayList<Double>();

        groundMotionLevels.add(5.0000e-03);
        groundMotionLevels.add(7.0000e-03);
        groundMotionLevels.add(1.3700e-02);
        groundMotionLevels.add(1.9200e-02);
        groundMotionLevels.add(2.6900e-02);
        groundMotionLevels.add(3.7600e-02);
        groundMotionLevels.add(5.2700e-02);
        groundMotionLevels.add(7.3800e-02);
        groundMotionLevels.add(9.8000e-02);
        groundMotionLevels.add(1.0300e-01);
        groundMotionLevels.add(1.4500e-01);
        groundMotionLevels.add(2.0300e-01);
        groundMotionLevels.add(2.8400e-01);
        groundMotionLevels.add(3.9700e-01);
        groundMotionLevels.add(5.5600e-01);
        groundMotionLevels.add(7.7800e-01);
        groundMotionLevels.add(1.0900e+00);
        groundMotionLevels.add(1.5200e+00);
        groundMotionLevels.add(2.1300e+00);

        ArrayList<Double[]> probabilitiesOfExc = new ArrayList<Double[]>();

        probabilitiesOfExc.add(new Double[] { 9.8728e-01, 9.8266e-01,
                9.4957e-01, 9.0326e-01, 8.1956e-01, 6.9192e-01, 5.2866e-01,
                3.6143e-01, 2.4231e-01, 2.2452e-01, 1.2831e-01, 7.0352e-02,
                3.6060e-02, 1.6579e-02, 6.4213e-03, 2.0244e-03, 4.8605e-04,
                8.1752e-05, 7.3425e-06 });

        GEMHazardCurveRepository set = new GEMHazardCurveRepository();

        set.setGridNode(sites);
        set.setProbList(probabilitiesOfExc);
        set.setGmLevels(groundMotionLevels);

        model.add(set, null);
    }

    @After
    public void tearDown() {
        client.shutdown();
    }

    @Test
    public void storesTheModelInCache() {
        String key = model.serialize(new Cache(LOCALHOST, PORT));
        assertEquals(new Gson().toJson(model), client.get(key));
    }

    @Test
    public void computesPMFs() {
        // using real values computed by D. Monelli
        model.computePMFs();

        List<Double> expectedGMLevels =
                Arrays.asList(0.006000, 0.010350, 0.016450, 0.023050, 0.032250,
                        0.045150, 0.063250, 0.085900, 0.100500, 0.124000,
                        0.174000, 0.243500, 0.340500, 0.476500, 0.667000,
                        0.934000, 1.305000, 1.825000);

        assertAlmostEquals(expectedGMLevels, model.getHcRepList().get(0)
                .getGmLevels());

        Double[] expectedPOs =
                { 4.620000e-03, 3.309000e-02, 4.631000e-02, 8.370000e-02,
                        1.276400e-01, 1.632600e-01, 1.672300e-01, 1.191200e-01,
                        1.779000e-02, 9.621000e-02, 5.795800e-02, 3.429200e-02,
                        1.948100e-02, 1.015770e-02, 4.396900e-03, 1.538350e-03,
                        4.042980e-04, 7.440950e-05 };

        assertAlmostEquals(expectedPOs, model.getHcRepList().get(0)
                .getProbExceedanceList(0));
    }

    private void assertAlmostEquals(Double[] expected, Double[] actual) {
        for (int i = 0; i < expected.length; i++) {
            assertEquals(expected[i], actual[i], TOLERANCE);
        }
    }

    private void assertAlmostEquals(List<Double> expected, List<Double> actual) {
        for (int i = 0; i < expected.size(); i++) {
            assertEquals(expected.get(i), actual.get(i), TOLERANCE);
        }
    }

}
