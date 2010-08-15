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

package org.gem.engine.risk.core.cache;

import java.util.HashMap;
import java.util.Map;

/**
 * A simple in memory cache implementation.
 * 
 * @author Andrea Cerisara
 * @version $Id: InMemoryCache.java 557 2010-07-16 08:32:09Z acerisara $
 */
public class InMemoryCache implements Cache
{

    private Map<String, Object> buffer;

    public InMemoryCache()
    {
        this.buffer = new HashMap<String, Object>();
    }

    @SuppressWarnings("unchecked")
    public <T> T get(String key)
    {
        checkKeyNotNull(key);
        return (T) buffer.get(key);
    }

    public void put(String key, Object value)
    {
        checkKeyNotNull(key);
        buffer.put(key, value);
    }

    private void checkKeyNotNull(String key)
    {
        if (key == null)
        {
            throw new IllegalArgumentException("null is not accepeted as a valid key");
        }
    }

}
