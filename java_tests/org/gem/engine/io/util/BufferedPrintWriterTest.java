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

package org.gem.engine.io.util;

import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;

import java.io.PrintWriter;

import org.junit.Before;
import org.junit.Test;

public class BufferedPrintWriterTest
{

    private PrintWriter writer;
    private BufferedPrintWriter lineWriter;

    @Before
    public void setUp()
    {
        writer = mock(PrintWriter.class);
    }

    @Test
    public void shouldFlushOnlyIfTheLimitHasBeenReached1()
    {
        writerFlushingEvery(2);
        lineWriter.print(null);
        verify(writer, times(0)).flush();
    }

    @Test
    public void shouldFlushOnlyIfTheLimitHasBeenReached2()
    {
        writerFlushingEvery(2);
        lineWriter.print(null);
        lineWriter.print(null);
        verify(writer, times(1)).flush();
    }

    @Test
    public void print()
    {
        writerFlushingEvery(1);
        lineWriter.print("MESSAGE");
        verify(writer).print("MESSAGE");
    }

    private void writerFlushingEvery(int flushEvery)
    {
        lineWriter = new BufferedPrintWriter(writer, flushEvery);
    }

}
