package org.gem.log;

import java.util.Date;

/**
 * Abstract AMQP connection factory interfaca
 */
public interface AMQPConnectionFactory {
    /// Create a new AMQP connection
    public AMQPConnection getConnection();
}
