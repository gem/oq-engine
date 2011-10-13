package org.gem.log;

import org.apache.log4j.spi.LoggingEvent;

/**
 * Abstract python logging bridge interface
 */
public interface PythonBridge {
    public void append(LoggingEvent event);
}
