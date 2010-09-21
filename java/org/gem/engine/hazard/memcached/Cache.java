package org.gem.engine.hazard.memcached;

import java.net.InetSocketAddress;

import net.spy.memcached.MemcachedClient;

public class Cache
{

    private static final int EXPIRE_TIME = 3600;

    private MemcachedClient client;

    public Cache(String host, int port) throws Exception
    {
        client = new MemcachedClient(new InetSocketAddress(host, port));
    }

    public void set(String key, Object obj)
    {
        client.set(key, EXPIRE_TIME, obj);
    }

    public void flush()
    {
        client.flush();
    }

    public Object get(String key)
    {
        return client.get(key);
    }

}
