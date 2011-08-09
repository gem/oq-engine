package org.gem.log;

import java.util.Date;

/**
 * Abstract AMQP connection interface
 */
public interface AMQPConnection {
    /// Set the AMQP host
    public void setHost(String host);

    /// Set the AMQP port
    public void setPort(int port);

    /// Set the AMQP user name
    public void setUsername(String username);

    /// Set the AMQP password
    public void setPassword(String password);

    /// Set the AMQP virtualhost
    public void setVirtualHost(String virtualHost);

    /// Close the AMQP connection
    public void close();

    /// Send a new message to the queue
    public void publish(String exchange, String routingKey, Date timestamp,
                        String level, String message);
}
