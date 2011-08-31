package org.gem.log;

import java.util.Arrays;
import java.util.Properties;

import org.apache.commons.collections.CollectionUtils;
import org.apache.commons.collections.Predicate;

import org.apache.log4j.BasicConfigurator;
import org.apache.log4j.Layout;
import org.apache.log4j.Level;
import org.apache.log4j.Logger;
import org.apache.log4j.PatternLayout;
import org.apache.log4j.PropertyConfigurator;

import org.junit.After;
import org.junit.Before;
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
    private DummyConnection dummyConnection;
    private DummyAppender dummyAppender;
    private Logger logger;

    @Before
    public void setUp() {
        logger = Logger.getLogger(AMQPAppenderTest.class);
        logger.setLevel(Level.INFO);
    }

    @After
    public void tearDown() {
        AMQPAppender.setConnectionFactory(null);

        dummyConnection = null;
        dummyAppender = null;
        DummyAppender.lastAppender = null;
        logger = null;

        // this calls close on the appenders (and so it closes the
        // (fake) RabbitMQ connections)
        BasicConfigurator.resetConfiguration();
    }

    private void setUpDummyAppender() {
        AMQPAppender.setConnectionFactory(new DummyConnectionFactory());

        dummyAppender = new DummyAppender();
        dummyAppender.setLayout(new PatternLayout());

        BasicConfigurator.configure(dummyAppender);
    }

    private DummyConnection.Entry entry(int index) {
        return dummyConnection.entries.get(index);
    }

    // logging sanity test
    @Test
    public void basicLogging() {
        setUpDummyAppender();

        logger.info("Test1");
        logger.warn("Test2");

        dummyConnection = (DummyConnection) dummyAppender.getConnection();

        assertThat(dummyConnection, is(not(equalTo(null))));
        assertThat(dummyConnection.entries.size(), is(equalTo(2)));

        assertThat(entry(0).exchange, is(equalTo("")));
        assertThat(entry(0).routingKey, is(equalTo("")));
        assertThat(entry(0).level, is(equalTo("INFO")));
        assertThat(entry(0).body, is(equalTo("Test1\n")));

        assertThat(entry(1).exchange, is(equalTo("")));
        assertThat(entry(1).routingKey, is(equalTo("")));
        assertThat(entry(1).level, is(equalTo("WARN")));
        assertThat(entry(1).body, is(equalTo("Test2\n")));
    }

    // test the routing key is used
    @Test
    public void routingKey() {
        setUpDummyAppender();

        dummyAppender.setRoutingKeyPattern("rk");

        logger.info("Test1");
        logger.warn("Test2");

        dummyConnection = (DummyConnection) dummyAppender.getConnection();

        assertThat(dummyConnection, is(not(equalTo(null))));
        assertThat(dummyConnection.entries.size(), is(equalTo(2)));
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

        dummyConnection = (DummyConnection) dummyAppender.getConnection();

        assertThat(dummyConnection, is(not(equalTo(null))));
        assertThat(dummyConnection.entries.size(), is(equalTo(2)));
        assertThat(entry(0).routingKey, is(equalTo("log.info")));
        assertThat(entry(1).routingKey, is(equalTo("log.warn")));
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

        dummyConnection = (DummyConnection) dummyAppender.getConnection();

        assertThat(dummyConnection, is(not(equalTo(null))));
        assertThat(dummyConnection.entries.size(), is(equalTo(1)));
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

        dummyConnection = (DummyConnection) dummyAppender.getConnection();

        assertThat(dummyConnection, is(not(equalTo(null))));
        assertThat(dummyConnection.entries.size(), is(equalTo(1)));

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
        AMQPAppender.setConnectionFactory(new DummyConnectionFactory());

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
        dummyConnection = (DummyConnection) dummyAppender.getConnection();

        // check layout
        Layout layout = dummyAppender.getLayout();

        assertThat(layout, is(instanceOf(PatternLayout.class)));

        PatternLayout patternLayout = (PatternLayout) layout;

        assertThat(patternLayout.getConversionPattern(),
                   is(equalTo("%d %-5p [%c] - %m%n")));

        // check message properties
        assertThat(dummyConnection, is(not(equalTo(null))));
        assertThat(dummyConnection.entries.size(), is(equalTo(1)));
        assertThat(entry(0).exchange, is(equalTo("amq.topic")));

        // check factory configuration
        DummyConnection connection = dummyAppender.getConnection();

        assertThat(connection.host, is(equalTo("amqp.openquake.org")));
        assertThat(connection.port, is(equalTo(4004)));
        assertThat(connection.username, is(equalTo("looser")));
        assertThat(connection.password, is(equalTo("s3krit")));
        assertThat(connection.virtualHost, is(equalTo("job.oq.org/test")));
    }
}
