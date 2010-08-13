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

package org.opensha.sha.imr.param.PropagationEffectParams;

import java.util.ArrayList;

import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.exceptions.EditableException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.exceptions.WarningException;
import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.DoubleDiscreteParameter;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterConstraint;
import org.opensha.commons.param.WarningDoubleParameter;
import org.opensha.commons.param.WarningParameterAPI;
import org.opensha.commons.param.editor.ConstrainedDoubleParameterEditor;
import org.opensha.commons.param.editor.DoubleParameterEditor;
import org.opensha.commons.param.editor.ParameterEditor;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;

/**
 * <b>Title:</b> WarningDoublePropagationEffectParameter<p>
 *
 * <b>Description:</b> Base Propagation Effect Parameter
 * that implements the WarningParameterAPI. This class
 * is only needed and distinct from the WarningDoubleParameter
 * because multiple inheritance is not supported in Java.
 * These PropagationEffect Parameters need a different
 * base class (PropagationEffectParameter) than the
 * WarningDoubleParameter ( DoubleParameter ). It basically
 * has the same functionality. See WarningDoublepParameter
 * for further documentation.
 * <p>
 *
 * @author Steven W. Rock
 * @version 1.0
 */
public abstract class WarningDoublePropagationEffectParameter
extends PropagationEffectParameter
implements WarningParameterAPI
{

	private transient ParameterEditor paramEdit = null;

	/** The warning constraint for this Parameter. */
	protected DoubleConstraint warningConstraint = null;

	/**
	 * Listeners that are interested in receiveing
	 * warnings when the warning constraints are exceeded.
	 * Only created if needed, else kept null, i.e. "Lazy Instantiation".
	 */
	protected transient ArrayList warningListeners = null;

	/**
	 * Set to true to turn off warnings, will automatically set the value,
	 * unless exceeds Absolute contrsints.
	 */
	protected boolean ignoreWarning;


	/**
	 * Set to true to turn off warnings, will automatically set the value, unless
	 * exceeds Absolute contrsints. Set to false so that warning constraints are
	 * enabled, i.e. throw a WarningConstraintException if exceed recommened warnings.
	 */
	public void setIgnoreWarning(boolean ignoreWarning) { this.ignoreWarning = ignoreWarning; }

	/**
	 * Returns warning constraint enabled/disabled. If true warnings are turned off ,
	 * will automatically set the value, unless exceeds Absolute contrsints.
	 * If set to false warning constraints are enabled, i.e. throw a
	 * WarningConstraintException if exceed recommened warnings.
	 */
	public boolean isIgnoreWarning() { return ignoreWarning; }




	/**
	 * Adds a listener to receive warning events when the warning constraints are exceeded.
	 * Only permitted if this parameter is currenlty editable, else an EditableException is thrown.
	 */
	public synchronized void addParameterChangeWarningListener( ParameterChangeWarningListener listener )
	throws EditableException
	{

		if( !this.editable ) throw new EditableException(C + ": setStrings(): " +
		"This constraint is currently not editable." );

		if ( warningListeners == null ) warningListeners = new ArrayList();
		if ( !warningListeners.contains( listener ) ) warningListeners.add( listener );

	}

	/**
	 * Adds a listener to receive warning events when the warning constraints are exceeded.
	 * Only permitted if this parameter is currenlty editable, else an EditableException is thrown.
	 */
	public synchronized void removeParameterChangeWarningListener( ParameterChangeWarningListener listener )
	throws EditableException
	{

		if( !this.editable ) throw new EditableException(C + ": setStrings(): " +
		"This constraint is currently not editable." );

		if ( warningListeners != null && warningListeners.contains( listener ) )
			warningListeners.remove( listener );
	}

	/**
	 * Sets the constraint if it is a DoubleConstraint and the parameter
	 *  is currently editable.
	 *
	 * @param warningConstraint     The new constraint for warnings
	 * @throws ParameterException   Thrown if the constraint is not a DoubleConstraint
	 * @throws EditableException    Thrown if the isEditable flag set to false.
	 */
	public void setWarningConstraint(ParameterConstraint warningConstraint)
	throws ParameterException, EditableException
	{
		if( !this.editable ) throw new EditableException(C + ": setStrings(): " +
		"This constraint is currently not editable." );

		this.warningConstraint = (DoubleConstraint)warningConstraint;
	}

	/** Returns the warning constraint. May return null. */
	public ParameterConstraint getWarningConstraint() throws ParameterException{
		return warningConstraint;
	}

	/**
	 *  Gets the min value of the constraint object. If the constraint
	 *  is not set returns null.
	 */
	public Object getWarningMin() throws Exception {
		if ( warningConstraint != null ) return warningConstraint.getMin();
		else return null;
	}


	/**
	 *  Returns the maximum allowed value of the constraint
	 *  object. If the constraint is not set returns null.
	 */
	public Object getWarningMax() {
		if ( warningConstraint != null ) return warningConstraint.getMax();
		else return null;

	}


	/**
	 *  Set's the parameter's value. There are several checks that must pass
	 *  before the value can be set.  The parameter must be currently editable,
	 *  else an EditableException is thrown. The warning constraints, if set will
	 *  throw a WarningException if exceeded. Finally if all other checks pass,
	 *  if the absoulte constraints are set, they cannot be exceeded. If they are
	 *  a Constraint Exception is thrown.
	 *
	 * @param  value                 The new value for this Parameter
	 * @throws  ParameterException   Thrown if the object is currenlty not
	 *      editable
	 * @throws  ConstraintException  Thrown if the object value is not allowed
	 */
	public synchronized void setValue( Object value ) throws ConstraintException, WarningException {

		String S = getName() + ": setValue(): ";
		if(D) System.out.println(S + "Starting: ");

		if ( !isAllowed( value ) ) {
			String err = S + "Value is not allowed: ";
			if( value != null ) err += value.toString();
			else err += "null value";

			if(D) System.out.println(err);
			throw new ConstraintException( err );
		}
		else if ( value == null ){
			if(D) System.out.println(S + "Setting allowed and recommended null value: ");
			this.value = null;
			org.opensha.commons.param.event.ParameterChangeEvent event = new org.opensha.commons.param.event.ParameterChangeEvent(
					this, getName(), getValue(), value );
			firePropertyChange( event );
		}
		else if ( !ignoreWarning && !isRecommended( value ) ) {

			if(D) System.out.println(S + "Firing Warning Event");

			ParameterChangeWarningEvent event = new
			ParameterChangeWarningEvent( (Object)this, this, this.value, value );

			fireParameterChangeWarning( event );
			throw new WarningException( S + "Value is not recommended: " + value.toString() );
		}
		else {
			if(D) System.out.println(S + "Setting allowed and recommended value: ");
			this.value = value;
			org.opensha.commons.param.event.ParameterChangeEvent event = new org.opensha.commons.param.event.ParameterChangeEvent(
					this, getName(), getValue(), value );
			firePropertyChange( event );
		}
		if(D) System.out.println(S + "Ending: ");
	}


	/**
	 *  Set's the parameter's value bypassing all checks including
	 *  the absolute constraint check. WARNING: SWR: This may be a bug.
	 *  Should we bypass the Absolute Constraints. ???
	 */
	public void setValueIgnoreWarning( Object value ) throws ConstraintException, ParameterException {
		//        this.value = value;
		super.setValue(value);
	}

	/**
	 *  Uses the constraint object to determine if the new value being set is
	 *  within recommended range. If no Constraints are present all values are
	 *  recommended, including null.
	 *
	 * @param  obj  Object to check if allowed via constraints
	 * @return      True if the value is allowed.
	 */
	public boolean isRecommended( Object obj ) {
		if ( warningConstraint != null ) return warningConstraint.isAllowed( (Double)obj );
		else return true;

	}


	/**
	 * Notifes all listeners of a ChangeWarningEvent has occured.
	 */
	public void fireParameterChangeWarning( ParameterChangeWarningEvent event ) {

		ArrayList vector;
		synchronized ( this ) {
			if ( warningListeners == null ) return;
			vector = ( ArrayList ) warningListeners.clone();
		}

		for ( int i = 0; i < vector.size(); i++ ) {
			ParameterChangeWarningListener listener = ( ParameterChangeWarningListener ) vector.get( i );
			listener.parameterChangeWarning( event );
		}

	}



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
	public int compareTo( Object obj ) throws ClassCastException {

		String S = C + ":compareTo(): ";

		if ( !( obj instanceof DoubleParameter )
				&& !( obj instanceof DoubleDiscreteParameter )
				&& !( obj instanceof WarningDoubleParameter )
				&& !( obj instanceof WarningDoublePropagationEffectParameter )
		) {
			throw new ClassCastException( S +
					"Object not a DoubleParameter, WarningDoubleParameter, DoubleDiscreteParameter, DistanceJBParameter, or WarningDoublePropagationEffectBParameter, unable to compare"
			);
		}

		int result = 0;

		Double n1 = ( Double ) this.getValue();
		Double n2 = null;

		if ( obj instanceof DoubleParameter ) {
			DoubleParameter param = ( DoubleParameter ) obj;
			n2 = ( Double ) param.getValue();
		}
		else if ( obj instanceof DoubleDiscreteParameter ) {
			DoubleDiscreteParameter param = ( DoubleDiscreteParameter ) obj;
			n2 = ( Double ) param.getValue();
		}
		else if ( obj instanceof WarningDoubleParameter ) {
			WarningDoubleParameter param = ( WarningDoubleParameter ) obj;
			n2 = ( Double ) param.getValue();
		}

		else if ( obj instanceof WarningDoublePropagationEffectParameter ) {
			WarningDoublePropagationEffectParameter param = ( WarningDoublePropagationEffectParameter ) obj;
			n2 = ( Double ) param.getValue();
		}

		return n1.compareTo( n2 );
	}




	/**
	 *  Compares value to see if equal.
	 *
	 * @param  obj                     The object to compare this to
	 * @return                         True if the values are identical
	 * @exception  ClassCastException  Is thrown if the comparing object is not
	 *      a DoubleParameter, or DoubleDiscreteParameter.
	 */
	public boolean equals( Object obj ) throws ClassCastException {
		String S = C + ":equals(): ";

		if ( !( obj instanceof DoubleParameter )
				&& !( obj instanceof DoubleDiscreteParameter )
				&& !( obj instanceof WarningDoubleParameter )
				&& !( obj instanceof WarningDoublePropagationEffectParameter )
		) {
			throw new ClassCastException( S + "Object not a DoubleParameter, WarningDoubleParameter, or DoubleDiscreteParameter, unable to compare" );
		}

		String otherName = ( ( ParameterAPI ) obj ).getName();
		if ( ( compareTo( obj ) == 0 ) && getName().equals( otherName ) ) {
			return true;
		}
		else return false;
	}

	/**
	 * Standard Java function. Creates a copy of this class instance
	 * so originaly can not be modified
	 */
	public abstract Object clone();

	public ParameterEditor getEditor() {
		if (paramEdit == null) {
			try {
				if (constraint == null)
					paramEdit = new DoubleParameterEditor(this);
				else
					paramEdit = new ConstrainedDoubleParameterEditor(this);
			} catch (Exception e) {
				throw new RuntimeException(e);
			}
		}
		return paramEdit;
	}

}
