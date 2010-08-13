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

// FIX - Needs more comments

/**
 *  <b>Title:</b> Window2D<p>
 *
 *  <b>Description:</b> This class represents the sub indices of a window into a
 *  two dimensional matrix. A two dimensional matrix is usually specified by x
 *  and y coordinates, i.e. rows and columns. So a two dimensional
 *  matrix will have a max number of rows and a max number of columns. This
 *  window will have a start row and start column, end row and end column which
 *  determines the number of rows and columns that you are peering into. <p>
 *
 *  This class is the data model ( javabean ) used by ContainerSubset2D to
 *  provide the indices as a window into the main Container2D matrix
 *  referenced within the ContainerSubset2D.<p>
 *
 * @author     Steven W. Rock
 * @created    February 25, 2002
 * @version    1.0
 */

public class Window2D implements java.io.Serializable{

    /** Class name used for debugging. */
    protected final static String C = "ContainerSubset2D";

    /** If true debugging statements are printed.  */
    protected final static boolean D = false;

    /** The first row of the window.  */
    protected int startRow = 0;

    /** The last row of the window. */
    protected int endRow = 0;

    /** The number of rows in this window. */
    protected int numRows = 0;

    /** The number of rows in the full matrix. */
    protected int maxNumRows = 0;

    /** The first column of the window. */
    protected int startCol = 0;

    /** The last column of the window. */
    protected int endCol = 0;

    /** The number of columns in this window. */
    protected int numCols = 0;

    /** The full number of columns in the full matrix. */
    protected int maxNumCols = 0;


    /** No-arg Constructor - does nothing. */
    public Window2D() { }

    /**
     *  This function determines if the specified row fits within the window. It
     *  does not go past the end row.
     *
     * @param  row  The row you wish to return from the window subset
     * @return      True if the row is within range, false otherwise.
     */
    public boolean isValidRow( int row ) {
        if ( row < 0 ) {
            return false;
        } else if ( ( startRow + row ) <= endRow ) {
            return true;
        } else {
            return false;
        }
    }


    /** Returns the first row of the window.  */
    public int getStartRow(){ return startRow; }


    /**
     *  This function determines if the specified input col fits within the
     *  window. It can not go past the end col.
     *
     * @param  col  The col you wish to return of the window subset
     * @return      True if the col is within range. False otherwise.
     */
    public boolean isValidCol( int col ) {
        if ( col < 0 ) {
            return false;
        } else if ( ( startCol + col ) <= endCol ) {
            return true;
        } else {
            return false;
        }
    }



    /**
     *  Takes an input row of the window subset and translates it back to the
     *  original larger matrix. In other words adds the start row to the input
     *  row. So if you specify 0 the result would return 20 if 20 was the start
     *  row in the original matrix.
     *
     * @param  row  Input row you wish to translate to the original matrix row.
     * @return      The translated Row value
     */
    public int getTranslatedRow( int row ) {
        return ( startRow + row );
    }


    /**
     *  Takes an input col of the window subset and translates it back to the
     *  original larger matrix.In other words adds the start col to the input
     *  col. So if you specify 0 the result would return 20 if 20 was the start
     *  col in the original matrix.
     *
     * @param  col  Input col you wish to translate to the original matrix col.
     * @return      The translated Col value
     */
    public int getTranslatedCol( int col ) {
        return ( startCol + col );
    }


    /**
     *  Returns the number of rows times the num of columns in this window.
     *
     * @return    numRows * numCol
     */
    public int windowSize() {
        return numRows * numCols;
    }


    /**
     *  Shift the start row of your window by delta. If delta is negative it
     *  will shift the window to a smaller starting row. If positive it will
     *  shift it to a larger starting row.
     *
     * @param  delta                               The amount you wish to shift
     *      the window in index units.
     * @exception  ArrayIndexOutOfBoundsException  This exception is thrown if
     *      the shift moves the windows either into negative values or outside
     *      the range of the original matrix.
     */
    public void shiftRows( int delta ) throws ArrayIndexOutOfBoundsException {

        String S = C + ": shiftCols():";
        this.startRow += delta;
        checkLowerBounds( S );
        calcUpperBounds();
        checkUpperBounds( S );

    }


