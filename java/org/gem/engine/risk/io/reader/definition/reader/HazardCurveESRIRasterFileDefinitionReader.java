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

package org.gem.engine.risk.io.reader.definition.reader;

import org.gem.engine.risk.core.Site;
import org.gem.engine.risk.io.reader.AsciiFileReader;
import org.gem.engine.risk.io.reader.definition.ESRIRasterFileDefinition;
import org.gem.engine.risk.io.reader.definition.GridDefinition;

/**
 * Implementation that reads an ESRI-like definition specified in the hazard curve shakemap files.
 * <p>
 * An example:<br/>
 * <i>[...]<br/>
 * 26   46  +27.0000    +39.5000    0.1000<br/>
 * [...]<br/></i>
 * <p>
 * This definition has:<br>
 * <ul>
 * <li>26 columns
 * <li>46 rows
 * <li>27.0000 as longitude for the lower left corner
 * <li>39.5000 as latitude for the lower left corner
 * <li>0.1000 as cell size
 * </ul>
 * <p>
 * The no data value is not specified and assumed to be zero, but it is not used actually.
 * 
 * @author Andrea Cerisara
 * @version $Id: HazardCurveESRIRasterFileDefinitionReader.java 582 2010-07-21 08:51:15Z acerisara $
 */
public class HazardCurveESRIRasterFileDefinitionReader implements ESRIRasterFileDefinitionReader
{

    private final String filename;

    /**
     * @param filename the name of the file containing the definition
     */
    public HazardCurveESRIRasterFileDefinitionReader(String filename)
    {
        this.filename = filename;
    }

    @Override
    public ESRIRasterFileDefinition read()
    {
        // one line to skip before reading the definition
        String[] tokens = new AsciiFileReader(filename).open().skipLines(1).parseNextLineAndClose("\t");

        // 4   6   +27.225 +41.575 0.1
        int rows = Integer.parseInt(tokens[1]);
        int columns = Integer.parseInt(tokens[0]);
        double cellSize = Double.parseDouble(tokens[4]);
        double xllcorner = Double.parseDouble(tokens[2]);
        double yllcorner = Double.parseDouble(tokens[3]);

        Site lowerLeftCorner = new Site(xllcorner, yllcorner);
        GridDefinition gridDefinition = new GridDefinition(rows, columns, 0);
        return new ESRIRasterFileDefinition(lowerLeftCorner, cellSize, gridDefinition);
    }

}
