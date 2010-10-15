/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with the Southern California
 * Earthquake Center (SCEC, http://www.scec.org) at the University of Southern
 * California and the UnitedStates Geological Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not
 * use this file except in compliance with the License. You may obtain a copy of
 * the License at
 * 
 * http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations under
 * the License.
 ******************************************************************************/

package org.opensha.commons.data;

import java.io.Serializable;
import java.util.Iterator;
import java.util.ListIterator;
import java.util.NoSuchElementException;

/**
 * <b>Title:</b> ContainerSubset2D
 * <p>
 * 
 * <b>Description:</b> Small read only window into larger Container2d. This
 * class takes a Container2D as a variable, then becomes a "window" into the
 * larger grid. Since this class implements Container2DAPI it "looks" like a
 * Container2D.
 * <p>
 * 
 * All this class does is provide convinience methods to zoom into a smaller
 * section of the referenced Container2D. It translates the window x and y
 * coordinate indices into the real indices of the referenced container.
 * <p>
 * 
 * The key to understanding this class is the Window2D that contains a minX,
 * maxX, minY and maxY values. These are the translation indices to go between
 * this subset coordinate system to the referencing container's coordinate
 * system. For example the 0th index along x axis in this subset container maps
 * to minX index in the main container.
 * <p>
 * 
 * Another trick used in this class is useful to understand. Basically the API
 * allows translation, modifications of the Window2D around the larger
 * referenced container. Because there are four variables to the Window2D, this
 * could take four method calls to change the data. Because there is more than
 * one step involved, and any one step can potentially fail, I needed to provide
 * a rollback mechanism to the last know good state. This is the purpose of the
 * oldWindow variable and the commit and rollback functions.
 * <p>
 * 
 * This class was designed with the purpose of examining rupture locals in a
 * fault gridded surface, but has been generalized to work with any
 * Container2DAPI.
 * <p>
 * 
 * @author Steven W. Rock
 * @created February 25, 2002
 * @version 1.0
 */

public class ContainerSubset2D<T> implements Container2DAPI<T>, Serializable {

    /**
	 * 
	 */
    private static final long serialVersionUID = 1L;

    /** Class name used for debbuging */
    protected final static String C = "ContainerSubset2D";

    /** if true print out debugging statements */
    protected final static boolean D = false;

    /**
     * Every container has a name associated with it to distinguish it from
     * other container instances. SUbsets can also have names different from the
     * referenced container. Also useful for displaying in a GUI.
     */
    protected String name = "";

    /**
     * Data containing indexing information into larger dataset. Contains xMin,
     * xMax, yMin, and yMax indexes. This allows translation from this subset
     * container coordinate system into the lerger referenced container. For
     * example the 0th index along the x axis in this subset container maps to
     * minX index in the main container.
     */
    protected Window2D window = new Window2D();

    /**
     * The API allows translation, modifications of the Window2D around the
     * larger referenced container. Because there are four variables to the
     * Window2D, this could take four method calls to change the data. Because
     * there is more than one step involved, and any one step can potentially
     * fail, I needed to provide a rollback mechanism to the last know good
     * state. This is the purpose of the oldWindow variable and the commit and
     * rollback functions. .
     */
    protected Window2D oldWindow = null;

    /** Internal reference to real data container. */
    protected Container2DAPI<T> data = null;

    /**
     * Constructor for the ContainerSubset2D object. Provides specifications
     * that allows the Window2D to be fully specified
     * 
     * @param numRows
     *            number of index points along the x-axis
     * @param numCols
     *            number of index points along the y-axis
     * @param startRow
     *            Staring row of this subset, put in Window2D
     * @param startCol
     *            Staring col of this subset, put in Window2D
     * @exception ArrayIndexOutOfBoundsException
     *                Thown if any of the idices go beyond the range of the
     *                referencing container
     */
    public ContainerSubset2D(int numRows, int numCols, int startRow,
            int startCol) throws ArrayIndexOutOfBoundsException {

        String S = C + ": Constructor():";

        window.startRow = startRow;
        window.startCol = startCol;
        window.numRows = numRows;
        window.numCols = numCols;

        window.checkLowerBounds(S);
        window.calcUpperBounds();

    }

    /**
     * Constructor for the ContainerSubset2D object. Provides specifications
     * that allows the Window2D to be fully specified. Also sets the reference
     * to the real data in the main Container2D
     * 
     * @param numRows
     *            number of index points along the x-axis
     * @param numCols
     *            number of index points along the y-axis
     * @param startRow
     *            Staring row of this subset, put in Window2D
     * @param startCol
     *            Staring col of this subset, put in Window2D
     * @exception ArrayIndexOutOfBoundsException
     *                Thown if any of the idices go beyond the range of the
     *                referencing container
     */
    public ContainerSubset2D(int numRows, int numCols, int startRow,
            int startCol, Container2DAPI<T> data)
            throws ArrayIndexOutOfBoundsException {

        String S = C + ": Constructor2():";

        window.startRow = startRow;
        window.startCol = startCol;
        window.numRows = numRows;
        window.numCols = numCols;

        window.checkLowerBounds(S);
        window.calcUpperBounds();
        setContainer2D(data);

    }

    /**
     * Allows setting the reference to a new Container2D. All indexes must have
     * been set already i the Window2D before calling this function. If invalid
     * data, the window is rolled back to the old one.
     * 
     * @param data
     *            The new container2D value
     * @exception ArrayIndexOutOfBoundsException
     *                Thown if any of the idices go beyond the range of the
     *                referencing container
     */
    public void setContainer2D(Container2DAPI<T> data)
            throws ArrayIndexOutOfBoundsException {
        String S = C + ": setContainer2D():";

        initTransaction();

        window.maxNumRows = data.getNumRows();
        window.maxNumCols = data.getNumCols();

        try {
            window.checkUpperBounds(S);
        } catch (ArrayIndexOutOfBoundsException e) {
            rollback();
            throw e;
        }
        commit();
        this.data = data;
    }

    /**
     * Used to update the starting row index in the Window2D. If invalid data,
     * the window is rolled back to the old one.
     * 
     * @param startRow
     *            The new startRow value
     * @exception ArrayIndexOutOfBoundsException
     *                Thrown if this start row is an invalid index in the main
     *                container, i.e. too large or negative.
     */
    public void setStartRow(int startRow) throws ArrayIndexOutOfBoundsException {

        String S = C + ": setStartRow():";
        initTransaction();
        window.startRow = startRow;

        try {
            window.checkLowerBounds(S);
            window.calcUpperBounds();
        } catch (ArrayIndexOutOfBoundsException e) {
            rollback();
            throw e;
        }
        commit();
    }

    /**
     * Internal helper function that performs various validation checks between
     * the Window2D values and the referenced container domain and range values.
     * Validates that all the subset indeces are within the main Container2D
     * space.
     * 
     * @throws ArrayIndexOutOfBoundsException
     *             Thrown if any of the values are invalid, such as negative
     *             indices.
     */
    protected void validate() throws ArrayIndexOutOfBoundsException {

        String S = C + ": validate():";
        window.checkLowerBounds(S);
        window.calcUpperBounds();
        window.checkUpperBounds(S);

        if (this.data == null) {
            throw new ArrayIndexOutOfBoundsException(S
                    + "Data list cannot be null");
        }

    }

    /**
     * Used to update the starting cal index in the Window2D. If invalid data,
     * the window is rolled back to the old one.
     * 
     * @param startRow
     *            The new startCal value in Window2D
     * @exception ArrayIndexOutOfBoundsException
     *                Thrown if this start cal is an invalid index in the main
     *                container, i.e. too large or negative.
     */
    public void setStartCol(int startCol) throws ArrayIndexOutOfBoundsException {
        String S = C + ": setStartCol():";
        initTransaction();
        window.startCol = startCol;

        try {
            window.checkLowerBounds(S);
            window.calcUpperBounds();
        } catch (ArrayIndexOutOfBoundsException e) {
            rollback();
            throw e;
        }
        commit();
    }

    /**
     * This method is required of the Contianer2dAPI. This subclass was designed
     * as read-only so throws an exception if you try to use this.
     * 
     * @param row
     *            x-coord
     * @param column
     *            y-coord
     * @param obj
     *            new object to place in the container cell
     * @exception ArrayIndexOutOfBoundsException
     *                Never thrown, function disabled.
     */
    public void set(int row, int column, T obj)
            throws ArrayIndexOutOfBoundsException {
        throw new java.lang.UnsupportedOperationException(
                "This function is not implemented in this subclass");
    }

    /**
     * Returns the container2D pointer contained in the subset window.
     * 
     * @return The container2D pointer
     */
    public Container2DAPI<T> getContainer2D() {
        return data;
    }

    /**
     * Gets the startRow index of the Window2D object
     * 
     * @return The startRow value
     */
    public int getStartRow() {
        return window.startRow;
    }

    /**
     * Gets the startColindex of the Window2D object
     * 
     * @return The startCol value
     */
    public int getStartCol() {
        return window.startCol;
    }

    /**
     * Returns number of rows in the Window2D.
     * 
     * @return The num rows
     */
    public int getNumRows() {
        return window.numRows;
    }

    /**
     * Returns number of cols in the Window2D.
     * 
     * @return The num cols
     */
    public int getNumCols() {
        return window.numCols;
    }

    /**
     * Returns the last row index on the Window2D
     * 
     * @return The numRows value
     */
    public int getEndRow() {
        return window.endRow;
    }

    /**
     * Returns the last col index on the Window2D
     * 
     * @return The numCols value
     */
    public int getEndCol() {
        return window.endCol;
    }

    /**
     * Returns the object stored in the Container2D at the subset's window
     * coordinates. These are translated to the real coordinates using the
     * Window2D
     * 
     * @param row
     *            x-coord
     * @param column
     *            y-coord
     * @return The java objectg stored in the container.
     * @exception ArrayIndexOutOfBoundsException
     *                If the indices value are invalid for the container2D
     */
    public T get(int row, int column) throws ArrayIndexOutOfBoundsException {

        String S = C + ": getColumnIterator(): ";

        if (!window.isValidCol(column)) {
            throw new ArrayIndexOutOfBoundsException(
                    S
                            + "The specified column is invalid, either negative or beyond upper index of window. "
                            + column);
        }

        if (!window.isValidRow(row)) {
            throw new ArrayIndexOutOfBoundsException(
                    S
                            + "The specified row is invalid, either negative or beyond upper index of window. "
                            + column);
        }

        int transRow = window.getTranslatedRow(row);
        int transCol = window.getTranslatedCol(column);

        return data.get(transRow, transCol);

    }

    /**
     * Iterate over all columns values in one row of the surface. Note this only
     * returns the column values in this subset window, not the full container.
     * 
     * @param row
     *            Row to get all column points from
     * @return The columnIterator value
     * @exception ArrayIndexOutOfBoundsException
     *                If the x-coord index value are invalid for the container2D
     */
    public ListIterator<T> getColumnIterator(int row)
            throws ArrayIndexOutOfBoundsException {

        String S = C + ": getColumnIterator(): ";

        if (!window.isValidRow(row)) {
            throw new ArrayIndexOutOfBoundsException(
                    S
                            + "The specified row is invalid, either negative or beyond upper index of window. "
                            + row);
        }

        validate();
        ColumnIterator it = new ColumnIterator(row);
        return it;
    }

    /**
     * Iterate over all row values in one column of the surface. Note this only
     * returns the row values in this subset window, not the full container.
     * 
     * @param row
     *            Column to get all row points from
     * @return The rowIterator value
     * @exception ArrayIndexOutOfBoundsException
     *                If the y-coord index value are invalid for the container2D
     */
    public ListIterator<T> getRowIterator(int column)
            throws ArrayIndexOutOfBoundsException {

        String S = C + ": getRowIterator(): ";
        if (!window.isValidCol(column)) {
            throw new ArrayIndexOutOfBoundsException(
                    S
                            + "The specified column is invalid, either negative or beyond upper index of window. "
                            + column);
        }

        validate();
        RowIterator it = new RowIterator(column);
        return it;
    }

    /**
     * Iterate over all cells in the subset window. This iterator starts with
     * the first column and returns all row elements, then moves to the next
     * column, and so on.
     * <p>
     * 
     * Note: This iterates only over the subset indices, not over the full
     * container. The iterator implementation is contained as an inner class in
     * this clas file.
     * 
     * @return The allByColumnsIterator value
     */
    public ListIterator<T> getAllByColumnsIterator() {
        validate();
        AllByColumnsIterator it = new AllByColumnsIterator();
        return it;
    }

    /**
     * Iterate over all cells in the subset window. This iterator starts with
     * the first row and returns all column elements, then moves to the next
     * row, and so on.
     * <p>
     * 
     * Note: This iterates only over the subset indices, not over the full
     * container. The iterator implementation is contained as an inner class in
     * this clas file.
     * 
     * @return The allByRowsIterator value
     */
    public ListIterator<T> getAllByRowsIterator() {
        validate();
        AllByRowsIterator it = new AllByRowsIterator();
        return it;
    }

    /**
     * Shifts the Window2D "window" into the main Container2D by the specified
     * number of index points. This allows the window to be moved over various
     * points of interest without construction of a brand new object.
     * 
     * @param delta
     *            Number of points to shift the Window2D along the x-axis
     * @exception ArrayIndexOutOfBoundsException
     *                Thrown if the shift moves the window outside the main
     *                container boundaries.
     */
    public void shiftRows(int delta) throws ArrayIndexOutOfBoundsException {

        // String S = C + ": shiftRows():";
        initTransaction();

        try {
            window.shiftRows(delta);
        } catch (ArrayIndexOutOfBoundsException e) {
            rollback();
            throw e;
        }
        commit();
    }

    /**
     * Start of a transaction - simply clones the Window2D into the old Window.
     * This is needed because resizing the window is a multistep process, i.e.
     * more than onw function call required to shift in the x, then the y
     * directions. Any of these functions can throw errors. So if one fails, we
     * have to "undo" all the previous successful function calls. They all must
     * succede or the resizing is considered a failure and all operations must
     * be undone, resetting to the original state. That is the purpose of the
     * rollback() function.
     */
    protected void initTransaction() {
        oldWindow = (Window2D) window.clone();
    }

    /**
     * Copies the oldWindow back into the Window2D, restoring the window to it's
     * previous size.
     */
    protected void rollback() {
        window = oldWindow;
        oldWindow = null;
    }

    /**
     * Completes a transaction. All required actions completed successfully so
     * the old window variable is deleted and the changes kept in the primary
     * Window2D.
     */
    protected void commit() {
        oldWindow = null;
    }

    /**
     * Shifts the Window2D "window" into the main Container2D by the specified
     * number of index points. This allows the window to be moved over various
     * points of interest without construction of a brand new object.
     * 
     * @param delta
     *            Number of points to shift the Window2D along the y-axis
     * @exception ArrayIndexOutOfBoundsException
     *                Thrown if the shift moves the window outside the main
     *                container boundaries.
     */
    public void shiftCols(int delta) throws ArrayIndexOutOfBoundsException {

        // String S = C + ": shiftCols():";
        initTransaction();

        try {
            window.shiftCols(delta);
        } catch (ArrayIndexOutOfBoundsException e) {
            rollback();
            throw e;
        }

    }

    /**
     * Returns the size of the subset window, numRows * numCols.
     * 
     * @return Description of the Return Value
     */
    public long size() {
        return window.windowSize();
    }

    /**
     * Returns true if a non-null java object resides at the specified cell,
     * i.e. row and column index.
     * 
     * @param row
     *            x-coord
     * @param column
     *            y-coord
     * @return true or false if the object exits.
     */
    public boolean exist(int row, int column) {

        String S = C + ": exist():";

        if (!window.isValidCol(column)) {
            throw new ArrayIndexOutOfBoundsException(
                    S
                            + "The specified column is invalid, either negative or beyond upper index of window. "
                            + column);
        }

        if (!window.isValidRow(row)) {
            throw new ArrayIndexOutOfBoundsException(
                    S
                            + "The specified row is invalid, either negative or beyond upper index of window. "
                            + column);
        }

        int transRow = window.getTranslatedRow(row);
        int transCol = window.getTranslatedCol(column);

        return data.exist(transRow, transCol);
    }

    /**
     * Sublcass not allowed to modify data, i.e. read only. Therefore this
     * function is not supported, but required by the API.
     */
    public void clear() {
        throw new java.lang.UnsupportedOperationException(
                "This function is not implemented in this subclass");
    }

    /**
     * Sublcass not allowed to modify data, i.e. read only. Therefore this
     * function is not supported, but required by the API.
     * 
     * @param row
     *            Description of the Parameter
     * @param column
     *            Description of the Parameter
     * @exception ArrayIndexOutOfBoundsException
     *                Description of the Exception
     * @exception java.lang.UnsupportedOperationException
     *                Description of the Exception
     */
    // public void delete( int row, int column )
    // throws
    // ArrayIndexOutOfBoundsException,
    // java.lang.UnsupportedOperationException {
    //
    // throw new java.lang.UnsupportedOperationException(
    // "This function is not implemented in this subclass" );
    // }

    /**
     * iterate over all data points, no guarentee of order returned
     * 
     * @return Description of the Return Value
     */
    public ListIterator<T> listIterator() {
        validate();
        AllByRowsIterator it = new AllByRowsIterator();
        return it;
    }

    /**
     * Use Window2D to generate this. Translates the internal data structure of
     * this 2D window into a Java2D array. This is needed fo specific JFreeChart
     * functionaliry.
     * 
     * @return Description of the Return Value
     */
    public Object[][] toJava2D() {

        int transRow, transCol;
        Object[][] d = new Object[window.numRows][window.numCols];
        for (int j = 0; j < window.numRows; j++) {
            for (int i = 0; i < window.numCols; i++) {
                transRow = window.getTranslatedRow(j);
                transCol = window.getTranslatedCol(i);
                d[i][j] = data.get(transRow, transCol);
            }
        }
        return d;
    }

    /**
     * <b>Title:</b> Container2DListIterator
     * <p>
     * 
     * <b>Description:</b> Base abstract class for all iterators. Stores the
     * indexes, etc, and implements nextIndex() and hasNext(). All unsupported
     * methods throws Exceptions.
     * <p>
     * 
     * This is how iterators should be handled, i.e. the class should be an
     * inner class so that the outside world only ever sees a ListIterator.
     * <p>
     * 
     * The iterator shouldn't be in a seperate class file because it needs
     * intimate knowledge to the data structure (in this case a java array)
     * which is usually hidden to the outside world. By making it an inner
     * class, the iterator has full access to the private variables of the data
     * class.
     * <p>
     * 
     * @author Steven W. Rock
     * @created February 25, 2002
     * @version 1.0
     */

    abstract class Container2DListIterator implements ListIterator<T> {

        /**
         * Description of the Field
         */
        int cursor = 0;
        /**
         * Description of the Field
         */
        int lastRet = -1;
        /**
         * Description of the Field
         */
        int lastIndex = 0;

        /**
         * returns full column to iterate over, pinned to one row
         */
        public Container2DListIterator() {
        }

        /**
         * Description of the Method
         * 
         * @param obj
         *            Description of the Parameter
         * @exception UnsupportedOperationException
         *                Description of the Exception
         */
        public void set(Object obj) throws UnsupportedOperationException {
            throw new UnsupportedOperationException(
                    "set(Object obj) Not implemented.");
        }

        /**
         * Description of the Method
         * 
         * @return Description of the Return Value
         */
        public boolean hasNext() {
            return cursor != lastIndex;
        }

        /**
         * Description of the Method
         * 
         * @return Description of the Return Value
         */
        public int nextIndex() {
            return cursor;
        }

        /**
         * Description of the Method
         * 
         * @return Description of the Return Value
         * @exception NoSuchElementException
         *                Description of the Exception
         */
        public abstract T next() throws NoSuchElementException;

        /**
         * Description of the Method
         * 
         * @return Description of the Return Value
         * @exception UnsupportedOperationException
         *                Description of the Exception
         */
        public T previous() throws UnsupportedOperationException {
            throw new UnsupportedOperationException(
                    "hasPrevious() Not implemented.");
        }

        /**
         * Description of the Method
         * 
         * @return Description of the Return Value
         * @exception UnsupportedOperationException
         *                Description of the Exception
         */
        public int previousIndex() throws UnsupportedOperationException {
            throw new UnsupportedOperationException(
                    "hasPrevious() Not implemented.");
        }

        /**
         * Description of the Method
         * 
         * @return Description of the Return Value
         * @exception UnsupportedOperationException
         *                Description of the Exception
         */
        public boolean hasPrevious() throws UnsupportedOperationException {
            throw new UnsupportedOperationException(
                    "hasPrevious() Not implemented.");
        }

        /**
         * Description of the Method
         * 
         * @param obj
         *            Description of the Parameter
         * @exception UnsupportedOperationException
         *                Description of the Exception
         */
        public void add(Object obj) throws UnsupportedOperationException {
            throw new UnsupportedOperationException(
                    "add(Object obj) Not implemented.");
        }

        /**
         * Description of the Method
         * 
         * @exception UnsupportedOperationException
         *                Description of the Exception
         */
        public void remove() throws UnsupportedOperationException {
            throw new UnsupportedOperationException("remove() Not implemented.");
        }

    }

    /**
     * <b>Title:</b> ColumnIterator
     * <p>
     * <b>Description:</b> Returns all column points for one row
     * <p>
     * 
     * @author Steven W. Rock
     * @created February 25, 2002
     * @version 1.0
     */
    class ColumnIterator extends Container2DListIterator {

        final static String C = "ColumnIterator";

        /**
         * Description of the Field
         */
        int translatedPinnedRow;

        /**
         * returns full column to iterate over, pinned to one row
         * 
         * @param row
         *            Description of the Parameter
         */
        public ColumnIterator(int row) throws ArrayIndexOutOfBoundsException {
            super();
            String S = C + ": Constructor():";

            if (!window.isValidRow(row)) {
                throw new ArrayIndexOutOfBoundsException(
                        S
                                + "The specified row is invalid, either negative or beyond upper index of window. "
                                + row);
            }

            translatedPinnedRow = window.getTranslatedRow(row);
            lastIndex = window.numCols;

        }

        /**
         * Description of the Method
         * 
         * @return Description of the Return Value
         * @exception NoSuchElementException
         *                Description of the Exception
         */
        public T next() throws NoSuchElementException {
            try {

                int transColumn = window.getTranslatedCol(cursor);
                T object = data.get(translatedPinnedRow, transColumn);
                lastRet = cursor++;
                return object;
            } catch (IndexOutOfBoundsException e) {
                throw new NoSuchElementException(
                        "You have iterated past the last element."
                                + e.toString());
            }
        }

    }

    /**
     * <b>Title:</b> RowIterator
     * <p>
     * <b>Description:</b> Returns all column points for one row
     * <p>
     * 
     * @author Steven W. Rock
     * @created February 25, 2002
     * @version 1.0
     */
    class RowIterator extends Container2DListIterator {

        final static String C = "RowIterator";

        /**
         * Description of the Field
         */
        int translatedPinnedCol;

        /**
         * returns full row to iterate over, pinned to one column
         * 
         * @param col
         *            Description of the Parameter
         */
        public RowIterator(int col) throws ArrayIndexOutOfBoundsException {
            super();
            String S = C + ": Constructor():";

            if (!window.isValidRow(col)) {
                throw new ArrayIndexOutOfBoundsException(
                        S
                                + "The specified col is invalid, either negative or beyond upper index of window. "
                                + col);
            }

            translatedPinnedCol = window.getTranslatedRow(col);
            lastIndex = window.numRows;

        }

        /**
         * Description of the Method
         * 
         * @return Description of the Return Value
         * @exception NoSuchElementException
         *                Description of the Exception
         */
        public T next() throws NoSuchElementException {
            try {

                int transRow = window.getTranslatedRow(cursor);
                T object = data.get(transRow, translatedPinnedCol);
                lastRet = cursor++;
                return object;
            } catch (IndexOutOfBoundsException e) {
                throw new NoSuchElementException(
                        "You have iterated past the last element."
                                + e.toString());
            }
        }

    }

    /**
     * <b>Title:</b> AllByColumnsIterator
     * <p>
     * <b>Description:</b> Returns all rows for a column, then moves to the next
     * column
     * <p>
     * 
     * @author Steven W. Rock
     * @created February 25, 2002
     * @version 1.0
     */
    class AllByColumnsIterator extends Container2DListIterator {

        /**
         * Description of the Field
         */
        int currentColumn = 0;
        /**
         * Description of the Field
         */
        int currentRow = 0;

        int transRow = 0;
        int transCol = 0;

        /**
         * Constructor for the AllByColumnsIterator object
         */
        public AllByColumnsIterator() {
            super();
            lastIndex = window.windowSize();
            transRow = window.startRow;
            transCol = window.startCol;
        }

        /**
         * Description of the Method
         * 
         * @return Description of the Return Value
         * @exception NoSuchElementException
         *                Description of the Exception
         */
        public T next() throws NoSuchElementException {

            try {

                T object = data.get(transRow, transCol);

                currentRow++;
                transRow = window.getTranslatedRow(currentRow);
                if (currentRow == window.numRows) {
                    currentRow = 0;
                    transRow = window.getTranslatedRow(currentRow);
                    currentColumn++;
                    transCol = window.getTranslatedCol(currentColumn);
                }

                lastRet = cursor++;
                return object;
            } catch (IndexOutOfBoundsException e) {
                throw new NoSuchElementException(
                        "You have iterated past the last element. "
                                + e.toString());
            }

        }
    }

    /**
     * <b>Title:</b> AllByRowsIterator
     * <p>
     * <b>Description:</b> Returns all columns for a row, then moves to the next
     * row
     * <p>
     * 
     * @author Steven W. Rock
     * @created February 25, 2002
     * @version 1.0
     */
    class AllByRowsIterator extends Container2DListIterator {

        /**
         * Description of the Field
         */
        int currentCol = 0;
        /**
         * Description of the Field
         */
        int currentRow = 0;

        int transRow = 0;
        int transCol = 0;

        /**
         * Constructor for the AllByRowsIterator object
         */
        public AllByRowsIterator() {
            super();
            lastIndex = window.windowSize();
            transRow = window.startRow;
            transCol = window.startCol;
        }

        /**
         * Description of the Method
         * 
         * @return Description of the Return Value
         * @exception NoSuchElementException
         *                Description of the Exception
         */
        public T next() throws NoSuchElementException {

            try {

                T object = data.get(transRow, transCol);

                currentCol++;
                transCol = window.getTranslatedCol(currentCol);
                if (currentCol == window.numCols) {
                    currentCol = 0;
                    transCol = window.getTranslatedCol(currentCol);
                    currentRow++;
                    transRow = window.getTranslatedRow(currentRow);
                }

                lastRet = cursor++;
                return object;
            } catch (IndexOutOfBoundsException e) {
                throw new NoSuchElementException(
                        "You have iterated past the last element."
                                + e.toString());
            }

        }

    }

    /** */
    final protected static char TAB = '\t';

    /** Prints out each location and fault information for debugging */
    public String toString() {

        StringBuffer b = new StringBuffer();
        b.append('\n');

        if (window == null) {
            b.append("No window specified, unable to print out locations");
        } else {

            int i = 0, j, counter = 0;
            while (i < window.numRows) {

                j = 0;
                while (j < window.numCols) {

                    b.append("" + i + TAB + j + TAB);
                    Object obj = this.get(i, j);
                    if (obj != null) {
                        b.append(obj.toString());
                        counter++;
                    } else
                        b.append("NULL");
                    b.append('\n');

                    j++;
                }
                i++;

            }
            b.append("\nNumber of Rows = " + window.numRows + '\n');
            b.append("Number of Columns = " + window.numCols + '\n');
            b.append("Size = " + window.numCols * window.numRows + '\n');
            b.append("Number of non-null objects = " + counter + '\n');
            b.append("Start Row of main Surface = " + window.startRow + '\n');
            b.append("Start COl of main Surface = " + window.startCol + '\n');
        }
        return b.toString();
    }

    /**
     * The main program for the Container2D class. Used to test and demonstrate
     * usage of this class.
     * 
     * @param args
     *            The command line arguments
     */
    public static void main(String[] args) {

        String S = C + ": Main(): ";
        System.out.println(S + "Starting");

        int xsize = 5;
        int ysize = 10;

        Container2D<String> data = new Container2D<String>(xsize, ysize);
        for (int x = 0; x < xsize; x++) {
            for (int y = 0; y < ysize; y++) {
                data.set(x, y, "[" + x + ", " + y + ']');
                System.out.println(S + data.get(x, y).toString());
            }
        }

        int numRows = 2;
        int numCols = 3;
        int startRow = 1;
        int startCol = 2;
        ContainerSubset2D<String> sub =
                new ContainerSubset2D<String>(numRows, numCols, startRow,
                        startCol, data);
        sub.validate();
        System.out.println(S + sub.window.toString());

        System.out.println(S);
        System.out.println(S);
        System.out.println(S + "getColumnIterator");

        ListIterator<String> it = sub.getColumnIterator(0);
        while (it.hasNext()) {

            String obj = it.next();
            System.out.println(S + obj.toString());

        }

        System.out.println(S);
        System.out.println(S);
        System.out.println(S + "getRowIterator");

        it = sub.getRowIterator(0);
        while (it.hasNext()) {

            String obj = it.next();
            System.out.println(S + obj.toString());

        }

        System.out.println(S);
        System.out.println(S);
        System.out.println(S + "getAllByRowssIterator");

        it = sub.getAllByRowsIterator();
        while (it.hasNext()) {

            String obj = it.next();
            System.out.println(S + obj.toString());

        }

        System.out.println(S);
        System.out.println(S);
        System.out.println(S + "getAllByColumnsIterator");

        it = sub.getAllByColumnsIterator();
        while (it.hasNext()) {

            String obj = it.next();
            System.out.println(S + obj.toString());

        }

        System.out.println(S);
        System.out.println(S);
        System.out.println(S + "List Iterator");

        it = sub.listIterator();
        while (it.hasNext()) {

            String obj = it.next();
            System.out.println(S + obj.toString());

        }

        System.out.println(S);
        System.out.println(S);
        System.out.println(S + "Shifting rows by 2");
        System.out.println(S + "Shifting cols by 1");
        System.out.println(S + "List Iterator");

        sub.shiftCols(1);
        sub.shiftRows(2);
        it = sub.listIterator();
        while (it.hasNext()) {

            String obj = it.next();
            System.out.println(S + obj.toString());

        }

        System.out.println(S + "Ending");

    }

    public void setName(String name) {
        this.name = name;
    }

    public String getName() {
        return name;
    }

    @Override
    public Iterator<T> iterator() {
        return listIterator();
    }
}
