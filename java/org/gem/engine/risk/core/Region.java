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

package org.gem.engine.risk.core;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Iterator;

import lombok.ToString;

/**
 * Describes a region.
 * <p>
 * A region is defined by an upper left and lower right {@link Site} and a cell size.
 * A region is conceptually composed by a set of cells. The upper left corner is always considered as the <i>center</i> of the first cell in the region, while
 * the lower right corner can be everywhere inside the last cell of the region.
 * <p>
 * The last cell of the region is computed starting from the upper left corner
 * and shifting the longitude and latitude by the number of columns and rows defined in the region, according to the cell size.
 * <p>
 * For example, given (in the format (longitude, latitude)):
 * <ul>
 * <li>upper left corner (1.0, 2.0)
 * <li>lower right corner (2.0, 1.0)
 * <li>cell size 0.5
 * </ul>
 * We are defining a region with nine cells (three columns and three rows) with a size of 0.5x0.5 each cell.
 * 
 * @author Andrea Cerisara
 * @version $Id: Region.java 578 2010-07-20 14:57:02Z acerisara $
 */
@ToString
public class Region implements Iterable<Site>
{

    private final Site to;
    private final Site from;
    private final double cellSize;

    /**
     * @param from the upper left corner of this region
     * @param to the lower right corner of this region
     * @param cellSize the cell size to use
     */
    public Region(Site from, Site to, double cellSize)
    {
        this.to = to;
        this.from = from;
        this.cellSize = cellSize;
    }

    /**
     * Returns the number of columns of this region, according to the cell size specified.
     * 
     * @return the number of columns of this region, according to the cell size specified
     */
    public int getColumns()
    {
        BigDecimal size = new BigDecimal(cellSize);
        BigDecimal to = new BigDecimal(this.to.getLongitude());
        BigDecimal from = new BigDecimal(this.from.getLongitude());

        return to.subtract(from).divide(size, 0, RoundingMode.HALF_DOWN).intValue() + 1;
    }

    /**
     * Returns the number of rows of this region, according to the cell size specified.
     * 
     * @return the number of rows of this region, according to the cell size specified
     */
    public int getRows()
    {
        BigDecimal size = new BigDecimal(cellSize);
        BigDecimal to = new BigDecimal(this.to.getLatitude());
        BigDecimal from = new BigDecimal(this.from.getLatitude());

        return from.subtract(to).divide(size, 0, RoundingMode.HALF_DOWN).intValue() + 1;
    }

    /**
     * Returns the number of cells of this region.
     * 
     * @return the number of cells of this region
     */
    public int numberOfCells()
    {
        return getColumns() * getRows();
    }

    /**
     * Returns the upper left corner of this region.
     * 
     * @return the upper left corner of this region
     */
    public Site getFrom()
    {
        return from;
    }

    /**
     * Returns the lower right corner of this region.
     * 
     * @return the lower right corner of this region
     */
    public Site getTo()
    {
        return to;
    }

    /**
     * Returns the cell size of this region.
     * 
     * @return the cell size of this region
     */
    public double getCellSize()
    {
        return cellSize;
    }

    /**
     * Returns the iterator to iterate on each cell of this region.
     * 
     * @return the iterator to iterate on each cell of this region
     */
    public Iterator<Site> iterator()
    {
        return new Iterator<Site>()
        {

            private Site currentSite = from;

            @Override
            public boolean hasNext()
            {
                return !(currentSite.getLatitude() - (lastSiteInTheRegion().getLatitude() - cellSize) < Site.EPSILON);
            }

            @Override
            public Site next()
            {
                Site result = currentSite;
                currentSite = nextSite();

                return result;
            }

            @Override
            public void remove()
            {
                throw new RuntimeException("Remove not implemented!");
            }

            private Site nextSite()
            {
                if (lastColumn())
                {
                    return theFirstSiteOnTheNextRow();
                }
                else
                {
                    return theNextSiteOnTheCurrentRow();
                }
            }

            private Site theNextSiteOnTheCurrentRow()
            {
                return new Site(currentSite.getLongitude() + cellSize, currentSite.getLatitude());
            }

            private Site theFirstSiteOnTheNextRow()
            {
                return new Site(from.getLongitude(), currentSite.getLatitude() - cellSize);
            }

            private boolean lastColumn()
            {
                return Math.abs(currentSite.getLongitude() - lastSiteInTheRegion().getLongitude()) < (cellSize / 2);
            }

            private Site lastSiteInTheRegion()
            {
                double width = cellSize * (getColumns() - 1);
                double height = cellSize * (getRows() - 1) * -1;

                return from.shiftLongitude(width).shiftLatitude(height);
            }

        };
    }

    /**
     * Returns the center of the cell at the given point, identified by a row and a column.
     * 
     * @param row the row used to get the cell
     * @param column the column used to get the cell
     * @return the center of the cell at the given point
     */
    protected Site centerOfCellAt(int row, int column)
    {
        Iterator<Site> iterator = iterator();
        Integer cellsToSkip = (getColumns() * (row - 1)) + (column - 1);

        for (int i = 0; i < cellsToSkip; i++)
        {
            iterator.next();
        }

        return iterator.next();
    }

    /**
     * Returns a region composed only by a cell with the center on the given site.
     * 
     * @param site the site used as center of the cell
     * @return a region composed only by the given cell
     */
    public static Region singleCellRegion(Site site)
    {
        return new Region(site, site, 1);
    }

    /**
     * Two regions are equal when the corners and the cell size are equal.
     */
    @Override
    public boolean equals(Object obj)
    {
        if (!(obj instanceof Region))
        {
            return false;
        }

        Region other = (Region) obj;
        return from.equals(other.from) && to.equals(other.to) && cellSize == other.cellSize;
    }

}
