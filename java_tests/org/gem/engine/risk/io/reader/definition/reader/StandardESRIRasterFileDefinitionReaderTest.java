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

package org.gem.engine.risk.io.reader.definition.reader;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import org.gem.engine.risk.BaseTestCase;
import org.gem.engine.risk.io.reader.definition.reader.ESRIRasterFileDefinitionReader;
import org.gem.engine.risk.io.reader.definition.reader.StandardESRIRasterFileDefinitionReader;
import org.junit.Before;
import org.junit.Test;

public class StandardESRIRasterFileDefinitionReaderTest extends BaseTestCase
{

    private ESRIRasterFileDefinitionReader reader;

    @Before
    public void setUp()
    {
        reader = new StandardESRIRasterFileDefinitionReader(pathFor("no_data.hdr"));
    }

    @Test
    // ncols 173
    public void shouldLoadTheNumberOfColumns()
    {
        assertEquals(173, reader.read().getColumns());
    }

    @Test
    // ncols 105
    public void shouldLoadTheNumberOfRows()
    {
        assertEquals(105, reader.read().getRows());
    }

    @Test
    // xllcorner 17.86699328744
    public void shouldLoadTheLowerLeftCornerLongitude()
    {
        assertEquals(17.86699328744, reader.read().getLowerLeftCorner().getLongitude(), 0.0);
    }

    @Test
    // yllcorner 42.093090478802
    public void shouldLoadTheLowerLeftCornerLatitude()
    {
        assertEquals(42.093090478802, reader.read().getLowerLeftCorner().getLatitude(), 0.0);
    }

    @Test
    // cellsize 0.00833333333333
    public void shouldLoadTheCellSize()
    {
        assertEquals(0.00833333333333, reader.read().getCellSize(), 0.0);
    }

    @Test
    // NODATA_value -9999
    public void shouldLoadTheNoDataValue()
    {
        assertTrue(reader.read().isNoData(-9999));
    }

}
