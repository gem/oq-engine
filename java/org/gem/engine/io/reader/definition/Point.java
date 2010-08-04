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
 * Describes a simple matrix bidimensional point.
 * 
 * @author Andrea Cerisara
 * @version $Id: Point.java 537 2010-06-16 18:29:36Z acerisara $
 */
public class Point
{

    private final int row;
    private final int column;

    /**
     * @param row the row of the point
     * @param column the column of the point
     */
    public Point(int row, int column)
    {
        this.row = row;
        this.column = column;
    }

    /**
     * Returns the row of this point.
     * 
     * @return the row of this point
     */
    public int getRow()
    {
        return row;
    }

    /**
     * Returns the column of this point.
     * 
     * @return the column of this point
     */
    public int getColumn()
    {
        return column;
    }

}
