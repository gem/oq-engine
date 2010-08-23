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

import java.util.ArrayList;
import java.util.Iterator;
import java.util.ListIterator;

import org.opensha.commons.data.DataPoint2D;
import org.opensha.commons.exceptions.DataPoint2DException;
import org.opensha.commons.exceptions.DiscretizedFuncException;
import org.opensha.commons.exceptions.InvalidRangeException;


/**
 * <b>Title:</b> EvenlyDiscretizedFunc<p>
 *
 * <b>Description:</b> Subclass of DiscretizedFunc and full implementation of
 * DiscretizedFuncAPI. Assumes even spacing between the x points represented by
 * the delta distance. Y Values are stored as doubles in an array of primitives. This
 * allows replacement of values at specified indexes.<p>
 *
 * Note that the basic unit for this function framework are DataPoint2D which contain
 * x and y values. Since the x-values are evenly space there are no need to store
 * them. They can be calculated on the fly based on index. So the internal storage
 * saves space by only saving the y values, and reconstituting the DataPoint2D values
 * as needed. <p>
 *
 * Since the x values are not stored, what is stored instead is the x-min value, x-max value,
 * and the delta spacing between x values. This is enough to calculate any x-value by
 * index.<p>
 *
 * This function can be used to generate histograms. To do that, tolerance should be set greater 
 * than delta.  Add methods should then be used to add to Y values for histograms. 
 * The x value is the mid-point of the histogram interval<p>
 * 
 * 
 * @author Steven W. Rock
 * @version 1.0
 */

public class EvenlyDiscretizedFunc extends DiscretizedFunc{

	private static final long serialVersionUID = 0xC4E0D3D;

    /** Class name used for debbuging */
    protected final static String C = "EvenlyDiscretizedFunc";

    /** if true print out debugging statements */
    protected final static boolean D = false;

    /** The internal storage collection of points, stored as a linked list */
    protected double points[];

    /** The minimum x-value in this series, pins the index values with delta */
    protected double minX=Double.NaN;

    /** The maximum x-value in this series */
    protected double maxX=Double.NaN;

    /** Distance between x points */
    protected double delta=Double.NaN;

    /** Number of points in this function */
    protected int num;

    /**
     * Helper boolean that indicates no values have been put
     * into this function yet. Used only internally.
     */
    protected boolean first = true;


    /**
     * This is one of two constructor options
     * to fully quantify the domain of this list, i.e.
     * the x-axis.
     *
     * @param min   - Starting x value
     * @param num   - number of points in list
     * @param delta - distance between x values
     */
    public EvenlyDiscretizedFunc(double min, int num, double delta) {

        set(min, num, delta);
    }


    /**
     * Fully quantify the domain of this list, i.e.
     * the x-axis. This function clears the list of points
      * previously in this function
     *
     * @param min   - Starting x value
     * @param num   - number of points in list
     * @param delta - distance between x values
     */

    public void set(double min, int num, double delta) {
      set(min, min + (num-1)*delta, num);
    }


    /**
     * The other three input options to fully quantify the domain
     * of this list, i.e. the x-axis.
     *
     * @param min   - Starting x value
     * @param num   - number of points in list
     * @param max - Ending x value
     */
    public EvenlyDiscretizedFunc(double min, double max, int num) {
      this.set(min, max, num);
    }

    /**
      * Three input options to fully quantify the domain
      * of this list, i.e. the x-axis. This function clears the list of points
      * previously in this function
      *
      * @param min   - Starting x value
      * @param num   - number of points in list
      * @param max - Ending x value
      */

    public void set(double min, double max, int num) {
      if (num <= 0)
        throw new DiscretizedFuncException("num points must be >= 0");

      if (num == 1 && min != max)
        throw new DiscretizedFuncException("min must equal max if num points = 1");

      if (min > max)
        throw new DiscretizedFuncException("min must be less than max");
      else if (min < max)
        delta = (max - min) / (num - 1);
      else { // max == min
        if (num == 1)
          delta = 0;
        else
          throw new DiscretizedFuncException("num must = 1 if min = max");
      }

      this.minX = min;
      this.maxX = max;
      this.num = num;

      points = new double[num];
    }