    /**
     *  Shift the start col of your window by delta. If delta is negative it
     *  will shift the window to a smaller col. If positive it will shift it to
     *  a larger col.
     *
     * @param  delta                               The amount you wish to shift
     *      the window in index units.
     * @exception  ArrayIndexOutOfBoundsException  This exception is thrown if
     *      the shift moves the windows either into negative values or outside
     *      the range of the original matrix.
     */
    public void shiftCols( int delta ) throws ArrayIndexOutOfBoundsException {

        String S = C + ": shiftCols():";
        this.startCol += delta;
        checkLowerBounds( S );
        calcUpperBounds();
        checkUpperBounds( S );

    }


    /**
     *  This function calculates the end row and column based on the user input
     *  of start row column and num rows and columns.
     */
    public void calcUpperBounds() {
        this.endRow = startRow + numRows - 1;
        this.endCol = startCol + numCols - 1;
    }


    /**
     *  Checks that the specified row and column are valid indices into the 2D
     *  array. This is a helper function that validates the user inputs that are
     *  all num larger than 0.
     *
     * @param  S                                   Debugging string used for
     *      error messaging.
     * @exception  ArrayIndexOutOfBoundsException  Thrown if any of the window
     *      index information is less than zero.
     */
    public void checkLowerBounds( String S )
             throws ArrayIndexOutOfBoundsException {

        if ( startRow < 0 ) {
            throw new ArrayIndexOutOfBoundsException( S + "Start row cannot be less than zero" );
        }
        if ( startCol < 0 ) {
            throw new ArrayIndexOutOfBoundsException( S + "Start column cannot be less than zero" );
        }
        if ( numRows < 0 ) {
            throw new ArrayIndexOutOfBoundsException( S + "Number of rows cannot be less than zero" );
        }
        if ( numCols < 0 ) {
            throw new ArrayIndexOutOfBoundsException( S + "Number of columns cannot be less than zero" );
        }
    }


    /**
     *  Checks that the specified row and column are valid indices into the 2D
     *  array. This is a heper function that validates that all start row and
     *  start col end row and end col are not larger than the original matrix
     *  max number of rows and max number of columns. In other words the window
     *  cannot go beyond the bounds of the original matrix.
     *
     * @param  S                                   Debugging string used for
     *      error messaging.
     * @exception  ArrayIndexOutOfBoundsException  Thrown if any index of the
     *      window ie. start and end row and col fall beyond the maximum number
     *      of rows and columns in the original matrix.
     */
    public void checkUpperBounds( String S )
             throws ArrayIndexOutOfBoundsException {

        if ( startRow > maxNumRows ) {
            throw new ArrayIndexOutOfBoundsException( S + "Start row cannot be greater than the last index of the larger dataset" );
        }
        if ( startCol > maxNumCols ) {
            throw new ArrayIndexOutOfBoundsException( S + "Start column cannot be greater than the last index of the larger dataset" );
        }

        if ( endRow > maxNumRows ) {
            throw new ArrayIndexOutOfBoundsException( S + "End row cannot be greater than the last index of the larger dataset" );
        }
        if ( endCol > maxNumCols ) {
            throw new ArrayIndexOutOfBoundsException( S + "End column cannot be greater than the last index of the larger dataset" );
        }
    }


    /**
     *  Returns an exact copy of this window. You can change the clone without
     *  affecting this original data, this original instance.
     *
     * @return    A cloned copy of this window.
     */
    public Object clone() {
        return cloneWindow();
    }


