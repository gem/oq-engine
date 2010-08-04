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
import static org.mockito.Mockito.when;

import org.gem.engine.data.DiscreteVulnerabilityFunction;
import org.gem.engine.data.distribution.Distribution;
import org.junit.Before;
import org.junit.Test;

public class LossRatioMeanTest
{

    private LossRatioMean lossRatio;
    private Distribution distribution;

    @Before
    public void setUp()
    {
        distribution = mock(Distribution.class);
        lossRatio = new LossRatioMean(distribution);
    }

    @Test
    public void zeroWhenTheFunctionHasNoValues()
    {
        DiscreteVulnerabilityFunction function = new DiscreteVulnerabilityFunction(null, null, null, null, null);
        assertEquals(0.0, lossRatio.compute(function), 0.0);
    }

    @Test
    public void compute()
    {
        DiscreteVulnerabilityFunction function = new DiscreteVulnerabilityFunction(null, null, null, null, null);
        function.addPair(5.0, 4.0);
        function.addPair(5.5, 5.0);

        when(distribution.cumulativeProbability(4.75, 5.25)).thenReturn(2.0);
        when(distribution.cumulativeProbability(5.25, 5.75)).thenReturn(3.0);
        assertEquals(23.0, lossRatio.compute(function), 0.0);
    }

}
