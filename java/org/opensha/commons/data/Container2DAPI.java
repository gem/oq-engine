/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with
 * the Southern California Earthquake Center (SCEC, http://www.scec.org)
 * at the University of Southern California and the UnitedStates Geological
 * Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ******************************************************************************/

package org.opensha.commons.data;

import java.util.ListIterator;

import org.opensha.commons.geo.Location;


/**
 *  <b>Title:</b> Container2DAPI<p>
 *
 *  <b>Description:</b> Main interface that all 2D data containers must
 *  implement. These provide functions for iteration through the elements,
 *  replacing elements, etc. Each element is any object that extends Object. <p>
 *
 *  This two dimensional grid acts more like a matrix than a geographical
 *  array of location objects. You can store anything in each grid point.
 *  One of the main purposes we use this class for is to store Location
 *  objects (latitude, longitude) at each grid point. It just so happens
 *  that the location objects are sorted spatially so that locations
 *  next to each other in real space are next to each other in the
 *  grid. The confusing point is that even though the grid is rectangular,
 *  the location objects may not map out to a rectangular grid on the
 *  earth's surface at all. This is a fine point distintion but worth noting
 *  due to confusion in designing this class.<p>
 *
 * @author     Steven W. Rock
 * @see        Location
 * @created    February 25, 2002
 * @version    1.0
 */

public interface Container2DAPI<T> extends NamedObjectAPI, Iterable<T> {

    /**
     *  Returns the number of rows int this two dimensional container.
     *
     * @return    Number of rows.
     */
    public int getNumRows();

    /**
     * Every container has a name associated with it to distinguish
     * it from other container instances.
     * @param name
     */
    public void setName(String name);


    /**
     *  Returns the number of columns in this two dimensional container.
     *
     * @return    Get number of columns.
     */
    public int getNumCols();


    /**
     *  Empties the list of all data. Note, the data may still exist
     *  elsewhere if it is referenced elsewhere.
     */
    public void clear();


    /**
     *  Check if this grid cell has a java object stored in it. Returns false if
     *  this gird point object is null.
     *
     * @param  row     The x coordinate of the cell.
     * @param  column  The y coordinate of the cell.
     * @return         True if an object has been set in this cell.
     */
    public boolean exist( int row, int column );


    /**
     *  returns the number of cells in this two dimensional matrix, i.e.
     *  numwRows * numCols.
     *
     * @return    The number of cells.
     */
    public long size();


    /**
     *  Places a Java object into one cell in this two dimensional matrix
     *  specified by the row and column indices.
     *
     * @param  row                                 The x coordinate of the cell.
     * @param  column                              The y coordinate of the cell.
     * @param  obj                                 The Java object to place in
     *      the cell.
     * @exception  ArrayIndexOutOfBoundsException  Thrown if the row and column
     *      are beyond the two dimensional matrix range.
     * @exception  ClassCastException              Thrown by subclasses that
     *      expect a particular type of Java object.
     */
    public void set( int row, int column, T obj ) throws
            ArrayIndexOutOfBoundsException,
            ClassCastException;

    /**
     *  Returns the object stored in this two dimensional grid cell.
     *
     * @param  row     The x coordinate of the cell.
     * @param  column  The y coordinate of the cell.
     * @return
     */
    public T get( int row, int column );


    /**
     *  Removes the object's reference stored in the grid cell.
     *  Doesn't delete the actual object, only removes the pointer
     *  reference.
     *
     * @param  row     The x coordinate of the cell.
     * @param  column  The y coordinate of the cell.
     */
//    public void delete( int row, int column );


    /**
     *  Returns an ordered list iterator over all columns associated with one
     *  row. This returns all the objects in that row. The results are returned
     *  from lowest index to highest along the interating row.
     *
     * @param  row                                 The x coordinate of the cell.
     * @return                                     The columnIterator value
     * @exception  ArrayIndexOutOfBoundsException  Thrown if the row is beyond
     *      the two dimensional matrix range.
     */
    public ListIterator<T> getColumnIterator( int row ) throws ArrayIndexOutOfBoundsException;


    /**
     *  Returns an ordered list iterator over all rows associated with one
     *  column. This returns all the objects in that column. The results are returned
     *  from lowest index to highest along the interating column.
     *
     * @param  column                              The y coordinate of the cell.
     * @return                                     The rowIterator value
     * @exception  ArrayIndexOutOfBoundsException  Thrown if the column is
     *      beyond the two dimensional matrix range.
     */
    public ListIterator<T> getRowIterator( int column ) throws ArrayIndexOutOfBoundsException;


    /**
     *  This returns an iterator of all the Java objects stored in this two
     *  dimensional matrix iterating over all rows within a column and then
     *  moving to the next column until iteration has been done over all rows
     *  and all columns.
     *
     * @return    The allByColumnsIterator value
     */
    public ListIterator<T> getAllByColumnsIterator();


    /**
     *  This returns an iterator of all the Java objects stored in this two
     *  dimensional matrix iterating over all columns within a rows and then
     *  moving to the next column until iteration has been done over all columns
     *  and all rows.
     *
     * @return    The allByRowsIterator value
     */
    public ListIterator<T> getAllByRowsIterator();


    /**
     *  The most generic iterator that returns all Java objects stored in this two
     *  dimensional matrix with no guarantee of ordering either by rows or by
     *  columns. Internally this function will probably just call
     *  get allByRowsIterator
     *
     * @return    Description of the Return Value
     */
    public ListIterator<T> listIterator();

    /**
     * state dump to a string, useful for debugging. Subclasses can implement
     * this anyway desired. A typical use is to print out grid information such
     * as size, number of rows, cols, and then iterate over all cells calling
     * toString() on the objects stored in each cell.
     */
    public String toString();

}
