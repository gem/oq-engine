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
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import org.gem.engine.data.FixedDiscreteFunction;
import org.junit.Before;
import org.junit.Test;

public class ProbabilityOfOccurrenceTest
{

    private Interpolator interpolator;
    private ProbabilityOfOccurrence calculator;

    @Before
    public void setUp()
    {
        interpolator = mock(Interpolator.class);
        FixedDiscreteFunction function = new FixedDiscreteFunction();

        function.addPair(0.0, 1.0);
        function.addPair(0.1, 2.0);
        function.addPair(0.2, 3.0);
        function.addPair(0.3, 4.0);
        function.addPair(0.4, 5.0);

        calculator = new ProbabilityOfOccurrence(interpolator, function);
    }

    @Test
    public void computeOnFirstValue1()
    {
        calculator.compute(0.1);
        verify(interpolator).interpolate((0.1 + 0.2) / 2);
    }

    @Test
    public void computeOnFirstValue2()
    {
        when(interpolator.interpolate((0.0 + 0.1) / 2)).thenReturn(0.5);
        assertEquals(0.5, calculator.compute(0.0), 0.0);
    }

    @Test
    public void computeOnLastValue1()
    {
        calculator.compute(0.4);
        verify(interpolator).interpolate((0.3 + 0.4) / 2);
    }

    @Test
    public void computeOnLastValue2()
    {
        when(interpolator.interpolate((0.3 + 0.4) / 2)).thenReturn(5.0);
        assertEquals(5.0, calculator.compute(0.4), 0.0); // PE for the last value is 0
    }

    @Test
    public void compute()
    {
        when(interpolator.interpolate((0.1 + 0.2) / 2)).thenReturn(1.0);
        when(interpolator.interpolate((0.2 + 0.3) / 2)).thenReturn(0.5);
        assertEquals(0.5, calculator.compute(0.2), 0.0);
    }

}
