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

import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.Iterator;
import java.util.ListIterator;
import java.util.Set;

import org.opensha.commons.data.DataPoint2D;
import org.opensha.commons.data.DataPoint2DComparatorAPI;
import org.opensha.commons.data.DataPoint2DToleranceComparator;
import org.opensha.commons.data.DataPoint2DTreeMap;
import org.opensha.commons.exceptions.DataPoint2DException;
import org.opensha.commons.exceptions.InvalidRangeException;

/**
 * <b>Title:</b> ArbitrarilyDiscretizedFunc<p>
 *
 * <b>Description:</b> This class is a sublcass implementation
 * of a DiscretizedFunc that stores the data internaly as a
 * sorted TreeMap of DataPoint2D. This subclass distinguishes itself
 * by the fact that it assumes no spacing interval along the x-axis.
 * Consecutive points can be spread out or bunched up in no predicatable
 * order.  For at least the default comparator (DataPoint2DComparator),
 * the tolerance determines whether the set() methods add the point
 * (if x value is more than tolerance away from that of all existing points)
 * or whether they replace an existing point (if within tolerance).  A tolerance
 * of less than about 1e-16 is effectively about 1e-16 due to the numerical
 * precision of floating point arithmetic (1.0 - (1.0+1e-16) = 1.0). <p>
 *
 * @author Steven W. Rock, Gupta Brothers
 * @version 1.0
 */

