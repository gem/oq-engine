/**
 * 
 */
package org.opensha.sha.param;

import java.util.ArrayList;

import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.exceptions.EditableException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.param.ParameterConstraintAPI;
import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ParameterEditor;
import org.opensha.sha.param.editor.MagDistStringParameterEditor;

/**
 * @author nitingupta
 *
 */
public class MagDistStringParameter extends StringParameter {

	   /** Class name for debugging. */
    protected final static String C = "MagDistStringParameter";
    /** If true print out debug statements. */
    protected final static boolean D = false;

    private transient ParameterEditor paramEdit = null;

	/**
	 * @param name
	 * @param strings
	 * @throws ConstraintException
	 */
	public MagDistStringParameter(String name, ArrayList strings)
			throws ConstraintException {
		super(name, strings);
		
	}

	/**
	 * @param name
	 * @param constraint
	 * @throws ConstraintException
	 */
	public MagDistStringParameter(String name, StringConstraint constraint)
			throws ConstraintException {
		super(name, constraint);
		
	}



	/**
	 * @param name
	 * @param strings
	 * @param value
	 * @throws ConstraintException
	 */
	public MagDistStringParameter(String name, ArrayList strings, String value)
			throws ConstraintException {
		super(name, strings, value);
		
	}

	/**
	 * @param name
	 * @param constraint
	 * @param value
	 * @throws ConstraintException
	 */
	public MagDistStringParameter(String name, StringConstraint constraint,
			String value) throws ConstraintException {
		super(name, constraint, value);
		
	}

	/**
	 * @param name
	 * @param constraint
	 * @param units
	 * @param value
	 * @throws ConstraintException
	 */
	public MagDistStringParameter(String name, StringConstraint constraint,
			String units, String value) throws ConstraintException {
		super(name, constraint, units, value);
		
	}
	
    /**
     * Sets the constraint reference if it is a StringConstraint
     * and the parameter is currently editable, else throws an exception.
     */
    public void setConstraint(ParameterConstraintAPI constraint) throws ParameterException, EditableException{

        String S = C + ": setConstraint(): ";
        checkEditable(S);

        if ( !(constraint instanceof StringConstraint )) {
            throw new ParameterException( S +
                "This parameter only accepts StringConstraint, unable to set the constraint."
            );
        }
        else super.setConstraint( constraint );
    }

    /**
     *  Gets the type attribute of the MagDistStringParameter object.
     * This is used to determine which type of GUI editor applies to this
     * parameter.
     *
     * @return    The GUI editor type
     */
    public String getType() {
        String type = C;
        return type;
    }


    /**
     * Returns a clone of the allowed strings of the constraint.
     * Useful for presenting in a picklist
     * @return    The allowedStrings vector
     */
    public ArrayList getAllowedStrings() {
        return ( ( StringConstraint ) this.constraint ).getAllowedStrings();
    }


    /**
     * Compares the values to if this is less than, equal to, or greater than
     * the comparing objects. Implementation of comparable interface. Helps
     * with sorting a list of parameters.
     *
     * @param  obj                     The object to compare this to
     * @return                         -1 if this value < obj value, 0 if equal,
     *      +1 if this value > obj value
     * @exception  ClassCastException  Is thrown if the comparing object is not
     *      a MagDistStringParameter *
     * @see                            Comparable
     */
    public int compareTo( Object obj ) throws ClassCastException {

        String S = C + ":compareTo(): ";

        if ( !( obj instanceof MagDistStringParameter ) ) {
            throw new ClassCastException( S + "Object not a MagDistStringParameter, unable to compare" );
        }

        MagDistStringParameter param = ( MagDistStringParameter ) obj;

        if( ( this.value == null ) && ( param.value == null ) ) return 0;
        int result = 0;

        String n1 = ( String ) this.getValue();
        String n2 = ( String ) param.getValue();

        return n1.compareTo( n2 );
    }


    /**
     * Compares the passed in MagDistStringParameter to see if it has
     * the same name and value. If the object is not a MagDistStringParameter
     * an exception is thrown. If the values and names are equal true
     * is returned, otherwise false is returned.
     *
     * @param  obj                     The object to compare this to
     * @return                         True if the values are identical
     * @exception  ClassCastException  Is thrown if the comparing object is not
     *      a MagDistStringParameter
     */
    public boolean equals( Object obj ) throws ClassCastException {
        String S = C + ":equals(): ";

        if ( !( obj instanceof MagDistStringParameter ) ) {
            throw new ClassCastException( S + "Object not a MagDistStringParameter, unable to compare" );
        }

        String otherName = ( ( MagDistStringParameter ) obj ).getName();
        if ( ( compareTo( obj ) == 0 ) && getName().equals( otherName ) ) {
            return true;
        }
        else { return false; }
    }


    /**
     *  Returns a copy so you can't edit or damage the origial.
     * Clones this object's value and all fields. The constraints
     * are also cloned.
     *
     * @return    Description of the Return Value
     */
    public Object clone() {

      StringConstraint c1=null;
      if(constraint != null)
         c1 = ( StringConstraint ) constraint.clone();

      MagDistStringParameter param = null;
        if( value == null ) {
          param = new MagDistStringParameter(name, c1);
          param.setUnits(units);
        }
        else param = new MagDistStringParameter( name, c1, units, this.value.toString() );
      
        if( param == null ) return null;
        param.editable = true;
        param.info = info;	
        return param;

    }

	@Override
	public ParameterEditor getEditor() {
		if (paramEdit == null) {
			paramEdit = new MagDistStringParameterEditor(this);
		}
		return paramEdit;
	}
}
