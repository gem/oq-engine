package org.gem.log;

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

public class AMQPAppender extends AppenderSkeleton {
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

        public String message;
        public Date timeStamp;
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

    public void setExchange(String exchange) {
        this.exchange = exchange;
    }

    public void setRoutingKeyPattern(String routingKeyPattern) {
        this.routingKeyPattern = new PatternLayout(routingKeyPattern);
    }

    public void setHost(String host) {
        this.host = host;
    }

    public void setPort(int port) {
        this.port = port;
    }

    public void setUsername(String username) {
        this.username= username;
    }

    public void setPassword(String password) {
        this.password = password;
    }

    public void setVirtualHost(String virtualHost) {
        this.virtualHost = virtualHost;
    }

    // TODO auto-declare exchange?
    // TODO set content type/content encoding/delivery mode/expiration
    //      headers/priority/durable?
    // TODO async connect/delivery?
    // TODO retry sending?

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

    protected Channel getChannel() throws IOException {
        if (channel != null && channel.isOpen())
            return channel;

        channel = getConnection().createChannel();

        return channel;
    }

    protected Connection getConnection() throws IOException {
        if (connection != null && connection.isOpen())
            return connection;

        connection = factory.newConnection();

        return connection;
    }

    protected void sendMessage(Channel channel, Event event)
        throws IOException {
        AMQP.BasicProperties.Builder props = new AMQP.BasicProperties.Builder();

        props.type(event.event.getLevel().toString());
        props.timestamp(event.timeStamp);

        String routingKey;
        if (routingKeyPattern != null)
            routingKey = routingKeyPattern.format(event.event);
        else
            routingKey = "";

        getChannel().basicPublish(exchange, routingKey, props.build(),
                                  event.message.getBytes());
    }
}
