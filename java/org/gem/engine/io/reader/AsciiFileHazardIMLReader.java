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

package org.gem.engine.io.reader;

import org.gem.engine.core.Site;
import org.gem.engine.core.reader.HazardReader;
import org.gem.engine.io.reader.definition.ESRIRasterFileDefinition;
import org.gem.engine.io.reader.definition.Point;

/**
 * Reads a set of IML values from an external ascii file.
 * <p>
 * This is a buffered implementation, so it is safe to use files with big size. This implementation is not thread safe.
 * This is the file format used:
 * <p>
 * <i>[Id]  [IMT]   [ERF]   [Src]   [rup]   [MAG]   [GMPE]<br/>
 * [78 36  27.225  39.825  0.05]<br/>
 * 6.0 6.0 6.0 6.0 6.0 6.0 6.0 5.5 5.5 5.5 5.5 5.5 5.5 5.5 5.5[...]<br/>
 * 5.0 5.0 5.0 6.0 6.0 5.0 6.0 5.5 5.5 6.5 5.5 5.5 5.5 5.5 5.5[...]<br/>
 * [...]
 * </i><p>
 * To know more about the format, take a look at the Report11-GEM1_Global_Risk_Calculations document, chapter 5.1.
 * 
 * @author Andrea Cerisara
 * @version $Id: AsciiFileHazardIMLReader.java 537 2010-06-16 18:29:36Z acerisara $
 */
public class AsciiFileHazardIMLReader implements HazardReader<Double>
{

    private static final int HEADER_LINES = 2;
    private static final int LINES_TO_BUFFER = 15;

    private final LineReader reader;
    private final ESRIRasterFileDefinition definition;

    /**
     * @param filename the name of the file to use
     * @param definition the ESRI raster file definition to use
     */
    public AsciiFileHazardIMLReader(String filename, ESRIRasterFileDefinition definition)
    {
        this.definition = definition;

        this.reader = new BufferedLineReader(new HeaderLineReader(HEADER_LINES, new AsciiFileReader(filename)),
                LINES_TO_BUFFER);
    }

    @Override
    public Double readAt(Site site)
    {
        Point point = definition.fromSiteToGridPoint(site);
        return Double.valueOf(reader.readAndSplit(point.getRow(), "\t")[point.getColumn() - 1]);
    }

}
