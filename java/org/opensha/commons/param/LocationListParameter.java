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
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.param.editor.LocationParameterEditor;
import org.opensha.commons.param.editor.ParameterEditor;

/**
 * <p>Title: LocationListParameter</p>
 * <p>Description: Make a parameter which is basically a parameterList for location
 * parameters.</p>
 * @author : Nitin Gupta and Vipin Gupta
 * @created : April 01,2004
 * @version 1.0
 */

public class LocationListParameter extends DependentParameter<LocationList>
implements java.io.Serializable{


	/** Class name for debugging. */
	protected final static String C = "LocationListParameter";
	/** If true print out debug statements. */
	protected final static boolean D = false;

	protected final static String PARAM_TYPE ="LocationListParameter";



	private final static String LOCATION_PARAM_NAME = "Location - ";
	private final static String LAT_PARAM_NAME = "Latitude";
	private final static String LON_PARAM_NAME = "Longitude";
	private final static String DEPTH_PARAM_NAME = "Depth";

	private final static String LAT_PARAM_UNITS = "degrees";
	private final static String LON_PARAM_UNITS = "degrees";
	private final static String DEPTH_PARAM_UNITS = "Kms";

	private transient ParameterEditor paramEdit = null;
	
	/**
	 *  No constraints specified for this parameter. Sets the name of this
	 *  parameter.
	 *
	 * @param  name  Name of the parameter
	 */
	public LocationListParameter(String name) {
		super(name,null,null,null);
	}


	/**
	 * No constraints specified, all values allowed. Sets the name and value.
	 *
	 * @param  name   Name of the parameter
	 * @param  locList  LocationList  object
	 */
	public LocationListParameter(String name, LocationList locList){
		super(name,null,null,locList);

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

		if ( !( obj instanceof LocationListParameter ) ) {
			throw new ClassCastException( S + "Object not a LocationListParameter, unable to compare" );
		}

		LocationListParameter param = ( LocationListParameter ) obj;

		if( ( this.value == null ) && ( param.value == null ) ) return 0;
		//int result = 0;

		LocationList n1 = ( LocationList) this.getValue();
		LocationList n2 = ( LocationList ) param.getValue();
		
		// TODO need to fix compareTo() up the Parameter heirarchy; it is often
		// abused, being used as a stand-in for equals() returning 0 or -1 but
		// never +1. wierd -ppowers

		// return n1.compareTo( n2 );
		
		return (n1.equals(n2)) ? 0 : -1;
	}


	/**
	 *
	 * @param locationParameters ParameterList
	 */
	public void setAllLocations(ParameterList locationParameters){

		//setting the independent Param List for this parameter
		setIndependentParameters(locationParameters);
		LocationList locList = new LocationList();
		ListIterator it = locationParameters.getParametersIterator();
		while(it.hasNext()){
			LocationParameter locParam = (LocationParameter)it.next();
			locList.add((Location)locParam.getValue());
		}
		setValue(locList);
	}

	/**
	 * Compares value to see if equal.
	 *
	 * @param  obj                     The object to compare this to
	 * @return                         True if the values are identical
	 * @exception  ClassCastException  Is thrown if the comparing object is not
	 *      a LocationListParameter.
	 */
	public boolean equals(Object obj) {
		String S = C + ":equals(): ";

		if (! (obj instanceof LocationListParameter)) {
			throw new ClassCastException(S +
					"Object not a LocationListParameter, unable to compare");
		}

		String otherName = ( (LocationListParameter) obj).getName();
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

		LocationListParameter param = null;
		if( value == null ) param = new LocationListParameter( name);
		else param = new LocationListParameter(name,(LocationList)value);
		if( param == null ) return null;
		param.editable = true;
		param.info = info;
		return param;
	}


	/**
	 *
	 * @returns the locationList contained in this parameter
	 */
	public LocationList getParameter(){
		return (LocationList)getValue();
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
		if (paramEdit == null) {
			paramEdit = new LocationParameterEditor(this);
		}
		return paramEdit;
	}


}


