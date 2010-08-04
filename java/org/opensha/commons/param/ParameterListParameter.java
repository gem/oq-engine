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

import java.util.ListIterator;

import org.dom4j.Element;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.param.editor.ParameterEditor;
import org.opensha.commons.param.editor.ParameterListParameterEditor;


/**
 * <p>Title: ParameterListParameter</p>
 * <p>Description: Make a parameter which is basically a parameterList</p>
 * @author : Nitin Gupta and Vipin Gupta
 * @created : Aug 18, 2003
 * @version 1.0
 */

public class ParameterListParameter extends DependentParameter<ParameterList>
implements java.io.Serializable{


	/** Class name for debugging. */
	protected final static String C = "ParameterListParameter";
	/** If true print out debug statements. */
	protected final static boolean D = false;

	protected final static String PARAM_TYPE ="ParameterListParameter";

	private transient ParameterEditor paramEdit = null;

	/**
	 *  No constraints specified for this parameter. Sets the name of this
	 *  parameter.
	 *
	 * @param  name  Name of the parameter
	 */
	public ParameterListParameter(String name) {
		super(name,null,null,null);
	}

	/**
	 * No constraints specified, all values allowed. Sets the name and value.
	 *
	 * @param  name   Name of the parameter
	 * @param  paramList  ParameterList  object
	 */
	public ParameterListParameter(String name, ParameterList paramList){
		super(name,null,null,paramList);
		//setting the independent Param List for this parameter
		setIndependentParameters(paramList);
	}



	/**
	 *  Compares the values to if this is less than, equal to, or greater than
	 *  the comparing objects.
	 *
	 * @param  obj                     The object to compare this to
	 * @return                         -1 if this value < obj value, 0 if equal,
	 *      +1 if this value > obj value
	 * @exception  ClassCastException  Is thrown if the comparing object is not
	 *      a ParameterListParameter.
	 */
	public int compareTo( Object obj ) {
		String S = C + ":compareTo(): ";

		if ( !( obj instanceof ParameterListParameter ) ) {
			throw new ClassCastException( S + "Object not a ParameterListParameter, unable to compare" );
		}

		ParameterListParameter param = ( ParameterListParameter ) obj;

		if( ( this.value == null ) && ( param.value == null ) ) return 0;
		int result = 0;

		ParameterList n1 = ( ParameterList) this.getValue();
		ParameterList n2 = ( ParameterList) param.getValue();

		return n1.compareTo( n2 );
	}


	/**
	 * Set's the parameter's value, which is basically a parameterList.
	 *
	 * @param  value                 The new value for this Parameter
	 * @throws  ParameterException   Thrown if the object is currenlty not
	 *      editable
	 */
	public void setValue( ParameterList value ) throws ParameterException {

		ListIterator it  = value.getParametersIterator();
		super.setValue(value );
		//setting the independent Param List for this parameter
		this.setIndependentParameters(value);
	}

	/**
	 * Compares value to see if equal.
	 *
	 * @param  obj                     The object to compare this to
	 * @return                         True if the values are identical
	 * @exception  ClassCastException  Is thrown if the comparing object is not
	 *      a ParameterListParameter.
	 */
	public boolean equals(Object obj) {
		String S = C + ":equals(): ";

		if (! (obj instanceof ParameterListParameter)) {
			throw new ClassCastException(S +
			"Object not a ParameterListParameter, unable to compare");
		}

		String otherName = ( (ParameterListParameter) obj).getName();
		if ( (compareTo(obj) == 0) && getName().equals(otherName)) {
			return true;
		}
		else {
			return false;
		}
	}

	/**
	 *  Returns a copy so you can't edit or damage the origial.
	 *
	 * @return    Exact copy of this object's state
	 */
	public Object clone(){

		ParameterListParameter param = null;
		if( value == null ) param = new ParameterListParameter( name);
		else param = new ParameterListParameter(name,(ParameterList)value);
		if( param == null ) return null;
		param.editable = true;
		return param;
	}

	/**
	 * Returns the ListIterator of the parameters included within this parameter
	 * @return
	 */
	public ListIterator getParametersIterator(){
		return ((ParameterList)this.getValue()).getParametersIterator();
	}

	/**
	 *
	 * @returns the parameterList contained in this parameter
	 */
	public ParameterList getParameter(){
		return (ParameterList)getValue();
	}

	/**
	 * Returns the name of the parameter class
	 */
	public String getType() {
		String type = this.PARAM_TYPE;
		return type;
	}

	/**
	 * This overrides the getmetadataString() method because the value here
	 * does not have an ASCII representation (and we need to know the values
	 * of the independent parameter instead).
	 * @returns Sstring
	 */
	public String getMetadataString() {
		return getDependentParamMetadataString();
	}

	public boolean setIndividualParamValueFromXML(Element el) {
		// TODO Auto-generated method stub
		return false;
	}

	public ParameterEditor getEditor() {
		if (paramEdit == null)
			paramEdit = new ParameterListParameterEditor(this);
		return paramEdit;
	}


}


