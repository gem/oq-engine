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
 * ValueWeight : This class allows to have a value and a weight can be assigned to that value.
 * for example: A rupture rate can be assigned and we  can assign a weight to that value of rate
 * @author vipingupta
 *
 */
public class ValueWeight {
	private final static String C = "ValueWeight";
	private double value = Double.NaN;  // value
	private double weight = Double.NaN; // weight associated with this value

	/**
	 * Default constructor
	 *
	 */
	public ValueWeight() { }

	/**
	 * Set the value and weight
	 * @param value
	 * @param weight
	 */
	public ValueWeight(double value, double weight) {
		setValue(value);
		setWeight(weight);
	}


	/**
	 * Get value
	 * @return
	 */
	public double getValue() {
		return value;
	}

	/**
	 * Set value
	 * @param value
	 */
	public void setValue(double value) {
		this.value = value;
	}

	/**
	 * Get weight
	 * @return
	 */
	public double getWeight() {
		return weight;
	}

	/**
	 * Set weight
	 * @param weight
	 */
	public void setWeight(double weight) {
		this.weight = weight;
	}

	/**
	 * clone
	 */
	public Object clone() {
		ValueWeight valWeight = new ValueWeight(this.value, this.weight);
		return valWeight;
	}

	/**
     *  Compares the values to if this is less than, equal to, or greater than
     *  the comparing objects. Weight is irrelevant in this case
     *
     * @param  obj                     The object to compare this to
     * @return                         -1 if this value < obj value, 0 if equal,
     *      +1 if this value > obj value
     * @exception  ClassCastException  Is thrown if the comparing object is not
     *      a ValueWeight.
     */
    public int compareTo( Object obj ) throws ClassCastException {

        String S = C + ":compareTo(): ";

        if ( !( obj instanceof ValueWeight ) ) {
            throw new ClassCastException( S + "Object not a ValueWeight, unable to compare" );
        }
        ValueWeight param = ( ValueWeight ) obj;
        Double thisVal = new Double(value);

        return thisVal.compareTo( new Double(param.value) );
    }
}
