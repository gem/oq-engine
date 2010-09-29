package org.opensha.gem.GEM1.calc.gemOutput;

import static org.junit.Assert.assertEquals;

import java.net.InetSocketAddress;
import java.util.ArrayList;

import net.spy.memcached.MemcachedClient;

import org.gem.engine.hazard.memcached.Cache;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.opensha.commons.data.Site;
import org.opensha.commons.geo.Location;

import com.google.gson.Gson;

public class GEMHazardCurveRepositoryListTest
{

    private static final int PORT = 11211;
    private static final String LOCALHOST = "localhost";

    private MemcachedClient client;

    @Before
    public void setUp() throws Exception
    {
        client = new MemcachedClient(new InetSocketAddress(LOCALHOST, PORT));
        client.flush(); // clear the server side cache
    }

    @After
    public void tearDown()
    {
        client.shutdown();
    }

    @Test
    public void canStoreTheModelInCache()
    {
        GEMHazardCurveRepositoryList model = sampleModel();
        String key = model.serialize(new Cache(LOCALHOST, PORT));
        assertEquals(new Gson().toJson(sampleModel()), client.get(key));
    }

    @Test
    public void canStoreTheComputedPMFsInCache()
    {
        GEMHazardCurveRepositoryList model = sampleModel();
        String key = model.serializePMFs(new Cache(LOCALHOST, PORT));
        
        assertEquals(new Gson().toJson(
                sampleModel().computePMFs()), client.get(key));
    }

    private GEMHazardCurveRepositoryList sampleModel()
    {
        GEMHazardCurveRepositoryList model = new GEMHazardCurveRepositoryList();

        ArrayList<Site> sites = new ArrayList<Site>();
        sites.add(new Site(new Location(1.0, 2.0)));
        sites.add(new Site(new Location(4.0, 4.0)));

        ArrayList<Double> groundMotionLevels = new ArrayList<Double>();

        groundMotionLevels.add(1.0);
        groundMotionLevels.add(2.0);
        groundMotionLevels.add(3.0);
        groundMotionLevels.add(4.0);

        Double[] values = { 0.4, 0.3, 0.2, 0.1 };
        ArrayList<Double[]> probabilitiesOfExc = new ArrayList<Double[]>();

        probabilitiesOfExc.add(values);
        probabilitiesOfExc.add(values);

        GEMHazardCurveRepository set = new GEMHazardCurveRepository();

        set.setTimeSpan(50);
        set.setGridNode(sites);
        set.setIntensityMeasureType("IMT");
        set.setProbExList(probabilitiesOfExc);
        set.setGmLevels(groundMotionLevels);

        model.setModelName("NAME");
        model.add(set, "END_BRANCH_LABEL");

        return model;
    }

}
