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

import java.util.ArrayList;
import java.util.ListIterator;

import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.exceptions.EditableException;

/**
 * <b>Title:</b> StringConstraint<p>
 *
 * <b>Description:</b> This constraint contains a list of possible allowed
 * string values. These can typically be presented in a GUI picklist. This is
 * the same fucntionality for all DiscreteParameterConstraints.
 *
 * @author     Sid Hellman, Steven W. Rock
 * @created    February 21, 2002
 * @version    1.0
 */

public class StringConstraint
        extends ParameterConstraint<String>
        implements DiscreteParameterConstraintAPI<String>
{

    /** Class name for debugging. */
    protected final static String C = "StringConstraint";
    /** If true print out debug statements. */
    protected final static boolean D = false;

    /** ArrayList list of possible string values, i.e. allowed values. */
    private ArrayList<String> strings = new ArrayList<String>();


    /** No-Arg constructor for the StringConstraint object. Calls the super() constructor. */
    public StringConstraint() { super(); }


    /**
     *  Constructor for the StringConstraint object. Sets all allowed strings
     *  via a ArrayList, which is copied into this object's internal storage
     *  structure.
     *
     * @param  strings                  ArrayList of allowed strings
     * @exception  ConstraintException  Thrown if the passed in vector size is 0
     */
    public StringConstraint( ArrayList<String> strings ) throws ConstraintException {
        if ( strings.size() > 0 ) this.strings = strings;
        else {
            String S = C + ": Constructor(ArrayList strings): ";
            throw new ConstraintException( S + "Input vector of constraint values cannot be empty" );
        }
    }


    /**
     *  Sets all allowed strings via a ArrayList, which is copied into this
     *  object's internal storage structure.
     *
     * @param  strings                  ArrayList of allowed strings
     * @exception  ConstraintException  Thrown if the passed in vector size is 0
     */
    public void setStrings( ArrayList strings ) throws ConstraintException, EditableException {

        String S = C + ": setStrings(): ";
        checkEditable(S);
        if ( ( strings != null ) && ( strings.size() > 0 ) ) this.strings = strings;
        else throw new ConstraintException( S + "Input vector of constraint values cannot be null or empty" );

    }

    /** Returns a cloned ArrayList of the allowed Strings. */
    public ArrayList<String> getAllowedStrings() { return ( ArrayList<String> ) strings.clone(); }

    /** Returns a cloned ArrayList of the allowed Strings. */
    public ArrayList<String> getAllowedValues() { return getAllowedStrings(); }


    /**
     * Determine if the new value being set is allowed. First checks
     * if null and if nulls are allowed. Then verifies the Object is
     * a String. Finally the code verifies that the String is
     * in the allowed strings vector. If any of these checks fails, false
     * is returned.
     *
     * @param  obj  Object to check if allowed String
     * @return      True if the value is allowed
     */
    public boolean isAllowed( String obj ) {

        if( nullAllowed && ( obj == null ) ) return true;
        else if ( !( obj instanceof String ) ) return false;
        else if ( !containsString( obj.toString() ) ) return false;
        else return true;
    }


    /** Returns an Iterator over allowed values.*/
    public ListIterator listIterator() { return strings.listIterator(); }

    /** Adds a String to the list of allowed values, if this constraint is editable. */
    public void addString( String str ) throws EditableException {
        checkEditable(C + ": addString(): ");
        if ( !containsString( str ) ) strings.add( str );
    }


    /** Removes a String to the list of allowed values, if this constraint is editable. */
     public void removeString( String str ) throws EditableException {
        checkEditable(C + ": removeString(): ");
        if ( containsString( str ) ) strings.remove( str );

    }


    /** Returns true if the string is in the allowed list, false otherwise*/
    public boolean containsString( String str ) {
      if (strings.contains(str))
        return true;
      else
        return false;
    }



    /** Returns number of allowed values. */
    public int size() { return strings.size(); }


    /**
     *  Prints out the current state of this parameter, i.e. classname and
     *  allowed values. Useful for debugging.
     */
    public String toString() {
        String TAB = "    ";
        StringBuffer b = new StringBuffer();
        b.append( C );

        if( name != null) b.append( TAB + "Name = " + name + '\n' );
        //b.append( TAB + "Is Editable = " + this.editable + '\n' );
        b.append( TAB + "Allowed values = " );

        boolean first = true;
        ListIterator it = strings.listIterator();
        while ( it.hasNext() ) {
            if ( !first ) {
                b.append( TAB + ", " + it.next() );
            } else {
                b.append( TAB + it.next() );
                first = false;
            }
        }
        b.append( TAB + "Null Allowed = " + this.nullAllowed+ '\n' );
        return b.toString();
    }


    /** Returns a copy so you can't edit or damage the origial. */
    public Object clone() {

        StringConstraint c1 = new StringConstraint();
        c1.name = name;
        ArrayList v = getAllowedStrings();
        ListIterator it = v.listIterator();
        while ( it.hasNext() ) {
            String val = ( String ) it.next();
            c1.addString( val );
        }

        c1.setNullAllowed( nullAllowed );
        c1.editable = true;
        return c1;
    }
}
