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

package org.opensha.sha.earthquake;

import java.util.Comparator;

/**
 * <p>Title: EqkRuptureMagComparator</p>
 *
 * <p>Description: It compares 2 EqkRupture Object based on their magnitudes.
 * </p>
 *
 *
 * @author not attributable
 * @version 1.0
 */
public class EqkRuptureMagComparator
    implements Comparator, java.io.Serializable {

  /**
   * Compares its two arguments for order. Returns a negative integer, zero, or
   * a positive integer as the first argument is less than, equal to, or greater than the second.
   * The implementor must ensure that sgn(compare(x, y)) == -sgn(compare(y, x))
   * for all x and y. (This implies that compare(x, y) must throw an exception if
   * and only if compare(y, x) throws an exception.)
   * The implementor must also ensure that the relation is transitive:
   * ((compare(x, y)>0) && (compare(y, z)>0)) implies compare(x, z)>0.
   * Finally, the implementer must ensure that compare(x, y)==0 implies that
   * sgn(compare(x, z))==sgn(compare(y, z)) for all z.
   * It is generally the case, but not strictly required that
   * (compare(x, y)==0) == (x.equals(y)). Generally speaking, any
   * comparator that violates this condition should clearly indicate this fact.
   * The recommended language is "Note: this comparator imposes orderings that
   * are inconsistent with equals."
   * @param object1 Object the first object to be compared.
   * @param object2 Object the second object to be compared.
   * @return int a negative integer, zero, or a positive integer
   *  as the first argument is less than, equal to, or greater
   * @todo Implement this java.util.Comparator method
   */
  public int compare(Object object1, Object object2) {
    EqkRupture eqkRup1 = (EqkRupture)object1;
    EqkRupture eqkRup2 = (EqkRupture)object2;
    if(eqkRup1.getMag() < eqkRup2.getMag())
      return -1;
    else if(eqkRup1.getMag() == eqkRup2.getMag())
      return 0;
    else
      return 1;
  }

}
