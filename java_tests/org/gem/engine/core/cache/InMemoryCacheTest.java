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

package org.gem.engine.core.cache;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNull;

import org.junit.Test;

public class InMemoryCacheTest
{

    private static final String KEY = "KEY";
    private static final String UNKNOWN_KEY = "UNKNOWNKEY";

    @Test
    public void getReturnsNullIfNoObjectCorrespondingToTheGivenKey()
    {
        assertNull(new InMemoryCache().get(UNKNOWN_KEY));
    }

    @Test
    public void getReturnsTheObjectWasPut()
    {
        InMemoryCache cache = new InMemoryCache();
        Object cachedObj = new Object();
        cache.put(KEY, cachedObj);

        assertEquals(cachedObj, cache.get(KEY));
    }

    @Test(expected = IllegalArgumentException.class)
    public void shouldThrownAnExceptionWhenGettingAnObjectWithNullKey()
    {
        new InMemoryCache().get(null);
    }

    @Test(expected = IllegalArgumentException.class)
    public void shouldThrownAnExceptionWhenInsertingAnObjectWithNullKey()
    {
        new InMemoryCache().put(null, new Object());
    }

}
