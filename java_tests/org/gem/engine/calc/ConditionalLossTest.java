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

package org.gem.engine.calc;

import static org.junit.Assert.assertEquals;

import org.gem.engine.data.FixedDiscreteFunction;
import org.junit.Before;
import org.junit.Test;

public class ConditionalLossTest
{

    private ConditionalLoss conditionalLoss;

    @Before
    public void setUp()
    {
        FixedDiscreteFunction function = new FixedDiscreteFunction();
        function.addPair(0.21, 0.131);
        function.addPair(0.24, 0.108);
        function.addPair(0.27, 0.089);
        function.addPair(0.30, 0.066);

        conditionalLoss = new ConditionalLoss(function);
    }

    @Test
    public void valueIsZeroIfTheProbabilityIsOutOfRange1()
    {
        assertEquals(0.0, conditionalLoss.compute(0.065), 0.0);
    }

    @Test
    public void valueIsZeroIfTheProbabilityIsOutOfRange2()
    {
        assertEquals(0.0, conditionalLoss.compute(0.132), 0.0);
    }

    @Test
    public void compute()
    {
        assertEquals(0.2526, conditionalLoss.compute(0.100), 0.00009);
    }

    @Test
    public void valueIsZeroIfTheFunctionHasNoValues()
    {
        assertEquals(0.0, new ConditionalLoss(new FixedDiscreteFunction()).compute(0.100), 0.0);
    }

}
