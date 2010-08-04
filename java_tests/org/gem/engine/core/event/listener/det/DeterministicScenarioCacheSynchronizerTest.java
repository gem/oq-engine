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

import static org.gem.engine.core.AdditionalPipeKeys.COV_IML;
import static org.gem.engine.core.AdditionalPipeKeys.MEAN_FUNCTION;
import static org.gem.engine.core.AdditionalPipeKeys.MEAN_IML;
import static org.gem.engine.data.builder.DiscreteVulnerabilityFunctionBuilder.aFunction;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.fail;

import org.gem.engine.core.cache.Cache;
import org.gem.engine.core.event.listener.BaseFilterTest;
import org.gem.engine.data.DiscreteVulnerabilityFunction;
import org.junit.Before;
import org.junit.Test;

public class DeterministicScenarioCacheSynchronizerTest extends BaseFilterTest implements Cache
{

    private Object cachedObj;
    private DiscreteVulnerabilityFunction function;

    @Before
    public void setUp()
    {
        function = aFunction().withCode("XX").build();

        addToPipe(COV_IML, 0.1);
        addToPipe(MEAN_IML, 5.0);
        addToPipe(A_KEY, A_VALUE);
        addToPipe(MEAN_FUNCTION, function);

        filter = new DeterministicScenarioCacheSynchronizer(this, A_KEY);
    }

    @Test
    public void shouldSaveInCacheTheComputedResult()
    {
        runOn(anySite());
        assertEquals(A_VALUE, cachedObj);
    }

    @Override
    public <T> T get(String key)
    {
        return null;
    }

    @Override
    public void put(String key, Object value)
    {
        if (new DeterministicScenarioCacheKey(function, 5.0, 0.1).toString().equals(key))
        {
            cachedObj = value;
        }
        else
        {
            fail("bad key!");
        }
    }

}
