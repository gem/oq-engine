package org.gem.engine.hazard.memcached;

import java.net.InetSocketAddress;

import net.spy.memcached.MemcachedClient;

import org.junit.After;
import org.junit.Before;

public class BaseMemcachedTest {

    protected static final int PORT = 11211;
    protected static final int EXPIRE_TIME = 3600;
    protected static final String LOCALHOST = "localhost";

    protected MemcachedClient client;

    @Before
    public void setUp() throws Exception {
        client = new MemcachedClient(new InetSocketAddress(LOCALHOST, PORT));
        client.flush(); // clear the server side cache
    }

    @After
    public void tearDown() throws Exception {
        client.shutdown();
    }

}
