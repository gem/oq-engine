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

import java.io.Serializable;
import java.util.ArrayList;
import java.util.Hashtable;
import java.util.Iterator;
import java.util.ListIterator;

import org.dom4j.Element;
import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.exceptions.ParameterException;

/**
 * <b>Title:</b> ParameterList<p>
 *
 * <b>Description:</b> List container for parameters. Specialized version of Hashtable.
 * The keys of the hashtable are the names of the parameters. Can add specialized
 * iterators so that it returns only specific types of paramters, i.e. return
 * all DoubleParameters. <p>
 *
 * This class assumes that two parameters are equal if they have the same name.
 * This implies that parameters have unique names. This must be the case for
 * all functions below that take a String name as an argument would fail if
 * two or more parameters have the same name. <p>
 *
 * An additional complication is that Parameters can have a constraint with a
 * different name. To handle this a mapping has to be generated such that
 * constraint name can be mapped back to the original parameter name. This is
 * accomplished via a hashtable. This is only performed in the occasional case
 * when the constraint name differs. In most cases the parameter name and
 * constraint name will be identical. Due to uniqueness of parameter names
 * this implies that all constraint names must be unique also, when differing
 * from the constraint name. <P>
 *
 * Note: Many of these functions are duplicated, where one form takes a
 * Parameter as input, and the second takes the Parameter name as a String as
 * input. THe first case can extract the parameter name, and proxy the
 * method call to the String name form. <p>
 *
 * 4/3/2002 SWR<BR>
 * WARNING - This class needs a little more work and a JUnit test case.
 * I added constraint names but didn't fully implement updating and removing
 * parameters with differing constraint names, only implemented addParameter
 * fully. <p>
 *
 * @author Steven W. Rock
 * @version 1.0
 */

public class ParameterList implements Serializable, Iterable<ParameterAPI<?>> {


	// *******************/
	// Variables
	// *******************/

	/**
	 * 
	 */
	private static final long serialVersionUID = -3799009507357699361L;
	/** Class name for debugging. */
	protected final static String C = "ParameterList";
	/** If true print out debug statements. */
	protected final static boolean D = false;

	/** Internal vector list of parameters. */
	protected ArrayList<ParameterAPI<?>> params = new ArrayList<ParameterAPI<?>>();

	/** Internal list of constraint name mapped to parameter name. */
	protected Hashtable<String, String> constraintNameMap = new Hashtable<String, String>();


	/* **********************/
	/** @todo  Constructors */
	/* **********************/

	/** no arg constructor. Does nothing. */
	public ParameterList() {}



	/* ****************************/
	/** @todo  Accessors, Setters */
	/* ****************************/

	/**
	 * Adds all parameters of the parameterlist to this one, if the
	 * named parameter is not already in the list. If a named parameter
	 * exists already a Parameter Exception is thrown.
	 */
	public void addParameterList(ParameterList list2) throws ParameterException{

		ListIterator<ParameterAPI<?>> it = list2.getParametersIterator();
		while( it.hasNext() ){
			ParameterAPI<?> param = (ParameterAPI<?>)it.next();
			if( !this.containsParameter(param) ){ this.addParameter(param); }        }

	}

	/**
	 * Adds the parameter to the internal sotrage of parameters if it
	 * doesn't exist, else throws exception. If the constraint has a different
	 * name from the parameter, the constraint name is mapped to the parameter
	 * name.
	 */
	public void addParameter(ParameterAPI param) throws ParameterException{

		String S = C + ": addParameter(): ";

		String name = param.getName();
		String constraintName = param.getConstraintName();

		if( getIndexOf(name)== -1) params.add(param);
		else throw new ParameterException(S + "A Parameter already exists named " + name);


		if( constraintName == null || constraintName.equals("") || constraintName.equals( name )) return;

		if( !constraintNameMap.containsKey(constraintName) ) {
			constraintNameMap.put(constraintName, name);
		}
		else{
			params.remove(name);
			throw new ParameterException(S + "A Parameter already exists with this constraint named " + constraintName);
		}



	}

