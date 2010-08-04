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

/**
 * Specifies objects that are capable of caching values.
 * 
 * @author Andrea Cerisara
 * @version $Id: Cache.java 556 2010-07-16 08:29:56Z acerisara $
 */
public interface Cache
{

    /**
     * Stores an object in this cache.
     * 
     * @param key the key used to store the object
     * @param value the object that needs to be stored
     * @throws IllegalArgumentException if the key is <code>null</code>
     */
    public void put(String key, Object value);

    /**
     * Returns the object corresponding to the given key.
     * 
     * @param key the key used to lookup the object
     * @return the cached object, or <code>null</code> if there is no cached object for the given key
     * @throws IllegalArgumentException if the key is <code>null</code>
     */
    public <T> T get(String key);

}
