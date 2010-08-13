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

package org.gem.engine.risk.data.distribution;

import static org.junit.Assert.assertEquals;

import org.gem.engine.risk.data.distribution.LogNormalDistribution;
import org.junit.Test;

public class LogNormalDistributionTest
{

    private LogNormalDistribution distribution;

    @Test
    public void standardDeviation1()
    {
        distribution = new LogNormalDistribution(1.5, 0.5);
        assertEquals(0.75, distribution.getStdDev(), 0.009);
    }

    @Test
    public void standardDeviation2()
    {
        distribution = new LogNormalDistribution(1.52356, 0.59473778);
        assertEquals(0.9061186920968, distribution.getStdDev(), 0.00000000000009);
    }

    @Test
    public void zeta()
    {
        distribution = new LogNormalDistribution(7.0, 0.1);
        assertEquals(0.0997513451195927, distribution.zeta(), 0.00000000000000009);
    }

    @Test
    public void lambda()
    {
        distribution = new LogNormalDistribution(7.0, 0.1);
        assertEquals(1.9409349836287293, distribution.lambda(), 0.00000000000000009);
    }

    @Test
    public void probabilityWithinARange()
    {
        distribution = new LogNormalDistribution(7.0, 0.1);
        assertEquals(0.0250, distribution.cumulativeProbability(5.25, 5.75), 0.00009);
        assertEquals(0.1114, distribution.cumulativeProbability(5.75, 6.25), 0.00009);
        assertEquals(0.2378, distribution.cumulativeProbability(6.25, 6.75), 0.00009);
        assertEquals(0.2795, distribution.cumulativeProbability(6.75, 7.25), 0.00009);
        assertEquals(0.2017, distribution.cumulativeProbability(7.25, 7.75), 0.00009);
        assertEquals(0.0974, distribution.cumulativeProbability(7.75, 8.25), 0.00009);
        assertEquals(0.0337, distribution.cumulativeProbability(8.25, 8.75), 0.00009);
        assertEquals(0.0089, distribution.cumulativeProbability(8.75, 9.25), 0.00009);
        assertEquals(0.0019, distribution.cumulativeProbability(9.25, 9.75), 0.00009);
    }

}
