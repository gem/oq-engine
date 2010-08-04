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
import static org.junit.Assert.assertEquals;

import org.gem.engine.core.Site;
import org.gem.engine.core.reader.CountryReader;
import org.gem.engine.data.country.Country;
import org.junit.Before;
import org.junit.Test;

public class CountryLoaderTest extends BaseFilterTest implements CountryReader
{

    private Country country;

    @Before
    public void setUp()
    {
        filter = new CountryLoader(this);
        country = Country.newCountry(1);
    }

    @Test
    public void shouldLoadACountryIntoThePipe()
    {
        runOn(anySite());
        assertEquals(country, pipeValueAtKey(COUNTRY));
    }

    @Override
    public Country readAt(Site site)
    {
        return country;
    }

}
