package org.gem.engine.hazard.redis;

import java.net.InetSocketAddress;

import org.jredis.ClientRuntimeException;
import org.jredis.RedisException;
import org.jredis.connector.ConnectionSpec;
import org.jredis.ri.alphazero.JRedisClient;
import org.jredis.ri.alphazero.connection.DefaultConnectionSpec;

/**
 * Store stuff in Redis.
 * 
 * This wraps the jredis library.
 * 
 * @author Christopher MacGown
 */
public class Cache {
    private JRedisClient client;

    /**
     * Default client constructor, defaults to database 10.
     */
    public Cache(String host, int port) {
        try {
            // Do the connection.
            client = new JRedisClient(getConnectionSpec(host, port, 0));
        } catch (ClientRuntimeException e) { 
            throw new RuntimeException(e);
        }
    }

    /**
     * Constructor for specifying database.
     */
    public Cache(String host, int port, int db) {
        try {
            // Do the connection.
            client = new JRedisClient(getConnectionSpec(host, port, db));
        } catch (ClientRuntimeException e) {
            throw new RuntimeException(e);
        }
    }

    /**
     * Get the connection spec for the client connection
     */
    private ConnectionSpec getConnectionSpec(String host, int port, int db) {
        ConnectionSpec connectionSpec = DefaultConnectionSpec.newSpec();
        InetSocketAddress addr = new InetSocketAddress(host, port);

        // Build the connection specification
        connectionSpec.setAddress(addr.getAddress()).setPort(addr.getPort())
                .setReconnectCnt(2) // # times to reconnect if we disconnected.
                .setDatabase(db);

        return connectionSpec;
    }

    /**
     * Throw a fit and break everything.
     */
    public boolean set(String key, Object value) {
        throw new RuntimeException("Lars frowns upon your shenanigans");
    }

    /**
     * Given a key and a string, write that string to Redis.
     * <p>
     * 
     * @param key
     *            The key to use.
     * @param value
     *            The value to be written.
     */
    public void set(String key, String value) {
        try {
            client.set(key, value);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    /**
     * Given a key, return the value from the client.
     * <p>
     * 
     * @param key
     *            The key to use.
     */
    public Object get(String key) {
        try {
            return new String(client.get(key));
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    public void flush() {
        try {
            client.flushdb();
        } catch (RedisException e) {
            throw new RuntimeException(e);
        }
    }
}
