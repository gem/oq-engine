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

package org.gem.engine.core.event.listener.det;

import org.gem.engine.core.cache.Cache;
import org.gem.engine.data.DiscreteVulnerabilityFunction;

/**
 * Represents a {@link Cache} key for the deterministic scenario.
 * <p>
 * In the deterministic scenario a result can be cached if the {@link DiscreteVulnerabilityFunction} is the same and the hazard IML mean/cov value are the same.
 * 
 * @author Andrea Cerisara
 * @version $Id: DeterministicScenarioCacheKey.java 567 2010-07-20 10:10:52Z acerisara $
 */
public class DeterministicScenarioCacheKey
{

    private final double cov;
    private final double mean;
    private final DiscreteVulnerabilityFunction function;

    public DeterministicScenarioCacheKey(DiscreteVulnerabilityFunction function, double mean, double cov)
    {
        this.cov = cov;
        this.mean = mean;
        this.function = function;
    }

    @Override
    public boolean equals(Object obj)
    {
        if (!(obj instanceof DeterministicScenarioCacheKey))
        {
            return false;
        }

        DeterministicScenarioCacheKey other = (DeterministicScenarioCacheKey) obj;
        // we can use the == operator with double because values are readed from external source and kept as is
        return function.equals(other.function) && mean == other.mean && cov == other.cov;
    }

    @Override
    public String toString()
    {
        return new StringBuffer(function.toString()).append(mean).append(cov).toString();
    }

    @Override
    public int hashCode()
    {
        return new StringBuffer(function.toString()).append(mean).append(cov).toString().hashCode();
    }

}