public class ArbitrarilyDiscretizedFunc extends DiscretizedFunc
                                        implements Serializable {

	private static final long serialVersionUID = 0xF1E37DA;
    /* Class name Debbuging variables */
    protected final static String C = "ArbitrarilyDiscretizedFunc";

    /* Boolean debugging variable to switch on and off debug printouts */
    protected final static boolean D = true;

    /**
     * The set of DataPoints2D that conprise the discretized function. These
     * are stored in a DataPoint2D TreeMap so they are sorted on the X-Values.<p>
     *
     * This TreeMap will not allow identical DataPoint2D. A comparator and equals()
     * is used to determine equality. Since you can specify any comparator you
     * want, this ArbitrarilyDiscretizedFunc can be adopted for most purposes.<p>
     *
     * Note: SWR: I had to make a special org.opensha. version of the Java TreeMap and
     * subclass DataPoint2DTreeMap to access internal objects in the Java TreeMap.
     * Java's Treemap had internal objects hidden as private, I exposed them
     * to subclasses by making them protected in org.opensha.data.TreeMap. This
     * was neccessary for index access to the points in the TreeMap. Seems like a poor
     * oversight on the part of Java.<p>
     */
    protected DataPoint2DTreeMap points = null;

    private static String TAB = "\t";

    /**
     * Creates an ArbitrarilyDiscretizedFunc from an DiscretizedFunc
     * 
     * @param func
     */
    public ArbitrarilyDiscretizedFunc(DiscretizedFunc func) {
    	this(func.getTolerance());
    	Iterator<DataPoint2D> it = func.getPointsIterator();
    	while (it.hasNext())
    		this.set(it.next());
    	this.setInfo(func.getInfo());
    	this.setName(func.getName());
    	this.setXAxisName(func.getXAxisName());
    	this.setYAxisName(func.getYAxisName());
    }

    /**
     * Constructor that takes a DataPoint2D Comparator. The comparator is used
     * for sorting the DataPoint2D. Using the no-arg constructor instantiates
     * the default Comparator that compares only x-values within tolerance to
     * determine if two points are equal.<p>
     *
     * The passed in comparator must be an implementor of DataPoint2DComparatorAPI.
     * These comparators know they are dealing with a DataPoint2D and usually
     * only compare the x-values for sorting. Special comparators may wish to
     * sort on both the x and y values, i.e. the data points are geographical
     * locations.
     */
    public ArbitrarilyDiscretizedFunc(Comparator comparator) {
        if( !( comparator instanceof DataPoint2DComparatorAPI ) ){
            throw new DataPoint2DException("Comparator must implement DataPoint2DComparatorAPI");
        }
        points = new DataPoint2DTreeMap(comparator);
    }

    /**
     * Constructor that takes a DataPoint2D Comparator. The comparator is used
     * for sorting the DataPoint2D. Using the no-arg constructor instantiates
     * the default Comparator that compares only x-values within tolerance to
     * determine if two points are equal.<p>
     *
     * The passed in comparator must be an implementor of DataPoint2DComparatorAPI.
     * These comparators know they are dealing with a DataPoint2D and usually
     * only compare the x-values for sorting. Special comparators may wish to
     * sort on both the x and y values, i.e. the data points are geographical
     * locations.
     */
    public ArbitrarilyDiscretizedFunc(DataPoint2DComparatorAPI comparator) {
        points = new DataPoint2DTreeMap(comparator);
    }

    /**
     * No-Arg Constructor that uses the default DataPoint2DToleranceComparator comparator.
     * The comparator is used for sorting the DataPoint2D. This default Comparator
     * compares only x-values within tolerance to determine if two points are equal.<p>
     */
    public ArbitrarilyDiscretizedFunc(double toleranace) {
        DataPoint2DToleranceComparator comparator = new DataPoint2DToleranceComparator();
        comparator.setTolerance(tolerance);
        points = new DataPoint2DTreeMap(comparator);
    }

    /**
     * No-Arg Constructor that uses the default DataPoint2DToleranceComparator comparator.
     * The comparator is used for sorting the DataPoint2D. This default Comparator
     * compares only x-values within tolerance to determine if two points are equal.<p>
     *
     * The default tolerance of 0 is used. This means that two x-values must be exactly
     * equal doubles to be considered equal.
     */
    public ArbitrarilyDiscretizedFunc() { points = new DataPoint2DTreeMap(); }



    /**
     * Sets the tolerance of this function. Overides the default function in the
     * abstract class in that it calls setTolerance in the tree map which
     * updates the comparator in there.
     *
     * These field getters and setters provide the basic information to describe
     * a function. All functions have a name, information string,
     * and a tolerance level that specifies how close two points
     * have to be along the x axis to be considered equal.  A tolerance
     * of less than about 1e-16 is effectively about 1e-16 due to the numerical
     * precision of floating point arithmetic (1.0 - (1.0+1e-16) = 1.0).
     */

    public void setTolerance(double newTolerance) throws InvalidRangeException {
        if( newTolerance < 0 )
            throw new InvalidRangeException("Tolerance must be larger or equal to 0");
        tolerance = newTolerance;
        points.setTolerance(newTolerance);
    }

    /** returns the number of points in this function list */
    public int getNum(){ return points.size(); }

     /**
      * return the minimum x value along the x-axis. Since the values
      * are sorted this is a very quick lookup
      */
    public double getMinX(){ return ((DataPoint2D)points.firstKey()).getX(); }
    /**
      * return the maximum x value along the x-axis. Since the values
      * are sorted this is a very quick lookup
      */
    public double getMaxX(){ return ((DataPoint2D)points.lastKey()).getX(); }

    /**
     * Return the minimum y value along the y-axis. This value is calculated
     * every time a DataPoint2D is added to the list and cached as a variable
     * so this function returns very quickly. Slows down adding new points
     * slightly.  I assume that most of the time these lists will be created
     * once, then used for plotting and in other functions, in other words
     * more lookups than inserts.
     */
    public double getMinY(){ return points.getMinY(); }
    /**
     * Return the maximum y value along the y-axis. This value is calculated
     * every time a DataPoint2D is added to the list and cached as a variable
     * so this function returns very quickly. Slows down adding new points
     * slightly.  I assume that most of the time these lists will be created
     * once, then used for plotting and in other functions, in other words
     * more lookups than inserts.
     */
     public double getMaxY(){ return points.getMaxY(); }


    /**
     * Returns the nth (x,y) point in the Function, else null
     * if this index point doesn't exist */
    public DataPoint2D get(int index){ return points.get(index); }


    /** Returns the x value of a point given the index */
    public double getX(int index){ return get(index).getX(); }

    /** Returns the y value of a point given the index */
    public double getY(int index){ return get(index).getY(); }

    /** returns the Y value given an x value - within tolerance, returns null if not found */
    public double getY(double x){ return points.get( x ).getY(); }


    /** returns the Y value given an x value - within tolerance, returns null if not found */
    public int getIndex(DataPoint2D point){ return points.getIndex( point ); }

    /** Returns the x value of a point given the index */
    public int getXIndex(double x){ return points.getIndex( new DataPoint2D(x, 0.0 ) ); }


    /** Either adds a new DataPoint, or replaces an existing one, within tolerance */
    public void set(DataPoint2D point) throws DataPoint2DException{ points.put(point); }

    /**
     * Either adds a new DataPoint, or replaces an existing one, within tolerance,
     * created from the input x and y values.
     */
    public void set(double x, double y) throws DataPoint2DException{ set(new DataPoint2D(x,y)); }


    /**
     * Replaces a y value for an existing point, accessed by index. If no DataPoint exists
     * nothing is done.
     */
    public void set(int index, double y) throws DataPoint2DException{
        DataPoint2D point = get(index);
        if( point != null ) {
            point.setY(y);
            set(point);
        }
    }

    /**
     * Determinces if a DataPoit2D exists in the treemap base on it's x value lookup.
     * Returns true if found, else false if point not in list.
     */
    public boolean hasPoint(DataPoint2D point){
        int index = getIndex(point);
        if( index < 0 ) return false;
        else return true;
    }

    /**
     * Determinces if a DataPoit2D exists in the treemap base on it's x value lookup.
     * Returns true if found, else false if point not in list.
     */
    public boolean hasPoint(double x, double y){
        return hasPoint( new DataPoint2D(x, y) );
    }



    /**
     * Returns an iterator over all datapoints in the list. Results returned
     * in sorted order. Returns null if no points present.
     * @return
     */
    public Iterator<DataPoint2D> getPointsIterator(){
        Set keys = points.keySet();
        if( keys != null ) return keys.iterator();
        else return null;
    }

    /**
     * Returns an iterator over all x-values in the list. Results returned
     * in sorted order. Returns null if no points present.
     * @return
     */
    public ListIterator<Double> getXValuesIterator(){
        ArrayList<Double> list = new ArrayList<Double>();
        int max = points.size();
        for( int i = 0; i < max; i++){
            list.add( new Double(this.getX(i)) );
        }
        return list.listIterator();
    }

    /**
     * Returns an iterator over all y-values in the list. Results returned
     * in sorted order along the x-axis. Returns null if no points present.
     * @return
     */
    public ListIterator<Double> getYValuesIterator(){
        ArrayList<Double> list = new ArrayList<Double>();
        int max = points.size();
        for( int i = 0; i < max; i++){
            list.add( new Double(this.getY(i)));
        }
        return list.listIterator();
    }


    /**
     * Given the imput y value, finds the two sequential
     * x values with the closest y values, then calculates an
     * interpolated x value for this y value, fitted to the curve. <p>
     *
     * Since there may be multiple y values with the same value, this
     * function just matches the first found.
     *
     * @param y(value for which interpolated first x value has to be found
     * @return x(this  is the interpolated x based on the given y value)
     */

    public double getFirstInterpolatedX(double y){
      // finds the size of the point array
      int max=points.size();
      //if Size of the function is 1 and Y value is equal to Y val of function
      //return the only X value
      if (max == 1 && y == getY(0))
        return getX(0);
      double y1=Double.NaN;
      double y2=Double.NaN;
      int i;

      boolean found = false; // this boolean hold whether the passed y value lies within range

      //finds the Y values within which the the given y value lies
      for(i=0;i<max-1;++i) {
        y1=getY(i);
        y2=getY(i+1);
        if((y<=y1 && y>=y2 && y2<=y1) || (y>=y1 && y<=y2 && y2>=y1)) {
          found = true;
          break;
        }
      }

      //if passed parameter(y value) is not within range then throw exception
      if(!found) throw new InvalidRangeException("Y Value ("+y+") must be within the range: "+getY(0)+" and "+getY(max-1));


      //finding the x values for the coressponding y values
      double x1=getX(i);
      double x2=getX(i+1);

      //using the linear interpolation equation finding the value of x for given y
      double x= ((y-y1)*(x2-x1))/(y2-y1) + x1;
      return x;
    }


    /**
     * Given the input y value, finds the two sequential
     * x values with the closest y values, then calculates an
     * interpolated x value for this y value, fitted to the curve.
     * The interpolated Y value returned is in the linear space but
     * the interpolation is done in the log space.
     * Since there may be multiple y values with the same value, this
     * function just matches the first found starting at the x-min point
     * along the x-axis.
     * @param y : Y value in the linear space coressponding to which we are required to find the interpolated
     * x value in the log space.
     * @return x(this  is the interpolated x based on the given y value)
     */
    public double getFirstInterpolatedX_inLogXLogYDomain(double y){
      // finds the size of the point array
      int max=points.size();
      //if Size of the function is 1 and Y value is equal to Y val of function
      //return the only X value
      if (max == 1 && y == getY(0))
        return getX(0);

      double y1=Double.NaN;
      double y2=Double.NaN;
      int i;

      boolean found = false; // this boolean hold whether the passed y value lies within range

      //finds the Y values within which the the given y value lies
      for(i=0;i<max-1;++i) {
        y1=getY(i);
        y2=getY(i+1);
        if((y<=y1 && y>=y2) || (y>=y1 && y<=y2)) {
          found = true;
          break;
        }
      }

      //if passed parameter(y value) is not within range then throw exception
      if(!found) throw new InvalidRangeException("Y Value ("+y+") must be within the range: "+getY(0)+" and "+getY(max-1));

      //finding the x values for the coressponding y values
      double x1=Math.log(getX(i));
      double x2=Math.log(getX(i+1));
      y1= Math.log(y1);
      y2= Math.log(y2);
      y= Math.log(y);

      //using the linear interpolation equation finding the value of x for given y
      double x= ((y-y1)*(x2-x1))/(y2-y1) + x1;
      return Math.exp(x);
    }



    /**
     * Given the imput x value, finds the two sequential
     * x values with the closest x values, then calculates an
     * interpolated y value for this x value, fitted to the curve.
     *
     * @param x(value for which interpolated first y value has to be found
     * @return y(this  is the interpolated x based on the given x value)
     */
    public double getInterpolatedY(double x){
    // finds the size of the point array
       int max=points.size();
       double x1=Double.NaN;
       double x2=Double.NaN;
       //if passed parameter(x value) is not within range then throw exception
       if(x>getX(max-1) || x<getX(0))
          throw new InvalidRangeException("x Value must be within the range: "+getX(0)+" and "+getX(max-1));
      //if x value is equal to the maximum value of all given X's then return the corresponding Y value
       if(x==getX(max-1))
         return getY(x);
      //finds the X values within which the the given x value lies
       for(int i=0;i<max-1;++i) {
         x1=getX(i);
         x2=getX(i+1);
        if(x>=x1 && x<=x2)
           break;
       }
       //finding the y values for the coressponding x values
       double y1=getY(x1);
       double y2=getY(x2);
       //using the linear interpolation equation finding the value of y for given x
       double y= ((y2-y1)*(x-x1))/(x2-x1) + y1;
       return y;
    }

    /**
     * This function interpolates the y-axis value corresponding to the given value of x.
     * the interpolation of the Y value is done in the log space for x and y values.
     * The Y value returned is in the linear space but the interpolation is done in the log space.  If 
     * both bounding y values are zero, then zero is returned.  If only one of the bounding y values is zero,
     * that value is converted to Double.MIN_VALUE.  If the interpolated y value is Double.MIN_VALUE, it 
     * is converted to 0.0.
     * @param x : X value in the linear space corresponding to which we are required to find the interpolated
     * y value in log space.
     * @return y(this  is the interpolated y in linear space based on the given x value)
     */
    public double getInterpolatedY_inLogXLogYDomain(double x){
      // finds the size of the point array
      int max=points.size();
      double x1=Double.NaN;
      double x2=Double.NaN;
      //if passed parameter(x value) is not within range then throw exception
      if(x>getX(max-1) || x<getX(0))
        throw new InvalidRangeException("x Value must be within the range: "+getX(0)+" and "+getX(max-1));
      //if x value is equal to the maximum value of all given X's then return the corresponding Y value
      if(x==getX(max-1))
        return getY(x);
      //finds the X values within which the the given x value lies
      for(int i=0;i<max-1;++i) {
        x1=getX(i);
        x2=getX(i+1);
        if(x>=x1 && x<=x2)
          break;
      }
      //finding the y values for the coressponding x values
      double y1 = getY(x1);
      double y2 = getY(x2);
      if(y1==0 && y2==0) return 0;
      if(y1==0) y1 = Double.MIN_VALUE;
      if(y2==0) y2 = Double.MIN_VALUE;
      double logY1=Math.log(y1);
      double logY2=Math.log(y2);
      x1 = Math.log(x1);
      x2 = Math.log(x2);
      x = Math.log(x);
      //using the linear interpolation equation finding the value of y for given x
      double y= ((logY2-logY1)*(x-x1))/(x2-x1) + logY1;
      double expY = Math.exp(y);
      if (expY == Double.MIN_VALUE) expY = 0.0;
      return expY;
    }
    
 /*  THIS WAS FOR DEBUGGING WHERE ERRORS OCCURRED IF ONLY ONE Y-VALUE WAS 0.0
    public double getInterpolatedY_inLogXLogYDomain(double x, boolean debug){
        // finds the size of the point array
        int max=points.size();
        double x1=Double.NaN;
        double x2=Double.NaN;
        //if passed parameter(x value) is not within range then throw exception
        if(x>getX(max-1) || x<getX(0))
          throw new InvalidRangeException("x Value must be within the range: "+getX(0)+" and "+getX(max-1));
        //if x value is equal to the maximum value of all given X's then return the corresponding Y value
        if(x==getX(max-1))
          return getY(x);
        //finds the X values within which the the given x value lies
        for(int i=0;i<max-1;++i) {
          x1=getX(i);
          x2=getX(i+1);
          if(x>=x1 && x<=x2)
            break;
        }
        //finding the y values for the coressponding x values
        double y1 = getY(x1);
        double y2 = getY(x2);
        if(y1==0 && y2==0) return 0;
        if(y1==0) y1 = Double.MIN_VALUE;
        if(y2==0) y2 = Double.MIN_VALUE;
        double logY1=Math.log(y1);
        double logY2=Math.log(y2);
if(debug) {
	System.out.println("tol="+this.tolerance);
	System.out.print(x1+"\t"+x2+"\t"+x+"\t");
}
        x1 = Math.log(x1);
        x2 = Math.log(x2);
        x = Math.log(x);
        //using the linear interpolation equation finding the value of y for given x
        double y= ((logY2-logY1)*(x-x1))/(x2-x1) + logY1;
        double expY = Math.exp(y);
        if (expY == Double.MIN_VALUE) expY = 0.0;
if(debug) {
    System.out.println(y1+"\t"+y2+"\t"+logY1+"\t"+logY2+"\t"+x1+"\t"+x2+"\t"+x+
    		"\t"+y+"\t"+Math.exp(x1)+"\t"+Math.exp(x2)+"\t"+Math.exp(x)+"\t"+expY+"\t"+Double.MIN_VALUE);
        }

		return expY;

      }
*/

    /**
     * This function interpolates the y-axis value corresponding to the given value of x.
     * the interpolation of the Y value is done in the log-y space.
     * The Y value returned is in the linear space.
     * @param x : X value in the linear space corresponding to which we are required to find the interpolated
     * y value in log space.
     * @return y(this  is the interpolated y in linear space based on the given x value)
     */
    public double getInterpolatedY_inLogYDomain(double x){
      // finds the size of the point array
      int max=points.size();
      double x1=Double.NaN;
      double x2=Double.NaN;
      //if passed parameter(x value) is not within range then throw exception
      if(x>getX(max-1) || x<getX(0))
        throw new InvalidRangeException("x Value must be within the range: "+getX(0)+" and "+getX(max-1));
      //if x value is equal to the maximum value of all given X's then return the corresponding Y value
      if(x==getX(max-1))
        return getY(x);
      //finds the X values within which the the given x value lies
      for(int i=0;i<max-1;++i) {
        x1=getX(i);
        x2=getX(i+1);
        if(x>=x1 && x<=x2)
          break;
      }
      //finding the y values for the coressponding x values
      double y1 = getY(x1);
      double y2 = getY(x2);
      if(y1==0 && y2==0) return 0;
      double logY1=Math.log(y1);
      double logY2=Math.log(y2);
      //using the linear interpolation equation finding the value of y for given x
      double y= ((logY2-logY1)*(x-x1))/(x2-x1) + logY1;
      return Math.exp(y);
    }

    private double extrapolate(double x1, double x2, double y1, double y2,
    		double x) {
    	// Create the linear regression function (slope and intercept)
    	//System.out.printf("\textrapolating(%f, %f, %f, %f, %f)\n",
    	//		x1, x2, y1, y2, x);
    	double slope = (y2 - y1) / (x2 - x1);
    	double intercept = y1 - (slope * x1);
    	//System.out.printf("\tSlope is: %f\tIntercept is: %f\n",
    	//		slope, intercept);
    	return (slope * x) + intercept;
    }
    
    public double getInterpExterpY_inLogYDomain(double x) {
    	try {
    		double v =  getInterpolatedY_inLogYDomain(x);
    		//System.err.println("interpolating(" + x + ")...");
    		return v;
    	} catch (InvalidRangeException irx) {
    		//System.err.println("extrapolating(" + x + ")...");
    		// We gotta extrapolate...
    		if(x < getX(0)) {
    			return Math.exp(extrapolate(getX(0), getX(1), Math.log(getY(0)),
    					Math.log(getY(1)), x));
    		} else {
    			int max = points.size();
    			return Math.exp(extrapolate(getX(max-2), getX(max-1),
    					Math.log(getY(max-2)), Math.log(getY(max-1)), x));
    		}
    	}
    }

    /**
     * This function returns a new copy of this list, including copies
     * of all the points. A shallow clone would only create a new DiscretizedFunc
     * instance, but would maintain a reference to the original points. <p>
     *
     * Since this is a clone, you can modify it without changing the original.
     * @return
     */
    public ArbitrarilyDiscretizedFunc deepClone(){

        ArbitrarilyDiscretizedFunc function = new ArbitrarilyDiscretizedFunc(  );
        function.setName(getName());
        function.setTolerance( getTolerance() );
        function.setInfo(getInfo());
        function.setXAxisName(this.getXAxisName());
        function.setYAxisName(this.getYAxisName());
        Iterator it = this.getPointsIterator();
        if( it != null ) {
            while(it.hasNext()) {
                function.set( (DataPoint2D)((DataPoint2D)it.next()).clone() );
            }
        }

        return function;

    }

    /**
     * Determines if two functions are the same by comparing
     * that each point x value is the same. This requires
     * the two lists to have the same number of points.
     */
    public boolean equalXValues(DiscretizedFuncAPI function){
        // String S = C + ": equalXValues():";
        if( this.getNum() != function.getNum() ) return false;
        Iterator it = this.getPointsIterator();
        while(it.hasNext()) {
            DataPoint2D point = (DataPoint2D)it.next();
            if( !function.hasPoint( point ) ) return false;
        }
        return true;

    }



    /**
     * Standard java function, usually used for debugging, prints out
     * the state of the list, such as number of points, the value of each point, etc.
     * @return
     */
    public String toString(){
      StringBuffer b = new StringBuffer();

      b.append("Name: " + getName() + '\n');
      b.append("Num Points: " + getNum() + '\n');
      b.append("Info: " + getInfo() + "\n\n");
      b.append("X, Y Data:" + '\n');
      b.append(getMetadataString()+ '\n');
      return b.toString();
    }

    /**
     *
     * @returns value of each point in the function in String format
     */
    public String getMetadataString(){
      StringBuffer b = new StringBuffer();
      Iterator it2 = this.getPointsIterator();

      while(it2.hasNext()){

        DataPoint2D point = (DataPoint2D)it2.next();
        double x = point.getX();
        double y = point.getY();
        b.append((float) x + TAB + (float) y + '\n');
      }
      return b.toString();
    }

    /**
     * Almost the same as toString() but used
     * specifically in a debugging context. Formatted slightly different
     * @return
     */
    public String toDebugString(){

        StringBuffer b = new StringBuffer();
        b.append(C + ": Log values:\n");
        Iterator it = this.getPointsIterator();
        while(it.hasNext()) {

            DataPoint2D point = (DataPoint2D)it.next();
            b.append( point.toString() + '\n');

        }


        return b.toString();
    }

    /**
     * This method creates serialized Outputstream for the DataPoint2D
     * @param s
     */
    private void writeObject(ObjectOutputStream s){
      Iterator it =getPointsIterator();
      try{
        s.writeObject(new Integer(getNum()));
        while(it.hasNext()){
          DataPoint2D data = (DataPoint2D)it.next();
          //System.out.println("Data: "+data.toString());
          s.writeObject(data);
        }
      }catch(IOException e){
        e.printStackTrace();
      }
    }

    /**
     * This method deserialises InputStream for the DataPoint2D
     * @param s
     */
    private void readObject(ObjectInputStream s){
      try{
        if(points == null)
          points = new DataPoint2DTreeMap();
        int num = ((Integer)s.readObject()).intValue();
        for(int i=0;i<num;++i){
          DataPoint2D data = (DataPoint2D)s.readObject();
          set(data);
        }
        //System.out.println("Data Object read: "+data.toString());
      }catch(ClassNotFoundException e){
        System.out.println("Class not found");
        e.printStackTrace();
      }catch(IOException e){
        System.out.println("IO Exception ");
        e.printStackTrace();
      }
    }


    /**
     * This function creates a new ArbitrarilyDiscretizedFunc whose X values are the
     * Y values of the calling function and Y values are the Y values of the function
     * passed as argument.
     * @param function DiscretizedFuncAPI function whose Y values will the Y values
     * of the new ArbitrarilyDiscretizedFunc.
     * @return ArbitrarilyDiscretizedFunc new ArbitrarilyDiscretizedFunc
     */
    public ArbitrarilyDiscretizedFunc getYY_Function(DiscretizedFuncAPI function){

      if(getNum() !=function.getNum())
        throw new InvalidRangeException("This operation cannot be performed on functions "+
      "with different size");

      ArbitrarilyDiscretizedFunc newFunction = new ArbitrarilyDiscretizedFunc();
      int numPoints = function.getNum();
      for(int j=0;j<numPoints;++j)
        newFunction.set(getY(j),function.getY(j));

      return newFunction;
    }


    /**
     * It finds out whether the X values are within tolerance of an integer value
     * @param tol tolerance value to consider  rounding errors
     *
     * @return true if all X values are within the tolerance of an integer value
     * else returns false
     */
    public boolean areAllXValuesInteger(double tolerance) {
      int num = getNum();
      double x, diff;
      for (int i = 0; i < num; ++i) {
        x = getX(i);
        diff = Math.abs(x - Math.rint(x));
        if (diff > tolerance) return false;
      }
      return true;
    }

    /**
     * Clear all the X and Y values from this function
     */
    public void clear() {
      points.clear();
    }

    public double[] getXVals() {
		double[] d = new double[points.size()];
		for (int i = 0; i < points.size(); ++i) {
			d[i] = getX(i);
		}
		return d;
	}

	public double[] getYVals() {
		double[] d = new double[points.size()];
		for (int i = 0; i < points.size(); ++i) {
			d[i] = getY(i);
		}
		return d;
	}
    /*  temp main method to investige numerical precision issues
public static void main( String[] args ) {

  ArbitrarilyDiscretizedFunc func = new ArbitrarilyDiscretizedFunc();
//  func.setTolerance(Double.MIN_VALUE);
  func.set(1.0,0);
  func.set(Double.MIN_VALUE,0);
  func.set(1+1e-16,1);
  func.set(1+2e-16,2);
  func.set(1+3e-16,3);
  func.set(1+4e-16,4);
  func.set(1+5e-16,5);
  func.set(1+6e-16,6);
  func.set(1+7e-16,7);
  func.set(1+8e-16,8);
  func.set(1+9e-16,9);
  func.set(1+10e-16,10);
  Iterator it = func.getPointsIterator();
  DataPoint2D point;
  while( it.hasNext()) {
    point = (DataPoint2D) it.next();
    System.out.println(point.getX()+"  "+point.getY());
  }
}

*/

    /*
    public void rebuild(){

        // make temporary storage
        ArrayList points = new ArrayList();

        // get all points
        Iterator it = getPointsIterator();
        if( it != null ) while(it.hasNext()) { points.add( (DataPoint2D)it.next() ); }

        // get all non-log points if any
        it = getNonLogPointsIterator();
        if( it != null ) while(it.hasNext()) { points.add( (DataPoint2D)it.next() ); }

        // clear permanent storage
        points.clear();
        nonPositivepoints.clear();

        // rebuild permanent storage
        it = points.listIterator();
        if( it != null ) while(it.hasNext()) { set( (DataPoint2D)it.next() ); }

        if( D ) System.out.println("rebuild: " + toDebugString());
        points = null;
    }

    public boolean isYLog() { return yLog; }
    public void setYLog(boolean yLog) {

        if( yLog != this.yLog ) {
            this.yLog = yLog;
            rebuild();
        }
    }

    public boolean isXLog() { return xLog; }
    public void setXLog(boolean xLog) {
        if( xLog != this.xLog ) {
            this.xLog = xLog;
            rebuild();
        }
    }

    */


}
