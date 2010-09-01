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

import org.dom4j.Element;
import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.param.editor.ConstrainedIntegerParameterEditor;
import org.opensha.commons.param.editor.IntegerParameterEditor;
import org.opensha.commons.param.editor.ParameterEditor;

/**
 *  <b>Title:</b> IntegerParameter<p>
 *
 *  <b>Description:</b> A Parameter that accepts Integers as it's values.
 * If constraints are present, setting the value must pass the constraint
 * check. Since the parameter class in an ancestor, all the parameter's fields are
 * inherited. <p>
 *
 * The constraints are IntegerConstraint which means a min and max values are
 * stored in the constraint that setting the parameter's value cannnt exceed.
 * If no constraint object is present then all values are permitted. <p>
 *
 * This class also extends DependentParameter so it may have a list of
 * independent parameters that it depends upon. <p>
 *
 * @see DependentParameter
 * @see DependentParameterAPI
 * @see ParameterAPI
 * @see Parameter
 * @see IntegerConstraint
 * @author     Sid Hellman, Steven W. Rock
 * @created    February 21, 2002
 * @version    1.0
 */
public class IntegerParameter
extends DependentParameter<Integer>
implements DependentParameterAPI<Integer>, ParameterAPI<Integer>
{

	/** Class name for debugging. */
	protected final static String C = "IntegerParameter";
	/** If true print out debug statements. */
	protected final static boolean D = false;

	private transient ParameterEditor paramEdit = null;
	
	/**
	 * Constructor with no constraints specified, all values are allowed.
	 * Also Sets the name of this parameter.
	 */
	public IntegerParameter( String name ) {
		super( name, null, null, null );
	}


	/**
	 * Constructor with no No constraints specified, all values are allowed.
	 * Sets the name and untis of this parameter.
	 */
	public IntegerParameter( String name, String units ) throws ConstraintException {
		this( name, null, units, null );
	}


	/**
	 *  Sets the name, defines the constraints min and max values. Creates the
	 *  constraint object from these values.
	 *
	 * @param  name                     Name of the parameter
	 * @param  min                      defines min of allowed values
	 * @param  max                      defines max of allowed values
	 * @exception  ConstraintException  thrown if the value is not allowed
	 * @throws  ConstraintException     Is thrown if the value is not allowed
	 */
	public IntegerParameter( String name, int min, int max ) throws ConstraintException {
		super( name, new IntegerConstraint( min, max ), null, null );
		//this.constraint.setName( name );
	}


	/**
	 *  Sets the name, defines the constraints min and max values, and sets the
	 *  units. Creates the constraint object from these values.
	 *
	 * @param  name                     Name of the parameter
	 * @param  min                      defines min of allowed values
	 * @param  max                      defines max of allowed values
	 * @param  units                    Units of this parameter
	 * @exception  ConstraintException  thrown if the value is not allowed
	 * @throws  ConstraintException     Is thrown if the value is not allowed
	 */
	public IntegerParameter( String name, int min, int max, String units ) throws ConstraintException {
		super( name, new IntegerConstraint( min, max ), null, null );
		//this.constraint.setName( name );
	}


	/**
	 *  Sets the name, defines the constraints min and max values. Creates the
	 *  constraint object from these values.
	 *
	 * @param  name                     Name of the parametet
	 * @param  min                      defines min of allowed values
	 * @param  max                      defines max of allowed values
	 * @exception  ConstraintException  thrown if the value is not allowed
	 * @throws  ConstraintException     Is thrown if the value is not allowed
	 */
	public IntegerParameter( String name, Integer min, Integer max ) throws ConstraintException {
		super( name, new IntegerConstraint( min, max ), null, null );
		//this.constraint.setName( name );
	}


	/**
	 *  Sets the name, defines the constraints min and max values. Creates the
	 *  constraint object from these values.
	 *
	 * @param  name                     Name of the parametet
	 * @param  min                      defines min of allowed values
	 * @param  max                      defines max of allowed values
	 * @exception  ConstraintException  thrown if the value is not allowed
	 * @throws  ConstraintException     Is thrown if the value is not allowed
	 */
	public IntegerParameter( String name, Integer min, Integer max, String units ) throws ConstraintException {
		super( name, new IntegerConstraint( min, max ), null, null );
		//this.constraint.setName( name );
	}


	/**
	 *  Sets the name, defines the constraints min and max values. Creates the
	 *  constraint object from these values.
	 *
	 * @param  name                     Name of the parametet
	 * @param  min                      defines min of allowed values
	 * @param  max                      defines max of allowed values
	 * @exception  ConstraintException  thrown if the value is not allowed
	 * @throws  ConstraintException     Is thrown if the value is not allowed
	 */
	public IntegerParameter( String name, IntegerConstraint constraint ) throws ConstraintException {
		super( name, constraint, null, null );
		//if( this.constraint.getName() == null ) this.constraint.setName( this.name );
	}


	/**
	 *  Sets the name, constraints, and sets the units.
	 *
	 * @param  name                     Name of the parameter
	 * @param  constraint               defines min and max range of allowed
	 *      values
	 * @param  units                    Units of this parameter
	 * @exception  ConstraintException  thrown if the value is not allowed
	 * @throws  ConstraintException     Is thrown if the value is not
	 *      allowed one. Null values are always allowed in the
	 *      constructors
	 */
	public IntegerParameter( String name, IntegerConstraint constraint, String units ) throws ConstraintException {
		super( name, constraint, units, null );
		//if( this.constraint.getName() == null ) this.constraint.setName( this.name );
	}


	/**
	 *  No constraints specified, all values allowed. Sets the name and value.
	 *
	 * @param  name   Name of the parameter
	 * @param  value  Integer value of this parameter
	 */
	public IntegerParameter( String name, Integer value ) {
		super(name, null, null, value);
	}


	/**
	 *  Sets the name, units and value. All values allowed because constraints
	 *  not set.
	 *
	 * @param  name                     Name of the parametet
	 * @param  value                    Integer value of this parameter
	 * @param  units                    Units of this parameter
	 * @exception  ConstraintException  thrown if the value is not allowed
	 * @throws  ConstraintException     Is thrown if the value is not allowed
	 */
	public IntegerParameter( String name, String units, Integer value ) throws ConstraintException {
		super( name, null, units, value );
	}


	/**
	 *  Sets the name, and value. Also defines the min and max from which the
	 *  constraint is constructed.
	 *
	 * @param  name                     Name of the parameter
	 * @param  value                    Integer value of this parameter
	 * @param  min                      defines max of allowed values
	 * @param  max                      defines min of allowed values
	 * @exception  ConstraintException  thrown if the value is not allowed
	 * @throws  ConstraintException     Is thrown if the value is not allowed
	 */
	public IntegerParameter( String name, int min, int max, Integer value ) throws ConstraintException {
		super( name, new IntegerConstraint( min, max ), null, value );
		//if( this.constraint.getName() == null ) this.constraint.setName( this.name );
	}

	/**
	 *  Sets the name, and value. Also defines the min and max from which the
	 *  constraint is constructed.
	 *
	 * @param  name                     Name of the parameter
	 * @param  value                    Integer value of this parameter
	 * @param  min                      defines max of allowed values
	 * @param  max                      defines min of allowed values
	 * @exception  ConstraintException  thrown if the value is not allowed
	 * @throws  ConstraintException     Is thrown if the value is not allowed
	 */
	public IntegerParameter( String name, Integer min, Integer max, Integer value ) throws ConstraintException {
		super( name, new IntegerConstraint( min, max ), null, value );
		//if( this.constraint.getName() == null ) this.constraint.setName( this.name );
	}


	/**
	 *  Sets the name, value and constraint. The value is checked if it is
	 *  within constraints.
	 *
	 * @param  name                     Name of the parameter
	 * @param  constraint               defines min and max range of allowed
	 *      values
	 * @param  value                    Integer value of this parameter
	 * @exception  ConstraintException  thrown if the value is not allowed
	 * @throws  ConstraintException     Is thrown if the value is not allowed
	 */
	public IntegerParameter( String name, IntegerConstraint constraint, Integer value ) throws ConstraintException {
		super( name, constraint, null, value );
		//if( this.constraint.getName() == null ) this.constraint.setName( this.name );
	}


	/**
	 *  Sets all values, and the constraint is created from the min and max
	 *  values. The value is checked if it is within constraints.
	 *
	 * @param  name                     Name of the parameter
	 * @param  value                    Integer value of this parameter
	 * @param  min                      defines min of allowed values
	 * @param  max                      defines max of allowed values
	 * @param  units                    Units of this parameter
	 * @exception  ConstraintException  Is thrown if the value is not allowed
	 * @throws  ConstraintException     Is thrown if the value is not allowed
	 */
	public IntegerParameter( String name, int min, int max, String units, Integer value ) throws ConstraintException {
		super( name, new IntegerConstraint( min, max ), units, value );
		//if( this.constraint.getName() == null ) this.constraint.setName( this.name );
	}

	/**
	 *  Sets all values, and the constraint is created from the min and max
	 *  values. The value is checked if it is within constraints.
	 *
	 * @param  name                     Name of the parameter
	 * @param  value                    Integer value of this parameter
	 * @param  min                      defines min of allowed values
	 * @param  max                      defines max of allowed values
	 * @param  units                    Units of this parameter
	 * @exception  ConstraintException  Is thrown if the value is not allowed
	 * @throws  ConstraintException     Is thrown if the value is not allowed
	 */
	public IntegerParameter( String name, Integer min, Integer max, String units, Integer value ) throws ConstraintException {
		super( name, new IntegerConstraint( min, max ), units, value );
		//if( this.constraint.getName() == null ) this.constraint.setName( this.name );
	}


	/**
	 *  This is the main constructor. All other constructors call this one.
	 *  Constraints must be set first, because the value may not be an allowed
	 *  one. Null values are always allowed in the constructor. If the
	 *  constraints are null, all values are allowed.
	 *
	 * @param  name                     Name of the parameter
	 * @param  constraint               defines min and max range of allowed
	 *      values
	 * @param  value                    Integer value of this parameter
	 * @param  units                    Units of this parameter
	 * @exception  ConstraintException  Is thrown if the value is not allowed
	 * @throws  ConstraintException     Is thrown if the value is not allowed
	 */
	public IntegerParameter( String name, IntegerConstraint constraint, String units, Integer value )
	throws ConstraintException {
		super( name, constraint, units, value );
		//if( this.constraint.getName() == null ) this.constraint.setName( this.name );
	}

	/**
	 * Sets the constraint if it is a StringConstraint and the parameter
	 * is currently editable. If this parameter is set non-editable
	 * an EditableConstraint is thrown.
	 */
	public void setConstraint(ParameterConstraintAPI constraint) throws ParameterException{

		String S = C + ": setConstraint(): ";
		checkEditable(S);

		if ( !(constraint instanceof IntegerConstraint )) {
			throw new ParameterException( S +
					"This parameter only accepts IntegerConstraints, unable to set the constraint."
			);
		}
		else super.setConstraint( constraint );

	}

	/**
	 *  Determine if the new value being set is allowed.
	 *
	 * @param  obj  Object to check if allowed via constraints
	 * @return      True if the value is allowed
	 */
	public boolean isAllowed( int i ){
		return isAllowed( new Integer(i) );
	}



	/**
	 * Returns the min value of the constraint object. Null is
	 * returned if there are no constraints set.
	 */
	public Integer getMin() throws Exception {
		if ( constraint != null )
			return ( ( IntegerConstraint ) constraint ).getMin() ;
		else return null;
	}


	/**
	 * Returns the min value of the constraint object. Null is
	 * returned if there are no constraints set.
	 */
	public Integer getMax() {
		if ( constraint != null )
			return ( ( IntegerConstraint ) constraint ).getMax();
		else return null;
	}


	/**
	 * Returns the type of this parameter. The type is just the classname
	 * if no constraints are present, else "Constrained" is prepended to the
	 * classname. The type is used to determine which parameter GUI editor
	 * to use.
	 */
	public String getType() {
		String type = C;
		// Modify if constrained
		ParameterConstraintAPI constraint = this.constraint;
		if (constraint != null) type = "Constrained" + type;
		return type;
	}


	/**
	 * Returns the type of this parameter. The type is just the classname
	 * if no constraints are present, else "Constrained" is prepended to the
	 * classname. The type is used to determine which parameter GUI editor
	 * to use.
	 */
	public int compareTo( Object obj ) throws ClassCastException {

		String S = C + ":compareTo(): ";

		if ( !( obj instanceof IntegerParameter ) )
			throw new ClassCastException( S + "Object not a IntegerParameter, unable to compare" );


		IntegerParameter param = ( IntegerParameter ) obj;

		int result = 0;

		Integer n1 = ( Integer ) this.getValue();
		Integer n2 = ( Integer ) param.getValue();

		return n1.compareTo( n2 );
	}


	/**
	 *  Compares value to see if equal.
	 *
	 * @param  obj                     The object to compare this to
	 * @return                         True if the values are identical
	 * @exception  ClassCastException  Is thrown if the comparing object is not
	 *      a IntegerParameter.
	 */
	public boolean equals( Object obj ) throws ClassCastException {

		String S = C + ":equals(): ";

		if ( !( obj instanceof IntegerParameter ) )
			throw new ClassCastException( S + "Object not a IntegerParameter, unable to compare" );

		String otherName = ( ( IntegerParameter ) obj ).getName();
		if ( ( compareTo( obj ) == 0 ) && getName().equals( otherName ) )
			return true;
		else return false;

	}


	/** Returns a copy so you can't edit or damage the original. */
	public Object clone() {
		IntegerConstraint c1=null;
		if(constraint != null)
			c1 = ( IntegerConstraint ) constraint.clone();
		IntegerParameter param = null;
		if( value == null ) param = new IntegerParameter( name, c1, units);
		else param = new IntegerParameter( name, c1, units, new Integer( this.value.toString() )  );
		if( param == null ) return null;
		param.editable = true;
		param.info = info;
		return param;
	}


	public boolean setIndividualParamValueFromXML(Element el) {
		try {
			int val = Integer.parseInt(el.attributeValue("value"));
			this.setValue(val);
			return true;
		} catch (NumberFormatException e) {
			e.printStackTrace();
			return false;
		}
	}

	public ParameterEditor getEditor() {
		if (paramEdit == null) {
			try {
				if (constraint == null)
					paramEdit = new IntegerParameterEditor(this);
				else
					paramEdit = new ConstrainedIntegerParameterEditor(this);
			} catch (Exception e) {
				throw new RuntimeException(e);
			}
		}
		return paramEdit;
	}

}
