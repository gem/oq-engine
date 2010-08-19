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

import static org.gem.engine.risk.core.AdditionalPipeKeys.HAZARD_CURVE;
import static org.gem.engine.risk.core.AdditionalPipeKeys.LOSS_RATIO_CURVE_RESULT;
import static org.gem.engine.risk.core.AdditionalPipeKeys.LRE_MATRIX_RATIOS_RESULT;
import static org.gem.engine.risk.core.AdditionalPipeKeys.LRE_MATRIX_RESULT;
import static org.gem.engine.risk.core.AdditionalPipeKeys.MEAN_FUNCTION;

import org.gem.engine.risk.calc.Interval;
import org.gem.engine.risk.calc.LossRatioCurve;
import org.gem.engine.risk.core.cache.Cache;
import org.gem.engine.risk.core.cache.Pipe;
import org.gem.engine.risk.core.event.Filter;
import org.gem.engine.risk.data.DiscreteVulnerabilityFunction;
import org.gem.engine.risk.data.HazardCurve;

/**
 * Computes the {@link LossRatioCurve} for the probabilistic scenario.
 * 
 * @author Andrea Cerisara
 * @version $Id: LossRatioCurveCalculator.java 567 2010-07-20 10:10:52Z acerisara $
 */
public class LossRatioCurveCalculator extends Filter
{

    @Override
    protected void filter(Cache buffer, Pipe pipe)
    {
        HazardCurve curve = pipe.get(HAZARD_CURVE);
        Double[][] LREM = pipe.get(LRE_MATRIX_RESULT);
        Interval ratios = pipe.get(LRE_MATRIX_RATIOS_RESULT);
        DiscreteVulnerabilityFunction function = pipe.get(MEAN_FUNCTION);

        pipe.put(LOSS_RATIO_CURVE_RESULT, new LossRatioCurve(ratios, LREM, curve).compute(function));
    }

}
