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

/**
 *  <b>Title:</b> DataPoint2D<p>
 *
 *  <b>Description:</b> Represents a 2 dimensional point (x,y) in function space. Each
 *  coordinate is represented by a double.<p>
 *
 *  The x value is the independent value, and the y value is the dependent
 *  value. Therefore this class is sorted on the x-value. Two DataPoint2D are
 *  equal if there x-values are equal, whatever the y value is. This will be
 *  useful in DiscretizedDFunctions.<p>
 *
 * @author     Steven W. Rock
 * @created    February 20, 2002
 * @see        DiscretizedFunction2DAPI
 * @version    1.0
 */

public class DataPoint2D implements Comparable,java.io.Serializable {


    /* The name of this class, used for debug statements */
    protected final static String C = "DataPoint2D";

    /** Static boolean whether to print out debugging statements  */
    protected final static boolean D = false;

    /**  X coordinate value */
    private double x= Double.NaN;

    /** Y coordinate value */
    private double y = Double.NaN;



    /**
     *  Constructor sets point data in x/y space
     *
     * @param  x  x corrdinate value
     * @param  y  y corrdinate value
     */
    public DataPoint2D( double x, double y ) {
        this.x = x;
        this.y = y;
    }


    /** Get the X coordinate */
    public double getX() { return x; }

    /** Set the X coordinate value. No validation checks are done on new value */
    public void setX( double newX ) { x = newX; }

    /** Get the Y coordinate */
    public double getY() { return y; }

    /** Set the Y coordinate. No validation checks are done on new value */
    public void setY( double newY ) { y = newY; }


    /**
     *  Set both coordinates at once.
     *  No validation checks are done on new values.
     *
     * @param  x  The x coordinate
     * @param  y  The y coordinate
     */
    public void set( double x, double y ) {
        this.x = x;
        this.y = y;
    }


    /**
     *  Set both coordinates at once from the passed in DataPoint2D.
     *  In other words performs a copy. No validation checks are
     *  done on new values.
     *
     * @param  point  Copies x and y value from this point
     */
    public void set( DataPoint2D point ) {
        this.x = point.getX();
        this.y = point.getY();
    }







    /**
     *  Special equals function that returns true if the X Coordinates are the
     *  same, totally ignores the Y Value. This is useful because these points
     *  are used in Discretized functions, and need to sort on the X-Value, the
     *  independent value. Useful for sorting the functions then plotting them
     *
     * @param  point  Point to compare x-value to
     * @return        true if the two x-values are the same
     */
    public boolean equals( DataPoint2D point ) {
       double xx = point.getX();
       if ( x== xx  ) return true;
       else  return false;
    }


    /**
     *  Same as equals(DataPoint2D) except that the X values only have to be
     *  close, within tolerance, to bec onsidered equal.
     *
     * @param  point      Point to compare x-value to
     * @param  tolerance  The distance that the two x-values can be and still
     *      considered equal
     * @return            true if the two x-values are the same within tolerance
     */
    public boolean equals( DataPoint2D point, double tolerance ) {

        double x = this.x;
        double xx = point.getX();

        if ( Math.abs( x - xx ) <= tolerance) return true;
        else return false;

    }


    /**
     *  Special equals to test that both x and y are the same
     *
     * @param  x  The value to compare this object's x-value to
     * @param  y  The value to compare this object's y-value to
     * @return    true if this x-value and y-value equals the passed in x and y
     *      values
     */
    public boolean equals( double x, double y ) {
        if ( ( this.x == x ) && ( this.y == y ) ) return true;
        else return false;
    }


    /**
     *  Returns true if the x values are equal
     *
     * @param  x  The value to compare this x-value to
     * @return    true if this x-value equals the passed in x value
     */
    public boolean equals( double x ) {
        if ( this.x == x ) return true;
        else return false;
    }


    /**
     *  Compares two DataPoint2D objects and returns 0 if they have the same x
     *  coordinates, -1 if the first object has a smaller X Value, and +1 if it
     *  has a larger x value.
     *
     * @param  obj                     The DataPoint2D to test
     * @return                         -1 if the x-value of this is smalleer
     *      than the comparing object are the same, 0 if the x-values are equal,
     *      and +1 if this x-value is larger.
     * @exception  ClassCastException  Is thrown if the passed in object is not
     *      a DataPoint2D
     */
    public int compareTo( Object obj ) throws ClassCastException {

        String S = C + ":compareTo(): ";

        if ( !( obj instanceof DataPoint2D ) ) {
            throw new ClassCastException( S + "Object not a DataPoint2D, unable to compare" );
        }

        DataPoint2D point = ( DataPoint2D ) obj;

        int result = 0;

        Double x =  new Double(this.x);
        Double xx = new Double(point.getX());

         return x.compareTo(xx);

    }



    /**
     *  Compares value to see if equal
     *
     * @param  obj                     The DataPoint2D to test
     * @return                         True if this x-value is the same as the
     *      comparing object
     * @exception  ClassCastException  Is thrown if the passed in object is not
     *      a DataPoint2D
     */
    public boolean equals( Object obj ) throws ClassCastException {
        if ( compareTo( obj ) == 0 ) {
            return true;
        } else {
            return false;
        }
    }


    /**
     *  Useful for debugging. Returns the classname and the x & y coordinates of
     *  the point.
     *
     * @return    A descriptive string of the object's state
     */
    public String toString() {
        String TAB = "    ";
        StringBuffer b = new StringBuffer();
        b.append( C );
        b.append( TAB + "X = " + x + '\n' );
        b.append( TAB + "Y = " + y + '\n' );
        return b.toString();
    }


    /**
     *  sets the y-value to the x-value and vise versa. <p>
     */
    protected void invert() {

        double xx = this.y;
        double yy = this.x;
        y = yy;
        x = xx;

    }


    /**
     *  Returns a copy of this DataPoint2D. If you change the copy, this
     *  original is unaltered.
     *
     * @return    An exact copy of this object.
     */
    public Object clone() {
        double xx = this.x;
        double yy = this.y;
        DataPoint2D point = new DataPoint2D( xx, yy );
        return point;
    }

}
