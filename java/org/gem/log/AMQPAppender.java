package org.gem.log;

// uses the AMQP Java client from http://www.rabbitmq.com/java-client.html

import com.rabbitmq.client.AMQP;
import com.rabbitmq.client.Channel;
import com.rabbitmq.client.Connection;
import com.rabbitmq.client.ConnectionFactory;

import java.io.IOException;

import java.util.Calendar;
import java.util.Date;

import org.apache.log4j.AppenderSkeleton;
import org.apache.log4j.Layout;
import org.apache.log4j.PatternLayout;
import org.apache.log4j.spi.LoggingEvent;

/**
 * Log4J appender class that sends log messages through RabbitMQ
 *
 * Example configuration:
 *
 * <pre><code>
 *   log4j.appender.rabbit=org.gem.log.AMQPAppender
 *   log4j.appender.rabbit.host=amqp.openquake.org
 *   log4j.appender.rabbit.port=4004
 *   log4j.appender.rabbit.username=looser
 *   log4j.appender.rabbit.password=s3krit
 *   log4j.appender.rabbit.virtualhost=job.oq.org/test
 *   log4j.appender.rabbit.routingKeyPattern=log.%p
 *   log4j.appender.rabbit.exchange=amq.topic
 *   log4j.appender.rabbit.layout=org.apache.log4j.PatternLayout
 *   log4j.appender.rabbit.layout.ConversionPattern=%d %-5p [%c] - %m%n
 * </code></pre>
 */
public class AMQPAppender extends AppenderSkeleton {
    /* Named constants for RabbitMQ delivery modes */
    private static final int DELIVERY_NONPERSISTENT = 1;
    private static final int DELIVERY_PERSISTENT = 2;

    /**
     * Collects all the data for a logging event
     */
    protected class Event {
        public Event(LoggingEvent event) {
            this.event = event;
            this.timeStamp = Calendar.getInstance().getTime();

            // Handle stack trace if required
            if (layout.ignoresThrowable()) {
                StringBuffer buffer = new StringBuffer(layout.format(event));
                String[] stackTrace = event.getThrowableStrRep();

                if (stackTrace != null)
                    for (String frame : stackTrace)
                        buffer.append(frame).append(Layout.LINE_SEP);

                this.message = buffer.toString();
            }
            else {
                this.message = layout.format(event);
            }
        }

        /// The log message (including stack trace if present)
        public String message;
        /// Timestamp when the message has been added to the logger
        public Date timeStamp;
        /// The original logging event
        public LoggingEvent event;
    }

    // AMQP configuration
    protected String host, virtualHost, username, password;
    protected int port;
    protected String exchange = "";
    protected PatternLayout routingKeyPattern = null;

    // AMQP connection
    protected ConnectionFactory factory;
    protected Connection connection;
    protected Channel channel;

    // constructors

    public AMQPAppender() {
        factory = new ConnectionFactory();

        host = "localhost";
        port = 5672;
        username = "guest";
        password = "guest";
        virtualHost = "/";

        activateOptions();
    }

    // configuration

    /// Set the exchange name
    public void setExchange(String exchange) {
        this.exchange = exchange;
    }

    /// Set the pattern (in PatternLayout format) used to create the routing key
    public void setRoutingKeyPattern(String routingKeyPattern) {
        this.routingKeyPattern = new PatternLayout(routingKeyPattern);
    }

    /// Set the AMQP host
    public void setHost(String host) {
        this.host = host;
    }

    /// Set the AMQP port
    public void setPort(int port) {
        this.port = port;
    }

    /// Set the AMQP user name
    public void setUsername(String username) {
        this.username= username;
    }

    /// Set the AMQP password
    public void setPassword(String password) {
        this.password = password;
    }

    /// Set the AMQP virtualhosy
    public void setVirtualHost(String virtualHost) {
        this.virtualHost = virtualHost;
    }

    // override/implement Appender methods

    @Override
    public void activateOptions() {
        super.activateOptions();

        factory.setHost(host);
        factory.setPort(port);
        factory.setUsername(username);
        factory.setPassword(password);
        factory.setVirtualHost(virtualHost);

        close();
    }

    // as per discussion on IRC, we do all the sending synchronously,
    // assuming RabbitMQ is available and fast in handling messages
    @Override
    protected void append(LoggingEvent event) {
        try {
            sendMessage(getChannel(), new Event(event));
        }
        catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    @Override
    public boolean requiresLayout() {
        return true;
    }

    @Override
    public void close() {
        if (connection != null && connection.isOpen()) {
            try {
                Connection currentConnection = connection;

                channel = null;
                connection = null;

                currentConnection.close();
            }
            catch (IOException e) {
                throw new RuntimeException(e);
            }
        }
    }

    // implementation

    /// Return the current AMQP channel or create a new one
    protected Channel getChannel() throws IOException {
        if (channel != null && channel.isOpen())
            return channel;

        channel = getConnection().createChannel();

        return channel;
    }

    /// Return the current AMQP connection or creates a new one
    protected Connection getConnection() throws IOException {
        if (connection != null && connection.isOpen())
            return connection;

        connection = factory.newConnection();

        return connection;
    }

    /// Send the log message to the AMQP server
    protected void sendMessage(Channel channel, Event event)
            throws IOException {
        AMQP.BasicProperties.Builder props = new AMQP.BasicProperties.Builder();

        props.type(event.event.getLevel().toString());
        props.timestamp(event.timeStamp);
        props.contentType("text/plain");
        props.deliveryMode(DELIVERY_PERSISTENT);

        String routingKey;
        if (routingKeyPattern != null)
            routingKey = routingKeyPattern.format(event.event);
        else
            routingKey = "";

        getChannel().basicPublish(exchange, routingKey, props.build(),
                                  event.message.getBytes());
    }
}
