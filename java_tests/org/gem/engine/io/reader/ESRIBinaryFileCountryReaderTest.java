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

package org.gem.engine.io.reader;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import org.gem.engine.core.Site;
import org.gem.engine.core.reader.CountryReader;
import org.gem.engine.core.reader.ExposureReader;
import org.gem.engine.io.reader.definition.ESRIRasterFileDefinition;
import org.gem.engine.io.reader.definition.GridDefinition;
import org.junit.Before;
import org.junit.Test;

public class ESRIBinaryFileCountryReaderTest implements ExposureReader
{

    private static final double NO_DATA = -9999.0;

    private Site site;
    private double value;
    private CountryReader reader;

    @Before
    public void setUp()
    {
        site = new Site(0.0, 0.0);
        GridDefinition gridDefinition = new GridDefinition(0, 0, (int) NO_DATA);
        ESRIRasterFileDefinition definition = new ESRIRasterFileDefinition(null, 0.0, gridDefinition);
        reader = new ESRIBinaryFileCountryReader(this, definition);
    }

    @Test
    public void shouldLoadTheCountryValueFromTheExposure()
    {
        value = 111.0;
        assertTrue(reader.readAt(site).isComputable());
        assertEquals(111.0, reader.readAt(site).getCode(), 0.0);
    }

    @Test
    public void shouldResultInAnEmptyCountryIfTheExposureHasNoData()
    {
        value = NO_DATA;
        assertFalse(reader.readAt(site).isComputable());
    }

    @Override
    public double readAt(Site site)
    {
        return value;
    }

}
