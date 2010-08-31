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
 * <b>Title:</b> ParameterConstraint<p>
 *
 * <b>Description:</b> Partial (abstract) implementation of the
 * ParameterConstraintAPI. This class implements some of the
 * simple common code base for all subclasses. There are
 * three fields and corresponding getters and setters that
 * are implemented. These fields are:
 *
 * <ul>
 * <li>name, getName(), setName().
 * <li>editable, isEditable(), setNonEditable(), checkEditable().
 * <li>nullAllowed, isNullAllowed(), setNullAllowed().
 * <ul>
 *
 * @author Steven W. Rock
 * @version 1.0
 */
public abstract class ParameterConstraint<E> implements ParameterConstraintAPI<E> {

    /** Class name for debugging. */
    protected final static String C = "ParameterConstraint";
    /** If true print out debug statements. */
    protected final static boolean D = false;


    /** No arg constructor does nothing. */
    public ParameterConstraint() {}

    /** This value indicates if the value is editable after it is first set. */
    protected boolean editable = true;

    /** Every constraint has a assigned name - useful for displays and lookups. */
    protected String name = null;

    /** Inidcates whether null values are allowed as possible values. */
    protected boolean nullAllowed = false;

    /**
     *  Every parameter constraint has a name, this function returns that name.
     *  Useful for displays and lookups.
     */
    public String getName(){ return name; }

    /** Every parameter constraint has a name, this function sets that name. */
    public void setName(String name) throws EditableException{
        checkEditable(C + ": setName(): ");
        this.name = name;
    }

    /**
     *  Disables editing units, info, constraints, et. Basically all set()s disabled
     *  except for setValue().
     */
    public void setNonEditable() { editable = false; }

    /** Determines if the value can be edited, i.e. changed once set. */
    public boolean isEditable() { return editable; }

    /**
     * Helper function that throws an EditableException if
     * this constraint is currently not editable.
     */
    protected void checkEditable(String S) throws EditableException{
        if( !editable ) throw new EditableException( S +
            "This parameter is currently not editable"
        );
    }

    /**
     * Returns a copy so you can't edit or damage the origial.
     * All concrete subclasses must implement this.
     */
    public abstract Object clone();

    /** Sets if null values are allowed. If true nulls are allowed. */
    public void setNullAllowed(boolean nullAllowed) throws EditableException {
        checkEditable(C + ": setNullAllowed(): ");
        this.nullAllowed = nullAllowed;
    }
    /** Returns if null values are allowed. If true nulls are allowed. */
    public boolean isNullAllowed() {
        return nullAllowed;
    }
}
