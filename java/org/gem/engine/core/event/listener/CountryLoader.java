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

package org.gem.engine.core.event.listener;

import static org.gem.engine.core.AdditionalPipeKeys.COUNTRY;
import static org.gem.engine.core.cache.Pipe.CURRENT_SITE;

import org.gem.engine.core.Site;
import org.gem.engine.core.cache.Cache;
import org.gem.engine.core.cache.Pipe;
import org.gem.engine.core.event.Filter;
import org.gem.engine.core.reader.CountryReader;
import org.gem.engine.data.country.Country;

/**
 * Loads a {@link Country} into the {@link Pipe}, using the current {@link Site}.
 * 
 * @author Andrea Cerisara
 * @version $Id: CountryLoader.java 567 2010-07-20 10:10:52Z acerisara $
 */
public class CountryLoader extends Filter
{

    private final CountryReader reader;

    /**
     * @param reader the reader used to load the country
     */
    public CountryLoader(CountryReader reader)
    {
        this.reader = reader;
    }

    @Override
    protected void filter(Cache buffer, Pipe pipe)
    {
        pipe.put(COUNTRY, reader.readAt((Site) pipe.get(CURRENT_SITE)));
    }

}
