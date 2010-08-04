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

package org.gem.engine.io.listener;

import java.io.OutputStream;
import java.io.PrintWriter;

import org.gem.engine.core.Region;
import org.gem.engine.core.cache.Cache;
import org.gem.engine.core.event.EventSourceListener;

/**
 * Writes an ESRI raster file header, according to the <a href="http://en.wikipedia.org/wiki/ESRI_grid">format</a>.
 * <p>
 * This filters doesn't close (just flush) the underlying stream.
 * 
 * @author Andrea Cerisara
 * @version $Id: ESRIHeaderWriter.java 567 2010-07-20 10:10:52Z acerisara $
 */
public class ESRIHeaderWriter extends EventSourceListener
{

    private final PrintWriter writer;

    /**
     * @param stream the output stream used to write the header to
     */
    public ESRIHeaderWriter(OutputStream stream)
    {
        this.writer = new PrintWriter(stream);
    }

    /**
     * @param writer the print writer used to write the header to
     */
    public ESRIHeaderWriter(PrintWriter writer)
    {
        this.writer = writer;
    }

    @Override
    public void process(String event, Cache buffer, Object... parameters)
    {
        Region region = (Region) parameters[0];

        writer.println("ncols " + region.getColumns());
        writer.println("nrows " + region.getRows());
        writer.println("xllcorner " + region.getFrom().getLongitude());
        writer.println("yllcorner " + region.getTo().getLatitude());
        writer.println("cellsize " + region.getCellSize());
        writer.println("NODATA_value -9999");

        writer.flush();
    }

}
