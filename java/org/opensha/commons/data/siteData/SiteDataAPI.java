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

package org.opensha.commons.data.siteData;

import java.io.IOException;
import java.util.ArrayList;

import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.Region;
import org.opensha.commons.metadata.XMLSaveable;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.editor.ParameterListEditor;

/**
 * This is the basic API for a class that provides site type information,
 * such as Vs30 and basin depth, for a particular region. It also contains 
 * the static strings for specifying types of data.
 * 
 * It uses generics to allow for any type of data object to be used, from
 * Strings and Doubles to an arbitrarily complex object.
 * 
 * @author Kevin Milner
 *
 * @param <Element>
 */
public interface SiteDataAPI<Element> extends NamedObjectAPI, XMLSaveable {
	
	public static final String XML_METADATA_NAME = "SiteDataAPI";
	
	/* ************ Site Data Types ************ */
	
	/**
	 * Vs 30 data type - Average Shear-Wave velocity in the upper 30 meters of a site (m/sec)
	 */
	public static final String TYPE_VS30 = "Vs30";
	/**
	 * Wills site classification data type - Can be translated to Vs30
	 */
	public static final String TYPE_WILLS_CLASS = "Wills Class";
	/**
	 * Depth to first Vs = 2.5 km/sec (km)
	 */
	public static final String TYPE_DEPTH_TO_2_5 = "Depth to Vs = 2.5 km/sec";
	/**
	 * Depth to first Vs = 1.0 km/sec (km)
	 */
	public static final String TYPE_DEPTH_TO_1_0 = "Depth to Vs = 1.0 km/sec";
	/**
	 * Elevation (m)
	 */
	public static final String TYPE_ELEVATION = "Elevation (m)";
	/**
	 * Topographic Slope, aka "scalar magnitudes of gradient vectors" from GMT (m/m)
	 */
	public static final String TYPE_TOPOGRAPHIC_SLOPE = "Topographic Slope (m/m)";
	
	/* ************ Type Flags ************ */
	
	/**
	 * Flag for site data with measured values
	 */
	public static final String TYPE_FLAG_MEASURED = "Measured";
	/**
	 * Flag for site data with inferred values
	 */
	public static final String TYPE_FLAG_INFERRED = "Inferred";
	
	/* ************ Site Data API ************ */
	
	/**
	 * This gives the applicable region for this data set.
	 * @return Region
	 */
	public Region getApplicableRegion();
	
	/**
	 * This gives the resolution of the dataset in degrees, or 0 for infinite resolution.
	 * 
	 * We could possibly add a 'units' field to allow for resolution in KM
	 * @return
	 */
	public double getResolution();
	
	/**
	 * Get the name of this dataset
	 * 
	 * @return
	 */
	public String getName();
	
	/**
	 * Get the short name of this dataset
	 * 
	 * @return
	 */
	public String getShortName();
	
	/** 
	 * Get the data type of this dataset
	 * 
	 * @return
	 */
	public String getDataType();
	
	/**
	 * Get the measurement type for this data, such as "Measured" or "Inferred"
	 * 
	 * @return
	 */
	public String getDataMeasurementType();
	
	/**
	 * Get the location of the closest data point
	 * 
	 * @param loc
	 * @return
	 */
	public Location getClosestDataLocation(Location loc) throws IOException;
	
	/**
	 * Get the value at the closest location
	 * 
	 * @param loc
	 * @return
	 */
	public Element getValue(Location loc) throws IOException;
	
	/**
	 * Get the value, with metadata, at the closest location
	 * 
	 * @param loc
	 * @return
	 * @throws IOException
	 */
	public SiteDataValue<Element> getAnnotatedValue(Location loc) throws IOException;
	
	/**
	 * Get the values, with metadata, at the closest locations
	 * 
	 * @param locs
	 * @return
	 * @throws IOException
	 */
	public SiteDataValueList<Element> getAnnotatedValues(LocationList locs) throws IOException;
	
	/**
	 * Get the value for each location in the given location list
	 * 
	 * @param loc
	 * @return
	 */
	public ArrayList<Element> getValues(LocationList locs) throws IOException;
	
	/**
	 * Returns true if the value is valid, and not NaN, N/A, or equivelant for the data type
	 * 
	 * @param el
	 * @return
	 */
	public boolean isValueValid(Element el);
	
	/**
	 * Returns true if there is data for the given site
	 * 
	 * @param loc - The location
	 * @param checkValid - Boolean for checking the validity of the value at the specified location
	 * @return
	 */
	public boolean hasDataForLocation(Location loc, boolean checkValid);
	
	/**
	 * Returns a list of adjustable parameters. For many types of site data, this will be empty, but for
	 * more complex ones like WaldGlobalVs2007, it's more complicated.
	 * 
	 * @return
	 */
	public ParameterList getAdjustableParameterList();
	
	/**
	 * Returns an editor for the parameter list. This is required because some data providers might have
	 * more complex parameters schemes that require direct access to the parameter editor (such as for enabling
	 * or disabling of parameters). 
	 * 
	 * @return
	 */
	public ParameterListEditor getParameterListEditor();
	
	/**
	 * Returns the metadata for this dataset.
	 * 
	 * @return
	 */
	public String getMetadata();
	
}
