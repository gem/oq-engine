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

import static org.gem.engine.risk.core.AdditionalPipeKeys.ASSET;
import static org.gem.engine.risk.core.AdditionalPipeKeys.LOSS_CURVE_RESULT;
import static org.gem.engine.risk.core.AdditionalPipeKeys.LOSS_RATIO_CURVE_RESULT;

import org.gem.engine.risk.calc.LossCurve;
import org.gem.engine.risk.core.cache.Cache;
import org.gem.engine.risk.core.cache.Pipe;
import org.gem.engine.risk.core.event.Filter;
import org.gem.engine.risk.data.DiscreteFunction;
import org.gem.engine.risk.data.asset.Asset;

/**
 * Computes the {@link LossCurve} for the probabilistic scenario.
 * 
 * @author Andrea Cerisara
 * @version $Id: LossCurveCalculator.java 567 2010-07-20 10:10:52Z acerisara $
 */
public class LossCurveCalculator extends Filter
{

    @Override
    protected void filter(Cache buffer, Pipe pipe)
    {
        Asset asset = pipe.get(ASSET);
        DiscreteFunction lossRatioCurve = pipe.get(LOSS_RATIO_CURVE_RESULT);
        pipe.put(LOSS_CURVE_RESULT, new LossCurve(lossRatioCurve).compute(asset.getValue()));
    }

}
