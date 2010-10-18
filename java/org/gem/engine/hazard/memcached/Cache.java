package org.gem.engine.hazard.memcached;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.util.concurrent.Future;

import net.spy.memcached.MemcachedClient;

/**
 * Represents an object that is capable of storing values.
 * <p>
 * Eventually could be an interface with different implementations, but now is
 * just a wrapper around the memcached client library.
 * 
 * @author Andrea Cerisara
 */
public class Cache {

    /**
     * The lifetime of the values stored on the server (in seconds)
     */
    private static final int EXPIRE_TIME = 3600;

    private MemcachedClient client;

    /**
     * Main constructor.
     * 
     * @param host
     *            the memcached remote server to use
     * @param port
     *            the memcached port to use
     */
    public Cache(String host, int port) {
        try {
            client = new MemcachedClient(new InetSocketAddress(host, port));
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    /**
     * Saves the object with the given key.
     * <p>
     * If a value with the same key is already present, it will be overwritten.
     * 
     * @param key
     *            the key to use
     * @param obj
     *            the object to save
     */
    public void set(String key, Object obj) {
        Future<Boolean> result = client.set(key, EXPIRE_TIME, obj);

        try {
            // shouldn't be necessary, just a patch waiting to find a better
            // way to do so (when this call returns the value is really set
            // on the server)
            result.get();
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    /**
     * Cleans the cache.
     */
    public void flush() {
        client.flush();
    }

    /**
     * Retrieves the object identified by the given key.
     * 
     * @param key
     *            the key to use
     * @return the object identified by the given key, or <code>null</code> if
     *         there is no object identified by the given key
     */
    public Object get(String key) {
        return client.get(key);
    }

}
