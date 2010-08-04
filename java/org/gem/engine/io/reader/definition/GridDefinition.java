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

package org.gem.engine.io.reader.definition;

/**
 * Describes the grid metadata of an ESRI raster file.
 * <p>
 * For more information about the format used, take a look <a href="http://en.wikipedia.org/wiki/ESRI_grid">here</a>.
 * 
 * @author Andrea Cerisara
 * @version $Id: GridDefinition.java 537 2010-06-16 18:29:36Z acerisara $
 */
public class GridDefinition
{

    private int rows;
    private int noData;
    private int columns;

    /**
     * @param rows the number of rows of the grid
     * @param columns the number of columns of the grid
     * @param noData the value considered as no data
     */
    public GridDefinition(int rows, int columns, int noData)
    {
        this.rows = rows;
        this.noData = noData;
        this.columns = columns;
    }

    /**
     * Returns the number of rows defined in the raster file.
     * 
     * @return the number of rows defined in the raster file
     */
    public int getRows()
    {
        return rows;
    }

    /**
     * Returns the number of columns defined in the raster file.
     * 
     * @return the number of columns defined in the raster file
     */
    public int getColumns()
    {
        return columns;
    }

    /**
     * Checks if the row of the point is within the range of this definition.
     * 
     * @param point the point to check
     * @throws RuntimeException if the row is out of range
     */
    public void checkRow(Point point)
    {
        if (point.getRow() > getRows() || point.getRow() < 1)
        {
            String message = "Row must be between 1 and " + getRows() + ", was " + point.getRow();
            throw new RuntimeException(message);
        }
    }

    /**
     * Checks if the column of the point is within the range of this definition.
     * 
     * @param point the point to check
     * @throws RuntimeException if the column is out of range
     */
    public void checkColumn(Point point)
    {
        if (point.getColumn() > getColumns() || point.getColumn() < 1)
        {
            String message = "Column must be between 1 and " + getColumns() + ", was " + point.getColumn();
            throw new RuntimeException(message);
        }
    }

    /**
     * Tells if the specified value is a no data value, according to this definition.
     * 
     * @param value the value to test
     * @return <code>true</code> if the value is no data value, <code>false</code> otherwise
     */
    public boolean isNoData(double value)
    {
        return noData == (int) value;
    }

}
