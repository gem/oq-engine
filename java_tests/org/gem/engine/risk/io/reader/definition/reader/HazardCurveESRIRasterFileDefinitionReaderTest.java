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
import org.gem.engine.risk.io.reader.definition.reader.HazardCurveESRIRasterFileDefinitionReader;
import org.junit.Before;
import org.junit.Test;

public class HazardCurveESRIRasterFileDefinitionReaderTest extends BaseTestCase
{

    private ESRIRasterFileDefinitionReader reader;

    @Before
    public void setUp()
    {
        String filename = "Hazard_curve.txt";
        reader = new HazardCurveESRIRasterFileDefinitionReader(pathFor(filename));
    }

    @Test
    // 4   6   +27.225 +41.575 0.1
    public void shouldLoadTheNumberOfColumns()
    {
        assertEquals(4, reader.read().getColumns());
    }

    @Test
    // 4   6   +27.225 +41.575 0.1
    public void shouldLoadTheNumberOfRows()
    {
        assertEquals(6, reader.read().getRows());
    }

    @Test
    // 4   6   +27.225 +41.575 0.1
    public void shouldLoadTheLowerLeftCornerLongitude()
    {
        assertEquals(27.225, reader.read().getLowerLeftCorner().getLongitude(), 0.0);
    }

    @Test
    // 4   6   +27.225 +41.575 0.1
    public void shouldLoadTheLowerLeftCornerLatitude()
    {
        assertEquals(41.575, reader.read().getLowerLeftCorner().getLatitude(), 0.0);
    }

    @Test
    // 251 254 -125.0000   +24.6000     0.10
    public void shouldLoadTheCellSize()
    {
        assertEquals(0.10, reader.read().getCellSize(), 0.0);
    }

    @Test
    // 251 254 -125.0000   +24.6000     0.10
    public void noDataValueIsZero()
    {
        assertTrue(reader.read().isNoData(0));
    }

}
