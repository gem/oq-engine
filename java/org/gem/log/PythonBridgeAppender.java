package org.gem.log;

import org.apache.log4j.AppenderSkeleton;
import org.apache.log4j.spi.LoggingEvent;

import org.gem.log.PythonBridge;

/**
 * Log4J appender class that sends log messages through JPype
 */
public class PythonBridgeAppender extends AppenderSkeleton {
    protected static PythonBridge bridge;

    @Override
    public void append(LoggingEvent event) {
        bridge.append(event);
    }

    @Override
    public boolean requiresLayout() {
        return false;
    }

    @Override
    public void close() {}
}
