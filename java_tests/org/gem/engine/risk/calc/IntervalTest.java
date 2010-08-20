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

import java.util.Arrays;

import org.gem.engine.risk.calc.Interval;
import org.junit.Test;

public class IntervalTest
{

    @Test(expected = RuntimeException.class)
    public void shouldThrowAnExceptionIfTheValueIsNotPresent1()
    {
        new Interval(1.0, 2.0).lowerBoundFor(3.0);
    }

    @Test(expected = RuntimeException.class)
    public void shouldThrowAnExceptionIfTheValueIsNotPresent2()
    {
        new Interval(1.0, 2.0).upperBoundFor(3.0);
    }

    @Test
    public void lowerBound()
    {
        assertEquals(1.5, new Interval(1.0, 2.0, 3.0).lowerBoundFor(2.0), 0.01);
    }

    @Test
    public void lowerBoundWithFirstElement()
    {
        assertEquals(0.5, new Interval(1.0, 2.0, 3.0).lowerBoundFor(1.0), 0.01);
    }

    @Test
    public void lowerBoundWithLastElement()
    {
        assertEquals(2.5, new Interval(1.0, 2.0, 3.0).lowerBoundFor(3.0), 0.01);
    }

    @Test
    public void upperBound()
    {
        assertEquals(2.5, new Interval(1.0, 2.0, 3.0).upperBoundFor(2.0), 0.01);
    }

    @Test
    public void upperBoundWithFirstElement()
    {
        assertEquals(1.5, new Interval(1.0, 2.0, 3.0).upperBoundFor(1.0), 0.01);
    }

    @Test
    public void upperBoundWithLastElement()
    {
        assertEquals(3.5, new Interval(1.0, 2.0, 3.0).upperBoundFor(3.0), 0.01);
    }

    @Test(expected = RuntimeException.class)
    public void toCloneWeNeedAtLeastTwoElements()
    {
        new Interval(Arrays.asList(1.0)).split(1);
    }

    @Test
    public void splitWithASingleIntervalAndNoValuesBetween()
    {
        assertEquals(new Interval(1.0, 2.0), new Interval(Arrays.asList(1.0, 2.0)).split(1));
    }

    @Test
    public void splitWithASingleIntervalAndAValueBetween()
    {
        assertEquals(new Interval(1.0, 1.5, 2.0), new Interval(Arrays.asList(1.0, 2.0)).split(2));
    }

    @Test
    public void splitWithASingleIntervalAndValuesBetween()
    {
        Interval result = new Interval(1.0, 1.25, 1.50, 1.75, 2.0);
        assertEquals(result, new Interval(1.0, 2.0).split(4));
    }

    @Test
    public void splitWithMultipleIntervalsAndAValueBetween()
    {
        Interval result = new Interval(1.0, 1.5, 2.0, 2.5, 3.0);
        assertEquals(result, new Interval(1.0, 2.0, 3.0).split(2));
    }

    @Test
    public void splitWithMultipleIntervalsAndValuesBetween()
    {
        Interval result = new Interval(1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0);
        assertEquals(result, new Interval(1.0, 2.0, 3.0).split(4));
    }

    @Test
    public void splitWithRealValuesFromTurkey()
    {
        Interval range = new Interval(0.0, 1.96E-15, 2.53E-12, 8.00E-10, 8.31E-08, 3.52E-06, 7.16E-05, 7.96E-04,
                5.37E-03, 2.39E-02, 7.51E-02, 1.77E-01);

        Interval result = new Interval(0.0, 3.9199999999999996E-16, 7.839999999999999E-16, 1.176E-15,
                1.5679999999999998E-15, 1.96E-15, 5.07568E-13, 1.0131759999999998E-12, 1.5187839999999998E-12,
                2.024392E-12, 2.53E-12, 1.62024E-10, 3.2151800000000003E-10, 4.81012E-10, 6.405060000000001E-10,
                8.0E-10, 1.726E-8, 3.372E-8, 5.0180000000000003E-8, 6.663999999999999E-8, 8.31E-8,
                7.704800000000001E-7, 1.4578600000000002E-6, 2.14524E-6, 2.8326200000000003E-6, 3.52E-6,
                1.7136000000000003E-5, 3.0752000000000006E-5, 4.4368000000000006E-5, 5.798400000000001E-5, 7.16E-5,
                2.1648000000000001E-4, 3.6136E-4, 5.0624E-4, 6.5112E-4, 7.96E-4, 0.0017108000000000002, 0.0026256,
                0.0035404, 0.0044552, 0.00537, 0.009076, 0.012782, 0.016488000000000003, 0.020194, 0.0239,
                0.034140000000000004, 0.04438, 0.05462, 0.06486, 0.0751, 0.09548, 0.11585999999999999, 0.13624,
                0.15661999999999998, 0.177);

        assertEquals(result, range.split(5));
    }

    @Test
    public void splitWithRealValuesFromTaiwan()
    {
        Interval range = new Interval(0.0, 1.877E-20, 8.485E-17, 8.427E-14, 2.495E-11, 2.769E-09, 1.372E-07, 3.481E-06,
                5.042E-05, 4.550E-04, 2.749E-03, 1.181E-02);

        assertEquals(56, range.split(5).size());
    }

}
