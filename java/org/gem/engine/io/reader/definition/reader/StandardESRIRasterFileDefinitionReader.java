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

package org.gem.engine.io.reader.definition.reader;

import org.gem.engine.core.Site;
import org.gem.engine.io.reader.AsciiFileReader;
import org.gem.engine.io.reader.AsciiFileReader.LineFilter;
import org.gem.engine.io.reader.definition.ESRIRasterFileDefinition;
import org.gem.engine.io.reader.definition.GridDefinition;

/**
 * Implementation that reads the standard definition according to the <a href="http://en.wikipedia.org/wiki/ESRI_grid">format</a>.
 * <p>
 * An example:<br/>
 * <i>ncols         173<br/>
 * nrows         105<br/>
 * xllcorner     17.86699328744<br/>
 * yllcorner     42.093090478802<br/>
 * cellsize      0.00833333333333<br/>
 * NODATA_value  -9999<br/>
 * byteorder     LSBFIRST</i><br/>
 * 
 * @author Andrea Cerisara
 * @version $Id: StandardESRIRasterFileDefinitionReader.java 537 2010-06-16 18:29:36Z acerisara $
 */
public class StandardESRIRasterFileDefinitionReader implements ESRIRasterFileDefinitionReader
{

    private final String filename;

    /**
     * @param filename the name of the file containing the definition
     */
    public StandardESRIRasterFileDefinitionReader(String filename)
    {
        this.filename = filename;
    }

    @Override
    public ESRIRasterFileDefinition read()
    {
        AsciiFileReader reader = new AsciiFileReader(filename).open();

        int columns = Integer.parseInt(parseNextLine(reader)[1]);
        int rows = Integer.parseInt(parseNextLine(reader)[1]);
        double xllcorner = Double.parseDouble(parseNextLine(reader)[1]);
        double yllcorner = Double.parseDouble(parseNextLine(reader)[1]);
        double cellSize = Double.parseDouble(parseNextLine(reader)[1]);
        int noDataValue = Integer.parseInt(parseNextLine(reader)[1]);

        reader.close();

        Site lowerLeftCorner = new Site(xllcorner, yllcorner);
        GridDefinition gridDefinition = new GridDefinition(rows, columns, noDataValue);
        return new ESRIRasterFileDefinition(lowerLeftCorner, cellSize, gridDefinition);
    }

    private String[] parseNextLine(AsciiFileReader reader)
    {
        // values have a variable number of spaces between, for example xllcorner     20.230647106036
        return reader.parseNextLine(" ", new LineFilter()
        {

            @Override
            public String filter(String line)
            {
                return collapseWhiteSpaces(line);
            }

            private String collapseWhiteSpaces(String line)
            {
                return line.replaceAll(" +", " ");
            }
        });
    }

}
