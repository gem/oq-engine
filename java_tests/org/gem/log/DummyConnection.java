package org.gem.log;

import org.junit.Ignore;

import java.util.ArrayList;
import java.util.Date;
import java.util.List;

@Ignore
class DummyConnectionFactory implements AMQPConnectionFactory {
    @Override
    public AMQPConnection getConnection() {
        return new DummyConnection();
    }
}

@Ignore
public class DummyConnection implements AMQPConnection {
    public class Entry {
        String exchange;
        String routingKey;
        String level;
        String body;
    }

    public List<Entry> entries = new ArrayList<Entry>();
    public String host, username, password, virtualHost;
    public int port;

    @Override
    public void setHost(String host) {
        this.host = host;
    }

    @Override
    public void setPort(int port) {
        this.port = port;
    }

    @Override
    public void setUsername(String username) {
        this.username = username;
    }

    @Override
    public void setPassword(String password) {
        this.password = password;
    }

    @Override
    public void setVirtualHost(String virtualHost) {
        this.virtualHost = virtualHost;
    }

    @Override
    public void close() {
        // nothing to do
    }

    @Override
    public void publish(String exchange, String routingKey, Date timestamp,
                        String level, String message) {
        Entry entry = new Entry();

        entry.exchange = exchange;
        entry.routingKey = routingKey;
        entry.level = level;
        entry.body = message;

        entries.add(entry);
    }
}
