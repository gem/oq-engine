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
}
