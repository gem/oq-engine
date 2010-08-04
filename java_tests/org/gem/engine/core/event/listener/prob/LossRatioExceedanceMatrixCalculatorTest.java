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

import static org.gem.engine.core.AdditionalPipeKeys.COV_FUNCTION;
import static org.gem.engine.core.AdditionalPipeKeys.LRE_MATRIX_RATIOS_RESULT;
import static org.gem.engine.core.AdditionalPipeKeys.LRE_MATRIX_RESULT;
import static org.gem.engine.core.AdditionalPipeKeys.MEAN_FUNCTION;
import static org.gem.engine.data.builder.DiscreteVulnerabilityFunctionBuilder.aFunction;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import org.gem.engine.calc.Interval;
import org.gem.engine.core.event.listener.BaseFilterTest;
import org.junit.Before;
import org.junit.Test;

public class LossRatioExceedanceMatrixCalculatorTest extends BaseFilterTest
{

    @Before
    public void setUp()
    {
        addToPipe(LRE_MATRIX_RATIOS_RESULT, new Interval());
        addToPipe(COV_FUNCTION, aFunction().withCode("XX").build());
        addToPipe(MEAN_FUNCTION, aFunction().withCode("XX").build());

        filter = new LossRatioExceedanceMatrixCalculator();
    }

    @Test
    public void shouldComputeAndSaveTheLREM()
    {
        runOn(anySite());

        // empty matrix because of the empty functions and the empty interval
        assertTrue(pipeValueAtKey(LRE_MATRIX_RESULT) instanceof Double[][]);
        assertEquals(0, ((Double[][]) pipeValueAtKey(LRE_MATRIX_RESULT)).length);
    }

}
