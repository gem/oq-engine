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

import static org.gem.engine.risk.core.AdditionalPipeKeys.DISTRIBUTION;
import static org.gem.engine.risk.core.AdditionalPipeKeys.LOSS_RATIO_RESULT;
import static org.gem.engine.risk.core.AdditionalPipeKeys.MEAN_FUNCTION;
import static org.gem.engine.risk.data.builder.DiscreteVulnerabilityFunctionBuilder.aFunction;
import static org.junit.Assert.assertEquals;

import org.gem.engine.risk.core.event.listener.BaseFilterTest;
import org.gem.engine.risk.core.event.listener.det.LossRatioMeanCalculator;
import org.gem.engine.risk.data.distribution.LogNormalDistribution;
import org.junit.Before;
import org.junit.Test;

public class LossRatioMeanCalculatorTest extends BaseFilterTest
{

    @Before
    public void setUp()
    {
        filter = new LossRatioMeanCalculator();

        addToPipe(DISTRIBUTION, new LogNormalDistribution(0.0, 0.0));
        addToPipe(MEAN_FUNCTION, aFunction().withCode("XX").build());
    }

    @Test
    public void shouldComputeAndSaveTheLossRatio()
    {
        runOn(anySite());
        // 0.0 is the result when the function has no values
        assertEquals(0.0, (Double) pipeValueAtKey(LOSS_RATIO_RESULT), 0.0);
    }

}
