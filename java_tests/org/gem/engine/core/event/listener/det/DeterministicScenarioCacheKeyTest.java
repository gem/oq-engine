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

package org.gem.engine.core.event.listener.det;

import static org.gem.engine.data.builder.DiscreteVulnerabilityFunctionBuilder.aFunction;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import org.gem.engine.data.DiscreteVulnerabilityFunction;
import org.junit.Before;
import org.junit.Test;

public class DeterministicScenarioCacheKeyTest
{

    private DiscreteVulnerabilityFunction function;

    @Before
    public void setUp()
    {
        function = aFunction().withCode("XX").build();
    }

    @Test
    public void sameObjectsMustProduceSameStrings()
    {
        DeterministicScenarioCacheKey key1 = new DeterministicScenarioCacheKey(function, 5.0, 0.001);
        DeterministicScenarioCacheKey key2 = new DeterministicScenarioCacheKey(function, 5.0, 0.001);

        assertTrue(key1.equals(key2));
        assertTrue(key1.toString().equals(key2.toString()));
    }

    @Test
    public void sameObjectsMustProduceSameHashcodes()
    {
        DeterministicScenarioCacheKey key1 = new DeterministicScenarioCacheKey(function, 5.0, 0.001);
        DeterministicScenarioCacheKey key2 = new DeterministicScenarioCacheKey(function, 5.0, 0.001);

        assertEquals(key1.hashCode(), key2.hashCode());
    }

    @Test
    public void differentObjectsMustProduceDifferentStrings1()
    {
        DeterministicScenarioCacheKey key1 = new DeterministicScenarioCacheKey(function, 5.0, 0.00001);
        DeterministicScenarioCacheKey key2 = new DeterministicScenarioCacheKey(function, 5.0, 0.00002);

        assertFalse(key1.equals(key2));
        assertFalse(key1.toString().equals(key2.toString()));
    }

    @Test
    public void differentObjectsMustProduceDifferentStrings2()
    {
        DeterministicScenarioCacheKey key1 = new DeterministicScenarioCacheKey(function, 5.0, 0.00001);
        DeterministicScenarioCacheKey key2 = new DeterministicScenarioCacheKey(function, 5.5, 0.00002);

        assertFalse(key1.equals(key2));
        assertFalse(key1.toString().equals(key2.toString()));
    }

    @Test
    public void differentObjectsMustProduceDifferentHashcodes1()
    {
        DeterministicScenarioCacheKey key1 = new DeterministicScenarioCacheKey(function, 5.0, 0.00001);
        DeterministicScenarioCacheKey key2 = new DeterministicScenarioCacheKey(function, 5.0, 0.00002);

        assertFalse(key1.hashCode() == key2.hashCode());
    }

    @Test
    public void differentObjectsMustProduceDifferentHashcodes2()
    {
        DeterministicScenarioCacheKey key1 = new DeterministicScenarioCacheKey(function, 5.0, 0.00001);
        DeterministicScenarioCacheKey key2 = new DeterministicScenarioCacheKey(function, 5.5, 0.00001);

        assertFalse(key1.hashCode() == key2.hashCode());
    }

}
