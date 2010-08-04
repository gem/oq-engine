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
import org.opensha.commons.geo.GeoTools;
import org.opensha.commons.geo.Location;
import org.opensha.commons.param.editor.ConstrainedLocationParameterEditor;
import org.opensha.commons.param.editor.LocationParameterEditor;
import org.opensha.commons.param.editor.ParameterEditor;

/**
 * <p>Title: LocationParameter</p>
 * <p>Description: Make a Location Parameter</p>
 * @author : Nitin Gupta and Vipin Gupta
 * @created : Aug 18, 2003
 * @version 1.0
 */

public class LocationParameter extends DependentParameter<Location>
implements java.io.Serializable{


	/** Class name for debugging. */
	protected final static String C = "LocationParameter";
	/** If true print out debug statements. */
	protected final static boolean D = false;

	public static String DEFAULT_LATITUDE_LABEL = "Latitude";
	public static String DEFAULT_LONGITUDE_LABEL = "Longitude";
	public static String DEFAULT_DEPTH_LABEL = "Depth";

	public static double DEFAULT_LATITUDE = 34.0;
	public static double DEFAULT_LONGITUDE = -118.0;
	public static double DEFAULT_DEPTH = 0.0;

	protected final static String PARAM_TYPE ="LocationParameter";

	//parameter list parameter that holds the location parameters
	protected ParameterListParameter locationParameterListParameter;

	//location parameters
	protected ParameterAPI latParam;
	protected ParameterAPI lonParam;
	protected ParameterAPI depthParam;

	//location object, value of this parameter
	private Location location;


	//location parameterlist parameter name static declaration
	private final static String LOCATION_PARAMETER_LIST_PARAMETER_NAME = "Location(lat,lon,depth)";
	private final static String LOCATION_WITHOUT_DEPTH_PARAMETER_LIST_PARAMETER_NAME = "Location(lat,lon)";

	private final static String DECIMAL_DEGREES = "Decimal Degrees";
	private final static String KMS = "kms";
	
	private transient ParameterEditor paramEdit = null;
	
	/**
	 * No constraints specified for this parameter. Sets the name of this
	 * parameter.
	 *
	 * @param  name  Name of the parameter
	 */
	public LocationParameter(String name) {
		this(name, LocationParameter.DEFAULT_LATITUDE_LABEL, LocationParameter.DEFAULT_LONGITUDE_LABEL, LocationParameter.DEFAULT_DEPTH_LABEL, null, 
				LocationParameter.DEFAULT_LATITUDE, 
				LocationParameter.DEFAULT_LONGITUDE,
				LocationParameter.DEFAULT_DEPTH);
	}

	/**
	 * Creates a location parameter with constraint being the list of locations.
	 * @param name String Name of the Location Parameter
	 * @param locationList ArrayList : List of the allowed locations
	 */
	public LocationParameter(String name, ArrayList locationList) throws
	ConstraintException {
		//super(name, new LocationConstraint(locationList), null, locationList.get(0));
		this(name, LocationParameter.DEFAULT_LATITUDE_LABEL, LocationParameter.DEFAULT_LONGITUDE_LABEL, LocationParameter.DEFAULT_DEPTH_LABEL, 
				new LocationConstraint(locationList), 
				((Location)locationList.get(0)).getLatitude(), 
				((Location)locationList.get(0)).getLongitude(), 
				((Location)locationList.get(0)).getDepth());
	}

	/**
	 * Creates a location parameter with constraint being list of locations and
	 * current value of the parameter from these list of locations.
	 * @param name String Parameter Name
	 * @param locationListConstraint LocationConstraint: Constraint on the location parameter
	 * @param value Location
	 */
	public LocationParameter(String name, LocationConstraint locationListConstraint,
			Location value) throws ConstraintException{
		//super(name, locationListConstraint, null, value);

		this(name, LocationParameter.DEFAULT_LATITUDE_LABEL, LocationParameter.DEFAULT_LONGITUDE_LABEL, LocationParameter.DEFAULT_DEPTH_LABEL,
				locationListConstraint, value.getLatitude(), value.getLongitude(), value.getDepth());
	}


	/**
	 * Creates a location parameter as parameterlist parameter. This creates
	 * a location parameter that holds lat param,lon param and depth parameter
	 * in a parameterListParameter.
	 * @param locationParamName String Parameter Name
	 * @param latParamName String Name of the lat param
	 * @param lonParamName String Name of the lon param
	 * @param depthParamName String Name of the depth param
	 * @param latValue Double valid Latitude value
	 * @param lonValue Double valid longitude value
	 * @param depthValue Double valid depth value
	 */
	public LocationParameter(String locationParamName,
			String latParamName, String lonParamName,
			String depthParamName, LocationConstraint constraint,
			Double latValue,
			Double lonValue, Double depthValue) {

		super(locationParamName,constraint,null,null);
		latParam = new DoubleParameter(latParamName,
				new DoubleConstraint(GeoTools.LAT_MIN,GeoTools.LAT_MAX),
				DECIMAL_DEGREES, latValue);
		lonParam = new DoubleParameter(lonParamName,
				new DoubleConstraint(GeoTools.LON_MIN,GeoTools.LON_MAX),
				DECIMAL_DEGREES, lonValue);
		depthParam = new DoubleParameter(depthParamName,
				new DoubleConstraint(GeoTools.DEPTH_MIN,1000),
				KMS, depthValue);

		ParameterList paramList = new ParameterList();
		paramList.addParameter(latParam);
		paramList.addParameter(lonParam);
		paramList.addParameter(depthParam);
		locationParameterListParameter = new ParameterListParameter(
				LOCATION_PARAMETER_LIST_PARAMETER_NAME,
				paramList);
		location = new Location(((Double)latParam.getValue()).doubleValue(),
				((Double)lonParam.getValue()).doubleValue(),
				((Double)depthParam.getValue()).doubleValue());
		setValue(location);
		//setting the independent parameters for the Location parameter
		setIndependentParameters(paramList);
	}

	/**
	 * Creates a location parameter as parameterlist parameter. This creates
	 * a location parameter that holds lat param,lon param and depth parameter
	 * in a parameterListParameter.
	 * @param locationParamName String Parameter Name
	 * @param latParamName String Name of the lat param
	 * @param lonParamName String Name of the lon param
	 * @param depthParamName String Name of the depth param
	 * @param latValue Double valid Latitude value
	 * @param lonValue Double valid longitude value
	 * @param depthValue Double valid depth value
	 */
	public LocationParameter(String locationParamName,
			String latParamName, String lonParamName,
			String depthParamName,
			Double latValue,
			Double lonValue, Double depthValue) {

		super(locationParamName,null,null,null);
		latParam = new DoubleParameter(latParamName,
				new DoubleConstraint(GeoTools.LAT_MIN,GeoTools.LAT_MAX),
				DECIMAL_DEGREES, latValue);
		lonParam = new DoubleParameter(lonParamName,
				new DoubleConstraint(GeoTools.LON_MIN,GeoTools.LON_MAX),
				DECIMAL_DEGREES, lonValue);
		depthParam = new DoubleParameter(depthParamName,
				new DoubleConstraint(GeoTools.DEPTH_MIN,50),
				KMS, depthValue);

		ParameterList paramList = new ParameterList();
		paramList.addParameter(latParam);
		paramList.addParameter(lonParam);
		paramList.addParameter(depthParam);
		locationParameterListParameter = new ParameterListParameter(
				LOCATION_PARAMETER_LIST_PARAMETER_NAME,
				paramList);
		location = new Location(((Double)latParam.getValue()).doubleValue(),
				((Double)lonParam.getValue()).doubleValue(),
				((Double)depthParam.getValue()).doubleValue());
		setValue(location);
		//setting the independent parameters for the Location parameter
		setIndependentParameters(paramList);
	}

	/**
	 * No constraints specified, all values allowed. Sets the name and value.
	 *
	 * @param  name   Name of the parameter
	 * @param  paramList  ParameterList  object
	 * @param loc Location Location object
	 */
	public LocationParameter(String name, ParameterList paramList,Location loc) {
		super(name,null,null,null);
		if(paramList.size() ==3)
			locationParameterListParameter = new ParameterListParameter(
					LOCATION_PARAMETER_LIST_PARAMETER_NAME,
					paramList);
		else
			locationParameterListParameter = new ParameterListParameter(
					LOCATION_WITHOUT_DEPTH_PARAMETER_LIST_PARAMETER_NAME,
					paramList);

		location = loc;
		setValue(location);
		//setting the independent parameters for the Location parameter
		setIndependentParameters(paramList);
	}


	/**
	 * returns location parameter.
	 * @return ParameterAPI : Returns the instance ParameterListParameter that holds the
	 * parameters constituting the location, if location parameter specifies no constraint.
	 * But if constraint is not null, then it returns the instance of LocationParameter with constraints,
	 * similar to String parameter with constraints.
	 */
	public ParameterAPI getLocationParameter(){
		if(constraint == null)
			return locationParameterListParameter;
		else
			return this;
	}


	/**
	 * Sets the constraint reference if it is a StringConstraint
	 * and the parameter is currently editable, else throws an exception.
	 */
	public void setConstraint(ParameterConstraintAPI constraint) throws ParameterException, EditableException{

		String S = C + ": setConstraint(): ";
		checkEditable(S);

		if ( !(constraint instanceof LocationConstraint )) {
			throw new ParameterException( S +
					"This parameter only accepts LocationConstraints, unable to set the constraint."
			);
		}
		else super.setConstraint( constraint );
	}


	/**
	 * Sets the location parameter with updated location value
	 * @param loc Location
	 */
	public void setValue(Location loc){
		location = loc;
		super.setValue(loc);
	}


	/**
	 * Returns the latitude of selected location
	 * @return double
	 */
	public double getLatitude(){
		if(constraint !=null)
			return location.getLatitude();
		else
			return ((Double)latParam.getValue()).doubleValue();
	}

	/**
	 * Returns the longitude of the selected location
	 * @return double
	 */
	public double getLongitude(){
		if(constraint !=null)
			return location.getLongitude();
		else
			return ((Double)lonParam.getValue()).doubleValue();
	}


	/**
	 * Returns the depth of the selected location
	 * @return double
	 */
	public double getDepth(){
		if(constraint !=null)
			return location.getDepth();
		else
			return ((Double)depthParam.getValue()).doubleValue();
	}

	/**
	 * Returns a clone of the allowed strings of the constraint.
	 * Useful for presenting in a picklist
	 * @return    The allowed Locations list
	 */
	public ArrayList getAllowedLocations() {
		return ( ( LocationConstraint ) this.constraint ).getAllowedLocations();
	}




	/**
	 *  Compares the values to if this is less than, equal to, or greater than
	 *  the comparing objects.
	 *
	 * @param  obj                     The object to compare this to
	 * @return                         -1 if this value < obj value, 0 if equal,
	 *      +1 if this value > obj value
	 * @exception  ClassCastException  Is thrown if the comparing object is not
	 *      a LocationParameter.
	 */
	public int compareTo( Object obj ) {
		String S = C + ":compareTo(): ";

		if (! (obj instanceof LocationParameter)) {
			throw new ClassCastException(S +
					"Object not a LocationParameter, unable to compare");
		}

		LocationParameter param = (LocationParameter) obj;

		if ( (this.value == null) && (param.value == null))return 0;
		int result = 0;

		Location n1 = (Location)this.getValue();
		Location n2 = (Location) param.getValue();

		if (n1.equals(n2))
			return 0;
		return -1;

	}


	/**
	 * Compares value to see if equal.
	 *
	 * @param  obj                     The object to compare this to
	 * @return                         True if the values are identical
	 * @exception  ClassCastException  Is thrown if the comparing object is not
	 *      a LocationParameter.
	 */
	public boolean equals( Object obj ) {
		String S = C + ":equals(): ";

		if (! (obj instanceof LocationParameter)) {
			throw new ClassCastException(S +
					"Object not a LocationParameter, unable to compare");
		}

		String otherName = ( (LocationParameter) obj).getName();
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
	public Object clone() {
		LocationConstraint c1 = null;
		LocationParameter param = null;
		if (constraint != null){
			c1 = (LocationConstraint) constraint.clone();
			param = new LocationParameter(name, c1,(Location)value);
		}
		else{
			if(value != null)
				param = new LocationParameter(name,
						(ParameterList)locationParameterListParameter.getValue(),
						(Location)value);
			else
				param = new LocationParameter(name);
		}
		param.editable = true;
		param.info = info;
		return param;

	}

	/**
	 * Returns the name of the parameter class
	 */
	public String getType() {
		String type;
		if (constraint != null) type = "Constrained" + PARAM_TYPE;
		else type = PARAM_TYPE;
		return type;
	}

	/**
	 * This overrides the getmetadataString() method because the value here
	 * does not have an ASCII representation (and we need to know the values
	 * of the independent parameter instead).
	 * @returns String
	 */
	public String getMetadataString() {
		if(constraint == null)
			return getDependentParamMetadataString();
		else //get the Metadata for the location parameter if it is a single parameter
			//similar to constraint string parameter.
			return super.getMetadataString();
	}


	public boolean setIndividualParamValueFromXML(Element el) {
		// TODO Auto-generated method stub
		return false;
	}

	public ParameterEditor getEditor() {
		if (paramEdit == null) {
			if (constraint == null)
				paramEdit = new LocationParameterEditor(this);
			else
				paramEdit = new ConstrainedLocationParameterEditor(this);
		}
		return paramEdit;
	}


}


