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

import static org.gem.engine.core.AdditionalPipeKeys.DISTRIBUTION;
import static org.gem.engine.core.AdditionalPipeKeys.LOSS_RATIO_RESULT;
import static org.gem.engine.core.AdditionalPipeKeys.MEAN_FUNCTION;

import org.gem.engine.calc.LossRatioMean;
import org.gem.engine.core.cache.Cache;
import org.gem.engine.core.cache.Pipe;
import org.gem.engine.core.event.Filter;
import org.gem.engine.data.DiscreteVulnerabilityFunction;
import org.gem.engine.data.distribution.Distribution;

/**
 * Computes the {@link LossRatioMean} for the deterministic scenario.
 * 
 * @author Andrea Cerisara
 * @version $Id: LossRatioMeanCalculator.java 567 2010-07-20 10:10:52Z acerisara $
 */
public class LossRatioMeanCalculator extends Filter
{

    @Override
    protected void filter(Cache buffer, Pipe pipe)
    {
        Distribution distribution = pipe.get(DISTRIBUTION);
        DiscreteVulnerabilityFunction function = pipe.get(MEAN_FUNCTION);
        pipe.put(LOSS_RATIO_RESULT, new LossRatioMean(distribution).compute(function));
    }

}
