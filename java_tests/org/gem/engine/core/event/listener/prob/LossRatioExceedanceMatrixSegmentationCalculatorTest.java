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

package org.gem.engine.core.event.listener.prob;

import static org.gem.engine.core.AdditionalPipeKeys.LRE_MATRIX_RATIOS_RESULT;
import static org.gem.engine.core.AdditionalPipeKeys.MEAN_FUNCTION;
import static org.gem.engine.data.builder.DiscreteVulnerabilityFunctionBuilder.aFunction;
import static org.junit.Assert.assertEquals;

import org.gem.engine.calc.Interval;
import org.gem.engine.core.event.listener.BaseFilterTest;
import org.junit.Before;
import org.junit.Test;

public class LossRatioExceedanceMatrixSegmentationCalculatorTest extends BaseFilterTest
{

    @Before
    public void setUp()
    {
        addToPipe(MEAN_FUNCTION, aFunction().withCode("XX").withPair(5.0, 1.0).build());
        filter = new LossRatioExceedanceMatrixSegmentationCalculator();
    }

    @Test
    public void shouldComputeAndSaveTheRatios()
    {
        runOn(anySite());

        assertEquals(new Interval(0.00, 0.20, 0.40, 0.60, 0.80, 1.00),
                (Interval) pipeValueAtKey(LRE_MATRIX_RATIOS_RESULT));
    }

}
