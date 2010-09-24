package org.gem.engine.hazard.memcached;

import static org.hamcrest.Matchers.is;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verifyZeroInteractions;

import java.lang.reflect.Type;
import java.net.InetSocketAddress;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import net.spy.memcached.MemcachedClient;

import org.junit.Before;
import org.junit.Test;
import org.opensha.commons.data.Site;
import org.opensha.commons.geo.Location;
import org.opensha.gem.GEM1.calc.gemOutput.GEMHazardCurveRepository;

import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;

public class HazardCurveSerializerTest
{

    private static final int PORT = 11211;
    private static final String LOCALHOST = "localhost";

    private static final String IMT = "IMT";
    private static final Double TIMESPAN = 50.0;

    private MemcachedClient client;
    private HazardCurveSerializer serializer;
    private GEMHazardCurveRepository repository;

    @Before
    public void setUp() throws Exception
    {
        serializer = new HazardCurveSerializer(new Cache(LOCALHOST, PORT));

        client = new MemcachedClient(new InetSocketAddress(LOCALHOST, PORT));
        client.flush(); // clear the server side cache

        repository = new GEMHazardCurveRepository();
        repository.setGmLevels(groundMotionLevels());
        repository.setIntensityMeasureType(IMT);
        repository.setTimeSpan(TIMESPAN);
    }

    @Test
    // learning test for http://sites.google.com/site/gson
    public void canSerializeAndDeserializeData()
    {
        List<Double> data = new ArrayList<Double>();
        data.add(1.0);
        data.add(2.0);
        data.add(3.0);

        Type listType = new TypeToken<List<Double>>()
        {

        }.getType();

        assertEquals(data, new Gson().fromJson(new Gson().toJson(data),
                listType));
    }

    @Test
    public void noSerializationWhenNoCurvesDefined()
    {
        // empty repository
        repository = new GEMHazardCurveRepository();

        Cache cache = mock(Cache.class);
        serializer = new HazardCurveSerializer(cache);

        serializeRepository();

        verifyZeroInteractions(cache);
    }

    @Test
    public void serializesASingleCurve() throws Exception
    {
        Location[] locations = { new Location(2.0, 1.0) };
        setDataFor(locations);

        serializeRepository();

        assertThat(cachedCurveAtKey("1.0+2.0"), is(sampleCurveAt(1.0, 2.0)));
    }

    @Test
    public void serializesMultipleCurves() throws Exception
    {
        Location[] locations = { new Location(2.0, 1.0), new Location(4.0, 4.0) };
        setDataFor(locations);

        serializeRepository();

        assertThat(cachedCurveAtKey("1.0+2.0"), is(sampleCurveAt(1.0, 2.0)));
        assertThat(cachedCurveAtKey("4.0+4.0"), is(sampleCurveAt(4.0, 4.0)));
    }

    @Test
    public void serializesACompleteHazardModel() throws Exception
    {

    }

    private void serializeRepository()
    {
        serializer.serialize(repository);
    }

    private void setDataFor(Location[] locations)
    {
        ArrayList<Site> sites = new ArrayList<Site>();

        for (Location location : locations)
        {
            sites.add(new Site(location));
        }

        repository.setGridNode(sites);
        repository.setProbExList(probabilitiesOfExc(locations.length));
    }

    // Y sample values
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

    // X sample values
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
                .asList(probabilitiesOfExc(1).get(0)), IMT, TIMESPAN);
    }

    private HazardCurveDTO cachedCurveAtKey(String key)
    {
        return new Gson().fromJson((String) client.get(key),
                HazardCurveDTO.class);
    }

}
