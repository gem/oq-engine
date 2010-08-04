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

import java.io.Serializable;
import java.util.Comparator;

import org.opensha.commons.exceptions.NamedObjectException;

/**
 * <b>Title:</b> NamedObjectComparator<p>
 *
 * <b>Description:</b> This class can compare any two objects that implement
 * the NamedObjectAPI and sort them alphabetically. This is useful for passing
 * into a Collections.sort(Collection, Comparator) function call to sort a list
 * alphabetically by named. One example is it's use in the ParameterEditorSheet
 * to edit Parameters.<p>
 *
 * You can set the ascending boolean to true to make the comparison to be sorted
 * acending, else sort comparision is descending.<p>
 *
 *
 * @author     Steven W. Rock
 * @created    February 21, 2002
 * @version    1.0
 */

public class NamedObjectComparator implements Comparator<NamedObjectAPI>, Serializable {

    /**
	 * 
	 */
	private static final long serialVersionUID = 1L;
	
	/** Class name for debugging. */
    final static String C = "NamedObjectComparator";
    /** If true print out debug statements. */
    final static boolean D = false;

    /** If true comparision sort ascending, else comparision sort descending. */
    private boolean ascending = true;

    /** Set's the comparation to ascending if true, else descending.  */
    public void setAscending( boolean a ) { ascending = a; }

    /** Returns true if comparision is ascending, false for descending. */
    public boolean isAscending() { return ascending; }


    /**
     *  Compares two NamedObject objects by name, which both implement
     *  comparable. Throws an exception if either comparing object is not an
     *  NamedObjects. Only the names of these objects are examined for
     *  comparison. This function allows sorting of named objects
     *  alphabetically.
     *
     * @param  o1                        First object to compare
     * @param  o2                        Second object to compare
     * @return                           +1 if the first object name > second
     *      object name, 0 if the two names are equal, and -1 if the first
     *      object name is < the second object's name, alphabetically.
     * @exception  NamedObjectException  Is thrown if either object doesn't
     *      implement NamedObjectAPI.
     * @see                              Comparable
     * @see                              NamedObjectAPI
     */
    public int compare( NamedObjectAPI o1, NamedObjectAPI o2 ) throws NamedObjectException {

        String S = C + ":compare(): ";
        if ( D ) {
            System.out.println( S + "Starting" );
        }
        int result = 0;

        if ( !( o1 instanceof NamedObjectAPI ) ) {
            throw new NamedObjectException( S + "First object doesn't implement NamedObjectAPI, unable to use. " + o1.getClass().getName() );
        }

        if ( !( o2 instanceof NamedObjectAPI ) ) {
            throw new NamedObjectException
                    ( S + "Second object doesn't implement NamedObjectAPI, unable to use. " + o2.getClass().getName() );
        }

        if ( D ) {
            System.out.println( S + "O1 = " + o1.toString() );
            System.out.println( S + "O2 = " + o2.toString() );
            System.out.println( S + "Getting the names: " + o1.getClass().getName() + ", " + o2.getClass().getName() );
        }


        NamedObjectAPI no1 = ( NamedObjectAPI ) o1;
        NamedObjectAPI no2 = ( NamedObjectAPI ) o2;

        String n1 = no1.getName().toString();
        String n2 = no2.getName().toString();

        result = n1.compareTo( n2 );

        if ( ascending ) return result;
        else return -result;

    }

}
