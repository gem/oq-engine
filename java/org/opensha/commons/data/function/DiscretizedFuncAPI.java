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

package org.opensha.commons.data.function;

import java.util.Iterator;
import java.util.ListIterator;

import org.opensha.commons.data.DataPoint2D;
import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.exceptions.DataPoint2DException;
import org.opensha.commons.metadata.XMLSaveable;

/**
 * <b>Title:</b> DiscretizedFuncAPI<p>
 *
 * <b>Description:</b> Interface that all Discretized Functions must implement. <P>
 *
 * A Discretized Function is a collection of x and y values grouped together as
 * the points that describe a function. A discretized form of a function is the
 * only ways computers can represent functions. Instead of having y=x^2, you
 * would have a sample of possible x and y values. <p>
 *
 * This functional framework is modeled after mathmatical functions
 * such as sin(x), etc. It assumes that there are no duplicate x values,
 * and that if two points have the same x value but different y values,
 * they are still considered the same point. The framework also sorts the
 * points along the x axis, so the first point contains the mimimum
 * x-value and the last point contains the maximum value.<p>
 *
 * Since this API represents the points in a list, alot of these API functions
 * are standard list access functions such as (paraphrasing) get(), set(),
 * delete(). numElements(), iterator(), etc.<p>
 *
 * There are three fields along with getXXX() and setXXX() matching the field
 * names. These javabean fields provide the basic information to describe
 * a function. All functions have a name, information string, and a
 * tolerance level that specifies how close two points have to be along
 * the x axis to be considered equal.<p>
 *
 * DataPoint2D = (x,y)<p>
 *
 * Note: This interface defines a tolerance so that you can say two x-values
 * are the same within this tolerance limit. THERE IS NO TOLERANCE FOR THE
 * Y-AXIS VALUES. This may be useful to add in the future.<p>
 *
 * @author Steven W. Rock
 * @see DataPoint2D
 * @version 1.0
 */

public interface DiscretizedFuncAPI extends java.io.Serializable, NamedObjectAPI, XMLSaveable {


    /* ******************************/
    /* Basic Fields Getters/Setters */
    /* ******************************/

    /** Sets the name of this function. */
    public void setName( String name );
    /** Returns the name of this function. */
    public String getName();

    /** Sets the info string of this function. */
    public void setInfo( String info );
    /** Returns the info of this function.  */
    public String getInfo();

    /** Sets the tolerance of this function. */
    public void setTolerance(double newTolerance);
    /** Returns the tolerance of this function.  */
    public double getTolerance();



    /* ******************************/
    /* Metrics about list as whole  */
    /* ******************************/

    /** returns the number of points in this function list */
    public int getNum();

    /** return the minimum x value along the x-axis */
    public double getMinX();

    /** return the maximum x value along the x-axis */
    public double getMaxX();

    /** return the minimum y value along the y-axis */
    public double getMinY();

    /** return the maximum y value along the y-axis */
    public double getMaxY();



    /* ******************/
    /* Point Accessors  */
    /* ******************/

    /** Returns the nth (x,y) point in the Function by index */
    public DataPoint2D get(int index);

    /** Returns the x-value given an index */
    public double getX(int index);

    /** Returns the y-value given an index */
    public double getY(int index);

    /** returns the y-value given an x-value - within tolerance */
    public double getY(double x);

    /**
     * Given the imput y value, finds the two sequential
     * x values with the closest y values, then calculates an
     * interpolated x value for this y value, fitted to the curve. <p>
     *
     * Since there may be multiple y values with the same value, this
     * function just matches the first found starting at the x-min point
     * along the x-axis.
     */
    public double getFirstInterpolatedX(double y);

    /**
     * Given the input x value, finds the two sequential
     * x values with the closest x values, then calculates an
     * interpolated y value for this x value, fitted to the curve.
     */
    public double getInterpolatedY(double x);



    /* ***************************/
    /* Index Getters From Points */
    /* ***************************/

    /**
     * Since the x-axis is sorted and points stored in a list,
     * they can be accessed by index. This function returns the index
     * of the specified x value if found within tolerance, else returns -1.
     */
    public int getXIndex(double x);

