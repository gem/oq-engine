package org.gem.engine.hazard.memcached;

import static org.hamcrest.Matchers.is;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;

import java.lang.reflect.Type;
import java.net.InetSocketAddress;
import java.util.ArrayList;
import java.util.List;

import net.spy.memcached.MemcachedClient;

import org.junit.Before;
import org.junit.Test;

import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;

public class HazardCurveSerializerTest
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

    @Test
    // learning test for http://sites.google.com/site/gson
    public void canSerializeAndDeserializeData()
    {
        List<Double> data = new ArrayList<Double>();
        data.add(1.0);
        data.add(2.0);
        data.add(3.0);

        Type listType = new TypeToken<List<Double>>(){}.getType();
        assertEquals(data, new Gson().fromJson(new Gson().toJson(data), listType));
    }

    @Test
    public void serializesASingleCurve() throws Exception
    {
        new HazardCurveSerializer("CURVE", new Cache(LOCALHOST, PORT)).serialize(sampleCurveAtSite(1.0, 2.0));

        assertThat(cachedCurveAtKey("CURVE"), is(sampleCurveAtSite(1.0, 2.0)));
    }

    @Test
    public void serializesMultipleCurves() throws Exception
    {
        List<HazardCurveDTO> curves = new ArrayList<HazardCurveDTO>();
        curves.add(sampleCurveAtSite(1.0, 2.0));
        curves.add(sampleCurveAtSite(2.0, 3.0));
        curves.add(sampleCurveAtSite(3.0, 4.0));

        Cache cache = mock(Cache.class);
        new HazardCurveSerializer("CURVE", cache).serialize(curves);

        // testing with a mock that the serializer serializes all the curves
        verify(cache).set("CURVE", sampleCurveAtSite(1.0, 2.0).toJSON());
        verify(cache).set("CURVE", sampleCurveAtSite(2.0, 3.0).toJSON());
        verify(cache).set("CURVE", sampleCurveAtSite(3.0, 4.0).toJSON());
    }

    private HazardCurveDTO sampleCurveAtSite(Double lon, Double lat)
    {
        // X sample values
        List<Double> groundMotionLevels = new ArrayList<Double>();
        groundMotionLevels.add(1.0);
        groundMotionLevels.add(2.0);
        groundMotionLevels.add(3.0);
        groundMotionLevels.add(4.0);

        // Y values
        List<Double> probabilitiesOfExc = new ArrayList<Double>();
        probabilitiesOfExc.add(1.0);
        probabilitiesOfExc.add(2.0);
        probabilitiesOfExc.add(3.0);
        probabilitiesOfExc.add(4.0);

        return new HazardCurveDTO(lon, lat, groundMotionLevels, probabilitiesOfExc);
    }

    private HazardCurveDTO cachedCurveAtKey(String string)
    {
        return new Gson().fromJson((String) client.get(string), HazardCurveDTO.class);
    }

}
