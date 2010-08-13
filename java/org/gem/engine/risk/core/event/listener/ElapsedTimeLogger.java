/*
 * [COPYRIGHT]
 *
 * [NAME] is free software; you can redistribute it and/or modify it
 * under the terms of the GNU Lesser General Public License as
 * published by the Free Software Foundation; either version 2.1 of
 * the License, or (at your option) any later version.
 *
 * This software is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this software; if not, write to the Free
 * Software Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA
 * 02110-1301 USA, or see the FSF site: http://www.fsf.org.
 */

package org.gem.engine.risk.core.event.listener;

import static org.gem.engine.risk.core.Engine.START;
import static org.gem.engine.risk.core.Engine.STOP;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.gem.engine.risk.core.cache.Cache;
import org.gem.engine.risk.core.event.MultiEventListener;

/**
 * Logs the elapsed time of the computation.
 * 
 * @author Andrea Cerisara
 * @version $Id: ElapsedTimeLogger.java 567 2010-07-20 10:10:52Z acerisara $
 */
public class ElapsedTimeLogger extends MultiEventListener
{

    private long startTime;

    private Log logger = LogFactory.getLog(this.getClass());

    public ElapsedTimeLogger()
    {
        dispatchTo(STOP, "stop");
        dispatchTo(START, "start");
    }

    public void start(Cache buffer, Object... parameters)
    {
        startTime = System.currentTimeMillis();
    }

    public void stop(Cache buffer, Object... parameters)
    {
        long elapsedTime = (System.currentTimeMillis() - startTime) / 1000;
        logger.info("Computation completed, execution time is " + elapsedTime + "s");
    }

}