    /**
     *  Returns an exact copy of this window. You can change the clone without
     *  affecting this original data, this original instance.
     *
     * @return    A cloned copy of this window.
     */
    public Window2D cloneWindow() {

        Window2D window = new Window2D();

        window.startCol = this.startCol;
        window.startRow = this.startRow;

        window.endCol = this.endCol;
        window.endRow = this.endRow;

        window.numCols = this.numCols;
        window.numRows = this.numRows;

        window.maxNumCols = this.maxNumCols;
        window.maxNumRows = this.maxNumRows;

        return window;
    }


    /**
     *  This function returns true if the input window has the same variables
     *  values as this window.
     *
     * @param  window  The input window to compare to this object.
     * @return         True if all indices ie. class variables are the same.
     */
    public boolean equalsWindow( Window2D window ) {

        if ( window.startCol != this.startCol ) {
            return false;
        }
        if ( window.startRow != this.startRow ) {
            return false;
        }

        if ( window.endCol != this.endCol ) {
            return false;
        }
        if ( window.endRow != this.endRow ) {
            return false;
        }

        if ( window.numCols != this.numCols ) {
            return false;
        }
        if ( window.numRows != this.numRows ) {
            return false;
        }

        if ( window.maxNumCols != this.maxNumCols ) {
            return false;
        }
        if ( window.maxNumRows != this.maxNumRows ) {
            return false;
        }

        return true;
    }


    /**
     *  This function returns true if the input window has the same variables
     *  values as this window.
     *
     * @param  obj  The input window to compare to this object.
     * @return      True if all indices ie. class variables are the same.
     */
    public boolean equals( Object obj ) {
        if ( obj instanceof Window2D ) {
            return equalsWindow( ( Window2D ) obj );
        } else {
            return false;
        }
    }


    /**
     *  Helper function used for debugging. This function prints out all
     *  variables current values.
     *
     * @return    Formatted string of instance information.
     */
    public String toString() {

        StringBuffer b = new StringBuffer();
        b.append( C );
        b.append( '\n' );

        b.append( "startCol = " );
        b.append( startCol );
        b.append( '\n' );

        b.append( "endCol = " );
        b.append( endCol );
        b.append( '\n' );

        b.append( "numCols = " );
        b.append( numCols );
        b.append( '\n' );

        b.append( "maxNumCols = " );
        b.append( maxNumCols );
        b.append( '\n' );

        b.append( "startRow = " );
        b.append( startRow );
        b.append( '\n' );

        b.append( "endRow = " );
        b.append( endRow );
        b.append( '\n' );

        b.append( "numRows = " );
        b.append( numRows );
        b.append( '\n' );

        b.append( "maxNumRows = " );
        b.append( maxNumRows );

        return b.toString();
    }


    /** Sets the startRow - javabean method */
    public void setStartRow(int startRow) { this.startRow = startRow; }

    /** Sets the startCol - javabean method */
    public void setStartCol(int startCol) { this.startCol = startCol; }

    /** Gets the startCol - javabean method */
    public int getStartCol() { return startCol; }

    /** Gets the numRows - javabean method */
    public int getNumRows() { return numRows; }

    /** Gets the numCols - javabean method */
    public int getNumCols() { return numCols; }

    /** Gets the maxNumRows - javabean method */
    public int getMaxNumRows() { return maxNumRows; }

    /** Gets the maxNumCols - javabean method */
    public int getMaxNumCols() { return maxNumCols; }

    /** Gets the endRow - javabean method */
    public int getEndRow() { return endRow; }

    /** Gets the endCol - javabean method */
    public int getEndCol() { return endCol; }

    /** Sets the numRows - javabean method */
    public void setNumRows(int numRows) { this.numRows = numRows; }

    /** Sets the numCols - javabean method */
    public void setNumCols(int numCols) { this.numCols = numCols; }

    /** Sets the endRow - javabean method */
    public void setEndRow(int endRow) { this.endRow = endRow; }

    /** Sets the endCol - javabean method */
    public void setEndCol(int endCol) { this.endCol = endCol; }

}
