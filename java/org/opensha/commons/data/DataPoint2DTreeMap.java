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

import java.util.Collection;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.Hashtable;
import java.util.Map;
import java.util.Set;

import org.opensha.commons.exceptions.InvalidRangeException;



/**
 *  <b>Title:</b> DataPoint2DTreeMap <p>
 *
 *  <b>Description:</b> Special Tree map that holds DataPoint2D as the key, so
 *  they are automatically sorted on the X-Coordinate. The reason for this
 *  subclass is to handle tolerances in the x-value when calling put(), get(),
 *  etc. The tolerance indicates how far apart two DataPoint2Ds can be in the
 *  X-Coordinate and still be considered equal. A tolerance of less than about
 *  1e-16 is effectively about 1e-16 due to the numerical precision of floating
 *  point arithmetic (1.0 - (1.0+1e-16) = 1.0). <P>
 *
 *  This class also provides a get(int index) method to get one of the
 *  DataPoints2D by it's location in the map. This is the whole purpose that we
 *  had to reimplement the TreeMap in this package instead of using the
 *  java.util.TreeMap<P>
 *
 *  Java's offical Description for TreeMap<P>
 *
 *  Red-Black tree based implementation of the <tt>SortedMap</tt> interface.
 *  This class guarantees that the map will be in ascending key order, sorted
 *  according to the <i>natural order</i> for the key's class (see <tt>
 *  Comparable</tt> ), or by the comparator provided at creation time, depending
 *  on which constructor is used.<p>
 *
 *  This implementation provides guaranteed log(n) time cost for the <tt>
 *  containsKey</tt> , <tt>get</tt> , <tt>put</tt> and <tt>remove</tt>
 *  operations. Algorithms are adaptations of those in Cormen, Leiserson, and
 *  Rivest's <I>Introduction to Algorithms</I> .<p>
 *
 *  Note that the ordering maintained by a sorted map (whether or not an
 *  explicit comparator is provided) must be <i>consistent with equals</i> if
 *  this sorted map is to correctly implement the <tt>Map</tt> interface. (See
 *  <tt>Comparable</tt> or <tt>Comparator</tt> for a precise definition of <i>
 *  consistent with equals</i> .) This is so because the <tt>Map</tt> interface
 *  is defined in terms of the equals operation, but a map performs all key
 *  comparisons using its <tt>compareTo</tt> (or <tt>compare</tt> ) method, so
 *  two keys that are deemed equal by this method are, from the standpoint of
 *  the sorted map, equal. The behavior of a sorted map <i>is</i> well-defined
 *  even if its ordering is inconsistent with equals; it just fails to obey the
 *  general contract of the <tt>Map</tt> interface.<p>
 *
 *  <b>Note that this implementation is not synchronized.</b> If multiple
 *  threads access a map concurrently, and at least one of the threads modifies
 *  the map structurally, it <i>must</i> be synchronized externally. (A
 *  structural modification is any operation that adds or deletes one or more
 *  mappings; merely changing the value associated with an existing key is not a
 *  structural modification.) This is typically accomplished by synchronizing on
 *  some object that naturally encapsulates the map. If no such object exists,
 *  the map should be "wrapped" using the <tt>Collections.synchronizedMap</tt>
 *  method. This is best done at creation time, to prevent accidental
 *  unsynchronized access to the map: <pre>
 *     Map m = Collections.synchronizedMap(new TreeMap(...));
 * </pre><p>
 *
 *  The iterators returned by all of this class's "collection view methods" are
 *  <i>fail-fast</i> : if the map is structurally modified at any time after the
 *  iterator is created, in any way except through the iterator's own <tt>remove
 *  </tt> or <tt>add</tt> methods, the iterator throws a <tt>
 *  ConcurrentModificationException</tt> . Thus, in the face of concurrent
 *  modification, the iterator fails quickly and cleanly, rather than risking
 *  arbitrary, non-deterministic behavior at an undetermined time in the future.
 *
 * @author     Steven W. Rock
 * @created    February 20, 2002
 * @version    1.0
 * @see        DataPoint2D
 * @see        DataPoint2DComparatorAPI
 * @see        DataPoint2DToleranceComparator
 * @see        TreeMap
 * @see        Map
 * @see        HashMap
 * @see        Hashtable
 * @see        Comparable
 * @see        Comparator
 * @see        Collection
 * @see        Collections#synchronizedMap(Map)
 * @since      1.2
 */
public class DataPoint2DTreeMap extends org.opensha.commons.data.TreeMap {

	private static final long serialVersionUID = 0xCE2A37B;
    /**
     *  Internal object used for the value in the TreeMap. This object is
     *  ignored, since we are storing the DataPoint2D in the keys of the
     *  TreeMap, which sorts the keys automatically.
     */
    protected final static Object PRESENT = new Object();

