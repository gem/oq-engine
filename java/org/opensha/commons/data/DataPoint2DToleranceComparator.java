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

import java.io.Serializable;

import org.opensha.commons.exceptions.InvalidRangeException;


/**
 *  <b>Title:</b> DataPoint2DComparatorAPI<p>
 *
 *  <b>Description:</b> Implementing comparator of DataPoint2d. The comparator
 *  uses a tolerance to specify that when two values are within tolerance of
 *  each other, they are equal<p>
 *
 * This class sounds more complicated that it really is. The whole purpose
 * is for calling the function compare(Object o1, Object o2). The x-coordinates
 * are obtained from each, then this algorythmn determines if the x-values are
 * equal:<p>
 *
 * Math.abs( x1 - x2 ) <= tolerance)<p>
 *
 * A tolerance=0 is actually abaout 1e-16 due to the numerical precision of floating
 * point arithmetic (1.0 + 1e-16 = 1.0 )<p>
 *
 * Note: In general comparators are created so that you can have more than one
 * sorting for a class. Imagine that you have a Javabean with 4 fields, id, first name,
 * last name, date created. Typical for a user record in a database. Now you can
 * build the compareTo() function inside this Javabean, nut then you can only sort
 * on 1 column. What if you present these javabeans in a GUI List, and you want to
 * sort on any field by clicking on the header. You simply make 4 comparators,
 * one for each field. Each header would use the particular comparator for the
 * sorting function. Very nice design pattern. <p>
 *
 * Now let's say you add another field. You simply make a new Comparator ( almost copy and paste).
 * You don't have to change youre Javabean or your sorting function. Just pass in this
 * new comparator. <p>
 *
 * @author     Steven W. Rock
 * @created    February 20, 2002
 * @see        DataPoint2DComparatorAPI
 * @version    1.0
 */

public class DataPoint2DToleranceComparator implements DataPoint2DComparatorAPI,
                                                       Serializable{

    /**
     *  The tolerance for determining whether two x values are different.  A
     *  tolerance of 0.0 (the default) is really about 1e-16 due to the numerical
     *  precision of floating point arithmetic ( 1.0 - (1.0+1e-16) = 0.0 ).
     *  Note that the tolerance must be smaller than 1/2 of any desired delta
     *  between data points. If the tolerance is less than zero an
     *  InvalidRangeException is thrown
     */
    protected double tolerance = 0.0 ;


    /**
     *  No-Argument constructor. Does nothing but construct the class instance.
     *
     * @exception  InvalidRangeException
     */
    public DataPoint2DToleranceComparator() throws InvalidRangeException { }


    /**
     *  Constructor that sets the tolerance when created. Throws an
     *  InvalidRangeException if the tolerance is less than zero. Negative
     *  tolerance makes no sense.
     *
     * @param  tolerance                  The distance two values can be apart
     *      and still considered equal
     * @exception  InvalidRangeException  Thrown if tolerance is negative
     */
    public DataPoint2DToleranceComparator( double tolerance ) throws InvalidRangeException {

        if ( tolerance < 0 ) {
            throw new InvalidRangeException( "Tolerance must be larger or equal to 0" );
        }

        this.tolerance = tolerance;
    }


    /**
     *  Tolerance indicates the distance two values can be apart, but still
     *  considered equal. This function returns the tolerance.  Any tolerance
     *  less than about 1e-16 is about 1e-16 due to the numerical precision of
     *  floating point arithmetic.
     *
     * @param  newTolerance               The new tolerance value
     * @exception  InvalidRangeException  Thrown if tolerance is negative
     */
    public void setTolerance( double newTolerance ) throws InvalidRangeException {
        if ( tolerance < 0 ) {
            throw new InvalidRangeException( "Tolerance must be larger or equal to 0" );
        }

        tolerance = newTolerance;
    }


    /**
     *  Tolerance indicates the distance two values can be apart, but still
     *  considered equal. This function returns the tolerance.
     *
     * @return    The tolerance value
     */
    public double getTolerance() {
        return tolerance;
    }


    /**
     *  Returns 0 if the two Objects are equal, -1 if the first object is less
     *  than the second, or +1 if it's greater. This function throws a
     *  ClassCastException if the two values are not DataPoint2Ds. Only the
     *  X-Value is compared, the Y-Value is ignored. If the distance between the
     *  two X-Values are less than or equal to the tolerance, they are
     *  considered equal. <P>
     *
     *  One use for this class is to sort a DiscretizedFunction by it's X-Values
     *  (independent variable) ascending, to prepare the function for plotting.
     *
     * @param  o1                      First DataPoint2D
     * @param  o2                      Second DataPoint2D
     * @return                         -1 if o1 < 02, 0 if o1 = o2, +1 if o1 >
     *      o2
     * @exception  ClassCastException  Thrown if either passed in arg is not a
     *      DataPoint2D
     */
    public int compare( Object o1, Object o2 ) throws ClassCastException {

        if ( !( o1 instanceof DataPoint2D ) ) {
            throw new ClassCastException( "The first object is not an DataPoint2D, unable to compare" );
        }

        if ( !( o2 instanceof DataPoint2D ) ) {
            throw new ClassCastException( "The second object is not an DataPoint2D, unable to compare" );
        }

        double x1 = ( ( DataPoint2D ) o1 ).getX();
        double x2 = ( ( DataPoint2D ) o2 ).getX();

        if ( Math.abs( x1 - x2 ) <= tolerance) {
            return 0;
        } else if ( x1 > x2 ) {
            return 1;
        } else {
            return -1;
        }

    }
}
