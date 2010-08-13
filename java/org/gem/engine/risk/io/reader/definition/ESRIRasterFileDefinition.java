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

package org.gem.engine.risk.io.reader.definition;

import org.gem.engine.risk.core.Site;

/**
 * Describes the metadata of an ESRI raster file.
 * <p>
 * For more information about the format used, take a look <a href="http://en.wikipedia.org/wiki/ESRI_grid">here</a>.
 * 
 * @author Andrea Cerisara
 * @version $Id: ESRIRasterFileDefinition.java 537 2010-06-16 18:29:36Z acerisara $
 */
public class ESRIRasterFileDefinition
{

    private final double cellSize;
    private final Site lowerLeftCorner;
    private GridDefinition gridDefinition;

    /**
     * @param lowerLeftCorner the lower left corner of the region described by the raster file
     * @param cellSize the cell size used in the region described by the raster file
     * @param gridDefinition the definition of the grid used in the raster file
     */
    public ESRIRasterFileDefinition(Site lowerLeftCorner, double cellSize, GridDefinition gridDefinition)
    {
        this.cellSize = cellSize;
        this.gridDefinition = gridDefinition;
        this.lowerLeftCorner = lowerLeftCorner;
    }

    /**
     * Returns the cell size used.
     * 
     * @return the cell size
     */
    public double getCellSize()
    {
        return cellSize;
    }

    /**
     * Returns the number of columns defined in the raster file.
     * 
     * @return the number of columns defined in the raster file
     */
    public int getColumns()
    {
        return gridDefinition.getColumns();
    }

    /**
     * Returns the number of rows defined in the raster file.
     * 
     * @return the number of rows defined in the raster file
     */
    public int getRows()
    {
        return gridDefinition.getRows();
    }

    /**
     * Tells if the specified value is a no data value, according to this definition.
     * 
     * @param value the value to test
     * @return <code>true</code> if the value is no data value, <code>false</code> otherwise
     */
    public boolean isNoData(double value)
    {
        return gridDefinition.isNoData(value);
    }

    private int latitudeToRow(double latitude)
    {
        // TODO Expose the Math.abs bug with a test!
        double latitudeOffset = Math.abs(latitude - lowerLeftCorner.getLatitude());
        return (int) (gridDefinition.getRows() - (latitudeOffset / cellSize)) + 1;
    }

    private int longitudeToColumn(double longitude)
    {
        double longitudeOffset = longitude - lowerLeftCorner.getLongitude();
        return (int) ((longitudeOffset / cellSize) + 1);
    }

    /**
     * Translates a site into a matrix bidimensional point.
     * 
     * @param site the site to translate
     * @return the related point, according to this definition
     * @throws ValueExceededException if the row or column is out of range
     */
    public Point fromSiteToGridPoint(Site site)
    {
        Point result = new Point(latitudeToRow(site.getLatitude()), longitudeToColumn(site.getLongitude()));

        gridDefinition.checkRow(result);
        gridDefinition.checkColumn(result);

        return result;
    }

    /**
     * Returns the lower left corner of the region described by the raster file.
     * 
     * @return the lower left corner of the region described by the raster file
     */
    public Site getLowerLeftCorner()
    {
        return lowerLeftCorner;
    }

}
