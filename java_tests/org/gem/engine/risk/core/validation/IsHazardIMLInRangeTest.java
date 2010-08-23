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

package org.gem.engine.risk.core.validation;

import static org.gem.engine.risk.core.AdditionalPipeKeys.MEAN_FUNCTION;
import static org.gem.engine.risk.core.AdditionalPipeKeys.MEAN_IML;
import static org.gem.engine.risk.data.builder.DiscreteVulnerabilityFunctionBuilder.aFunction;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import org.gem.engine.risk.core.cache.Pipe;
import org.gem.engine.risk.core.validation.IsHazardIMLInRange;
import org.junit.Before;
import org.junit.Test;

public class IsHazardIMLInRangeTest
{

    private Pipe pipe;

    @Before
    public void setUp()
    {
        pipe = new Pipe();
        pipe.put(MEAN_FUNCTION, aFunction().withPair(6.0, 0.1).withPair(7.0, 0.1).build());
    }

    @Test
    public void isSatisfiedWhenTheHazardIMLIsWithinTheVulnerabilityFunctionRange1()
    {
        pipe.put(MEAN_IML, 5.0);
        assertFalse(new IsHazardIMLInRange().isSatisfiedBy(pipe));
    }

    @Test
    public void isSatisfiedWhenTheHazardIMLIsWithinTheVulnerabilityFunctionRange2()
    {
        pipe.put(MEAN_IML, 8.0);
        assertFalse(new IsHazardIMLInRange().isSatisfiedBy(pipe));
    }

    @Test
    public void isSatisfiedWhenTheHazardIMLIsWithinTheVulnerabilityFunctionRange3()
    {
        pipe.put(MEAN_IML, 6.0);
        assertTrue(new IsHazardIMLInRange().isSatisfiedBy(pipe));
    }

    @Test
    public void isSatisfiedWhenTheHazardIMLIsWithinTheVulnerabilityFunctionRange4()
    {
        pipe.put(MEAN_IML, 7.0);
        assertTrue(new IsHazardIMLInRange().isSatisfiedBy(pipe));
    }

    @Test
    public void isSatisfiedWhenTheHazardIMLIsWithinTheVulnerabilityFunctionRange5()
    {
        pipe.put(MEAN_IML, 6.5);
        assertTrue(new IsHazardIMLInRange().isSatisfiedBy(pipe));
    }

}
