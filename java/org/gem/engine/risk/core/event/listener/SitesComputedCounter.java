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

import static org.gem.engine.risk.core.cache.Pipe.REGION;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.gem.engine.risk.core.Region;
import org.gem.engine.risk.core.Site;
import org.gem.engine.risk.core.cache.Cache;
import org.gem.engine.risk.core.cache.Pipe;
import org.gem.engine.risk.core.event.Filter;

/**
 * Logs the computed {@link Site}.
 * 
 * @author Andrea Cerisara
 * @version $Id: SitesComputedCounter.java 567 2010-07-20 10:10:52Z acerisara $
 */
public class SitesComputedCounter extends Filter
{

    private int counter;
    private int printEvery;

    private Log logger = LogFactory.getLog(this.getClass());

    /**
     * @param printEvery the number of computed sites between each log
     */
    public SitesComputedCounter(int printEvery)
    {
        this.printEvery = printEvery;
    }

    @Override
    protected void filter(Cache buffer, Pipe pipe)
    {
        counter++;
        Region region = pipe.get(REGION);

        if (counter % printEvery == 0)
        {
            logger.info("Sites computed " + counter + "/" + region.numberOfCells());
        }
    }

}
