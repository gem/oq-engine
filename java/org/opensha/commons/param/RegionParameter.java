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
import org.opensha.commons.exceptions.RegionConstraintException;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.Region;
import org.opensha.commons.param.editor.ParameterEditor;
import org.opensha.commons.param.editor.RegionParameterEditor;

/**
 * <p>Title: LocationParameter</p>
 * <p>Description: Make a Location Parameter</p>
 * @author : Nitin Gupta and Vipin Gupta
 * @created : Aug 18, 2003
 * @version 1.0
 */

public class RegionParameter extends DependentParameter<Region>
implements java.io.Serializable{


	/** Class name for debugging. */
	protected final static String C = "RegionParameter";
	/** If true print out debug statements. */
	protected final static boolean D = false;

	protected final static String PARAM_TYPE ="RegionParameter";

	//parameter list parameter that holds the location parameters
	protected ParameterListParameter regionParameterListParameter;

	public final static String MIN_LONGITUDE = "Min Longitude";
	public final static String MAX_LONGITUDE = "Max Longitude";
	public final static String MIN_LATITUDE =  "Min Latitude";
	public final static String MAX_LATITUDE =  "Max Latitude";

	private DoubleParameter minLon = new DoubleParameter(MIN_LONGITUDE,
			new Double(-360), new Double(360),new Double(-119.5));
	private DoubleParameter maxLon = new DoubleParameter(MAX_LONGITUDE,
			new Double(-360), new Double(360),new Double(-117));
	private DoubleParameter minLat = new DoubleParameter(MIN_LATITUDE,
			new Double(-90), new Double(90), new Double(33.5));
	private DoubleParameter maxLat = new DoubleParameter(MAX_LATITUDE,
			new Double(-90), new Double(90), new Double(34.7));

	//location parameters
	protected ParameterAPI minLatParam;
	protected ParameterAPI maxLatParam;
	protected ParameterAPI minLonParam;
	protected ParameterAPI maxLonParam;

	//location object, value of this parameter
	private Region region;


	//location parameterlist parameter name static declaration
	private final static String REGION_PARAMETER_LIST_PARAMETER_NAME = "Rectangular Region";

	private transient ParameterEditor paramEdit = null;
	
	/**
	 * No constraints specified for this parameter. Sets the name of this
	 * parameter.
	 *
	 * @param  name  Name of the parameter
	 */
	public RegionParameter(String name) {
		super(name,null,null,null);
		setupParams(null);
	}

	/**
	 *
	 * Creates a location parameter with constraint being list of locations and
	 * current value of the parameter from these list of locations.
	 * @param name String Name of the location parameter
	 * @param locationList ArrayList : List of allowed locations
	 * @param value Location : Parameter value, should be one of the allowed location
	 */
	public RegionParameter(String name, Region value) throws
	ConstraintException {
		super(name, null, null, value);
		region = value;
		setupParams(value);
	}

	public RegionParameter(String name, String units,
			double minLat, double maxLat, double minLon, double maxLon) throws ConstraintException, RegionConstraintException {
		super(name, null, units, new Region(
				new Location(minLat,minLon),
				new Location(maxLat, maxLon)));
		region = (Region)value;
		setupParams(region);
	}


	public void setupParams(Region value) {
		if (value == null) {
//			try {
				value = new Region(
						new Location((Double)minLat.getValue(), (Double)minLon.getValue()),
						new Location((Double)maxLat.getValue(), (Double)maxLon.getValue()));
//			} catch (RegionConstraintException e) {
//				// TODO Auto-generated catch block
//				e.printStackTrace();
//			}
		}

		ParameterList paramList = new ParameterList();
		paramList.addParameter(minLat);
		paramList.addParameter(maxLat);
		paramList.addParameter(minLon);
		paramList.addParameter(maxLon);

		regionParameterListParameter = new ParameterListParameter(
				REGION_PARAMETER_LIST_PARAMETER_NAME,
				paramList);

		setValue(value);

		setIndependentParameters(paramList);
	}


	/**
	 * returns location parameter.
	 * @return ParameterAPI : Returns the instance ParameterListParameter that holds the
	 * parameters constituting the location, if location parameter specifies no constraint.
	 * But if constraint is not null, then it returns the instance of LocationParameter with constraints,
	 * similar to String parameter with constraints.
	 */
	public ParameterAPI getRegionParameter(){
		if(constraint == null)
			return regionParameterListParameter;
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
	public void setValue(Region reg){
		minLat.setValue(reg.getMinLat());
		maxLat.setValue(reg.getMaxLat());
		minLon.setValue(reg.getMinLon());
		maxLon.setValue(reg.getMaxLon());
		region = reg;
		super.setValue(region);
	}


	/**
	 * Returns the latitude of selected location
	 * @return double
	 */
	public double getMinLatitude(){
		if(constraint !=null)
			return region.getMinLat();
		else
			return ((Double)minLat.getValue()).doubleValue();
	}

	/**
	 * Returns the latitude of selected location
	 * @return double
	 */
	public double getMaxLatitude(){
		if(constraint !=null)
			return region.getMaxLat();
		else
			return ((Double)maxLat.getValue()).doubleValue();
	}

	/**
	 * Returns the latitude of selected location
	 * @return double
	 */
	public double getMinLongitude(){
		if(constraint !=null)
			return region.getMinLon();
		else
			return ((Double)minLon.getValue()).doubleValue();
	}

	/**
	 * Returns the latitude of selected location
	 * @return double
	 */
	public double getMaxLongitude(){
		if(constraint !=null)
			return region.getMaxLon();
		else
			return ((Double)maxLon.getValue()).doubleValue();
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

		if (! (obj instanceof RegionParameter)) {
			throw new ClassCastException(S +
					"Object not a RegionParameter, unable to compare");
		}

		RegionParameter param = (RegionParameter) obj;

		if ( (this.value == null) && (param.value == null))return 0;
		int result = 0;

		Region n1 = this.getValue();
		Region n2 = param.getValue();

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
		RegionParameter param = null;

		if (value != null)
			param = new RegionParameter(name,
					(Region) value);
		else
			param = new RegionParameter(name);
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
		if (paramEdit == null)
			paramEdit = new RegionParameterEditor(this);
		return paramEdit;
	}


}


