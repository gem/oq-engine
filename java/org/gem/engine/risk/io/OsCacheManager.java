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

package org.gem.engine.risk.io;

import org.gem.engine.risk.core.cache.Cache;

import com.opensymphony.oscache.base.NeedsRefreshException;
import com.opensymphony.oscache.general.GeneralCacheAdministrator;

/**
 * An implementation of the caching component which uses the <a href="http://www.opensymphony.com/oscache/">OSCache</a> library.
 * 
 * @author Andrea Cerisara
 * @version $Id: OsCacheManager.java 567 2010-07-20 10:10:52Z acerisara $
 */
public class OsCacheManager implements Cache
{

    private final GeneralCacheAdministrator manager;

    public OsCacheManager()
    {
        manager = new GeneralCacheAdministrator();
    }

    @Override
    @SuppressWarnings("unchecked")
    public <T> T get(String key)
    {
        try
        {
            return (T) manager.getFromCache(key);
        }
        catch (NeedsRefreshException e)
        {
            return null;
        }
    }

    @Override
    public void put(String key, Object value)
    {
        manager.putInCache(key, value);
    }

}
