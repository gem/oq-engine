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

import static org.gem.engine.core.AdditionalPipeKeys.CONDITIONAL_LOSS_RESULT;
import static org.junit.Assert.assertNotNull;

import org.gem.engine.core.event.listener.BaseFilterTest;
import org.gem.engine.data.FixedDiscreteFunction;
import org.junit.Before;
import org.junit.Test;

public class ConditionalLossCalculatorTest extends BaseFilterTest
{

    @Before
    public void setUp()
    {
        FixedDiscreteFunction curve = new FixedDiscreteFunction();
        curve.addPair(0.1, 1.0);

        addToPipe(A_KEY, curve);
        filter = new ConditionalLossCalculator(0.1, A_KEY); // out of range probability
    }

    @Test
    public void shouldComputeAndSaveTheConditionalLoss()
    {
        runOn(anySite());
        assertNotNull(pipeValueAtKey(CONDITIONAL_LOSS_RESULT));
    }

}
