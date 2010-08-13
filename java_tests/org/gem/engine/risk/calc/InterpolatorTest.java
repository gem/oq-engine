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

package org.gem.engine.risk.calc;

import static org.junit.Assert.assertEquals;

import org.gem.engine.risk.calc.Interpolator;
import org.gem.engine.risk.data.FixedDiscreteFunction;
import org.junit.Before;
import org.junit.Test;

public class InterpolatorTest
{

    private Interpolator interpolator;

    @Before
    public void setUp()
    {
        FixedDiscreteFunction function = new FixedDiscreteFunction();
        function.addPair(0.1, 1.0);
        function.addPair(0.2, 2.0);
        function.addPair(0.3, 3.0);
        function.addPair(0.4, 4.0);

        interpolator = new Interpolator(function);
    }

    @Test(expected = IllegalArgumentException.class)
    public void canNotInterpolateOnFirstValue()
    {
        interpolator.interpolate(0.1);
    }

    @Test(expected = IllegalArgumentException.class)
    public void canNotInterpolateOnLastValue()
    {
        interpolator.interpolate(0.4);
    }

    @Test
    public void interpolate1()
    {
        assertEquals(1.50, interpolator.interpolate(0.15), 0.01);
    }

    @Test
    public void interpolate2()
    {
        assertEquals(3.50, interpolator.interpolate(0.35), 0.01);
    }

    @Test
    public void interpolate3()
    {
        assertEquals(2.00, interpolator.interpolate(0.20), 0.01);
    }

    @Test
    public void interpolate4()
    {
        FixedDiscreteFunction function = new FixedDiscreteFunction();
        function.addPair(0.079, 6.68E-02);
        function.addPair(0.100, 2.55E-02);
        function.addPair(0.126, 8.81E-03);
        function.addPair(0.158, 2.74E-03);
        function.addPair(0.200, 7.56E-04);
        function.addPair(0.251, 1.82E-04);
        function.addPair(0.316, 3.74E-05);
        function.addPair(0.398, 6.55E-06);
        function.addPair(0.501, 9.71E-07);
        function.addPair(0.631, 1.22E-07);
        function.addPair(0.791, 6.68E-08);
        function.addPair(1.000, 2.55E-09);

        assertEquals(1.93E-04, new Interpolator(function).interpolate(0.25), 0.000001);
        assertEquals(2.46E-05, new Interpolator(function).interpolate(0.35), 0.00000001);
    }

}