    /** Sets all y values to NaN */
    public void clear(){ for( int i = 0; i < num; i++){ points[i] = Double.NaN; } }

    /**
     * Returns true if two values are within tolerance to
     * be considered equal. Used internally
     */
    protected boolean withinTolerance(double x, double xx){
        if( Math.abs( x - xx)  <= this.tolerance) return true;
        else return false;
    }


   /** Returns the spacing between x-values */
    public double getDelta() { return delta; }

    /** Returns the number of points in this series */
    public int getNum(){ return num; }


    /**
     * Returns the minimum x-value in this series. Since the value is
     * stored, lookup is very quick
     */
    public double getMinX(){ return minX; }

    /**
     * Returns the maximum x-value in this series. Since the value is
     * stored, lookup is very quick
     */
    public double getMaxX(){ return maxX; }


    /**
     * Returns the minimum y-value in this series. Since the value could
     * appear aywhere along the x-axis, each point needs to be
     * examined, lookup is slower the larger the dataset. <p>
     *
     * Note: An alternative would be to check for the min value every time a
     * point is inserted and store the miny value. This would only slightly slow down
     * the insert, but greatly speed up the lookup. <p>
     */
    public double getMinY(){
        double minY = Double.POSITIVE_INFINITY;
        for(int i = 0; i<num; ++i)
            if(points[i] < minY) minY = points[i];
        return minY;
    }

    /**
     * Returns the maximum y-value in this series. Since the value could
     * appear aywhere along the x-axis, each point needs to be
     * examined, lookup is slower the larger the dataset. <p>
     *
     * Note: An alternative would be to check for the min value every time a
     * point is inserted and store the miny value. This would only slightly slow down
     * the insert, but greatly speed up the lookup. <p>
     */
    public double getMaxY(){
        double maxY = Double.NEGATIVE_INFINITY;
        for(int i = 0; i<num; ++i)
            if(points[i] > maxY) maxY = points[i];
        return maxY;
    }


    /**
     * Returns an x and y value in a DataPoint2D based on index
     * into the y-points array.  The index is based along the x-axis.
     */
    public DataPoint2D get(int index){
        return new DataPoint2D(getX(index), getY(index));
    }

    /**
     * Returns the ith x element in this function. Returns null
     * if index is negative or greater than number of points.
     * The index is based along the x-axis.
     */
    public double getX(int index){
        if( index < 0 || index > ( num -1 ) ) return Double.NaN;
        else return ( minX + delta * index );
    }

    /**
     * Returns the ith y element in this function. Returns null
     * if index is negative or greater than number of points.
     * The index is based along the x-axis.
     */
    public double getY(int index){
        if( index < 0 || index > ( num -1 ) ) return Double.NaN;
        return points[index];
    }

    /**
     * Returns they-value associated with this x-value. First
     * the index of the x-value is calculated, within tolerance.
     * Then they value is obtained by it's index into the storage
     * array. Returns null if x is not one of the x-axis points.
     */
    public double getY(double x){ return getY( getXIndex( x) ); }

    /**
     * Returns the index of the supplied value provided it's within the tolerance
     * of one of the dicretized values.
     */
    public int getXIndex( double x) throws DataPoint2DException{

        int i = Math.round((float)((x-minX)/delta));
        if( withinTolerance(x, this.getX(i) ))
          return i;
        else
          throw new DataPoint2DException(C + ": set(): This point doesn't match a permitted x value.");
/*
        // Steve's old approach:

        double xx = x;              // Why this?
        double xxMin = this.minX;   // Why this?

        for( int i = 0; i < num; i++){
            if( withinTolerance(xx, ( xxMin + i*delta ) ) ) return i;
        }
       throw new DataPoint2DException(C + ": set(): This point doesn't match a permitted x value.");
*/
    }

