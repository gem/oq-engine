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
 *  <b>Title:</b> IntegerConstraint<p>
 *
 *  <b>Description:</b> Constraint Object containing a min and max integer value
 *  allowed. Need a check that min is less that max. If min == max that means
 *  only one discrete value is allowed <p>
 *
 *  <b>Description:</b> A Integer Constraint represents a range of allowed
 * values between a min and max integer value, inclusive. The main purpose of
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
 * @created    February 21, 2002
 * @version    1.0
 */
public class IntegerConstraint extends ParameterConstraint<Integer>  {

    /** Class name for debugging. */
    protected final static String C = "IntegerConstraint";
    /** If true print out debug statements. */
    protected final static boolean D = false;

     /** The minimum value allowed in this constraint, inclusive */
    protected Integer min = null;
    /** The maximum value allowed in this constraint, inclusive */
    protected Integer max = null;


    /** No-Arg Constructor, constraints are null so all values allowed */
    public IntegerConstraint() { super(); }


    /**
     * Constructor that sets the constraints during instantiation.
     * Sets the min and max values allowed in this constraint. No checks
     * are performed that min and max are consistant with each other.<P>
     *
     * @param  min  The min value allowed
     * @param  max  The max value allowed
     */
    public IntegerConstraint( int min, int max ) {
        this.min = new Integer( min );
        this.max = new Integer( max );
    }

    /**
     * Constructor that sets the constraints during instantiation.
     * Sets the min and max values allowed in this constraint. No checks
     * are performed that min and max are consistant with each other.<P>
     *
     * @param  min  The min value allowed
     * @param  max  The max value allowed
     */
    public IntegerConstraint( Integer min, Integer max ) {
        this.min = min;
        this.max = max;
    }


    /** Sets the min and max values allowed in this constraint. No checks
      * are performed that min and max are consistant with each other.
      *
      * @param  min  The new min value
      * @param  max  The new max value
      * @throws EditableException Thrown when the constraint or parameter
      * containing this constraint has been made non-editable.
      */
    public void setMinMax( Integer min, Integer max ) throws EditableException {

        String S = C + ": setMinMax(): ";
        checkEditable(S);

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
    public void setMinMax( int min, int max ) throws EditableException {
        setMinMax( new Integer( min ), new Integer( max ) );
    }




    /** Returns the min allowed value of this constraint. */
    public Integer getMin() { return min; }

    /** Gets the max allowed value of this constraint */
    public Integer getMax() { return max; }

    /**
     * Checks if the passed in value is within the min and max, inclusive of
     * the end points. First the value is chekced if it's null and null values
     * are allowed. Then it checks the passed in object is a Integer. If the
     * constraint min and max values are null, true is returned, else the value
     * is compared against the min and max values. If any of these checks fails
     * false is returned. Otherwise true is returned.
     *
     * @param  obj  The object to check if allowed.
     * @return      True if this is a Double and one of the allowed values.
     */
    public boolean isAllowed( Integer i ) {
        if( nullAllowed && ( i == null ) ) return true;
        if( ( min == null ) || ( max == null ) ) return true;
        else if( ( i.compareTo( this.min ) >= 0 ) && ( i.compareTo( this.max ) <= 0 ) )
            return true;
        else return false;
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
    public boolean isAllowed( int i ) {
        return isAllowed( new Integer( i ) );
    }


    /** Returns the classname of the constraint, and the min & max as a debug string */
    public String toString() {
        String TAB = "    ";
        StringBuffer b = new StringBuffer();
        if( name != null) b.append( TAB + "Name = " + name + '\n' );
        if( min != null)  b.append( TAB + "Min = " + min.toString() + '\n' );
        if( max != null) b.append( TAB + "Max = " + max.toString() + '\n' );
        b.append( TAB + "Null Allowed = " + this.nullAllowed+ '\n' );
        return b.toString();
    }


    /** Creates a copy of this object instance so the original cannot be altered. */
    public Object clone() {
        IntegerConstraint c1 = new IntegerConstraint( min, max );
        c1.setName( name );
        c1.setNullAllowed( nullAllowed );
        c1.editable = true;
        return c1;
    }

}
