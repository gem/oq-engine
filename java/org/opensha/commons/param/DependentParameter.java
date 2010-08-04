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
import java.util.Iterator;
import java.util.ListIterator;

import org.dom4j.Element;
import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.exceptions.EditableException;
import org.opensha.commons.exceptions.ParameterException;

/**
 * <b>Title:</b> DependentParameter<p>
 *
 * <b>Description:</b> Partial (abstract) implementation of the
 * DependentParameterAPI. A dependent parameter is simply a Parameter
 * where it's values and/or constraints depend on other independent
 * parametes. The basic functionality is to just maintain the list
 * of parameters this depends on. There is no special logic between
 * these parameters.  <p>
 *
 * This abstract class provides all the basic functionality
 * of adding, checking and removing independent parameters from
 * the internal storage structure. Internally the parameter list
 * is store in a ArrayList so the parameters oerding is maintained
 * in the same way they are added to the list <p>
 *
 * All the DependentParameterAPI functions are implemented. This class
 * is specified as abstract so that it can never be instantiated
 * by itself, only in a subclass. <p>
 *
 * @author Steven W. Rock
 * @version 1.0
 */
public abstract class DependentParameter<E>
extends Parameter<E>
implements DependentParameterAPI<E>
{

	/**
	 * ArrayList to store the independent Parameters
	 */
	protected ArrayList<ParameterAPI<?>> independentParameters = new ArrayList<ParameterAPI<?>>();
	//gets the Parameters Metadata
	protected String metadataString;

	/** Empty no-arg constructor. Only calls super constructor. */
	public DependentParameter() { super(); }


	/**
	 *  This is the main constructor. All subclass constructors call this one.
	 *  Constraints must be set first, because the value may not be an allowed
	 *  one. Null values are always allowed in the constructor.
	 *
	 * @param  name                     Name of this parameter
	 * @param  constraint               Constraints for this Parameter. May be
	 *      set to null
	 * @param  units                    The units for this parameter
	 * @param  value                    The value object of this parameter.
	 * @exception  ConstraintException  Description of the Exception
	 * @throws  ConstraintException     This is thrown if the passes in
	 *      parameter is not allowed
	 */
	public DependentParameter(
			String name,
			ParameterConstraintAPI<E> constraint,
			String units,
			E value )
	throws ConstraintException
	{
		super(name, constraint, units, value);
		//if( (constraint != null) && (constraint.getName() == null) )
		//constraint.setName( name );

	}



	/**
	 * Returns an iterator of all parameters in the list.<p>
	 *
	 */
	public ListIterator<ParameterAPI<?>> getIndependentParametersIterator(){
		return getIndependentParameterList().getParametersIterator();
	}




	/** Returns parameter from list if exist else throws exception */
	public ParameterAPI getIndependentParameter(String name) throws ParameterException {

		int index = getIndexOf(name);
		if( index != -1 ) {
			ParameterAPI<?> param = (ParameterAPI<?>)independentParameters.get(index);
			return param;
		}
		else{
			String S = C + ": getParameter(): ";
			throw new ParameterException(S + "No parameter exists named " + name);
		}

	}


	/**
	 *
	 * @param paramName
	 * @returns the index of the parameter Name in the ArrayList
	 */
	private int getIndexOf(String paramName){
		int size =  independentParameters.size();
		for(int i=0;i<size;++i){
			if(((ParameterAPI<?>)independentParameters.get(i)).getName().equals(paramName))
				return i;
		}
		return -1;
	}

	/**
	 *
	 * @returns the dependent parameter name and all its independent Params Values.
	 */
	public String getIndependentParametersKey(){

		// This provides a key for coefficient lookup in hashtable
		StringBuffer key = new StringBuffer( name );

		Iterator it = independentParameters.iterator();
		while( it.hasNext() ){
			Object value = ((ParameterAPI)it.next()).getValue();
			if( value != null ){
				key.append( '/' );
				key.append( value.toString() );
			}
		}

		// Update the currently selected coefficient
		return key.toString();

	}

	/**
	 * Checks if the parameter exists in the list, returns
	 * true only if it finds a name match. No other comparision is done.
	 * We may want to increase the comparision in the future, i.e. returns
	 * true if has same independent parameters, etc.
	 */
	public boolean containsIndependentParameter(String paramName){
		int index = getIndexOf(paramName);
		if( index != -1 ) { return true; }
		else{ return false; }
	}

	/**
	 * Clears out any existing parameters, then adds all parameters of the
	 * input parameterlist to this object
	 */
	public void setIndependentParameters(ParameterList list)throws ParameterException, EditableException{

		String S = C + ": setIndependentParameters(): ";
		checkEditable(S);
		independentParameters.clear();
		if(list != null){
			ListIterator it = list.getParametersIterator();
			while (it.hasNext()) {
				ParameterAPI param = (ParameterAPI) it.next();
				independentParameters.add(param);
			}
		}
	}

	/**
	 * Rather than giving the name and value info, this returns the name and the name/value
	 * pairs for all the parameters in the IndependentParameterList of this parameter.
	 * This can be used for any parameters where the value does not have a sensible
	 * ascii representation (e.g., a ParameterListParameter).
	 * @return
	 */
	public String getDependentParamMetadataString() {
		if(independentParameters.size() >0){
			StringBuffer metadata = new StringBuffer();
			metadata.append(getName() + " [ ");
			ListIterator list = getIndependentParametersIterator();
			while (list.hasNext()) {
				ParameterAPI tempParam = (ParameterAPI) list.next();
				metadata.append(tempParam.getMetadataString() + " ; ");
				/* Note that the getmetadatSring is called here rather than the
           getDependentParamMetadataString() method becuase the former is
           so far overriden in all Parameter types that have independent
           parameters; we may want to change this later on. */
			}
			metadata.replace(metadata.length() - 2, metadata.length(), " ]");
			metadataString = metadata.toString();
		}
		return metadataString;
	}

	/**
	 * Sets the Metadata String for the parameter that has dependent parameters.
	 */
	public void setDependentParamMetadataString(String dependentParamMedataString){
		metadataString = dependentParamMedataString;
	}


	/** Adds the parameter if it doesn't exist, else throws exception */
	public void addIndependentParameter(ParameterAPI parameter) throws ParameterException, EditableException{

		String S = C + ": addIndependentParameter(): ";
		checkEditable(S);

		String name = parameter.getName();
		int index = getIndexOf(name);
		if( index == -1 ) independentParameters.add(parameter);
		else throw new ParameterException(S + "A Parameter already exists named " + name);

	}


	/** removes parameter if it exists, else throws exception */
	public void removeIndependentParameter(String name) throws ParameterException, EditableException {

		String S = C + ": removeIndependentParameter(): ";
		checkEditable(S);
		int index = getIndexOf(name);
		if( index != -1 ) { independentParameters.remove(index); }
		else throw new ParameterException(S + "No Parameter exist named " + name + ", unable to remove");

	}

	/**
	 *
	 * @returns the independent parameter list for the dependent parameter
	 */
	public ParameterList getIndependentParameterList(){
		Iterator it = independentParameters.iterator();
		ParameterList list = new ParameterList();

		while( it.hasNext() ){
			ParameterAPI param = (ParameterAPI)it.next();
			list.addParameter(param);
		}
		return list;
	}



	/**
	 * Returns the number of independent parameters
	 */
	public int getNumIndependentParameters() {
		return independentParameters.size();
	}


	@Override
	public Object clone() {
		// TODO Auto-generated method stub
		return null;
	}

	/**
	 * This should set the value of this individual parameter. The values of the independent parameters
	 * will be set by the final setValueFromXMLMetadata method
	 * 
	 * @param el
	 * @return
	 */
	public abstract boolean setIndividualParamValueFromXML(Element el);

	public final boolean setValueFromXMLMetadata(Element el) {
		// first set the value of this parameter
		boolean success = this.setIndividualParamValueFromXML(el);

		if (!success)
			return false;

		Element depParamsEl = el.element(DependentParameterAPI.XML_INDEPENDENT_PARAMS_NAME);

		if (depParamsEl == null)
			return true;

		Iterator<Element> it = depParamsEl.elementIterator();
		while (it.hasNext()) {
			Element paramEl = it.next();
			String name = paramEl.attribute("name").getValue();
			ParameterAPI<?> param;
			try {
				param = this.getIndependentParameter(name);
				boolean newSuccess = param.setValueFromXMLMetadata(paramEl);
				System.out.println("Setting indep param " + name + " from XML...success? " + newSuccess);
				if (!newSuccess)
					success = false;
			} catch (ParameterException e) {
				System.err.println("Parameter '" + getName() + "' doesn't have an independent parameter named" +
						" '" + name + "', and cannot be set from XML");
			}
		}

		return success;
	}
}