    /**
     *  Flag to indicate if any DataPoints have been added yet
     */
    protected boolean first = true;

    /**
     *  The comparator used for sorting the dataPoints2D
     */
    public DataPoint2DComparatorAPI comparator = new DataPoint2DToleranceComparator();


    /**
     *  Uses a default DataPoint2DToleranceComparator as the comparator<P>
     *
     *  <b>TreeMap Description</b> <br>
     *  Constructs a new, empty map, sorted according to the keys' natural
     *  order. All keys inserted into the map must implement the <tt>Comparable
     *  </tt> interface. Furthermore, all such keys must be <i>mutually
     *  comparable</i> : <tt>k1.compareTo(k2)</tt> must not throw a
     *  ClassCastException for any elements <tt>k1</tt> and <tt>k2</tt> in the
     *  map. If the user attempts to put a key into the map that violates this
     *  constraint (for example, the user attempts to put a string key into a
     *  map whose keys are integers), the <tt>put(Object key, Object value)</tt>
     *  call will throw a <tt>ClassCastException</tt> .
     *
     * @see    Comparable
     */
    public DataPoint2DTreeMap() {
        super();

        //DataPoint2DTreeMap map = new DataPoint2DTreeMap( comparator );
        this.comparator = new DataPoint2DToleranceComparator();

    }


    /**
     *  Constructs a new, empty map, sorted according to the given comparator.
     *  All keys inserted into the map must be <i>mutually comparable</i> by the
     *  given comparator: <tt>comparator.compare(k1, k2)</tt> must not throw a
     *  <tt>ClassCastException</tt> for any keys <tt>k1</tt> and <tt>k2</tt> in
     *  the map. If the user attempts to put a key into the map that violates
     *  this constraint, the <tt>put(Object key, Object value)</tt> call will
     *  throw a <tt>ClassCastException</tt> .
     *
     * @param  c  the comparator that will be used to sort this map. A <tt>null
     *      </tt> value indicates that the keys' <i>natural ordering</i> should
     *      be used.
     */
    public DataPoint2DTreeMap( Comparator c ) {
        super( c );
        first = true;
    }


    /**
     *  Set's the tolerance of this series, i.e. the tolerance of the Comparator
     *  used to sort the series by the X-Values (see comments above about numerical
     *  precision issues).
     *
     * @param  newTolerance               The new tolerance value
     * @exception  InvalidRangeException  Description of the Exception
     */
    public void setTolerance( double newTolerance ) throws InvalidRangeException {
        if ( newTolerance < 0 ) {
            throw new InvalidRangeException( "Tolerance must be larger or equal to 0" );
        }

        comparator.setTolerance( newTolerance );
    }


    /**
     *  Special function that recreates the Map with the new comparator.
     *  Programmers MUST set their reference of this DataPoint2DTreeMap to the
     *  new returned one. Can fix this in the future - what is required is that
     *  instead of extending the TreeMap, that I copy all the TreeMap code into
     *  this class. The Comparator is private in TreeMap
     *
     * @param  comparator  The new comparator value
     * @return             Description of the Return Value
     */
    public DataPoint2DTreeMap setComparator( DataPoint2DComparatorAPI comparator ) {

        DataPoint2DTreeMap map = new DataPoint2DTreeMap( comparator );
        Set set = this.keySet();
        java.util.Iterator it = set.iterator();
        while ( it.hasNext() ) {
            DataPoint2D d2 = ( DataPoint2D ) it.next();
            map.put( d2 );
        }
        map.comparator = comparator;
        return map;
    }


    /**
     *  Returns the nth element in this series, based on index. This is required
     *  for the graphing package and was the whole reason for implementing
     *  org.opensha.util.TreeMap
     *
     * @param  index  Description of the Parameter
     * @return        Description of the Return Value
     */
    public DataPoint2D get( int index ) {

        if ( index >= this.size() ) {
            return null;
        }

        Set set = this.keySet();
        java.util.Iterator it = set.iterator();
        DataPoint2D point = null;

        int counter = 0;
        while ( counter <= index ) {
            point = ( DataPoint2D ) it.next();
            counter++;
        }
        return point;
    }

    /**
     *  Finds the first point with the spcified x value within tolerance of the
     *  comparator. Returns null if none found
     *
     * @param  index  Description of the Parameter
     * @return        Description of the Return Value
     */
    public DataPoint2D get( double x ) {

        Set set = this.keySet();
        java.util.Iterator it = set.iterator();
        DataPoint2D point = null;
        DataPoint2D findPoint = new DataPoint2D(x,0.0);

        while( it.hasNext() ){

            point = ( DataPoint2D ) it.next();
            if( comparator.compare(point, findPoint) == 0 )
                return point;

        }

        return null;
    }

