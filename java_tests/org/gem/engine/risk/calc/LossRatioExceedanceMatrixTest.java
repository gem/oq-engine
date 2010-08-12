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
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import org.gem.engine.risk.calc.Interval;
import org.gem.engine.risk.calc.LossRatioExceedanceMatrix;
import org.gem.engine.risk.calc.LossRatioExceedanceMatrixSegmentation;
import org.gem.engine.risk.data.DiscreteVulnerabilityFunction;
import org.gem.engine.risk.data.distribution.Distribution;
import org.gem.engine.risk.data.distribution.DistributionFactory;
import org.junit.Before;
import org.junit.Test;

public class LossRatioExceedanceMatrixTest
{

    private Distribution distribution;
    private LossRatioExceedanceMatrix matrix;
    private DiscreteVulnerabilityFunction cov;
    private DiscreteVulnerabilityFunction mean;

    @Before
    public void setUp()
    {
        distribution = mock(Distribution.class);
        DistributionFactory factory = mock(DistributionFactory.class);

        cov = new DiscreteVulnerabilityFunction(null, null, null, DistributionFactory.LOG_NORMAL, null);
        cov.addPair(5.0, 0.1);
        cov.addPair(5.5, 0.2);

        mean = new DiscreteVulnerabilityFunction(null, null, null, DistributionFactory.LOG_NORMAL, null);
        mean.addPair(5.0, 1.0);
        mean.addPair(5.5, 2.0);

        matrix = new LossRatioExceedanceMatrix(new LossRatioExceedanceMatrixSegmentation().compute(mean), factory);
        when(factory.create(DistributionFactory.LOG_NORMAL, 1.0, 0.1)).thenReturn(distribution);
        when(factory.create(DistributionFactory.LOG_NORMAL, 2.0, 0.2)).thenReturn(distribution);
    }

    @Test
    public void emptyFunctionsAndIntervalMeansEmptyMatrix()
    {
        cov = new DiscreteVulnerabilityFunction(null, null, null, DistributionFactory.LOG_NORMAL, null);
        mean = new DiscreteVulnerabilityFunction(null, null, null, DistributionFactory.LOG_NORMAL, null);
        matrix = new LossRatioExceedanceMatrix(new Interval(), null); // empty interval
        assertEquals(0, matrix.compute(mean, cov).length); // empty functions
    }

    @Test
    public void compute()
    {
        when(distribution.cumulativeProbability(0.0 + 0.20)).thenReturn(0.1);
        when(distribution.cumulativeProbability(0.0 + 0.40)).thenReturn(0.2);
        when(distribution.cumulativeProbability(0.0 + 0.60)).thenReturn(0.3);
        when(distribution.cumulativeProbability(0.0 + 0.80)).thenReturn(0.4);
        when(distribution.cumulativeProbability(1.0)).thenReturn(0.7);
        when(distribution.cumulativeProbability(1.0 + 0.20)).thenReturn(0.8);
        when(distribution.cumulativeProbability(1.0 + 0.40)).thenReturn(0.9);
        when(distribution.cumulativeProbability(1.0 + 0.60)).thenReturn(1.0);
        when(distribution.cumulativeProbability(1.0 + 0.80)).thenReturn(1.1);
        when(distribution.cumulativeProbability(2.0)).thenReturn(1.2);

        assertEquals(2, matrix.compute(mean, cov)[0].length);

        assertEquals(1.0 - 0.1, matrix.compute(mean, cov)[0][0], 0.00000009);
        assertEquals(1.0 - 0.1, matrix.compute(mean, cov)[0][1], 0.00000009);
        assertEquals(1.0 - 0.2, matrix.compute(mean, cov)[1][0], 0.00000009);
        assertEquals(1.0 - 0.2, matrix.compute(mean, cov)[1][1], 0.00000009);
        assertEquals(1.0 - 0.3, matrix.compute(mean, cov)[2][0], 0.00000009);
        assertEquals(1.0 - 0.3, matrix.compute(mean, cov)[2][1], 0.00000009);
        assertEquals(1.0 - 0.4, matrix.compute(mean, cov)[3][0], 0.00000009);
        assertEquals(1.0 - 0.4, matrix.compute(mean, cov)[3][1], 0.00000009);
        assertEquals(1.0 - 0.7, matrix.compute(mean, cov)[4][0], 0.00000009);
        assertEquals(1.0 - 0.7, matrix.compute(mean, cov)[4][1], 0.00000009);
        assertEquals(1.0 - 0.8, matrix.compute(mean, cov)[5][0], 0.00000009);
        assertEquals(1.0 - 0.8, matrix.compute(mean, cov)[5][1], 0.00000009);
        assertEquals(1.0 - 0.9, matrix.compute(mean, cov)[6][0], 0.00000009);
        assertEquals(1.0 - 0.9, matrix.compute(mean, cov)[6][1], 0.00000009);
        assertEquals(1.0 - 1.0, matrix.compute(mean, cov)[7][0], 0.00000009);
        assertEquals(1.0 - 1.0, matrix.compute(mean, cov)[7][1], 0.00000009);

        // negative values are not allowed
        assertEquals(0.0, matrix.compute(mean, cov)[8][0], 0.0);
        assertEquals(0.0, matrix.compute(mean, cov)[8][1], 0.0);
        assertEquals(0.0, matrix.compute(mean, cov)[9][0], 0.0);
        assertEquals(0.0, matrix.compute(mean, cov)[9][1], 0.0);

        // value for the last row is 1.0
        assertEquals(1.0 - 0.7, matrix.compute(mean, cov)[10][0], 0.0);
        assertEquals(1.0 - 0.7, matrix.compute(mean, cov)[10][1], 0.0);
    }

    @Test
    // (1 - probability) < 0.00001 must be zero and not > 1.0
    public void computeWithZeroValues()
    {
        when(distribution.cumulativeProbability(0.0 + 0.20)).thenReturn(0.1);
        when(distribution.cumulativeProbability(0.0 + 0.40)).thenReturn(1.0 - 0.00001);
        when(distribution.cumulativeProbability(0.0 + 0.60)).thenReturn(1.0 - 0.000009);
        when(distribution.cumulativeProbability(0.0 + 0.80)).thenReturn(-0.5);

        assertEquals(1.0 - 0.1, matrix.compute(mean, cov)[0][0], 0.00000009);
        assertEquals(1.0 - 0.1, matrix.compute(mean, cov)[0][1], 0.00000009);
        assertEquals(0.0, matrix.compute(mean, cov)[1][0], 0.0);
        assertEquals(0.0, matrix.compute(mean, cov)[1][1], 0.0);
        assertEquals(0.0, matrix.compute(mean, cov)[2][0], 0.0);
        assertEquals(0.0, matrix.compute(mean, cov)[2][1], 0.0);
        assertEquals(1.0, matrix.compute(mean, cov)[3][0], 0.0);
        assertEquals(1.0, matrix.compute(mean, cov)[3][1], 0.0);
    }

}
