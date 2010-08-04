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
import static org.mockito.Mockito.verify;

import java.io.PrintWriter;

import org.gem.engine.io.listener.PrintWriterCloser;
import org.junit.Test;

public class PrintWriterCloserTest
{

    private PrintWriter writer;
    private PrintWriterCloser closer;

    public PrintWriterCloserTest()
    {
        writer = mock(PrintWriter.class);
        closer = new PrintWriterCloser(writer);
    }

    @Test
    public void shouldFlushTheStream()
    {
        process();
        verify(writer).flush();
    }

    @Test
    public void shouldCloseTheStream()
    {
        process();
        verify(writer).close();
    }

    private void process()
    {
        closer.process(null, null);
    }

}
