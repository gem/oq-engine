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

import static org.hamcrest.Matchers.closeTo;
import static org.hamcrest.Matchers.is;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import org.gem.engine.data.DiscreteVulnerabilityFunction;
import org.gem.engine.data.distribution.Distribution;
import org.junit.Before;
import org.junit.Test;

public class LossRatioStdDevTest
{

    private Distribution distribution;
    private LossRatioStdDev lossStdDev;

    @Before
    public void setUp()
    {
        distribution = mock(Distribution.class);
        lossStdDev = new LossRatioStdDev(distribution);
    }

    @Test
    public void zeroWhenTheFunctionsHaveNoValues()
    {
        DiscreteVulnerabilityFunction cov = new DiscreteVulnerabilityFunction(null, null, null, null, null);
        DiscreteVulnerabilityFunction mean = new DiscreteVulnerabilityFunction(null, null, null, null, null);
        assertEquals(0.0, lossStdDev.compute(mean, cov), 0.0);
    }

    @Test
    public void compute()
    {
        DiscreteVulnerabilityFunction cov = new DiscreteVulnerabilityFunction(null, null, null, null, null);
        DiscreteVulnerabilityFunction mean = new DiscreteVulnerabilityFunction(null, null, null, null, null);

        cov.addPair(5.0, 0.7);
        cov.addPair(5.5, 0.7);
        cov.addPair(6.0, 0.7);
        cov.addPair(6.5, 0.6);
        cov.addPair(7.0, 0.6);
        cov.addPair(7.5, 0.6);
        cov.addPair(8.0, 0.5);
        cov.addPair(8.5, 0.5);
        cov.addPair(9.0, 0.4);
        cov.addPair(9.5, 0.4);
        cov.addPair(10.0, 0.3);

        mean.addPair(5.0, 1.963E-015);
        mean.addPair(5.5, 0.000000000002525);
        mean.addPair(6.0, 0.0000000007995);
        mean.addPair(6.5, 0.00000008311);
        mean.addPair(7.0, 0.000003519);
        mean.addPair(7.5, 0.00007159);
        mean.addPair(8.0, 0.0007964);
        mean.addPair(8.5, 0.005371);
        mean.addPair(9.0, 0.02389);
        mean.addPair(9.5, 0.07511);
        mean.addPair(10.0, 0.1773);

        when(distribution.cumulativeProbability(4.75, 5.25)).thenReturn(0.0261);
        when(distribution.cumulativeProbability(5.25, 5.75)).thenReturn(0.0749);
        when(distribution.cumulativeProbability(5.75, 6.25)).thenReturn(0.1399);
        when(distribution.cumulativeProbability(6.25, 6.75)).thenReturn(0.1862);
        when(distribution.cumulativeProbability(6.75, 7.25)).thenReturn(0.1888);
        when(distribution.cumulativeProbability(7.25, 7.75)).thenReturn(0.1538);
        when(distribution.cumulativeProbability(7.75, 8.25)).thenReturn(0.1048);
        when(distribution.cumulativeProbability(8.25, 8.75)).thenReturn(0.0616);
        when(distribution.cumulativeProbability(8.75, 9.25)).thenReturn(0.0321);
        when(distribution.cumulativeProbability(9.25, 9.75)).thenReturn(0.0152);
        when(distribution.cumulativeProbability(9.75, 10.25)).thenReturn(0.0066);

        double stdDev = lossStdDev.compute(mean, cov);
        assertThat(stdDev, is(closeTo(0.018, 0.0009)));
    }

}
