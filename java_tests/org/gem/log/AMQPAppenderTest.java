package org.gem.log;

import org.apache.log4j.BasicConfigurator;
import org.apache.log4j.Logger;
import org.apache.log4j.PatternLayout;

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

        logger.info("Test");

        dummyChannel = (DummyChannel) dummyAppender.getChannel();

        assertThat(dummyChannel.entries.size(), is(equalTo(1)));

        DummyChannel.Entry entry = dummyChannel.entries.get(0);

        assertThat(entry.exchange, is(equalTo("")));
        assertThat(entry.routingKey, is(equalTo("")));
        assertThat(entry.properties.getType(), is(equalTo("INFO")));
        assertThat(entry.body, is(equalTo("Test\n")));
    }
}