	/**
	 * Maps back the constraint name to parameter name if this is a constraint name.
	 * @param name      The value to check if it is a constraint
	 * @return          Either the unmodified name if not constraint name, else the parameter
	 * name from the mappings if this is a constraint name.
	 */
	public String getParameterName( String name ){
		if( constraintNameMap.containsKey(name) ) return (String)constraintNameMap.get( name );
		return name;
	}

	/** Returns parameter if exist else throws exception. */
	public ParameterAPI getParameter(String name) throws ParameterException {

		name = getParameterName( name );
		int index = getIndexOf(name);
		if( index!=-1 ) {
			ParameterAPI param = (ParameterAPI)params.get(index);
			return param;
		}
		else{
			String S = C + ": getParameter(): ";
			throw new ParameterException(S + "No parameter exists named " + name);
		}

	}


	/** Returns parameter contained value object if the parameter exist, else throws exception. */
	public Object getValue(String name) throws ParameterException{

		name = getParameterName( name );
		int index = getIndexOf(name);
		if( (index!=-1) ) {
			ParameterAPI param = (ParameterAPI)params.get(index);
			Object obj = param.getValue();
			return obj;
		}
		else{
			String S = C + ": getValue(): ";
			throw new ParameterException(S + "No parameter exists named " + name);
		}
	}

	/** Set's a new value to a Parameter in the list if it exists, else throws exception. */
	public void setValue(String name, Object value) throws ParameterException, ConstraintException {

		String S = C + ": setValue(): ";
		if(D) System.out.println(S + "Starting");

		name = getParameterName( name );
		int index = getIndexOf(name);
		if( index !=-1 ) {
			ParameterAPI param = (ParameterAPI)params.get(index);
			param.setValue(value);
		}
		else{

			throw new ParameterException(S + "No parameter exists named " + name);
		}

		if(D) System.out.println(S + "Ending");

	}

	/** Returns parameter type of named parameter in list, if not exist throws exception. */
	public String getType(String name) throws ParameterException {
		name = getParameterName( name );
		int index = getIndexOf(name);
		if( index!=-1) {
			ParameterAPI param = (ParameterAPI)params.get(index);
			String str = param.getType();
			return str;
		}
		else{
			String S = C + ": getType(): ";
			throw new ParameterException(S + "No parameter exists named " + name);
		}
	}


	/** Checks if the parameter exists in the list. Returns true if it does, else returns false. */
	public boolean containsParameter(ParameterAPI param){

		String name = param.getName();
		int index = getIndexOf(name);
		if( index!=-1 ) { return true; }
		else{ return false; }

	}

	/** Checks if the parameter exists in the list. Returns true if it does, else returns false. */
	public boolean containsParameter(String paramName){
		int index = getIndexOf(paramName);
		if( index!=-1 ) { return true; }
		else{ return false; }

	}


	/** Removes parameter if it exists, else throws exception. */
	public void removeParameter(ParameterAPI param) throws ParameterException {
		String name = param.getName();
		removeParameter(name);
	}

	/** Removes parameter if it exists, else throws exception. */
	public void removeParameter(String name) throws ParameterException {
		int index = getIndexOf(name);
		if( index!=-1 ) { params.remove(index); }
		else{
			String S = C + ": removeParameter(): ";
			throw new ParameterException(S + "No Parameter exist named " + name + ", unable to remove");
		}
	}


	/**
	 * Updates an existing parameter with the new value.
	 * Throws parameter exception if parameter doesn't exist.
	 */
	public void updateParameter(ParameterAPI param) throws ParameterException {
		String name = param.getName();
		removeParameter(name);
		addParameter(param);
	}

	/**
	 * Returns an iterator of all parameters in the list. Returns the list in
	 * the order the elements were added.
	 */
	public ListIterator<ParameterAPI<?>> getParametersIterator(){

		ArrayList<ParameterAPI<?>> v = new ArrayList<ParameterAPI<?>>();
		int size = this.params.size();
		for(int i = 0; i<size;++i) {
			ParameterAPI obj = params.get(i);
			v.add(obj);
		}

		return v.listIterator();
	}



