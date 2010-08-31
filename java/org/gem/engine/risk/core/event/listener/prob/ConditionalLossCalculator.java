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

package org.gem.engine.risk.core.event.listener.prob;

import static org.gem.engine.risk.core.AdditionalPipeKeys.CONDITIONAL_LOSS_RESULT;

import org.gem.engine.risk.calc.ConditionalLoss;
import org.gem.engine.risk.core.cache.Cache;
import org.gem.engine.risk.core.cache.Pipe;
import org.gem.engine.risk.core.event.Filter;
import org.gem.engine.risk.data.DiscreteFunction;

/**
 * Computes the {@link ConditionalLoss} for the probabilistic scenario.
 * 
 * @author Andrea Cerisara
 * @version $Id: ConditionalLossCalculator.java 567 2010-07-20 10:10:52Z acerisara $
 */
public class ConditionalLossCalculator extends Filter
{

    private final String key;
    private final double probability;

    /**
     * @param probability the probability used
     * @param key the key used to store the result in the pipe
     */
    public ConditionalLossCalculator(double probability, String key)
    {
        this.key = key;
        this.probability = probability;
    }

    @Override
    protected void filter(Cache buffer, Pipe pipe)
    {
        DiscreteFunction curve = pipe.get(key);
        pipe.put(CONDITIONAL_LOSS_RESULT, new ConditionalLoss(curve).compute(probability));
    }

}
