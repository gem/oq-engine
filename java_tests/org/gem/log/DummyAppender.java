package org.gem.log;

import org.junit.Ignore;

@Ignore
public class DummyAppender extends AMQPAppender {
    public static DummyAppender lastAppender;

    public DummyAppender() {
        super();

        lastAppender = this;
    }

    public DummyConnection getConnection() {
        return (DummyConnection) connection;
    }
}
