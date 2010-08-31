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

import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;

/**
 * <b>Title:</b> WarningParameterAPI<p>
 *
 * <b>Description:</b> This interface must be implemented by
 * all parameters that will provide a warning that the
 * constraints are being exeeceded. This differes from a normal
 * constraint in that a normal constraint cannot be ignored,
 * whereas a warning constraint will provide notification, but can
 * be ignored when setting values. So implementing parameters
 * will have two constraints, the WarningConstraint and the
 * regular absolute Constraint. <p>
 *
 * WARNING: One flaw with this design is that this interface is hardwired
 * to deal with Doubles as the value of the constraint. This is
 * really a DoubleWarningParameterAPI. <p>
 *
 * @author Steven W. Rock
 * @version 1.0
 */

public interface WarningParameterAPI<E> extends ParameterAPI<E> {

    /** Sets a flag to ignore the warning - overides constraint */
    public void setIgnoreWarning(boolean ignoreWarning);
    /** Returns true if constraint warning will be ignored */
    public boolean isIgnoreWarning();

    /** Sets the warning constraint in this parameter as a ParameterConstraint. */
    public void setWarningConstraint(ParameterConstraint warningConstraint);

    /** Gets the warning constraint in this parameter as a ParameterConstraint. */
    public ParameterConstraint getWarningConstraint() throws ParameterException;


    /**
     * Adds a parameter change warning listener who will receive notification
     * events when the warning constraints are exceeded.
     */
    public void addParameterChangeWarningListener( ParameterChangeWarningListener listener );

    /**
     * Removes a parameter change warning listener who was receiving notification
     * events when the warning constraints were exceeded.
     */
    public void removeParameterChangeWarningListener( ParameterChangeWarningListener listener );




    /**
     * Uses the constraint object to determine if the new value being set is within
     * recommended range. If no Constraints are present all values are recommended.
     *
     * @param  obj  Object to check if allowed via constraints
     * @return      True if the value is allowed
     */
    public boolean isRecommended( E obj );

    /**
     * Set's the parameter's value bypassing the warning constraint. This is
     * how warnings are ignored.
     *
     * @param  value                 The new value for this Parameter
     * @throws  ParameterException   Thrown if the object is currenlty not
     *      editable
     * @throws  ConstraintException  Thrown if the object value is not allowed as determined
     * by the absolute constraints.
     */
    public void setValueIgnoreWarning( E value ) throws ConstraintException, ParameterException;


    /**
     *  This is the warning event notification system that notifies all
     * listeners when a warning has occured.
     */
    public void fireParameterChangeWarning( ParameterChangeWarningEvent event );


    /**
     *  Compares the values to if this is less than, equal to, or greater than
     *  the comparing objects.
     *
     * @param  obj                     The object to compare this to
     * @return                         -1 if this value < obj value, 0 if equal,
     *      +1 if this value > obj value
     * @exception  ClassCastException  Is thrown if the comparing object is not
     *      a DoubleParameter, or DoubleDiscreteParameter.
     */
    public int compareTo( Object obj ) throws ClassCastException;

    /**
     *  Compares value to see if equal.
     * @param  obj                     The object to compare this to
     * @return                         True if the values are identical
     * @exception  ClassCastException  Is thrown if the comparing object is not
     *      a DoubleParameter, or DoubleDiscreteParameter.
     */
    public boolean equals( Object obj ) throws ClassCastException ;

    /**
     *  Returns a copy so you can't edit or damage the origial.
     * @return    Exact copy of this object's state
     */
    public Object clone() ;


    /**
     * Gets the min Double value of the warning constraint.
     * @return                The min value
     * @exception  Exception  Description of the Exception
     */
    public E getWarningMin() throws Exception ;


    /**
     * Gets the max Double value of the warning constraint.
     * @return    The max value
     */
    public E getWarningMax() ;

}
