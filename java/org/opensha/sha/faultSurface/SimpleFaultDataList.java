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

package org.opensha.sha.faultSurface;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.ListIterator;

import org.opensha.commons.exceptions.InvalidRangeException;


// Fix - Needs more comments

/**
 * <b>Title:</b> SimpleFaultDataList<p>
 * <b>Description:</b> List container for a collection of SimpleFaultData objects <p>
 *
 * @author Steven W. Rock
 * @version 1.0
 */

public class SimpleFaultDataList {

    protected final static String C = "SimpleFaultDataList";
    protected final static boolean D = false;

    /**
     *  Contains the list of Locations
     */
    protected ArrayList<SimpleFaultData> list = new ArrayList<SimpleFaultData>();
    protected HashMap<String, SimpleFaultData> map = new HashMap<String, SimpleFaultData>();


    /**
     *  Returns parameter at the specified index if exist, else throws
     *  exception. Recall that these list are stored in a ArrayList, which is
     *  like an array. Therefore you can access items by index.
     *
     * @param  index  Description of the Parameter
     * @return        The simpleFaultDataAt value
     */
    public SimpleFaultData getSimpleFaultDataAt( int index ) throws InvalidRangeException {
        checkIndex(index);
        return list.get( index );
    }


    /**
     *  Returns the SimpleFaultData by the name of the internal FaultTrace
     *
     * @param  index  Description of the Parameter
     * @return        The simpleFaultDataAt value
     */
    public SimpleFaultData getSimpleFaultData( String name)  {
        return (SimpleFaultData)map.get( name );
    }


    private void checkIndex(int index) throws InvalidRangeException {

        if( size() < index + 1 ) throw new InvalidRangeException(
            C + ": getSimpleFaultDataAt(): " +
            "Specified index larger than array size."
        );

    }

    /**
     *  adds the parameter if it doesn't exist, else throws exception
     *
     * @param  simpleFaultData  Description of the Parameter
     * @param  index     Description of the Parameter
     */
    public void replaceSimpleFaultDataAt( SimpleFaultData simpleFaultData, int index ) throws InvalidRangeException  {
        checkIndex(index);
        SimpleFaultData f1 = this.getSimpleFaultDataAt( index );
        map.remove( f1.getFaultTrace().getName() );
        list.add(index, simpleFaultData);
        map.put( simpleFaultData.getFaultTrace().getName(), simpleFaultData );
    }


    /**
     *  adds the object to the end of the list
     *
     * @param  simpleFaultData  The feature to be added to the SimpleFaultData attribute
     */
    public void addSimpleFaultData( SimpleFaultData simpleFaultData ) {
        map.put( simpleFaultData.getFaultTrace().getName(), simpleFaultData );
        list.add(simpleFaultData);
    }


    /**
     *  Returns a list iterator of all Fault Traces in this list, in the order they
     *  were added to the list
     *
     * @return    list iterator over SimpleFaultData objects
     */
    public ListIterator<SimpleFaultData> listIterator() {
        return list.listIterator();
    }


    /**
     *  Removes all Fault Traces from this list
     */
    public void clear() {
        list.clear();
        map.clear();
    }


    /**
     *  Returns the number of objects in this list
     *
     * @return    number of SimpleFaultData objects
     */
    public int size() { return list.size(); }


    private final static String TAB = "  ";
    public String toString(){

        StringBuffer b = new StringBuffer(C);
        b.append('\n');
        b.append(TAB + "Size = " + size());

        ListIterator<SimpleFaultData> it = listIterator();
        while( it.hasNext() ){

            SimpleFaultData trace = (SimpleFaultData)it.next();
            b.append('\n' + TAB + trace.toString());
        }

        return b.toString();

    }

}
