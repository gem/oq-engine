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

import java.io.PrintWriter;

import org.gem.engine.risk.core.cache.Cache;
import org.gem.engine.risk.core.event.EventSourceListener;

/**
 * Flushes and closes a stream.
 * 
 * @author Andrea Cerisara
 * @version $Id: PrintWriterCloser.java 567 2010-07-20 10:10:52Z acerisara $
 */
public class PrintWriterCloser extends EventSourceListener
{

    private final PrintWriter writer;

    /**
     * @param writer the writer to close
     */
    public PrintWriterCloser(PrintWriter writer)
    {
        this.writer = writer;
    }

    @Override
    public void process(String event, Cache buffer, Object... parameters)
    {
        writer.flush();
        writer.close();
    }

}