   /**
     * Calls set( x value, y value ). A DataPoint2DException is thrown
     * if the x value is not an x-axis point.
     */
    public void set(DataPoint2D point) throws DataPoint2DException {

        set( point.getX(), point.getY());
    }

    /**
     * Sets the y-value at a specified index. The x-value index is first
     * calculated, then the y-value is set in it's array. A
     * DataPoint2DException is thrown if the x value is not an x-axis point.
     */
    public void set(double x, double y) throws DataPoint2DException {
        int index = getXIndex( x );
        points[index] = y;
    }
    
    /**
     * This method can be used for generating histograms if tolerance is set greater than delta.
     * Adds to the y-value at a specified index. The x-value index is first
     * calculated, then the y-value is added in it's array.  
     * The specified x value is the mid-point of the histogram interval.
     * 
     * DataPoint2DException is thrown if the x value is not an x-axis point.
     */
    public void add(double x, double y) throws DataPoint2DException {
        int index = getXIndex( x );
        points[index] = y+points[index];
    }

    /**
     * this function will throw an exception if the index is not
     * within the range of 0 to num -1
     */
    public void set(int index, double y) throws DataPoint2DException {
        if( index < 0 || index > ( num -1 ) ) {
            throw new DataPoint2DException(C + ": set(): The specified index doesn't match this function domain.");
        }
        points[index] = y;
    }
    
    /**
     * This method can be used for generating histograms if tolerance is set greater than delta.
     * Adds to the y-value at a specified index. The specified x value is the mid-point of the histogram interval.
     * 
     * this function will throw an exception if the index is not
     * within the range of 0 to num -1
     */
    public void add(int index, double y) throws DataPoint2DException {
        if( index < 0 || index > ( num -1 ) ) {
            throw new DataPoint2DException(C + ": set(): The specified index doesn't match this function domain.");
        }
        points[index] = y+points[index];
    }
    

    /**
     * This function may be slow if there are many points in the list. It has to
     * reconstitute all the DataPoint2D x-values by index, only y values are stored
     * internally in this function type. A DataPoint2D is built for each y value and
     * added to a local ArrayList. Then the iterator of the local ArrayList is returned.
     */
    public Iterator getPointsIterator(){
        ArrayList<DataPoint2D> list = new ArrayList<DataPoint2D>();
        for( int i = 0; i < num; i++){
            list.add( new DataPoint2D( getX(i), getY(i) ) );
        }
        return list.listIterator();
    }

    /**
     * This returns an iterator over x values as Double objects
     */
    public ListIterator getXValuesIterator(){
        ArrayList<Double> list = new ArrayList<Double>();
        for( int i = 0; i < num; i++){ list.add(new Double(getX(i))); }
        return list.listIterator();
    }