    /**
     * Since the x-axis is sorted and points stored in a list,
     * they can be accessed by index. This function returns the index
     * of the specified x value in the DataPoint2D if found withing tolerance,
     * else returns -1.
     */
    public int getIndex(DataPoint2D point);



    /* ***************/
    /* Point Setters */
    /* ***************/

    /** Either adds a new DataPoint, or replaces an existing one, within tolerance */
    public void set(DataPoint2D point) throws DataPoint2DException;

    /**
     * Creates a new DataPoint, then either adds it if it doesn't exist,
     * or replaces an existing one, within tolerance
     */
    public void set(double x, double y) throws DataPoint2DException;

    /** Replaces a DataPoint y-value at the specifed index. */
    public void set(int index, double Y);



    /* **********/
    /* Queries  */
    /* **********/

    /**
     * Determine wheither a point exists in the list,
     * as determined by it's x-value within tolerance.
     */
    public boolean hasPoint(DataPoint2D point);


    /**
     * Determine wheither a point exists in the list,
     * as determined by it's x-value within tolerance.
     */
    public boolean hasPoint(double x, double y);



    /* ************/
    /* Iterators  */
    /* ************/

    /**
     * Returns an iterator over all datapoints in the list. Results returned
     * in sorted order.
     * @return
     */
    public Iterator<DataPoint2D> getPointsIterator();


    /**
     * Returns an iterator over all x-values in the list. Results returned
     * in sorted order.
     * @return
     */
    public ListIterator<Double> getXValuesIterator();


    /**
     * Returns an iterator over all y-values in the list. Results returned
     * in sorted order along the x-axis.
     * @return
     */
    public ListIterator<Double> getYValuesIterator();



    /* **************************/
    /* Standard Java Functions  */
    /* **************************/

    /**
     * Standard java function, usually used for debugging, prints out
     * the state of the list, such as number of points, the value of each point, etc.
     */
    public String toString();

    /**
     * Determines if two lists are equal. Typical implementation would verify
     * same number of points, and the all points are equal, using the DataPoint2D
     * equals() function.
     */
    public boolean equals( DiscretizedFuncAPI function );

    /**
     * This function returns a new copy of this list, including copies
     * of all the points. A shallow clone would only create a new DiscretizedFunc
     * instance, but would maintain a reference to the original points. <p>
     *
     * Since this is a clone, you can modify it without changing the original.
     */
    public DiscretizedFuncAPI deepClone();

    /**
     * This function interpolates the Y values in the log space between x and y values.
     * The Y value returned is in the linear space but the interpolation is done in the log space.
     * @param x : X value in the linear space corresponding to which we are required to find the interpolated
     * y value in log space.
     */
    public double getInterpolatedY_inLogXLogYDomain(double x);

    
    /**
     * This function interpolates the Y values in the log-Y space.
     * The Y value returned is in the linear space.
     * @param x : X value in the linear space corresponding to which we are required to find the interpolated
     * y value in log space.
     */
    public double getInterpolatedY_inLogYDomain(double x);

    /**
     * Given the input y value, finds the two sequential
     * x values with the closest y values, then calculates an
     * interpolated x value for this y value, fitted to the curve.
     * The interpolated Y value returned is in the linear space but
     * the interpolation is done in the log space.
     * Since there may be multiple y values with the same value, this
     * function just matches the first found starting at the x-min point
     * along the x-axis.
     * @param y : Y value in the linear space corresponding to which we are 
     * required to find the interpolated
     * x value in the log space.
     */
    public double getFirstInterpolatedX_inLogXLogYDomain(double y);

    /**
     * prints out the state of the list, such as number of points,
     * the value of each point, etc.
     * @returns value of each point in the function in String format
     */
    public String getMetadataString();

    /**
     * It finds out whether the X values are within tolerance of an integer value
     * @param tolerance tolerance value to consider  rounding errors
     *
     * @return true if all X values are within the tolerance of an integer value
     * else returns false
     */
    public boolean areAllXValuesInteger(double tolerance);
    
    /**
     * Get the Y value for the point with closest X
     * 
     * @param x
     * @return
     */
    public double getClosestY(double x);
    
    /**
     * Get the X value for the point with closest Y
     * 
     * @param y
     * @return
     */
    public double getClosestX(double y);

}
