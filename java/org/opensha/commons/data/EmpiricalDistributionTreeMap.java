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

import java.util.Comparator;

/**
 *  <b>Title:</b> EmpiricalDistributionTreeMap <p>
 *
 * <b>Description:</b> This class is similar to DataPoint2DTreeMap,
 * except that rather than replacing a point that has the same x value (or within
 * tolerance, which is required to be zero here), the y values are added together.
 * This is useful for making an empirical distribution where the y-values represent
 * the frequency of occurrence of each x value.  In this context, a nonzero tolerance
 * would not make sense because a values might fall into different points depending
 * on what order they're added.  Due to the numerical precision of floating point
 * arithmetic, the tolerance is really about 1e-16. <P>
 *
 * I'm not sure that allowing difference comparators (other than the default)
 * makes any sense.<P>
 *
 * See documentation for EmpiricalDistributionTreeMap for more info
 *
 *
 * @author     Edward H. Field
 * @created    February 6, 2003
 * @version    1.0
  */
public class EmpiricalDistributionTreeMap extends org.opensha.commons.data.DataPoint2DTreeMap {


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
    public EmpiricalDistributionTreeMap() {
        super();

        EmpiricalDistributionTreeMap map = new EmpiricalDistributionTreeMap( comparator );
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
    public EmpiricalDistributionTreeMap( Comparator c ) {
        super( c );
        first = true;
    }




    /**
     *  Parent method is overridded here so that rather than replacing an existing
     *  point that has the same x-value (within tolerance, which is zero here),
     *  the y-values are added together.
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

                DataPoint2D newKey = new DataPoint2D( key.getX(), key.getY() + ((DataPoint2D) t.key).getY());
                t.key = newKey;
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

}
