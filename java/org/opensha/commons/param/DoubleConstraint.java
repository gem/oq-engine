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

package org.opensha.commons.param;

import org.opensha.commons.exceptions.EditableException;

/**
 * <b>Title:</b> DoubleConstraint<p>
 *
 * <b>Description:</b> A doubleConstraint represents a range of allowed
 * values between a min and max double value, inclusive. The main purpose of
 * this class is to call isAllowed() which will return true if the value
 * is withing the range. Null values may or may not be allowed. See the
 * ParameterConstraint javadocs for further documentation. <p>
 *
 * Note: It is up to the programmer using this class to ensure that the
 * min value is less than the max value. As an enhancement to this class
 * setting min and max could be validated that min is not greater than max. <p>
 *
 * @see ParameterConstraint
 * @author     Sid Hellman, Steven W. Rock
 * @created    February 20, 2002
 * @version    1.0
 */
public class DoubleConstraint extends ParameterConstraint<Double> {

    /** Class name for debugging. */
    protected final static String C = "DoubleConstraint";
    /** If true print out debug statements. */
    protected final static boolean D = false;


    /** The minimum value allowed in this constraint, inclusive */
    protected Double min = null;
    /** The maximum value allowed in this constraint, inclusive */
    protected Double max = null;

    /** No-Arg Constructor, constraints are null so all values allowed */
    public DoubleConstraint() { super(); }


    /**
     * Constructor for the DoubleConstraint object. Sets the min and max values
     * allowed in this constraint. No checks are performed that min and max are
     * consistant with each other.
     *
     * @param  min  The min value allowed
     * @param  max  The max value allowed
     */
    public DoubleConstraint( double min, double max ) {
        this.min = new Double(min);
        this.max = new Double(max);
    }


    /**
     * Constructor for the DoubleConstraint object. Sets the min and max values
     * allowed in this constraint. No checks are performed that min and max are
     * consistant with each other.
     *
     * @param  min  The min value allowed
     * @param  max  The max value allowed
     */
    public DoubleConstraint( Double min, Double max ) {
        this.min = min;
        this.max = max;
    }

    /**
     * Sets the min and max values allowed in this constraint. No checks
     * are performed that min and max are consistant with each other.
     *
     * @param  min  The new min value
     * @param  max  The new max value
     * @throws EditableException Thrown when the constraint or parameter
     * containing this constraint has been made non-editable.
     */
    public void setMinMax( double min, double max ) throws EditableException {
        String S = C + ": setMinMax(double, double): ";
        checkEditable(S);
        this.min = new Double( min ) ;
        this.max = new Double( max ) ;
    }


    /** Sets the min and max values allowed in this constraint. No checks
     * are performed that min and max are consistant with each other.
     *
     * @param  min  The new min value
     * @param  max  The new max value
     * @throws EditableException Thrown when the constraint or parameter
     * containing this constraint has been made non-editable.
     */
    public void setMinMax( Double min, Double max ) throws EditableException {
        String S = C + ": setMinMax(Double, Double): ";
        checkEditable(S);
        this.min = min;
        this.max = max;
    }


    /** Returns the min allowed value of this constraint. */
    public Double getMin() { return min; }

    /** Gets the max allowed value of this constraint */
    public Double getMax() { return max; }

    /**
     * Checks if the passed in value is within the min and max, inclusive of
     * the end points. First the value is chekced if it's null and null values
     * are allowed. Then it checks the passed in object is a Double. If the
     * constraint min and max values are null, true is returned, else the value
     * is compared against the min and max values. If any of these checks fails
     * false is returned. Otherwise true is returned.
     *
     * @param  obj  The object to check if allowed.
     * @return      True if this is a Double and one of the allowed values.
     */
    public boolean isAllowed( Double d ) {
        if( d == null ) return nullAllowed;
        if( ( min == null ) || ( max == null ) ) return true;
        else if( ( d.compareTo(min) >= 0 ) && ( d.compareTo(max) <= 0 ) ) return true;
        return false;
    }


    /**
     * Checks if the passed in value is within the min and max, inclusive of
     * the end points. First the value is checked if it's null and null values
     * are allowed. If the constraint min and max values are null, true is
     * returned, else the value is compared against the min and max values. If
     * any of these checks fails false is returned. Otherwise true is returned.
     *
     * @param  obj  The object to check if allowed.
     * @return      True if this is one of the allowed values.
     */
    public boolean isAllowed( double d ) { return isAllowed( new Double( d ) ); }


    /** returns the classname of the constraint, and the min & max as a debug string */
    public String toString() {
        String TAB = "    ";
        StringBuffer b = new StringBuffer();
        if( name != null ) b.append( TAB + "Name = " + name + '\n' );
        if( min != null ) b.append( TAB + "Min = " + min.toString() + '\n' );
        if( max != null ) b.append( TAB + "Max = " + max.toString() + '\n' );
        b.append( TAB + "Null Allowed = " + this.nullAllowed+ '\n' );
        return b.toString();
    }


    /** Creates a copy of this object instance so the original cannot be altered. */
    public Object clone() {
        DoubleConstraint c1 = new DoubleConstraint( min, max );
        c1.setName( name );
        c1.setNullAllowed( nullAllowed );
        c1.editable = true;
        return c1;
    }

}
