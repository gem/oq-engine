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
import static org.junit.Assert.assertTrue;

import org.gem.engine.risk.data.distribution.Distribution;
import org.gem.engine.risk.data.distribution.DistributionFactory;
import org.gem.engine.risk.data.distribution.LogNormalDistribution;
import org.junit.Before;
import org.junit.Test;

public class DistributionFactoryTest
{

    private DistributionFactory factory;

    @Before
    public void setUp()
    {
        factory = new DistributionFactory();
    }

    @Test(expected = RuntimeException.class)
    public void shouldThrowAnExceptionIfTheTypeIsUnknown2()
    {
        factory.create("XX", 1.0, 1.0);
    }

    @Test
    public void aLnTypeShouldResultInALogNormalDistribution()
    {
        assertTrue(factory.create(DistributionFactory.LOG_NORMAL, 1.0, 1.0) instanceof LogNormalDistribution);
    }

    @Test
    public void canCreateADistributionUsingMeanAndCovValues()
    {
        Distribution distribution = factory.create(DistributionFactory.LOG_NORMAL, 1.0, 2.0);
        assertEquals(1.0, distribution.getMean(), 0.0);
        assertEquals(2.0, distribution.getStdDev(), 0.0);
    }

}