	/**
	 * Searches for the named parameter, then replaces the parameter
	 * it is currently editing.
	 * @param parameterName : Name of the parameter that is being removed
	 * @param param : New parameter that is replacing the old parameter
	 */
	public void replaceParameter( String parameterName, ParameterAPI param ) {

		parameterName = getParameterName( parameterName );
		int index = getIndexOf(parameterName);
		if ( index != -1 ) {
			removeParameter( parameterName );
			addParameter( param );
		}

	}



	/**
	 * compares 2 ParameterList to see if they are equal.
	 * It compares them by checking each parameter with the passed argument
	 * obj is present in the parameterList, it is compared with.
	 * It also checks if both the parameterLists have same parameters and have the
	 * same values.
	 * @param obj instance of ParameterList
	 * @return int 0 if both object are same else return -1
	 */
	public int compareTo(Object obj){

		int result =0;

		if (! (obj instanceof ParameterList)) {
			throw new ClassCastException(C +
					"Object not a ParameterList, unable to compare");
		}

		ParameterList paramList = (ParameterList) obj;

		ListIterator<ParameterAPI<?>> it = paramList.getParametersIterator();

		if(size() != paramList.size())
			return -1;

		while(it.hasNext()){
			ParameterAPI param1 = (ParameterAPI)it.next();
			ParameterAPI param2 = (ParameterAPI)getParameter(param1.getName());
			result = param2.compareTo(param1);
			if(result !=0)
				break;

		}

		return result;

	}

	/**
	 * Returns an iterator of all parameter names of the paramters in the list.
	 * Returns the list in the order the elements were added.
	 */
	public ListIterator<String> getParameterNamesIterator(){
		ArrayList<String> v = new ArrayList<String>();
		int size = this.params.size();
		for(int i = 0; i<size;++i) {
			ParameterAPI obj = (ParameterAPI)params.get(i);
			v.add(obj.getName());
		}
		return v.listIterator();
	}

	/** Removes all parameters from the list, making it empty, ready for new parameters.  */
	public void clear(){ params.clear(); }

	/** Returns the number of parameters in the list. */
	public int size(){ return params.size(); }

	/**
	 * Returns true if all the parameters have the same names and values.
	 * One use will be to determine if two DisctetizedFunctions
	 * are the same, i.e. set up with the same independent parameters.
	 */
	public boolean equals(ParameterList list){

		// Not same size, can't be equal
		if( this.size() != list.size() ) return false;

		// Check each individual Parameter
		ListIterator<ParameterAPI<?>> it = this.getParametersIterator();
		while(it.hasNext()){

			// This list's parameter
			ParameterAPI<?> param1 = it.next();

			// List may not contain parameter with this list's parameter name
			if ( !list.containsParameter(param1.getName()) ) return false;

			// Found two parameters with same name, check equals, actually redundent,
			// because that is what equals does
			ParameterAPI<?> param2 = list.getParameter(param1.getName());
			if( !param1.equals(param2) ) return false;

			// Now try compare to to see if value the same, can fail if two values
			// are different, or if the value object types are different
			try{ if( param1.compareTo( param2 ) != 0 ) return false; }
			catch(ClassCastException ee) { return false; }

		}

		// Passed all tests - return true
		return true;

	}

	/**
	 * Returns true if all the parameters have the same names.
	 * One use will be to determine if two DisctetizedFunctions
	 * can be plotted on the same axis, i.e. set up with the
	 * same independent parameters.
	 */
	public boolean equalNames(ParameterList list){

		// Not same size, can't be equal
		if( this.size() != list.size() ) return false;

		// Check each individual Parameter
		ListIterator<ParameterAPI<?>> it = this.getParametersIterator();
		while(it.hasNext()){

			// This list's parameter
			ParameterAPI<?> param1 = it.next();

			// List may not contain parameter with this list's parameter name
			if ( !list.containsParameter(param1.getName()) ) return false;

		}

		// Passed all tests - return true
		return true;

	}

