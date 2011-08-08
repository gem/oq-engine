package org.gem.log;

import com.rabbitmq.client.ConnectionFactory;

import java.util.Properties;

import org.apache.log4j.BasicConfigurator;
import org.apache.log4j.Layout;
import org.apache.log4j.Logger;
import org.apache.log4j.PatternLayout;
import org.apache.log4j.PropertyConfigurator;

import org.junit.Test;

import static org.junit.Assert.assertThat;

import static org.junit.matchers.JUnitMatchers.*;

import static org.hamcrest.CoreMatchers.*;

public class AMQPAppenderTest {
    private DummyChannel dummyChannel;
    private DummyAppender dummyAppender;
    private Logger logger = Logger.getLogger(AMQPAppenderTest.class);

    void tearDown() {
        dummyChannel = null;
        dummyAppender = null;
        DummyAppender.lastAppender = null;

        // this closes the RabbitMQ connections
        BasicConfigurator.resetConfiguration();
    }

    private void setUpDummyAppender() {
        dummyAppender = new DummyAppender();
        dummyAppender.setLayout(new PatternLayout());

        BasicConfigurator.configure(dummyAppender);
    }

    @Test
    public void basicLogging() {
        setUpDummyAppender();

        logger.info("Test1");
        logger.warn("Test2");

        dummyChannel = (DummyChannel) dummyAppender.getChannel();

        assertThat(dummyChannel.entries.size(), is(equalTo(2)));

        DummyChannel.Entry entry1 = dummyChannel.entries.get(0);

        assertThat(entry1.exchange, is(equalTo("")));
        assertThat(entry1.routingKey, is(equalTo("")));
        assertThat(entry1.properties.getType(), is(equalTo("INFO")));
        assertThat(entry1.body, is(equalTo("Test1\n")));

        DummyChannel.Entry entry2 = dummyChannel.entries.get(1);

        assertThat(entry2.exchange, is(equalTo("")));
        assertThat(entry2.routingKey, is(equalTo("")));
        assertThat(entry2.properties.getType(), is(equalTo("WARN")));
        assertThat(entry2.body, is(equalTo("Test2\n")));
    }

    @Test
    public void routingKey() {
        setUpDummyAppender();

        dummyAppender.setRoutingKeyPattern("rk");

        logger.info("Test1");
        logger.warn("Test2");

        dummyChannel = (DummyChannel) dummyAppender.getChannel();

        assertThat(dummyChannel.entries.size(), is(equalTo(2)));

        DummyChannel.Entry entry1 = dummyChannel.entries.get(0);

        assertThat(entry1.routingKey, is(equalTo("rk")));

        DummyChannel.Entry entry2 = dummyChannel.entries.get(1);

        assertThat(entry2.routingKey, is(equalTo("rk")));
    }

    @Test
    public void routingKeyPattern() {
        setUpDummyAppender();

        dummyAppender.setRoutingKeyPattern("log.%p");

        logger.info("Test1");
        logger.warn("Test2");

        dummyChannel = (DummyChannel) dummyAppender.getChannel();

        assertThat(dummyChannel.entries.size(), is(equalTo(2)));

        DummyChannel.Entry entry1 = dummyChannel.entries.get(0);

        assertThat(entry1.routingKey, is(equalTo("log.INFO")));

        DummyChannel.Entry entry2 = dummyChannel.entries.get(1);

        assertThat(entry2.routingKey, is(equalTo("log.WARN")));
    }

    @Test
    public void log4jSetup() {
        Properties props = new Properties();

        props.setProperty("log4j.rootLogger", "DEBUG, rabbit");

        props.setProperty("log4j.appender.rabbit",
                          "org.gem.log.DummyAppender");

        // connection parameters
        props.setProperty("log4j.appender.rabbit.host",
                          "amqp.openquake.org");
        props.setProperty("log4j.appender.rabbit.port",
                          "4004");
        props.setProperty("log4j.appender.rabbit.username",
                          "looser");
        props.setProperty("log4j.appender.rabbit.password",
                          "s3krit");
        props.setProperty("log4j.appender.rabbit.virtualHost",
                          "job.oq.org/test");

        // message parameters
        props.setProperty("log4j.appender.rabbit.routingKeyPattern",
                          "log.%p");
        props.setProperty("log4j.appender.rabbit.exchange",
                          "amq.topic");

        // layout
        props.setProperty("log4j.appender.rabbit.layout",
                          "org.apache.log4j.PatternLayout");
        props.setProperty("log4j.appender.rabbit.layout.ConversionPattern",
                          "%d %-5p [%c] - %m%n");

        PropertyConfigurator.configure(props);

        logger.info("Test1");

        dummyAppender = DummyAppender.lastAppender;
        dummyChannel = (DummyChannel) dummyAppender.getChannel();

        // check layout
        Layout layout = dummyAppender.getLayout();

        assertThat(layout, is(instanceOf(PatternLayout.class)));

        PatternLayout patternLayout = (PatternLayout) layout;

        assertThat(patternLayout.getConversionPattern(),
                   is(equalTo("%d %-5p [%c] - %m%n")));

        // check message properties
        assertThat(dummyChannel.entries.size(), is(equalTo(1)));

        DummyChannel.Entry entry1 = dummyChannel.entries.get(0);

        assertThat(entry1.exchange, is(equalTo("amq.topic")));

        // check factory configuration
        ConnectionFactory factory = dummyAppender.getFactory();

        assertThat(factory.getHost(), is(equalTo("amqp.openquake.org")));
        assertThat(factory.getPort(), is(equalTo(4004)));
        assertThat(factory.getUsername(), is(equalTo("looser")));
        assertThat(factory.getPassword(), is(equalTo("s3krit")));
        assertThat(factory.getVirtualHost(), is(equalTo("job.oq.org/test")));
    }
}
