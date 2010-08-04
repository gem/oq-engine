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

import java.io.PrintWriter;

/**
 * A wrapper that flushes the stream at given intervals.
 * 
 * @author Andrea Cerisara
 * @version $Id: BufferedPrintWriter.java 537 2010-06-16 18:29:36Z acerisara $
 */
public class BufferedPrintWriter
{

    private int flushEvery;
    private int flushCounter;
    private PrintWriter writer;

    /**
     * @param writer the writer used to write the output to
     * @param flushEvery the number of writes between each flush
     */
    public BufferedPrintWriter(PrintWriter writer, int flushEvery)
    {
        this.writer = writer;
        this.flushEvery = flushEvery;
    }

    /**
     * The flush interval is assumed to be 1000.
     * 
     * @param writer the writer used to write the output to
     */
    public BufferedPrintWriter(PrintWriter writer)
    {
        this(writer, 1000);
    }

    /**
     * Prints the given message.
     * 
     * @param message the message to print
     */
    public void print(String message)
    {
        flushCounter++;
        writer.print(message);

        if (streamNeedsFlush())
        {
            writer.flush();
            flushCounter = 0;
        }
    }

    private boolean streamNeedsFlush()
    {
        return flushCounter == flushEvery;
    }

}
