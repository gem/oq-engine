/**
 * 
 */
package org.opensha.commons.param;

import org.dom4j.Element;
import org.opensha.commons.data.ValueWeight;
import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.exceptions.EditableException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.param.editor.DoubleValueWeightParameterEditor;
import org.opensha.commons.param.editor.ParameterEditor;

/**
 * <b>Title:</b> DoubleValueWeightParameter<p>
 * 
 *  <b>Description:</b> Generic Data Object that contains a ValueWeight object and
 *  optionally a min/ max  for values and min/max  for weights stored in a constraint object. If no
 *  constraint object is present then all values should be permitted.
 *  The units are applied to value and weight is assumed to be unitless.
 *  <p>
 *  
 *  @author vipingupta
 *
 */
public class DoubleValueWeightParameter extends DependentParameter
				implements DependentParameterAPI, ParameterAPI {
	  /** Class name for debugging. */
    protected final static String C = "DoubleValueWeightParameter";
    /** If true print out debug statements. */
    protected final static boolean D = false;
    
    private transient ParameterEditor paramEdit = null;


    /**
     *  No constraints specified, all values allowed. Sets the name of this
     *  parameter.
     *
     * @param  name  Name of the parameter
     */
    public DoubleValueWeightParameter( String name ) {
        super( name, null, null, null );
    }


    /**
     *  No constraints specified, all values allowed. Sets the name and untis of
     *  this parameter.
     *
     * @param  name   Name of the parameter
     * @param  units  Units of this parameter
     */
    public DoubleValueWeightParameter( String name, String units ) {
        super( name, null, units, null );
    }


    /**
     *  Sets the name, defines the constraints min and max values and weights. Creates the
     *  constraint object from these values.
     *
     * @param  name                     Name of the parameter
     * @param  minVal                   defines min of allowed values
     * @param  maxVal                   defines max of allowed values
     * @param  minWt					 defines min of allowed weights	
     * @param  maxWt					 defines max of allowed weights
     * @exception  ConstraintException  thrown if the value is not allowed
     * @throws  ConstraintException     Is thrown if the value is not allowed
     */
    public DoubleValueWeightParameter( String name, double minVal, double maxVal, double minWt, double maxWt ) throws ConstraintException {
        super( name, new DoubleValueWeightConstraint( minVal, maxVal, minWt, maxWt ), null, null );
    }


    /**
     *  Sets the name, defines the constraints min and max values and weights, and sets the
     *  units. Creates the constraint object from these values.
     *
     * @param  name                     Name of the parameter
     * @param  minVal                   defines min of allowed values
     * @param  maxVal                   defines max of allowed values
     * @param  minWt					 defines min of allowed weights
     * @param  maxWt					 defines max of allowed weights	
     * @param  units                    Units of this parameter
     * @exception  ConstraintException  thrown if the value is not allowed
     * @throws  ConstraintException     Is thrown if the value is not allowed
     */
    public DoubleValueWeightParameter( String name, double minVal, double maxVal, double minWt, double maxWt, String units ) throws ConstraintException {
        super( name, new DoubleValueWeightConstraint( minVal, maxVal, minWt, maxWt ), units, null );
    }


     /**  Sets the name, defines the constraints min and max values. Creates the
     *  constraint object from these values.
     *
     * @param  name                     Name of the parameter
     * @param  minVal                   defines min of allowed values
     * @param  maxVal                   defines max of allowed values
     * @param  minWt					 defines min of allowed weights
     * @param  maxWt					 defines max of allowed weights	
     * @exception  ConstraintException  thrown if the value is not allowed
     * @throws  ConstraintException     Is thrown if the value is not allowed
     */
    public DoubleValueWeightParameter( String name, Double minVal, Double maxVal, Double minWt, Double maxWt ) throws ConstraintException {
        super( name, new DoubleValueWeightConstraint( minVal, maxVal, minWt, maxWt ), null, null );
    }


    /**
     *  Sets the name, defines the constraints min and max values and weights, and sets the
     *  units. Creates the constraint object from these values.
     *
     * @param  name                     Name of the parameter
     * @param  minVal                   defines min of allowed values
     * @param  maxVal                   defines max of allowed values
     * @param  minWt					 defines min of allowed weights
     * @param  maxWt					 defines max of allowed weights	
     * @param  units                    Units of this parameter
     * @exception  ConstraintException  thrown if the value is not allowed
     * @throws  ConstraintException     Is thrown if the value is not allowed
     */
    public DoubleValueWeightParameter( String name, Double minVal, Double maxVal, Double minWt, Double maxWt, String units ) throws ConstraintException {
        super( name, new DoubleValueWeightConstraint( minVal, maxVal, minWt, maxWt ), units, null );
    }


    /**
     *  Sets the name and Constraints object.
     *
     * @param  name                     Name of the parameter
     * @param  constraint               defines min and max range of allowes values and weights
     * @exception  ConstraintException  thrown if the value is not allowed
     * @throws  ConstraintException     Is thrown if the value is not allowed
     */
    public DoubleValueWeightParameter( String name, DoubleValueWeightConstraint constraint ) throws ConstraintException {
        super( name, constraint, null, null );
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
     *      allowedallowed one. Null values are always allowed in the
     *      constructors
     */
    public DoubleValueWeightParameter( String name, DoubleValueWeightConstraint constraint, String units ) throws ConstraintException {
        super( name, constraint, units, null );
     }


    /**
     *  No constraints specified, all values allowed. Sets the name, value and weight.
     *
     * @param  name   Name of the parameter
     * @param  value   ValueWeight value of this parameter
     * @param weight  Double weight of this value 
     */
    public DoubleValueWeightParameter( String name, ValueWeight value ) {
        super(name, null, null, value);
    }


    /**
     *  Sets the name, units, value. All values and weights allowed because constraints.
     *  not set.
     *
     * @param  name                     Name of the parameter
     * @param  value                    ValueWeight value of this parameter
     * @param  units                    Units of this parameter
     * @exception  ConstraintException  thrown if the value is not allowed
     * @throws  ConstraintException     Is thrown if the value is not allowed
     */
    public DoubleValueWeightParameter( String name, String units, ValueWeight value ) throws ConstraintException {
        super( name, null, units, value );
    }


    /**
     *  Sets the name and value. Also defines the min and max for value and weight from which the
     *  constraint is constructed.
     *
     * @param  name                     Name of the parameter
     * @param  value                    ValueWeight value of this parameter
     * @param  minVal                   defines min of allowed values
     * @param  maxVal                   defines max of allowed values
     * @param  minWt					 defines min of allowed weights
     * @param  maxWt					 defines max of allowed weights
     * @exception  ConstraintException  thrown if the value is not allowed
     * @throws  ConstraintException     Is thrown if the value is not allowed
     */
    public DoubleValueWeightParameter( String name, double minVal, double maxVal, double minWt, double maxWt, ValueWeight value ) throws ConstraintException {
        super( name, new DoubleValueWeightConstraint( minVal, maxVal, minWt, maxWt ), null, value );
    }


    /**
     *  Sets the name and value. Also defines the min and max from which the
     *  constraint is constructed.
     *
     * @param  name                     Name of the parameter
     * @param  value                    ValueWeight value of this parameter
     * @param  minVal                   defines min of allowed values
     * @param  maxVal                   defines max of allowed values
     * @param minWt						 defines min of allowed weights
     * @param maxWt						 defines max of allowed weight
     * @exception  ConstraintException  thrown if the value is not allowed
     * @throws  ConstraintException     Is thrown if the value is not allowed
     */
    public DoubleValueWeightParameter( String name, Double minVal, Double maxVal, Double minWt, Double maxWt, ValueWeight value) throws ConstraintException {
        super( name, new DoubleValueWeightConstraint( minVal, maxVal, minWt, maxWt ), null, value );
    }

    /**
     *  Sets the name, value and constraint. The value is checked if it is
     *  within constraints.
     *
     * @param  name                     Name of the parameter
     * @param  constraint               defines min and max range of allowed
     *      values
     * @param  value                    Double value of this parameter
     * @exception  ConstraintException  thrown if the value is not allowed
     * @throws  ConstraintException     Is thrown if the value is not allowed
     */
    public DoubleValueWeightParameter( String name, DoubleConstraint constraint, ValueWeight value) throws ConstraintException {
        super( name, constraint, null, value );
    }


    /**
     *  Sets all values, and the constraint is created from the min and max
     *  values. The value is checked if it is within constraints.
     *
     * @param  name                     Name of the parameter
     * @param  value                    ValueWeight value of this parameter
     * @param  minVal                   defines min of allowed values
     * @param  maxVal                   defines max of allowed values
     * @param  minWt					 defines min of allowed weights
     * @param  maxWt					 defines max of allowed weights		
     * @param  units                    Units of this parameter
     * @exception  ConstraintException  Is thrown if the value is not allowed
     * @throws  ConstraintException     Is thrown if the value is not allowed
     */
    public DoubleValueWeightParameter( String name, double minVal, double maxVal, double minWt, double maxWt, String units, ValueWeight value ) throws ConstraintException {
        super( name, new DoubleValueWeightConstraint( minVal, maxVal, minWt, maxWt ), units, value );
    }


    /**
     *  Sets value and the constraint is created from the min and max
     *  values. The value and weight are checked if they are  within constraints.
     *
     * @param  name                     Name of the parameter
     * @param  value                    ValueWeight value of this parameter
     * @param  minVal                   defines min of allowed values
     * @param  maxVal                   defines max of allowed values
     * @param  minWt					 defines min of allowed weights
     * @param  maxWt					 defines max of allowed weights
     * @param  units                    Units of this parameter
     * @exception  ConstraintException  Is thrown if the value is not allowed
     * @throws  ConstraintException     Is thrown if the value is not allowed
     */
    public DoubleValueWeightParameter( String name, Double minVal, Double maxVal, Double minWt, Double maxWt, String units, ValueWeight value ) throws ConstraintException {
        super( name, new DoubleValueWeightConstraint( minVal, maxVal, minWt, maxWt ), units, value );
    }


    /**
     *  Constraints must be set first, because the value may not be an allowed
     *  one. Null values are always allowed in the constructor. If the
     *  constraints are null, all values are allowed.
     *
     * @param  name                     Name of the parameter
     * @param  constraint               defines min and max range of allowed
     *      values and weights
     * @param  value                    ValueWeight value of this parameter
     * @param  units                    Units of this parameter
     * @exception  ConstraintException  Is thrown if the value is not allowed
     * @throws  ConstraintException     Is thrown if the value is not allowed
     */

    public DoubleValueWeightParameter( String name, DoubleValueWeightConstraint constraint, String units, ValueWeight value )
             throws ConstraintException {
        super( name, constraint, units, value );
    }



    /**
     * Sets the constraint if it is a DoubleValueWeightConstraint and the parameter
     * is currently editable.
     *
     * @param constraint            The new constraint.
     * @throws ParameterException   Thrown if constraint is not a DoubleValueWeightConstraint.
     * @throws EditableException    Thrown if the parameter is currently uneditable.
     */
    public void setConstraint(ParameterConstraintAPI constraint)
        throws ParameterException, EditableException
    {

        String S = C + ": setConstraint(): ";
        checkEditable(S);

        if ( !(constraint instanceof DoubleValueWeightConstraint )) {
            throw new ParameterException( S +
                "This parameter only accepts DoubleValueWeightConstraint, unable to set the constraint."
            );
        }
        else super.setConstraint( constraint );

    }

    /** Gets the min value of the constraint object. */
    public Double getMinVal() throws Exception {
        if ( constraint != null ) return ( ( DoubleValueWeightConstraint ) constraint ).getMinVal();
        else return null;
    }


    /** Returns the maximum allowed values. */
    public Double getMaxVal() {
        if ( constraint != null ) return ( ( DoubleValueWeightConstraint ) constraint ).getMaxVal();
        else return null;
    }


    /** Gets the min weight of the constraint object. */
    public Double getMinWeight() throws Exception {
        if ( constraint != null ) return ( ( DoubleValueWeightConstraint ) constraint ).getMinWt();
        else return null;
    }


    /** Returns the maximum allowed weight. */
    public Double getMaxWeight() {
        if ( constraint != null ) return ( ( DoubleValueWeightConstraint ) constraint ).getMaxWt();
        else return null;
    }


    /**
     *  Gets the type of this parameter. Used by the Editor framework to decide
     *  what type of editor to create for this parameter.
     */
    public String getType() {
        String type = C;
        // Modify if constrained
       // ParameterConstraintAPI constraint = this.constraint;
       // if (constraint != null) type = "Constrained" + type;
        return type;
    }


    /**
     *  Compares the values to if this is less than, equal to, or greater than
     *  the comparing objects. Weight is irrelevant in this case
     *
     * @param  obj                     The object to compare this to
     * @return                         -1 if this value < obj value, 0 if equal,
     *      +1 if this value > obj value
     * @exception  ClassCastException  Is thrown if the comparing object is not
     *      a DoubleValueWeightParameter.
     */
    public int compareTo( Object obj ) throws ClassCastException {

        String S = C + ":compareTo(): ";

        if ( !( obj instanceof DoubleValueWeightParameter ) ) {
            throw new ClassCastException( S + "Object not a DoubleValueWeightParameter, unable to compare" );
        }

        ValueWeight n1 = ( ValueWeight ) this.getValue();
        DoubleValueWeightParameter param = ( DoubleValueWeightParameter ) obj;
        ValueWeight n2 = ( ValueWeight ) param.getValue();;
        return n1.compareTo( n2 );
    }


    /**
     *  Set's the parameter's value.
     *
     * @param  value                 The new value for this Parameter
     * @throws  ParameterException   Thrown if the object is currenlty not
     *      editable.
     * @throws  ConstraintException  Thrown if the object value is not allowed.
     */
    public void setValue( ValueWeight value ) throws ConstraintException, ParameterException {
        setValue(value );
    }

    /**
     *  Uses the constraint object to determine if the new value being set is
     *  allowed. If no Constraints are present all values are allowed. This
     *  function is now available to all subclasses, since any type of
     *  constraint object follows the same api.
     *
     * @param  obj  Object to check if allowed via constraints
     * @return      True if the value is allowed
     */
    public boolean isAllowed( ValueWeight d ) {
        return isAllowed( (Object)d );
    }

    /**
     *
     *  Uses the constraint object to determine if the new value being set is
     *  allowed. If no Constraints are present all values are allowed. This
     *  function is now available to all subclasses, since any type of
     *  constraint object follows the same api.
     *
     * @param  obj  Object to check if allowed via constraints, must be object of type
     * ValueWeight else it will return false
     * @return      True if the value is allowed
     */
    public boolean isAllowed(Object valueWeight){
      if (valueWeight instanceof ValueWeight || (valueWeight==null))
        return super.isAllowed(valueWeight);
      return false;
    }

  

    /**
     *  Compares the names and value to see if they are same.
     *
     * @param  obj                     The object to compare this to
     * @return                         True if the values and names are identical
     * @exception  ClassCastException  Is thrown if the comparing object is not
     *      a DoubleValueWeightParameter.
     */
    public boolean equals( Object obj ) throws ClassCastException {
        String S = C + ":equals(): ";

        if ( !( obj instanceof DoubleValueWeightParameter ) ) {
            throw new ClassCastException( S + "Object not a DoubleValueWeightParameter,  unable to compare" );
        }

        String otherName = ( ( DoubleValueWeightParameter ) obj ).getName();
        if ( ( compareTo( obj ) == 0 ) && getName().equals( otherName ) ) {
            return true;
        } else {
            return false;
        }
    }


    /** Returns a copy so you can't edit or damage the origial. */
    public Object clone() {
    	DoubleValueWeightConstraint c1=null;
      if(constraint != null)
        c1 = ( DoubleValueWeightConstraint ) constraint.clone();
      	DoubleValueWeightParameter param = null;
        if( value == null ) param = new DoubleValueWeightParameter( name, c1, units);
        else param = new DoubleValueWeightParameter( name, c1, units, (ValueWeight)( (ValueWeight) this.value).clone()  );
        if( param == null ) return null;
        param.editable = true;
        param.info = info;
        return param;
    }


	public boolean setIndividualParamValueFromXML(Element el) {
		// TODO Auto-generated method stub
		return false;
	}


	public ParameterEditor getEditor() {
		if (paramEdit == null) {
			try {
				paramEdit = new DoubleValueWeightParameterEditor(this);
				// ConstrainedDoubleValueWeightParameterEditor hasn't been implemented yet, although the
				// class exists
//				else
//					paramEdit = new ConstrainedDoubleValueWeightParameterEditor(this);
			} catch (Exception e) {
				throw new RuntimeException(e);
			}
		}
		return paramEdit;
	}
}
