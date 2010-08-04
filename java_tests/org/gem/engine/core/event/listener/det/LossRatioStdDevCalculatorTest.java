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

import static org.gem.engine.core.AdditionalPipeKeys.COV_FUNCTION;
import static org.gem.engine.core.AdditionalPipeKeys.DISTRIBUTION;
import static org.gem.engine.core.AdditionalPipeKeys.LOSS_RATIO_STD_DEV_RESULT;
import static org.gem.engine.core.AdditionalPipeKeys.MEAN_FUNCTION;
import static org.gem.engine.data.builder.DiscreteVulnerabilityFunctionBuilder.aFunction;
import static org.junit.Assert.assertEquals;

import org.gem.engine.core.event.listener.BaseFilterTest;
import org.gem.engine.data.distribution.LogNormalDistribution;
import org.junit.Before;
import org.junit.Test;

public class LossRatioStdDevCalculatorTest extends BaseFilterTest
{

    @Before
    public void setUp()
    {
        filter = new LossRatioStdDevCalculator();

        addToPipe(COV_FUNCTION, aFunction().withCode("YY").build());
        addToPipe(MEAN_FUNCTION, aFunction().withCode("XX").build());
        addToPipe(DISTRIBUTION, new LogNormalDistribution(0.0, 0.0));
    }

    @Test
    public void shouldComputeAndSaveTheLossRatioStdDev()
    {
        runOn(anySite());
        // 0.0 is the result when the functions have no values
        assertEquals(0.0, (Double) pipeValueAtKey(LOSS_RATIO_STD_DEV_RESULT), 0.0);
    }

}
