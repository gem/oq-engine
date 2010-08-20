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

import org.gem.engine.risk.calc.Interval;
import org.gem.engine.risk.calc.LossRatioExceedanceMatrixSegmentation;
import org.gem.engine.risk.data.DiscreteVulnerabilityFunction;
import org.junit.Test;

public class LossRatioExceedanceMatrixSegmentationTest
{

    @Test
    public void compute()
    {
        DiscreteVulnerabilityFunction function = new DiscreteVulnerabilityFunction(null, null, null, null, null);

        function.addPair(5.0, 1.0);
        function.addPair(5.5, 2.0);

        assertEquals(new Interval(0.00, 0.20, 0.40, 0.60, 0.80, 1.00, 1.20, 1.40, 1.60, 1.80, 2.00),
                new LossRatioExceedanceMatrixSegmentation().compute(function));
    }

}
