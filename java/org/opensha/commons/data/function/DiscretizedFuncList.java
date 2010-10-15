/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with the Southern California
 * Earthquake Center (SCEC, http://www.scec.org) at the University of Southern
 * California and the UnitedStates Geological Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not
 * use this file except in compliance with the License. You may obtain a copy of
 * the License at
 * 
 * http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations under
 * the License.
 ******************************************************************************/

package org.opensha.commons.data.function;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.ListIterator;

import org.opensha.commons.data.DataPoint2D;
import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.exceptions.DiscretizedFuncException;

/**
 * <b>Title:</b> DiscretizedFuncList
 * <p>
 * 
 * <b>Description:</b> List container for Discretized Functions. This class
 * stores Discretized func API ( and any subclass ) internally in an array list
 * and provides standard list access functions such as (paraphrasing) get(),
 * set(), delete(), iterator(), size(), etc.
 * <p>
 * 
 * Currently any type of DiscretizedFunctionAPI is allowed in the list.
 * Subclasses can overide isFunctionAllowed() to provide added constraints on
 * what can belong in this list.
 * <p>
 * 
 * Note: Since this class behaves like an ArrayList, functions in the list may
 * be accessed by index, or by iterator.
 * <p>
 * 
 * @author Steven W. Rock
 * @version 1.0
 */
public class DiscretizedFuncList implements NamedObjectAPI {

    /* ****************** */
    /** @todo Variables */
    /* ****************** */

    /* Class name Debbuging variables */
    protected final static String C = "DiscretizedFuncList";

    /* Boolean debugging variable to switch on and off debug printouts */
    protected final static boolean D = false;

    /**
     * List of DiscretizedFuncAPI. This is the internal data storage for the
     * functions.
     */
    protected ArrayList functions = new ArrayList();

    /**
     * Every function list has a information string that can be used in
     * displays, etc.
     */
    protected String info = "";

    /** Every function list have a name for identifying it amoung several */
    protected String name = "";

    /**
     * The X-Axis name, may be the same for all items in the list. .
     * <p>
     * SWR: Not sure if this is needed any more. Have to check into is.
     */
    protected String xAxisName = "";

    /**
     * The Y-Axis name, may be the same for all items in the list. .
     * <p>
     * SWR: Not sure if this is needed any more. Have to check into is.
     */
    protected String yAxisName = "";

    /* ********************* */
    /** @todo Constructors */
    /* ********************* */

    /** no arg constructor, this constructor currently is empty. */
    public DiscretizedFuncList() {
        super();
    }

    /* ************************************* */
    /** @todo Simple field getters/setters */
    /* ************************************* */

    /** Returns the name of this list */
    public String getName() {
        return name;
    }

    /** Sets the name of this list */
    public void setName(String name) {
        this.name = name;
    }

    /** Returns the info of this list */
    public String getInfo() {
        return info;
    }

    /** Sets the info of this list */
    public void setInfo(String info) {
        this.info = info;
    }

    /** Returns the xAxisName of this list */
    public String getXAxisName() {
        return xAxisName;
    }

    /** Sets the xAxisName of this list */
    public void setXAxisName(String name) {
        this.xAxisName = name;
    }

    /** Returns the yAxisName of this list */
    public String getYAxisName() {
        return yAxisName;
    }

    /** Sets the yAxisName of this list */
    public void setYAxisName(String name) {
        this.yAxisName = name;
    }

    /**
     * Combo Name of the X and Y axis, used for determining if two
     * DiscretizedFunction2DAPIs represent the same thing.
     */
    public String getXYAxesName() {
        return xAxisName + ',' + yAxisName;
    }

    /* ************************* */
    /** @todo Function Helpers */
    /* ************************* */

    /** returns true if a function exists at the specified index */
    private boolean hasFunctionAtIndex(int index) {
        if ((index + 1) > functions.size())
            return false;
        else
            return true;
    }

    /**
     * Returns the function at the specified index, else null if no function
     * exists at that index.
     */
    private DiscretizedFuncAPI getFunction(int index) {
        return (DiscretizedFuncAPI) functions.get(index);
    }

    /**
     * Currently only returns true. Further functionality may be added in the
     * future or by subclasses.
     * 
     * @param function
     * @return
     */
    public boolean isFuncAllowed(DiscretizedFuncAPI function) {
        return true;
    }

    /* ***************************** */
    /** @todo Basic List functions */
    /* ***************************** */

    /** Removes all function references from this list */
    public void clear() {
        functions.clear();
    }

    /** Returns an ordered FIFO iterator over each function in the list */
    public ListIterator listIterator() {
        return functions.listIterator();
    }

    /**
     * Returns an iterator over the functions in the lsit, no guarentee of order
     */
    public Iterator iterator() {
        return functions.iterator();
    }

    /** Returns the number of functions in the list */
    public int size() {
        return functions.size();
    }

    /**
     * Returns the index of the first occurrence of the function in this list;
     * returns -1 if the object is not found. Uses equals() to determing if the
     * same.
     * 
     * @param function
     * @return
     */
    public int indexOf(DiscretizedFunc function) {
        int counter = 0;
        ListIterator it = listIterator();
        while (it.hasNext()) {
            DiscretizedFuncAPI f1 = (DiscretizedFuncAPI) it.next();
            if (f1.equals(function))
                return counter;
            counter++;
        }
        return -1;
    }

    /**
     * Removes the function at the specified index
     * 
     * @param index
     */
    public void remove(int index) {
        // System.out.println("Number in list:"+functions.size());
        functions.remove(index);
    }

    /**
     * Removes the specified function if it exists as determined by equals().
     * This function iterates over the list, comapring each stored function to
     * the input argument. May be time consuming if many functions in the list.
     * 
     * @param function
     */
    public void remove(DiscretizedFuncAPI function) {
        ListIterator it = listIterator();
        if (it != null) {
            while (it.hasNext()) {
                DiscretizedFuncAPI f1 =
                        (org.opensha.commons.data.function.DiscretizedFuncAPI) it
                                .next();
                if (f1.equals(function)) {
                    functions.remove(f1);
                    return;
                }
            }
        }
    }

    /**
     * Removes any functions in the passed in list that exist in this list. Only
     * removes the union of these two function list. Will leave functions in
     * this list that doesn't exist in second. Use clear() to compleatly empty
     * this list. This function calls remove() on every function in the passed
     * in list.
     * 
     * @param list
     */
    public void removeAll(DiscretizedFuncList list) {
        ListIterator it = list.listIterator();
        while (it.hasNext()) {
            DiscretizedFuncAPI function = (DiscretizedFuncAPI) it.next();
            remove(function);
        }
    }

    /**
     * Checks if the DiscretizedFuncAPI exists in the list. Loops through each
     * function in the list and calls function.equals( function2 ) against the
     * passed in function to determine if this function exists.
     */
    public boolean contains(DiscretizedFuncAPI function) {
        ListIterator it = listIterator();
        if (it != null) {
            while (it.hasNext()) {
                DiscretizedFuncAPI f1 =
                        (org.opensha.commons.data.function.DiscretizedFuncAPI) it
                                .next();
                if (f1.equals(function))
                    return true;
            }
            return false;
        } else
            return false;
    }

    /**
     * Verifies that the passed in list is a subset of this list. Loops through
     * each function in the passes in list and calls contains( function2 )
     * against the passed in function to determine if this function exists.
     */
    public boolean containsAll(DiscretizedFuncList list) {
        ListIterator it = list.listIterator();
        while (it.hasNext()) {
            DiscretizedFuncAPI function = (DiscretizedFuncAPI) it.next();
            if (!contains(function))
                return false;
        }
        return true;
    }

    /**
     * Adds the DiscretizedFuncAPI if it doesn't exist based on the equals()
     * method, else throws exception. This function first checks if the passed
     * in function is allowed. In this class specification all functions are
     * allowed. Subclasses may further restrict this.
     */
    public void add(DiscretizedFuncAPI function)
            throws DiscretizedFuncException {

        if (!isFuncAllowed(function))
            throw new DiscretizedFuncException(C + ": add(): "
                    + "This function is not allowed.");
        // if( contains(function) ) throw new DiscretizedFunction2DException(C +
        // ": add(): " + "This function is already in the list.");
        functions.add(function);

    }

    /**
     * Adds all DiscretizedFuncAPI of the DiscretizedFuncList to this one, if
     * the named DiscretizedFuncAPI is not already in the list.
     */
    public void addAll(DiscretizedFuncList list)
            throws DiscretizedFuncException {

        ListIterator it = list.listIterator();
        while (it.hasNext()) {
            DiscretizedFuncAPI function = (DiscretizedFuncAPI) it.next();
            try {
                add(function);
            } catch (DiscretizedFuncException ex) {
            }
        }

    }

    /**
     * Returns the DiscretizedFuncAPI at the specified index. If index is larger
     * than the number of functions, null is returned.
     * 
     * @param index
     *            into the list.
     * @return DiscretizedFuncAPI function of interest.
     */
    public DiscretizedFuncAPI get(int index) {
        DiscretizedFuncAPI f = null;
        if (hasFunctionAtIndex(index))
            f = (DiscretizedFuncAPI) functions.get(index);
        return f;
    }

    /**
     * Updates an existing function in the list or adds it if it doesn't exist.
     * This function simply calls remove() then add().
     */
    public void update(DiscretizedFuncAPI function) {
        remove(function);
        add(function);
    }

    /**
     * Returns true if all the DisctetizedFunctions in this list are equal.
     * Equality is determined if the two lists are the same size, then calls
     * containsAll()
     */
    public boolean equals(Object list) {
        if (list instanceof DiscretizedFuncList) {
            DiscretizedFuncList listObj = (DiscretizedFuncList) list;
            // Not same size, can't be equal
            if (this.size() != listObj.size())
                return false;

            // next check boolean flags
            // if( allowedDifferentAxisNames != list.allowedDifferentAxisNames )
            // return false;
            // if( allowedIdenticalFunctions != list.allowedIdenticalFunctions )
            // return false;

            // All functions must be present
            if (!containsAll(listObj))
                return false;

            // Passed all tests - return true
            return true;
        }

        return false;

    }

    /**
     * Returns a copy of this list, therefore any changes to the copy cannot
     * affect this original list. A deep clone is different from a normal Java
     * clone or shallow clone in that each function in the list is also cloned.
     * A shallow clone would only return a new instance of this
     * DiscretizedFuncList, but not clone the elements. It would maintain a
     * pointer to the same elements.
     */
    public DiscretizedFuncList deepClone() {

        DiscretizedFuncList l = new DiscretizedFuncList();

        ListIterator it = listIterator();
        while (it.hasNext()) {

            // This list's parameter
            DiscretizedFuncAPI f = ((DiscretizedFuncAPI) it.next()).deepClone();
            l.add(f);

        }

        // l.allowedDifferentAxisNames = allowedDifferentAxisNames;
        // l.allowedIdenticalFunctions = allowedIdenticalFunctions;

        l.name = name;
        l.info = info;
        l.xAxisName = xAxisName;
        l.yAxisName = yAxisName;

        return l;

    }

    private static String TAB = "\t";

    /**
     * Debugging information. Dumps the state of this object, number of
     * functions present, and calls the toString() of each element to dump it's
     * state.
     * <p>
     * 
     * This is the function called to format the data for raw data display in
     * the IMRTesterApplet.
     * <p>
     * 
     * Note: SWR: Still needs work to reformat the data better. Currently output
     * is x, y for each function seperatly. A better output format would be in
     * spreadsheet format, since all functions in the IMRTesterApplet share the
     * same x values. Currently not implemented.
     * <p>
     */
    public String toString() {

        String S = C + ": toString(): ";

        StringBuffer b = new StringBuffer();
        b.append("\n");
        b.append("X-Axis: " + this.xAxisName + '\n');
        b.append("Y-Axis: " + this.yAxisName + '\n');
        b.append("Number of Data Sets: " + this.size() + '\n');

        ListIterator it = listIterator();
        boolean first = true;
        int counter = 0;
        while (it.hasNext()) {

            DiscretizedFuncAPI function = (DiscretizedFuncAPI) it.next();
            Iterator it2 = function.getPointsIterator();

            counter++;
            b.append("\nData Set #" + counter + '\n');
            b.append("Name: " + function.getName() + '\n');
            b.append("Num Points: " + function.getNum() + '\n');
            b.append("Info: " + function.getInfo() + "\n\n");
            b.append("X, Y Data:" + '\n');

            while (it2.hasNext()) {

                DataPoint2D point = (DataPoint2D) it2.next();
                double x = point.getX();
                double y = point.getY();
                b.append((float) x + TAB + (float) y + '\n');
            }

        }

        return b.toString();
    }

    /**
     * Returns all datapoints in a matrix, x values in first column, first
     * functions y vaules in second, second function's y values in the third,
     * etc. This function should be optimized by actually accessing the
     * underlying TreeMap.
     * <p>
     * 
     * Note: SWR This function has been renamed from toString(). This function
     * no longer works, but contains the formatting rules needed to still be
     * imploemented by toString().
     */
    public String toStringOld() {

        String S = C + ": toString(): ";

        StringBuffer b = new StringBuffer();
        b.append("Discretized Function Data Points\n");
        b.append("X-Axis: " + this.xAxisName + '\n');
        b.append("Y-Axis: " + this.yAxisName + '\n');
        b.append("Number of Data Sets: " + this.size() + '\n');

        StringBuffer b2 = new StringBuffer();

        final int numPoints = 100;
        final int numSets = this.size();

        Number[][] model = new Number[numSets][numPoints];
        double[] xx = new double[numPoints];
        String[] rows = new String[numPoints];

        ListIterator it1 = listIterator();
        boolean first = true;
        int counter = 0;
        b.append("\nColumn " + (counter + 1) + ". X-Axis");
        while (it1.hasNext()) {

            DiscretizedFuncAPI function = (DiscretizedFuncAPI) it1.next();
            b.append("\nColumn " + (counter + 2) + ". Y-Axis: "
                    + function.toString());

            Iterator it = function.getPointsIterator();

            // Conversion
            if (D)
                System.out.println(S + "Converting Function to 2D Array");
            int i = 0;
            while (it.hasNext()) {

                DataPoint2D point = (DataPoint2D) it.next();

                if (first) {
                    double x1 = point.getX();
                    xx[i] = x1;
                }

                double y1 = point.getY();
                model[counter][i] = new Double(y1);

                i++;
            }
            // rows[counter] = function.getXYAxesName();
            if (first)
                first = false;
            counter++;

        }

        for (int i = 0; i < numPoints; i++) {
            b2.append('\n');
            for (int j = 0; j < numSets; j++) {

                if (j == 0)
                    b2.append("" + xx[i] + '\t' + model[j][i].toString());
                else
                    b2.append('\t' + model[j][i].toString());

            }

        }

        b.append("\n\n-------------------------");
        b.append(b2.toString());
        b.append("\n-------------------------\n");

        return b.toString();

    }

}

// Not needed any more but a subclass may want this functionality in the future.
// private boolean allowedDifferentAxisNames = false;
// private boolean allowedIdenticalFunctions = false;

/*
 * public void setAllowedDifferentAxisNames(boolean allowedDifferentAxisNames) {
 * this.allowedDifferentAxisNames = allowedDifferentAxisNames; } public boolean
 * isAllowedDifferentAxisNames() { return allowedDifferentAxisNames; } public
 * void setAllowedIdenticalFunctions(boolean allowedIdenticalFunctions) {
 * this.allowedIdenticalFunctions = allowedIdenticalFunctions; } public boolean
 * isAllowedIdenticalFunctions() { return allowedIdenticalFunctions; }
 */
