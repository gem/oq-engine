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

package org.gem.engine.core.event.listener;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.gem.engine.core.Region;
import org.gem.engine.core.cache.Cache;
import org.gem.engine.core.event.EventListener;

/**
 * Logs the {@link Region} information.
 * <p>
 * You need to attach this listener to the <code>org.gem.engine.core.Engine.START</code> event of the engine.
 * 
 * @author Andrea Cerisara
 * @version $Id: RegionLogger.java 567 2010-07-20 10:10:52Z acerisara $
 */
public class RegionLogger implements EventListener
{

    private Log logger = LogFactory.getLog(this.getClass());

    @Override
    public void process(String event, Cache buffer, Object... parameters)
    {
        Region region = (Region) parameters[0];

        logger.info("Number of sites to compute " + region.numberOfCells());
        logger.info("Starting computation FROM " + region.getFrom() + " TO " + region.getTo());
        logger.info("Number of rows " + region.getRows() + ", columns " + region.getColumns());
    }

}
