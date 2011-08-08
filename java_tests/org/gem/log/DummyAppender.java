package org.gem.log;

import com.rabbitmq.client.Channel;
import com.rabbitmq.client.Connection;
import com.rabbitmq.client.ConnectionFactory;

import org.junit.Ignore;

@Ignore
public class DummyAppender extends AMQPAppender {
    public static DummyAppender lastAppender;

    public DummyAppender() {
        super();

        lastAppender = this;
    }

    public ConnectionFactory getFactory() {
        return factory;
    }

    @Override
    protected Channel getChannel() {
        if (channel == null)
            channel = new DummyChannel();

        return channel;
    }

    @Override
    protected Connection getConnection() {
        return null;
    }
}
