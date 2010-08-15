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

package org.gem.engine.risk.core.event.listener.det;

import static org.gem.engine.risk.core.AdditionalPipeKeys.COV_IML;
import static org.gem.engine.risk.core.AdditionalPipeKeys.MEAN_IML;
import static org.gem.engine.risk.core.cache.Pipe.CURRENT_SITE;

import org.gem.engine.risk.core.Site;
import org.gem.engine.risk.core.cache.Cache;
import org.gem.engine.risk.core.cache.Pipe;
import org.gem.engine.risk.core.event.Filter;
import org.gem.engine.risk.core.reader.HazardReader;

/**
 * Loads an hazard IML in the {@link Pipe}, using the current {@link Site}.
 * 
 * @author Andrea Cerisara
 * @version $Id: HazardIMLLoader.java 567 2010-07-20 10:10:52Z acerisara $
 */
public class HazardIMLLoader extends Filter
{

    private final HazardReader<Double> covs;
    private final HazardReader<Double> means;

    /**
     * @param means the hazard reader used for the mean
     * @param covs the hazard reader used for the cov
     */
    public HazardIMLLoader(HazardReader<Double> means, HazardReader<Double> covs)
    {
        this.covs = covs;
        this.means = means;
    }

    @Override
    protected void filter(Cache buffer, Pipe pipe)
    {
        pipe.put(COV_IML, covs.readAt((Site) pipe.get(CURRENT_SITE)));
        pipe.put(MEAN_IML, means.readAt((Site) pipe.get(CURRENT_SITE)));
    }

}
