package org.gem.engine.hazard.memcached;

import static org.hamcrest.Matchers.is;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verifyZeroInteractions;

import java.net.InetSocketAddress;
import java.util.ArrayList;
import java.util.Arrays;

import net.spy.memcached.MemcachedClient;

import org.junit.Before;
import org.junit.Test;
import org.opensha.commons.data.Site;
import org.opensha.commons.geo.Location;
import org.opensha.gem.GEM1.calc.gemOutput.GEMHazardCurveRepository;
import org.opensha.gem.GEM1.calc.gemOutput.GEMHazardCurveRepositoryList;

import com.google.gson.Gson;

public class HazardCurveSerializerTest
{

    private static final int PORT = 11211;
    private static final String LOCALHOST = "localhost";

    private static final String IMT = "IMT";
    private static final Double TIMESPAN = 50.0;
    private static final String END_BRANCH_LABEL = "EBL";

    private MemcachedClient client;
    private HazardCurveSerializer serializer;
    private GEMHazardCurveRepositoryList repository;

    @Before
    public void setUp() throws Exception
    {
        serializer = new HazardCurveSerializer(new Cache(LOCALHOST, PORT));

        client = new MemcachedClient(new InetSocketAddress(LOCALHOST, PORT));
        client.flush(); // clear the server side cache

        repository = new GEMHazardCurveRepositoryList();
    }

    @Test
    // learning test for http://sites.google.com/site/gson
    public void canSerializeAndDeserializeData()
    {
        assertEquals("TEST", new Gson().fromJson(new Gson().toJson("TEST"),
                String.class));
    }

    @Test
    public void noSerializationWhenNoCurvesDefined()
    {
        // empty repository
        repository = new GEMHazardCurveRepositoryList();

        Cache cache = mock(Cache.class);
        serializer = new HazardCurveSerializer(cache);

        serializeRepository();

        verifyZeroInteractions(cache);
    }

    @Test
    public void serializesAModelWithASingleCurve() throws Exception
    {
        buildSampleCurvesFor(new Location(2.0, 1.0));

        serializeRepository();

        assertThat(cachedCurveAtKey("1.0+2.0"), is(sampleCurveAt(1.0, 2.0)));
    }

    @Test
    public void serializesAModelWithMultipleCurves() throws Exception
    {
        buildSampleCurvesFor(new Location(2.0, 1.0), new Location(4.0, 4.0));

        serializeRepository();

        assertThat(cachedCurveAtKey("1.0+2.0"), is(sampleCurveAt(1.0, 2.0)));
        assertThat(cachedCurveAtKey("4.0+4.0"), is(sampleCurveAt(4.0, 4.0)));
    }

    @Test
    public void serializesMultipleModels() throws Exception
    {
        buildSampleCurvesFor(new Location(2.0, 1.0));
        buildSampleCurvesFor(new Location(4.0, 4.0));

        serializeRepository();

        assertThat(cachedCurveAtKey("1.0+2.0"), is(sampleCurveAt(1.0, 2.0)));
        assertThat(cachedCurveAtKey("4.0+4.0"), is(sampleCurveAt(4.0, 4.0)));
    }

    private void serializeRepository()
    {
        serializer.serialize(repository);
    }

    private void buildSampleCurvesFor(Location... locations)
    {
        ArrayList<Site> sites = new ArrayList<Site>();

        for (Location location : locations)
        {
            sites.add(new Site(location));
        }

        GEMHazardCurveRepository set = new GEMHazardCurveRepository();
        set.setProbExList(probabilitiesOfExc(locations.length));
        set.setGmLevels(groundMotionLevels());
        set.setIntensityMeasureType(IMT);
        set.setTimeSpan(TIMESPAN);
        set.setGridNode(sites);

        repository.add(set, END_BRANCH_LABEL);
    }

    // fixed Y sample values
    private ArrayList<Double[]> probabilitiesOfExc(Integer numberOfSites)
    {
        Double[] values = { 1.0, 2.0, 3.0, 4.0 };
        ArrayList<Double[]> probabilitiesOfExc = new ArrayList<Double[]>();

        for (int i = 0; i < numberOfSites; i++)
        {
            probabilitiesOfExc.add(values);
        }

        return probabilitiesOfExc;
    }

    // fixed X sample values
    private ArrayList<Double> groundMotionLevels()
    {
        ArrayList<Double> groundMotionLevels = new ArrayList<Double>();

        groundMotionLevels.add(1.0);
        groundMotionLevels.add(2.0);
        groundMotionLevels.add(3.0);
        groundMotionLevels.add(4.0);

        return groundMotionLevels;
    }

    private HazardCurveDTO sampleCurveAt(Double lon, Double lat)
    {
        return new HazardCurveDTO(lon, lat, groundMotionLevels(), Arrays
                .asList(probabilitiesOfExc(1).get(0)), IMT, TIMESPAN,
                END_BRANCH_LABEL);
    }

    private HazardCurveDTO cachedCurveAtKey(String key)
    {
        return new Gson().fromJson((String) client.get(key),
                HazardCurveDTO.class);
    }

}
