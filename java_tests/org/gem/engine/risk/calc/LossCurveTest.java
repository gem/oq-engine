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

import org.gem.engine.risk.calc.LossCurve;
import org.gem.engine.risk.data.FixedDiscreteFunction;
import org.junit.Test;

public class LossCurveTest
{

    @Test
    public void emptyFunctionIfTheLossRatioCurveHasNoValues()
    {
        assertEquals(0, new LossCurve(new FixedDiscreteFunction()).compute(5.0).getDomain().size());
    }

    @Test
    public void compute()
    {
        FixedDiscreteFunction function = new FixedDiscreteFunction();
        function.addPair(0.1, 1.0);
        function.addPair(0.2, 2.0);
        function.addPair(0.3, 3.0);
        function.addPair(0.4, 4.0);
        function.addPair(0.5, 5.0);

        LossCurve curve = new LossCurve(function);

        assertEquals(1.0, curve.compute(5.0).getFor(0.1 * 5.0), 0.0);
        assertEquals(2.0, curve.compute(5.0).getFor(0.2 * 5.0), 0.0);
        assertEquals(3.0, curve.compute(5.0).getFor(0.3 * 5.0), 0.0);
        assertEquals(4.0, curve.compute(5.0).getFor(0.4 * 5.0), 0.0);
        assertEquals(5.0, curve.compute(5.0).getFor(0.5 * 5.0), 0.0);
    }

}
