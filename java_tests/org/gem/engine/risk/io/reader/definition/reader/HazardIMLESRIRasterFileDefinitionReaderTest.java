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
import org.gem.engine.risk.io.reader.definition.reader.HazardIMLESRIRasterFileDefinitionReader;
import org.junit.Before;
import org.junit.Test;

public class HazardIMLESRIRasterFileDefinitionReaderTest extends BaseTestCase
{

    private ESRIRasterFileDefinitionReader reader;

    @Before
    public void setUp()
    {
        reader = new HazardIMLESRIRasterFileDefinitionReader(pathFor("Hazard_MMI.txt"));
    }

    @Test
    // [78 36  27.225  39.825  0.05]
    public void shouldLoadTheNumberOfColumns()
    {
        assertEquals(78, reader.read().getColumns());
    }

    @Test
    // [78 36  27.225  39.825  0.05]
    public void shouldLoadTheNumberOfRows()
    {
        assertEquals(36, reader.read().getRows());
    }

    @Test
    // [78 36  27.225  39.825  0.05]
    public void shouldLoadTheLowerLeftCornerLongitude()
    {
        assertEquals(27.225, reader.read().getLowerLeftCorner().getLongitude(), 0.0);
    }

    @Test
    // [78 36  27.225  39.825  0.05]
    public void shouldLoadTheLowerLeftCornerLatitude()
    {
        assertEquals(39.825, reader.read().getLowerLeftCorner().getLatitude(), 0.0);
    }

    @Test
    // [78 36  27.225  39.825  0.05]
    public void shouldLoadTheCellSize()
    {
        assertEquals(0.05, reader.read().getCellSize(), 0.0);
    }

    @Test
    // [78 36  27.225  39.825  0.05]
    public void noDataValueIsZero()
    {
        assertTrue(reader.read().isNoData(0));
    }

}