    /**
     * This returns an iterator over y values as Double objects
     */
    public ListIterator getYValuesIterator(){
        ArrayList<Double> list = new ArrayList<Double>();
        for( int i = 0; i < this.num; i++){ list.add(new Double(getY(i))); }
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
         double y1=Double.NaN;
         double y2=Double.NaN;
         int i;


         //if Size of the function is 1 and Y value is equal to Y val of function
         //return the only X value
         if(num == 1 && y == getY(0))
           return getX(0);

         boolean found = false; // this boolean hold whether the passed y value lies within range

         //finds the Y values within which the the given y value lies
         for(i=0;i<num-1;++i) {
           y1=getY(i);
           y2=getY(i+1);
           if((y<=y1 && y>=y2 && y2<=y1) || (y>=y1 && y<=y2 && y2>=y1)) {
             found = true;
             break;
           }
         }

         //if passed parameter(y value) is not within range then throw exception
         if(!found) throw new InvalidRangeException("Y Value ("+y+") must be within the range: "+getY(0)+" and "+getY(num-1));


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
         double y1=Double.NaN;
         double y2=Double.NaN;
         int i;

         //if Size of the function is 1 and Y value is equal to Y val of function
         //return the only X value
         if(num == 1 && y == getY(0))
           return getX(0);


         boolean found = false; // this boolean hold whether the passed y value lies within range

         //finds the Y values within which the the given y value lies
         for(i=0;i<num-1;++i)
         {
           y1=getY(i);
           y2=getY(i+1);
           if((y<=y1 && y>=y2 && y2<=y1) || (y>=y1 && y<=y2 && y2>=y1)) {
             found = true;
             break;
           }
         }

         //if passed parameter(y value) is not within range then throw exception
         if(!found) throw new InvalidRangeException("Y Value ("+y+") must be within the range: "+getY(0)+" and "+getY(num-1));


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
        * This function interpolates the y-axis value corresponding to the given value of x
        * @param x(value for which interpolated first y value has to be found
        * @return y(this  is the interpolated y based on the given x value)
        */
       public double getInterpolatedY(double x){
       double x1=Double.NaN;
       double x2=Double.NaN;
       //if passed parameter(x value) is not within range then throw exception
       if(x>getX(num-1) || x<getX(0))
          throw new InvalidRangeException("x Value ("+x+") must be within the range: "+getX(0)+" and "+getX(num-1));
      //finds the X values within which the the given x value lies
       for(int i=0;i<num-1;++i) {
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
     * The Y value returned is in the linear space but the interpolation is done in the log space.
     * @param x : X value in the linear space corresponding to which we are required to find the interpolated
     * y value in log space.
     * @return y(this  is the interpolated y in linear space based on the given x value)
     */
    public double getInterpolatedY_inLogXLogYDomain(double x){
       double x1=Double.NaN;
       double x2=Double.NaN;
       //if passed parameter(x value) is not within range then throw exception
       if(x>getX(num-1) || x<getX(0))
          throw new InvalidRangeException("x Value must be within the range: "+getX(0)+" and "+getX(num-1));
      //finds the X values within which the the given x value lies
       for(int i=0;i<num-1;++i) {
         x1=getX(i);
         x2=getX(i+1);
        if(x>=x1 && x<=x2)
           break;
       }
       //finding the y values for the coressponding x values
       double y1=Math.log(getY(x1));
       double y2=Math.log(getY(x2));
       x1 = Math.log(x1);
       x2 = Math.log(x2);
       x = Math.log(x);
       //using the linear interpolation equation finding the value of y for given x
       double y= ((y2-y1)*(x-x1))/(x2-x1) + y1;
       return Math.exp(y);
    }


    /**
     * This function interpolates the y-axis value corresponding to the given value of x.
     * the interpolation of the Y value is done in the log space y values.
     * The Y value returned is in the linear space but the interpolation is done in the log space.
     * @param x : X value in the linear space corresponding to which we are required to find the interpolated
     * y value in log space.
     * @return y(this  is the interpolated y in linear space based on the given x value)
     */
    public double getInterpolatedY_inLogYDomain(double x){
       double x1=Double.NaN;
       double x2=Double.NaN;
       //if passed parameter(x value) is not within range then throw exception
       if(x>getX(num-1) || x<getX(0))
          throw new InvalidRangeException("x Value must be within the range: "+getX(0)+" and "+getX(num-1));
      //finds the X values within which the the given x value lies
       for(int i=0;i<num-1;++i) {
         x1=getX(i);
         x2=getX(i+1);
        if(x>=x1 && x<=x2)
           break;
       }
       //finding the y values for the coressponding x values
       double y1=Math.log(getY(x1));
       double y2=Math.log(getY(x2));
       //using the linear interpolation equation finding the value of y for given x
       double y= ((y2-y1)*(x-x1))/(x2-x1) + y1;
       return Math.exp(y);
    }



    /** Returns a copy of this and all points in this DiscretizedFunction.
     *  A copy, or clone has all values the same, but is a different java class
     *  instance. That means you can change the copy without affecting the original
     *  instance. <p>
     *
     * This is a deep clone so all fields and all data points are copies. <p>
     */
    public DiscretizedFuncAPI deepClone(){

        EvenlyDiscretizedFunc f = new EvenlyDiscretizedFunc(
            minX, num, delta
        );

        f.info = info;
        f.minX = minX;
        f.maxX = maxX;
        f.name = name;
        f.tolerance = tolerance;
        f.setInfo(this.getInfo());
        f.setName(this.getName());
        for(int i = 0; i<num; i++)
            f.set(i, points[i]);

        return f;
    }


    /**
     * Determines if two functions are the same by comparing
     * that each point x value is the same, within tolerance
     */
    public boolean equalXValues(DiscretizedFuncAPI function){
        //String S = C + ": equalXValues():";

        if( !(function instanceof EvenlyDiscretizedFunc ) ) return false;
        if( num != function.getNum() ) return false;


        double min = minX;
        double min1 = ((EvenlyDiscretizedFunc)function).getMinX();
        if( !withinTolerance( min, min1 ) ) return false;

        double d = delta;
        double d1 = ((EvenlyDiscretizedFunc)function).getDelta();
        if( d != d1 ) return false;

        return true;

    }

    /**
    * It finds out whether the X values are within tolerance of an integer value
    * @param tol tolerance value to consider  rounding errors
    *
    * @return true if all X values are within the tolerance of an integer value
    * else returns false
    */
   public boolean areAllXValuesInteger(double tolerance) {

     double diff;
     // check that min X and delta are integer values
     diff = Math.abs(minX - Math.rint(minX));
     if (diff > tolerance) return false;
     diff = Math.abs(delta - Math.rint(delta));
     if (diff > tolerance) return false;
     return true;

   }



    /**
     * Determines if two functions are the same by comparing
     * that each point x value is the same, within tolerance,
     * and that each y value is the same, including nulls.
     */
    public boolean equalXAndYValues(DiscretizedFuncAPI function){
        //String S = C + ": equalXAndYValues():";

        if( !equalXValues(function) ) return false;

        for( int i = 0; i < num; i++){

            double y1 = getY(i);
            double y2 = function.getY(i);

            if( y1 == Double.NaN &&  y2 != Double.NaN ) return false;
            else if( y2 == Double.NaN &&  y1 != Double.NaN ) return false;
            else if( y1 != y2 ) return false;

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
      //Iterator it2 = this.getPointsIterator();

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
        b.append((float) x + "\t  " + (float) y + '\n');
      }
      return b.toString();
    }

    /**
     * Returns true if the x value is withing tolerance of an x-value in this list,
     * and the y value is equal to y value in the list.
     */
    public boolean hasPoint(DataPoint2D point){
        return hasPoint(point.getX(),point.getY());
    }

    /**
    * Returns true if the x value is withing tolerance of an x-value in this list,
    * and the y value is equal to y value in the list.
     */
    public boolean hasPoint(double x, double y){
      try {
        int index = getXIndex( x );
        double yVal = this.getY(index);
        if( yVal == Double.NaN || yVal!=y) return false;
          return true;
      } catch(DataPoint2DException e) {
          return false;
      }
    }

     /** Returns the index of this DataPoint based on it's x any y value
      *  both the x-value and y-values in list should match with that of point
      * returns -1 if there is no such value in the list
      * */
     public int getIndex(DataPoint2D point){
       try {
         int index= getXIndex( point.getX() );
         if (index < 0) return -1;
         double y = this.getY(index);
         if(y!=point.getY()) return -1;
         return index;
       }catch(DataPoint2DException e) {
          return -1;
       }
    }
     
     public static void main(String args[]) {
    	 EvenlyDiscretizedFunc func = new EvenlyDiscretizedFunc(5.0,9.0, 41);
    	 func.setTolerance(func.getDelta()/2);
    	 System.out.println(func.getXIndex(8.899999999999999));
     }

}
