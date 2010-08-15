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

package org.gem.engine.risk.io.reader;

import java.io.FileInputStream;
import java.io.IOException;

import org.gem.engine.risk.core.Site;
import org.gem.engine.risk.core.reader.ExposureReader;
import org.gem.engine.risk.io.reader.definition.ESRIRasterFileDefinition;
import org.gem.engine.risk.io.reader.definition.Point;

/**
 * Reads exposures using an ESRI raster binary file as source.
 * <p>
 * This is a buffered implementation, so it is safe to use files with big size. This implementation is not thread safe.<br/>
 * For more information about the format used, take a look <a href="http://en.wikipedia.org/wiki/ESRI_grid">here</a>.
 * 
 * @author Andrea Cerisara
 * @version $Id: ESRIBinaryFileExposureReader.java 537 2010-06-16 18:29:36Z acerisara $
 */
public class ESRIBinaryFileExposureReader implements ExposureReader
{

    private long offSet;
    private final String filename;
    private ByteArrayBuffer buffer;
    private final ESRIRasterFileDefinition definition;

    /**
     * @param filename the name of the file to use
     * @param definition the ESRI raster file definition to use
     */
    public ESRIBinaryFileExposureReader(String filename, ESRIRasterFileDefinition definition)
    {
        this.filename = filename;
        this.definition = definition;
        this.buffer = new ByteArrayBuffer();
    }

    private void closeStream(FileInputStream input)
    {
        try
        {
            input.close();
        }
        catch (IOException e)
        {
            throw new RuntimeException(e);
        }
    }

    private long bytesToSkip(Point point)
    {
        // TODO Expose the int bug with a test!
        long rowsToSkip = (point.getRow() - 1) * definition.getColumns();
        long rowsToSkipInBytes = rowsToSkip * 4;
        long columnsToSkipInBytes = (point.getColumn() - 1) * 4;

        return rowsToSkipInBytes + columnsToSkipInBytes;
    }

    @Override
    public double readAt(Site site)
    {
        Point point = definition.fromSiteToGridPoint(site);

        if (bufferNeedsUpdate(point))
        {
            FileInputStream input = null;

            try
            {
                input = new FileInputStream(filename);
                input.skip(bytesToSkip(point));

                buffer.fillBuffer(input);
                offSet = bytesToSkip(point);
            }
            catch (Exception e)
            {
                throw new RuntimeException(e);
            }
            finally
            {
                closeStream(input);
            }
        }

        return buffer.doubleAt((int) (bytesToSkip(point) - offSet));
    }

    private boolean bufferNeedsUpdate(Point point)
    {
        long limit = bytesToSkip(point) + 4;
        return limit > (offSet + (buffer.isEmpty() ? 0 : buffer.size())) || limit < offSet;
    }

}
