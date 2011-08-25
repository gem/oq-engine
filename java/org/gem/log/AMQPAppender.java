package org.gem.log;

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
    /**
     * Collects all the data for a logging event
     */
    protected class Event {
        public Event(LoggingEvent event) {
            this.event = event;
            this.timestamp = Calendar.getInstance().getTime();

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
        public Date timestamp;
        /// The original logging event
        public LoggingEvent event;
    }

    // AMQP configuration
    protected String host, virtualHost, username, password;
    protected int port;
    protected String exchange = "";
    protected PatternLayout routingKeyPattern = null;

    // AMQP communication
    protected static AMQPConnectionFactory connectionFactory;
    protected AMQPConnection connection;

    // constructors

    public AMQPAppender() {
        host = "localhost";
        port = 5672;
        username = "guest";
        password = "guest";
        virtualHost = "/";

        activateOptions();
    }

    public static void setConnectionFactory(AMQPConnectionFactory factory) {
        connectionFactory = factory;
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

    /// Set the AMQP virtualhost
    public void setVirtualHost(String virtualHost) {
        this.virtualHost = virtualHost;
    }

    // override/implement Appender methods

    @Override
    public void activateOptions() {
        super.activateOptions();

        if (connection == null)
            return;

        applyConnectionParameters();
    }

    // as per discussion on IRC, we do all the sending synchronously,
    // assuming RabbitMQ is available and fast in handling messages
    @Override
    protected void append(LoggingEvent event) {
        sendMessage(new Event(event));
    }

    @Override
    public boolean requiresLayout() {
        return true;
    }

    @Override
    public void close() {
        if (connection != null)
            connection.close();
    }

    // implementation

    /// Send the log message to the AMQP server
    protected void sendMessage(Event event) {
        String routingKey;
        if (routingKeyPattern != null)
            routingKey = routingKeyPattern.format(event.event);
        else
            routingKey = "";

        if (connection == null)
            openConnection();

        connection.publish(exchange, routingKey, event.timestamp,
                           event.event.getLevel().toString(),
                           event.message);
    }

    private void openConnection() {
        connection = connectionFactory.getConnection();
        applyConnectionParameters();
    }

    private void applyConnectionParameters() {
        connection.setHost(host);
        connection.setPort(port);
        connection.setUsername(username);
        connection.setPassword(password);
        connection.setVirtualHost(virtualHost);

        // force the connection close (so it will be reopened with the
        // new parameters the next time a message is sent)
        connection.close();
    }
}
