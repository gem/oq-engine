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

package org.gem.engine.risk.io.listener;

import static org.junit.Assert.assertEquals;

import java.io.ByteArrayOutputStream;

import org.gem.engine.risk.core.Region;
import org.gem.engine.risk.core.Site;
import org.gem.engine.risk.core.event.listener.BaseFilterTest;
import org.gem.engine.risk.io.listener.ESRIHeaderWriter;
import org.junit.Before;
import org.junit.Test;

public class ESRIHeaderWriterTest extends BaseFilterTest
{

    private ESRIHeaderWriter writer;
    private ByteArrayOutputStream output;

    @Before
    public void setUp()
    {
        this.output = new ByteArrayOutputStream();
        this.writer = new ESRIHeaderWriter(output);
    }

    @Test
    public void shouldWriteTheHeaderInESRIFormat()
    {
        writer.process(null, null, new Region(new Site(1.0, 2.0), new Site(2.0, 1.0), 0.5));
        String header = "ncols 3\nnrows 3\nxllcorner 1.0\nyllcorner 1.0\ncellsize 0.5\nNODATA_value -9999\n";

        assertEquals(header, output.toString());
    }

}
