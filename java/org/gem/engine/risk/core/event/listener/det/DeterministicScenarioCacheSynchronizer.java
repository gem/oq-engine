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
import static org.gem.engine.risk.core.AdditionalPipeKeys.MEAN_FUNCTION;
import static org.gem.engine.risk.core.AdditionalPipeKeys.MEAN_IML;

import org.gem.engine.risk.core.cache.Cache;
import org.gem.engine.risk.core.cache.Pipe;
import org.gem.engine.risk.core.event.Filter;
import org.gem.engine.risk.data.DiscreteVulnerabilityFunction;

/**
 * Stores an object to the {@link Cache} using the {@link DeterministicScenarioCacheKey} code as key.
 * <p>
 * This filters is useful to store data that change only when the related {@link DeterministicScenarioCacheKey} change.
 * 
 * @author Andrea Cerisara
 * @version $Id: DeterministicScenarioCacheSynchronizer.java 567 2010-07-20 10:10:52Z acerisara $
 */
public class DeterministicScenarioCacheSynchronizer extends Filter
{

    private final String key;
    private final Cache cache;

    /**
     * @param cache the cache implementation used
     * @param key the key used to store the data in the pipe
     */
    public DeterministicScenarioCacheSynchronizer(Cache cache, String key)
    {
        this.key = key;
        this.cache = cache;
    }

    @Override
    protected void filter(Cache buffer, Pipe pipe)
    {
        Double cov = pipe.get(COV_IML);
        Double mean = pipe.get(MEAN_IML);
        DiscreteVulnerabilityFunction function = pipe.get(MEAN_FUNCTION);

        cache.put(new DeterministicScenarioCacheKey(function, mean, cov).toString(), pipe.get(key));
    }

}
