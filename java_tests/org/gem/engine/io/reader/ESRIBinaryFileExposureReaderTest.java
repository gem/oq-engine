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

import org.gem.engine.BaseTestCase;
import org.gem.engine.core.Site;
import org.gem.engine.core.reader.ExposureReader;
import org.junit.Before;
import org.junit.Test;

public class ESRIBinaryFileExposureReaderTest extends BaseTestCase
{

    private ExposureReader exposure;

    @Before
    public void setUp()
    {
        exposure = allValuesFilledExposure();
    }

    // boundaries are 20.230647106036 <= longitude <= 21.651480439368, 40.436791304463 <= latitude <= 41.415957971129
    @Test(expected = RuntimeException.class)
    public void shouldFailWithABadRow1()
    {
        exposure.readAt(new Site(10.0, 40.736791304463));
    }

    // boundaries are 20.230647106036 <= longitude <= 21.651480439368, 40.436791304463 <= latitude <= 41.415957971129
    @Test(expected = RuntimeException.class)
    public void shouldFailWithABadRow2()
    {
        exposure.readAt(new Site(30.0, 40.736791304463));
    }

    // boundaries are 20.230647106036 <= longitude <= 21.651480439368, 40.436791304463 <= latitude <= 41.415957971129
    @Test(expected = RuntimeException.class)
    public void shouldFailWithABadColumn1()
    {
        exposure.readAt(new Site(20.420647106036, 20.0));
    }

    // boundaries are 20.230647106036 <= longitude <= 21.651480439368, 40.436791304463 <= latitude <= 41.415957971129
    @Test(expected = RuntimeException.class)
    public void shouldFailWithABadColumn2()
    {
        exposure.readAt(new Site(20.420647106036, 50.0));
    }

}
