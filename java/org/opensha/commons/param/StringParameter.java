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

import org.dom4j.Element;
import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.exceptions.EditableException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.param.editor.ConstrainedStringParameterEditor;
import org.opensha.commons.param.editor.ParameterEditor;
import org.opensha.commons.param.editor.StringParameterEditor;

/**
 *  <b>Title:</b> StringParameter<p>
 *
 *  <b>Description:</b> String Parameter that accepts strings as it's values.
 * If constraints are present, setting the value must pass the constraint
 * check. Since the Parameter class in an ancestor, all Parameter's fields are
 * inherited. <p>
 *
 * The constraints are StringConstraint which implies a StringParameter value
 * can only be choosen from a list of strings. <p>
 *
 * Note: SWR: The constraint object could be "supercharged" by using Regular
 * Expressions introduced in java 1.4. Then we wouldn't need a list
 * of allowed values but rather a matcher pattern. For example "[A-Za-z]*"
 * would allow all values that start with a lowercase or upper case
 * alphabet letter. <p>
 *
 * @author     Sid Hellman, Steven W. Rock
 * @created    February 21, 2002
 * @version    1.0
 */

public class StringParameter
    extends DependentParameter<String>
    implements DependentParameterAPI<String>, ParameterAPI<String>
{

    /** Class name for debugging. */
    protected final static String C = "StringParameter";
    /** If true print out debug statements. */
    protected final static boolean D = false;
    
    private transient ParameterEditor paramEdit = null;

    /**
     * Constructor doesn't specify a constraint, all values allowed. This
     * constructor sets the name of this parameter.
     */
    public StringParameter( String name ) { this.name = name; }


    /**
     * Input vector is turned into StringConstraints object. If vector
     * contains no elements an exception is thrown. This constructor
     * also sets the name of this parameter.
     *
     * @param  name                     Name of the parametet
     * @param  strings                  Converted to the Constraint object
     * @exception  ConstraintException  Thrown if vector of allowed values is
     *      empty
     * @throws  ConstraintException     Thrown if vector of allowed values is
     *      empty
     */
    public StringParameter( String name, ArrayList strings ) throws ConstraintException {
        this( name, new StringConstraint( strings ), null, null );
    }


    /**
     * Constructor that sets the name and Constraint during initialization.
     *
     * @param  name                     Name of the parametet
     * @param  constraint               Constraint object
     * @exception  ConstraintException  Description of the Exception
     * @throws  ConstraintException     Is thrown if the value is not allowed
     */
    public StringParameter( String name, StringConstraint constraint ) throws ConstraintException {
        this( name, constraint, null, null );
    }


    /**
     *  No constraints specified, all values allowed. This constructor
     * set's the name of this parameter as well as the value.
     *
     * @param  name   Name of the parametet
     * @param  value  value of this parameter
     */
    public StringParameter( String name, String value ) {
        this.name = name;
        this.value = value;
    }


    /**
     * No constraints specified, all values allowed.
     * Sets the name, units and value.
     *
     * @param  name                     Name of the parameter
     * @param  units                    Units of the parameter
     * @param  value                    value of this parameter
     * @exception  ConstraintException  Description of the Exception
     */
    public StringParameter( String name, String units, String value ) throws ConstraintException {
        this( name, null, units, value );
    }


    /**
     * Sets the name, vector of string converted to a constraint, amd value.
     *
     * @param  name                     Name of the parametet
     * @param  strings                  vector of allowed values converted to a
     *      constraint
     * @param  value                    value of this parameter
     * @exception  ConstraintException  Is thrown if the value is not allowed
     * @throws  ConstraintException     Is thrown if the value is not allowed
     */
    public StringParameter( String name, ArrayList strings, String value ) throws ConstraintException {
        this( name, new StringConstraint( strings ), null, value );
    }


    /**
     * Sets the name, constraint, and value.
     *
     * @param  name                     Name of the parametet
     * @param  constraint               List of allowed values
     * @param  value                    value of this parameter
     * @exception  ConstraintException  Is thrown if the value is not allowed
     * @throws  ConstraintException     Is thrown if the value is not allowed
     */
    public StringParameter( String name, StringConstraint constraint, String value ) throws ConstraintException {
        this( name, constraint, null, value );
    }



    /**
     *  This is the main constructor. All other constructors call this one.
     *  Constraints must be set first, because the value may not be an allowed
     *  one. Null values are always allowed in the constructor. All values are
     *  set in this constructor; name, value, units, and constructor
     *
     * @param  name                     Name of the parametet
     * @param  constraint               Lsit of allowed values
     * @param  value                    value object of this parameter
     * @param  units                    Units of this parameter
     * @exception  ConstraintException  Is thrown if the value is not allowed
     * @throws  ConstraintException     Is thrown if the value is not allowed
     */
    public StringParameter( String name, StringConstraint constraint, String units, String value )
             throws ConstraintException {
        super( name, constraint, units, value );
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
                "This parameter only accepts StringConstraints, unable to set the constraint."
            );
        }
        else super.setConstraint( constraint );
    }

    /**
     *  Gets the type attribute of the StringParameter object. Returns
     * the class name if unconstrained, else "Constrained" + classname.
     * This is used to determine which type of GUI editor applies to this
     * parameter.
     *
     * @return    The GUI editor type
     */
    public String getType() {
        String type = C;
        // Modify if constrained
        ParameterConstraintAPI constraint = this.constraint;
        if (constraint != null) type = "Constrained" + type;
        return type;
    }


    /**
     * Returns a clone of the allowed strings of the constraint.
     * Useful for presenting in a picklist
     * @return    The allowedStrings vector
     */
    public ArrayList<String> getAllowedStrings() {
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
     *      a StringParameter *
     * @see                            Comparable
     */
    public int compareTo( Object obj ) throws ClassCastException {

        String S = C + ":compareTo(): ";

        if ( !( obj instanceof StringParameter ) ) {
            throw new ClassCastException( S + "Object not a StringParameter, unable to compare" );
        }

        StringParameter param = ( StringParameter ) obj;

        if( ( this.value == null ) && ( param.value == null ) ) return 0;
        int result = 0;

        String n1 = ( String ) this.getValue();
        String n2 = ( String ) param.getValue();

        return n1.compareTo( n2 );
    }


    /**
     * Compares the passed in String parameter to see if it has
     * the same name and value. If the object is not a String parameter
     * an exception is thrown. If the values and names are equal true
     * is returned, otherwise false is returned.
     *
     * @param  obj                     The object to compare this to
     * @return                         True if the values are identical
     * @exception  ClassCastException  Is thrown if the comparing object is not
     *      a StringParameter
     */
    public boolean equals( Object obj ) throws ClassCastException {
        String S = C + ":equals(): ";

        if ( !( obj instanceof StringParameter ) ) {
            throw new ClassCastException( S + "Object not a StringParameter, unable to compare" );
        }

        String otherName = ( ( StringParameter ) obj ).getName();
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

        StringParameter param = null;
        if( value == null ) {
          param = new StringParameter(name, c1);
          param.setUnits(units);
        }
        else param = new StringParameter( name, c1, units, this.value.toString() );
        if( param == null ) return null;
        param.editable = true;
        param.info = info;
        return param;

    }


	public boolean setIndividualParamValueFromXML(Element el) {
		String val = el.attributeValue("value");
		if (val.length() == 0) {
			try {
				this.setValue("");
			} catch (ConstraintException e) {
				System.err.println("Warning: could not set String Param to empty string from XML");
			} catch (ParameterException e) {
				System.err.println("Warning: could not set String Param to empty string from XML");
			}
		} else {
			this.setValue(val);
		}
		return true;
	}

	public ParameterEditor getEditor() {
		if (paramEdit == null) {
			if (constraint == null)
				try {
					paramEdit = new StringParameterEditor(this);
				} catch (Exception e) {
					throw new RuntimeException(e);
				}
			else
				paramEdit = new ConstrainedStringParameterEditor(this);
		}
		return paramEdit;
	}

}
