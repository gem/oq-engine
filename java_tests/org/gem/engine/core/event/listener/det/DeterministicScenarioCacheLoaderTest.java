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

import static org.gem.engine.core.AdditionalEvents.CACHE_EMPTY;
import static org.gem.engine.core.AdditionalPipeKeys.COV_IML;
import static org.gem.engine.core.AdditionalPipeKeys.MEAN_FUNCTION;
import static org.gem.engine.core.AdditionalPipeKeys.MEAN_IML;
import static org.gem.engine.data.builder.DiscreteVulnerabilityFunctionBuilder.aFunction;
import static org.hamcrest.Matchers.is;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertThat;

import org.gem.engine.core.cache.Cache;
import org.gem.engine.core.event.listener.BaseFilterTest;
import org.junit.Before;
import org.junit.Test;

public class DeterministicScenarioCacheLoaderTest extends BaseFilterTest implements Cache
{

    private final static Double COV = 0.1;
    private final static Double CACHE_HIT = 5.0;
    private final static Double CACHE_MISS = 4.0;
    private final static String CACHED_STUFF = "STUFF";

    @Before
    public void setUp()
    {
        filter = new DeterministicScenarioCacheLoader(this, A_KEY);
        filter.on(CACHE_EMPTY, this);
    }

    @Test
    public void anEmptyCacheMeansAnEmptyResult()
    {
        preparePipeFor(CACHE_MISS);
        runOn(anySite());

        assertNull(pipeValueAtKey(A_KEY));
    }

    @Test
    public void shouldLoadTheCachedStuffIntoThePipeOnCacheHit()
    {
        preparePipeFor(CACHE_HIT);
        runOn(anySite());

        assertEquals(CACHED_STUFF, pipeValueAtKey(A_KEY));
    }

    @Test
    public void shouldRaiseAnEventWhenCacheIsEmpty()
    {
        preparePipeFor(CACHE_MISS);
        runOn(anySite());

        assertPipeForwarded();
        assertThat(eventRaised, is(CACHE_EMPTY));
    }

    private void preparePipeFor(double mean)
    {
        addToPipe(COV_IML, COV);
        addToPipe(MEAN_IML, mean);
        addToPipe(MEAN_FUNCTION, aFunction().withCode("XX").build());
    }

    @SuppressWarnings("unchecked")
    public <T> T get(String key)
    {
        if (new DeterministicScenarioCacheKey(aFunction().withCode("XX").build(), CACHE_HIT, COV).toString()
                .equals(key))
        {
            return (T) CACHED_STUFF;
        }
        else
        {
            return null;
        }
    }

    @Override
    public void put(String key, Object value)
    {
        // TODO Auto-generated method stub
    }

}
