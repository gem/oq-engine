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

import static org.gem.engine.risk.core.cache.Pipe.REGION;
import static org.gem.engine.risk.io.listener.ESRIAsciiWriter.NEW_LINE;
import static org.gem.engine.risk.io.listener.ESRIAsciiWriter.NODATA_value;
import static org.gem.engine.risk.io.listener.ESRIAsciiWriter.TAB;
import static org.junit.Assert.assertEquals;

import java.io.ByteArrayOutputStream;
import java.io.PrintWriter;

import org.gem.engine.risk.core.Region;
import org.gem.engine.risk.core.Site;
import org.gem.engine.risk.core.event.listener.BaseFilterTest;
import org.gem.engine.risk.io.listener.ESRIAsciiWriter;
import org.junit.Before;
import org.junit.Test;

public class ESRIAsciiWriterTest extends BaseFilterTest
{

    private ESRIAsciiWriter writer;
    private ByteArrayOutputStream stream;

    @Before
    public void setUp()
    {
        addToPipe(A_KEY, A_VALUE);
        addToPipe(REGION, twoColumnsRegion());

        stream = new ByteArrayOutputStream();
        writer = new ESRIAsciiWriter(new PrintWriter(stream), A_KEY, 1);
    }

    @Test
    public void noDataWhenResultIsEmpty()
    {
        writer.printEmptyResult(A_BUFFER, pipe);
        assertEquals(NODATA_value + TAB, stream.toString());
    }

    @Test
    public void shouldWriteOnANewLineWhenTheEndOfRowHasBeenReached()
    {
        writer.printEmptyResult(A_BUFFER, pipe);
        writer.printEmptyResult(A_BUFFER, pipe);
        writer.printEmptyResult(A_BUFFER, pipe);

        assertEquals(NODATA_value + TAB + NODATA_value + TAB + NEW_LINE + NODATA_value + TAB, stream.toString());
    }

    @Test
    public void shouldPrintTheResult()
    {
        writer.printResult(A_BUFFER, pipe);
        assertEquals(A_VALUE + TAB, stream.toString());
    }

    private Region twoColumnsRegion()
    {
        return new Region(new Site(1.0, 1.0), new Site(2.0, 1.0), 1.0);
    }

}