    /** returns the Y value given an x value - within tolerancea, returns null if not found */
    public int getIndex(DataPoint2D point){

        Set set = this.keySet();
        java.util.Iterator it = set.iterator();

        DataPoint2D point2 = null;
        int counter = 0;
        while( it.hasNext() ){

            point2 = ( DataPoint2D ) it.next();
            if( comparator.compare(point, point2) == 0 )
                return counter;

            counter++;
        }

        return -1;

    }

    /**
     *  Returns the smallest Y-Value in this series
     *
     * @return    The minY value
     */
    public double getMinY() {
      double minY = Double.NaN;
      Set set = this.keySet();
      java.util.Iterator it = set.iterator();
      // set the first value as max initially
      if(it.hasNext())  minY = (( DataPoint2D ) it.next()).getY();
      DataPoint2D point2 = null;
      // now compare the Y values with other points
      while( it.hasNext() ){
        point2 = ( DataPoint2D ) it.next();
        if(point2.getY() < minY) minY =  point2.getY();
      }
      return minY;
    }

    /**
     *  Returns the largest Y-Value in this series
     *
     * @return    The maxY value
     */
    public double getMaxY() {
      double maxY = Double.NaN;
      Set set = this.keySet();
      java.util.Iterator it = set.iterator();
      // set the first value as max initially
      if(it.hasNext())  maxY = (( DataPoint2D ) it.next()).getY();
      DataPoint2D point2 = null;
      // now compare the Y values with other points
      while( it.hasNext() ){
        point2 = ( DataPoint2D ) it.next();
        if(point2.getY() > maxY) maxY =  point2.getY();
      }
      return maxY;
    }


    /**
     *  Returns the tolerance of this series, i.e. the tolerance of the
     *  Comparator
     *
     * @return    The tolerance value
     */
    public double getTolerance() { return comparator.getTolerance(); }


    /**
     *  Associates the specified value with the specified key in this map. If
     *  the map previously contained a mapping for this key, the old value is
     *  replaced.
     *
     * @param  key                    key with which the specified value is to
     *      be associated.
     * @param  value                  value to be associated with the specified
     *      key.
     * @return                        previous value associated with specified
     *      key, or <tt>null</tt> if there was no mapping for key. A <tt>null
     *      </tt> return can also indicate that the map previously associated
     *      <tt>null</tt> with the specified key.
     * @throws  ClassCastException    key cannot be compared with the keys
     *      currently in the map. THe key is not an instance of DataPoint2D
     * @throws  NullPointerException  key is <tt>null</tt> and this map uses
     *      natural order, or its comparator does not tolerate <tt>null</tt>
     *      keys.
     */
    public Object put( Object key, Object value ) {

        if ( key instanceof DataPoint2D ) {
            return put( ( DataPoint2D ) key );
        } else {
            throw new ClassCastException( "This treemap accepts only DataPoint2Ds" );
        }

    }


    /**
     *  Associates the specified value with the specified key in this map. If
     *  the map previously contained a mapping for this key, the old value is
     *  replaced.<P>
     *
     *  Caluclautes the min and max Y-Values in this series as points are added
     *
     * @param  key                    key with which the specified value is to
     *      be associated.
     * @return                        previous value associated with specified
     *      key, or <tt>null</tt> if there was no mapping for key. A <tt>null
     *      </tt> return can also indicate that the map previously associated
     *      <tt>null</tt> with the specified key.
     * @throws  ClassCastException    key cannot be compared with the keys
     *      currently in the map.
     * @throws  NullPointerException  key is <tt>null</tt> and this map uses
     *      natural order, or its comparator does not tolerate <tt>null</tt>
     *      keys.
     */
    public Object put( DataPoint2D key ) {

        Object value = this.PRESENT;

        Entry t = root;

        if ( t == null ) {
            incrementSize();
            root = new Entry( key, value, null );
            return null;
        }

        while ( true ) {

            int cmp = compare( key, t.key );

            if ( cmp == 0 ) {

                t.key = key;
                return t.setValue( value );

            }
            else if ( cmp < 0 ) {

                if ( t.left != null ) t = t.left;
                else {
                    incrementSize();
                    t.left = new Entry( key, value, t );
                    fixAfterInsertion( t.left );
                    return null;
                }
            }
            else {

                // cmp > 0
                if ( t.right != null ) { t = t.right; }
                else {
                    incrementSize();
                    t.right = new Entry( key, value, t );
                    fixAfterInsertion( t.right );
                    return null;
                }
            }
        }

    }


    /**
     *  Removes all mappings from this TreeMap.
     */
    public void clear() {
        super.clear();
        first = true;
    }

}
