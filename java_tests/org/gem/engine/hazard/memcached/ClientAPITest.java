package org.gem.engine.hazard.memcached;

import static org.junit.Assert.assertEquals;

import java.net.InetSocketAddress;
import java.util.ArrayList;
import java.util.List;

import net.spy.memcached.MemcachedClient;

import org.junit.Before;
import org.junit.Test;

/**
 * Sample JavaToJava memcached tests (probably useless in our context)
 * just to verify how the API works.
 * 
 * @author Andrea Cerisara
 */
public class ClientAPITest
{

    private static final int EXPIRE_TIME = 3600;

    private MemcachedClient client;

    @Before
    public void setUp() throws Exception
    {
        client = new MemcachedClient(new InetSocketAddress("localhost", 11211));
        client.flush(); // clear the server side cache
    }

    @Test
    public void canStoreAndGetASimpleType()
    {
        client.set("STRING", EXPIRE_TIME, "VALUE");

        assertEquals("VALUE", client.get("STRING"));
    }

    @Test
    public void canStoreAndGetAList()
    {
        List<Double> results = new ArrayList<Double>();
        results.add(1.0);
        results.add(2.0);
        results.add(3.0);

        client.set("LIST", EXPIRE_TIME, results);

        assertEquals(results, client.get("LIST"));
    }

    @Test
    public void canStoreAndGetAComplexType()
    {
        client.set("OBJ", EXPIRE_TIME, new AReallyCoolObject(1.0, 2.0));

        assertEquals(new AReallyCoolObject(1.0, 2.0), client.get("OBJ"));
    }

}
