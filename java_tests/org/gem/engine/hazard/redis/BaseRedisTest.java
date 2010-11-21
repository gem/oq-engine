package org.gem.engine.hazard.redis;

import org.junit.Before;

public class BaseRedisTest {
    protected static final int PORT = 6379;
    protected static final int EXPIRE_TIME = 3600;
    protected static final String LOCALHOST = "localhost";

    protected Cache client;

    @Before
    public void setUp() throws Exception {
        client = new Cache(LOCALHOST, PORT);
        client.flush(); // clear the server side cache
    }
}