	/**
	 * Returns a copy of this list, therefore any changes to the copy
	 * cannot affect this original list.
	 */
	public Object clone(){

		String S = C + ": clone(): ";
		ParameterList list = new ParameterList();
		if( this.size() < 1 ) return list;
		int size = this.params.size();
		for(int i = 0; i<size;++i) {
			ParameterAPI param = (ParameterAPI)params.get(i);
			list.addParameter( (ParameterAPI)param.clone() );
		}

		return list;
	}

	/** Prints out all parameters in this list. For debugging purposes */
	public String toString(){

		String S = C + ": toString():";

		StringBuffer b = new StringBuffer();
		boolean first = true;

		ArrayList<String> v=new ArrayList<String>();

		int vectorSize = params.size();
		for(int i = 0; i<vectorSize;++i) {
			ParameterAPI param = (ParameterAPI)params.get(i);
			v.add(param.getName());
		}

		Iterator<String> it = v.iterator();
		while(it.hasNext()){

			String key = (String)it.next();
			if(D) System.out.println(S + "Next Parameter Key = " + key);

			int index = getIndexOf(key);
			ParameterAPI param = (ParameterAPI)params.get(index);
			ParameterConstraintAPI constraint = param.getConstraint();

			boolean ok = true;
			if(constraint instanceof DiscreteParameterConstraintAPI){

				int size = ((DiscreteParameterConstraintAPI)constraint).size();
				if( size < 2) ok = false;

			}

			if( ok ){

				String val = "N/A";
				Object obj = param.getValue();
				if( obj != null) val = obj.toString();

				if(D) System.out.println(S + val);
				if(first){
					first = false;
					b.append( key + " = " + val );
				}
				else {
					b.append( ", " + key + " = " + val );
				}
			}
		}

		return b.toString();

	}


	/**
	 * this function iterates over all the parameters in
	 * the parematerList and get their metadata in the
	 * string format.
	 *
	 * @returns the metadata string for the parameterList
	 *
	 * Metadata returned from this function can only be used
	 * to set the values of the parameters, cannot be used to
	 * recreate the parameters.
	 * Note: See getParameterListMetadataXML function which returns
	 * the metadata in the XML format and can used to recreate the
	 * parameterList from scratch.
	 */
	public String getParameterListMetadataString(){
		return getParameterListMetadataString("; ");
	}

	public String getParameterListMetadataString(String delimiter){
		int size  = params.size();
		StringBuffer metaData = new StringBuffer();
		boolean first = true;
		for(int i=0;i<size;++i){
			ParameterAPI tempParam=(ParameterAPI)params.get(i);
			if(first){
				metaData.append(tempParam.getMetadataString());
				first = false;
			}
			else
				metaData.append(delimiter+tempParam.getMetadataString());
		}
		return metaData.toString();
	}



	/** Returns the index of the named Parameter in this list. Returns -1 if not found. */
	private int getIndexOf(String key) {
		int size = params.size();
		for(int i=0;i<size;++i) {
			ParameterAPI param = (ParameterAPI)params.get(i);
			if(key.equalsIgnoreCase(param.getName()))
				return i;
		}
		return -1;
	}


	public Iterator<ParameterAPI<?>> iterator() {
		return this.params.iterator();
	}

	public static boolean setParamsInListFromXML(ParameterList paramList, Element paramListEl) {
		boolean failure = false;
		for (ParameterAPI<?> param : paramList) {
			Iterator<Element> it = paramListEl.elementIterator();
			boolean matched = false;
			while (it.hasNext()) {
				Element el = it.next();
				if (param.getName().equals(el.attribute("name").getValue())) {
					matched = true;
					//					  System.out.println("Found a match!");
					if (param.setValueFromXMLMetadata(el)) {
						//						  System.out.println("Parameter set successfully!");
					} else {
						System.err.println("Parameter could not be set from XML!");
						System.err.println("It is possible that the parameter type doesn't yet support loading from XML");
						failure = true;
					}
				}
			}
			if (!matched) {
				System.err.println("Parameter '" + param.getName() + "' from XML can not be set because it can't be" +
				" found in the given ParameterList!");
				failure = true;
			}
		}

		return !failure;
	}

}
