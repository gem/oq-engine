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

import static org.gem.engine.data.builder.DiscreteVulnerabilityFunctionBuilder.aFunction;
import static org.gem.engine.data.builder.HazardCurveBuilder.aCurve;
import static org.junit.Assert.assertEquals;

import org.gem.engine.data.DiscreteVulnerabilityFunction;
import org.gem.engine.data.HazardCurve;
import org.junit.Before;
import org.junit.Test;

public class LossRatioCurveTest
{

    private LossRatioCurve curve;
    private DiscreteVulnerabilityFunction function;

    @Before
    public void setUp()
    {
        function = aFunction().withCode("XX").withPair(5.0, 0.0).withPair(6.0, 0.0).withPair(7.0, 0.0).withPair(8.0,
                0.0).build();

        HazardCurve hazardCurve = aCurve().withPair(5.0, 0.138).withPair(6.0, 0.099).withPair(7.0, 0.068).withPair(8.0,
                0.041).build();

        Double[][] LREM = new Double[][] { { 0.695, 0.858, 0.990, 1.000 }, { 0.266, 0.510, 0.841, 0.999 } };
        curve = new LossRatioCurve(new Interval(1.0, 2.0), LREM, hazardCurve);
    }

    @Test
    public void compute()
    {
        assertEquals(0.2891, curve.compute(function).getFor(1.0), 0.00009);
        assertEquals(0.1853, curve.compute(function).getFor(2.0), 0.00009);
    }

}
