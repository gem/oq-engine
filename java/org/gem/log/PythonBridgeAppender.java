/*
    Copyright (c) 2010-2012, GEM Foundation.

    OpenQuake is free software: you can redistribute it and/or modify it
    under the terms of the GNU Affero General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    OpenQuake is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
*/

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
