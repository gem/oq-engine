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

import static org.gem.engine.core.cache.Pipe.REGION;

import java.io.PrintWriter;

import org.gem.engine.core.Region;
import org.gem.engine.core.Site;
import org.gem.engine.core.cache.Cache;
import org.gem.engine.core.cache.Pipe;
import org.gem.engine.core.event.MultiEventFilter;
import org.gem.engine.io.util.BufferedPrintWriter;

/**
 * Writes an ESRI raster file output, according to the <a href="http://en.wikipedia.org/wiki/ESRI_grid">format</a>.
 * <p>
 * This is a {@link MultiEventFilter} and these two methods are available:<br/>
 * <ul>
 * <li><code>printResult</code> to print a valid result
 * <li><code>printEmptyResult</code> to print a NODATA_value when the computation can't be completed for the current {@link Site}
 * </ul>
 * 
 * @author Andrea Cerisara
 * @version $Id: ESRIAsciiWriter.java 567 2010-07-20 10:10:52Z acerisara $
 */
public class ESRIAsciiWriter extends MultiEventFilter
{

    protected static final String TAB = "\t";
    protected static final String NEW_LINE = "\n";
    protected static final String NODATA_value = "-9999";

    private final String key;
    private int currentColumn;
    private BufferedPrintWriter writer;

    /**
     * @param writer the writer used to write the output to
     * @param key the key used to get the data to write from the pipe
     */
    public ESRIAsciiWriter(PrintWriter writer, String key)
    {
        this.key = key;
        this.currentColumn = 1;
        this.writer = new BufferedPrintWriter(writer);
    }

    /**
     * @param writer the writer used to write the output to
     * @param key the key used to get the data to write from the pipe
     * @param flushEvery the number of writes between each stream flush
     */
    public ESRIAsciiWriter(PrintWriter writer, String key, int flushEvery)
    {
        this(writer, key);
        this.writer = new BufferedPrintWriter(writer, flushEvery);
    }

    /**
     * @param pipe the pipe used in the current filters chain
     */
    public void printResult(Cache buffer, Pipe pipe)
    {
        print(pipe.get(key), (Region) pipe.get(REGION));
    }

    private void print(Object value, Region region)
    {
        StringBuffer result = new StringBuffer();

        if (currentColumn > region.getColumns())
        {
            currentColumn = 1;
            result.append(NEW_LINE);
        }

        currentColumn++;
        writer.print(result.append(value).append(TAB).toString());
    }

    /**
     * @param pipe the pipe used in the current filters chain
     */
    public void printEmptyResult(Cache buffer, Pipe pipe)
    {
        print(NODATA_value, (Region) pipe.get(REGION));
    }

}
