package org.gem.log;

import com.rabbitmq.client.ConnectionFactory;

import java.util.Arrays;
import java.util.Properties;

import org.apache.commons.collections.CollectionUtils;
import org.apache.commons.collections.Predicate;

import org.apache.log4j.BasicConfigurator;
import org.apache.log4j.Layout;
import org.apache.log4j.Logger;
import org.apache.log4j.PatternLayout;
import org.apache.log4j.PropertyConfigurator;

import org.junit.Test;

import static org.junit.Assert.assertThat;

import static org.junit.matchers.JUnitMatchers.*;

import static org.hamcrest.CoreMatchers.*;

// A Layout that (pretends to) handle throwables
class ThrowablePatternLayout extends PatternLayout {
    @Override
    public boolean ignoresThrowable() {
        return false;
    }
}

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

    private DummyChannel.Entry entry(int index) {
        return dummyChannel.entries.get(0);
    }

    // logging sanity test
    @Test
    public void basicLogging() {
        setUpDummyAppender();

        logger.info("Test1");
        logger.warn("Test2");

        dummyChannel = (DummyChannel) dummyAppender.getChannel();

        assertThat(dummyChannel.entries.size(), is(equalTo(2)));

        assertThat(entry(0).exchange, is(equalTo("")));
        assertThat(entry(0).routingKey, is(equalTo("")));
        assertThat(entry(0).properties.getType(), is(equalTo("INFO")));
        assertThat(entry(0).properties.getContentType(),
                   is(equalTo("text/plain")));
        assertThat(entry(0).properties.getDeliveryMode(), is(equalTo(2)));
        assertThat(entry(0).body, is(equalTo("Test1\n")));

        assertThat(entry(1).exchange, is(equalTo("")));
        assertThat(entry(1).routingKey, is(equalTo("")));
        assertThat(entry(1).properties.getType(), is(equalTo("WARN")));
        assertThat(entry(1).properties.getContentType(),
                   is(equalTo("text/plain")));
        assertThat(entry(1).properties.getDeliveryMode(), is(equalTo(2)));
        assertThat(entry(1).body, is(equalTo("Test2\n")));
    }

    // test the routing key is used
    @Test
    public void routingKey() {
        setUpDummyAppender();

        dummyAppender.setRoutingKeyPattern("rk");

        logger.info("Test1");
        logger.warn("Test2");

        dummyChannel = (DummyChannel) dummyAppender.getChannel();

        assertThat(dummyChannel.entries.size(), is(equalTo(2)));
        assertThat(entry(0).routingKey, is(equalTo("rk")));
        assertThat(entry(1).routingKey, is(equalTo("rk")));
    }

    // test the routing key is used as a pattern
    @Test
    public void routingKeyPattern() {
        setUpDummyAppender();

        dummyAppender.setRoutingKeyPattern("log.%p");

        logger.info("Test1");
        logger.warn("Test2");

        dummyChannel = (DummyChannel) dummyAppender.getChannel();

        assertThat(dummyChannel.entries.size(), is(equalTo(2)));
        assertThat(entry(0).routingKey, is(equalTo("log.INFO")));
        assertThat(entry(1).routingKey, is(equalTo("log.WARN")));
    }

    // test that throwable handling is left to the layout if required
    @Test
    public void layoutHandlesThrowable() {
        setUpDummyAppender();

        dummyAppender.setLayout(new ThrowablePatternLayout());

        Exception cause = new RuntimeException("Ouch");
        Exception exception = new Exception("Error", cause);

        cause.fillInStackTrace();
        exception.fillInStackTrace();

        logger.info("Test1", exception);

        dummyChannel = (DummyChannel) dummyAppender.getChannel();

        assertThat(dummyChannel.entries.size(), is(equalTo(1)));
        assertThat(entry(0).body, is(equalTo("Test1\n")));
    }

    // test that throwable handling is done by the logger if required
    @Test
    public void layoutIgnoresThrowable() {
        setUpDummyAppender();

        Exception cause = new RuntimeException("Ouch");
        Exception exception = new Exception("Error", cause);

        cause.fillInStackTrace();
        exception.fillInStackTrace();

        logger.info("Test1", exception);

        dummyChannel = (DummyChannel) dummyAppender.getChannel();

        assertThat(dummyChannel.entries.size(), is(equalTo(1)));

        assertThat(entry(0).body, is(not(equalTo("Test1\n"))));

        String[] lines = entry(0).body.split("\n");

        assertThat(lines[0], is(equalTo("Test1")));
        // stack trace sanity check
        assertThat(lines[1], is(equalTo("java.lang.Exception: Error")));
        // check the message contains the cause exception
        assertThat(CollectionUtils.find(Arrays.asList(lines), new Predicate() {
                public boolean evaluate(Object input) {
                    return input.equals(
                        "Caused by: java.lang.RuntimeException: Ouch");
                }
            }), is(not(equalTo(null))));
    }

    // test that the logger handles all the documented properties
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
        assertThat(entry(0).exchange, is(equalTo("amq.topic")));

        // check factory configuration
        ConnectionFactory factory = dummyAppender.getFactory();

        assertThat(factory.getHost(), is(equalTo("amqp.openquake.org")));
        assertThat(factory.getPort(), is(equalTo(4004)));
        assertThat(factory.getUsername(), is(equalTo("looser")));
        assertThat(factory.getPassword(), is(equalTo("s3krit")));
        assertThat(factory.getVirtualHost(), is(equalTo("job.oq.org/test")));
    }
}
