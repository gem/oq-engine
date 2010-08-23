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

package org.opensha.sha.earthquake;


import java.util.ArrayList;
import java.util.ListIterator;

import org.opensha.commons.data.NamedObjectAPI;
import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.Region;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.sha.util.TectonicRegionType;


/**
 * <p>Title: EqkRupForecastBaseAPI</p>
 * <p>Description: This defines the common interface that applies to both an EqkRupForecast 
 * and an ERF_LIST (the methods that are common betwen the two).</p>
 * @author : Ned Field, Nitin Gupta and Vipin Gupta
 * @created Sept 30,2004
 * @version 1.0
 */

public interface EqkRupForecastBaseAPI extends NamedObjectAPI{
	
	/**
	 * To increase load time for applications, the name of each ERF should be stored
	 * as a public static final String called "NAME". This is the default name, and should
	 * be overridden in implementing classes.
	 */
	public static final String NAME = "Unnamed ERF";

	/**
	 * This method tells the forecast that the user is done setting parameters and that
	 * it can now prepare itself for use.  We could avoid needing this method if the 
	 * forecast updated every time a parameter was changed, but this would be very inefficient
	 * with forecasts that take a lot of time to update.  This also avoids problems associated
	 * with accidentally changing a parameter in the middle of a calculation.
	 * @return
	 */
	public void updateForecast();

	/**
	 * Update and save the serialized forecast into a file
	 */
	public String updateAndSaveForecast();

	/**
	 * This method sets the time-span field
	 * @param time
	 */
	public void setTimeSpan(TimeSpan time);


	/**
	 * This method gets the time-span field
	 */
	public TimeSpan getTimeSpan();


	/**
	 * This will set the parameter with the given
	 * name to the given value.
	 * @param name String Name of the Adjustable Parameter
	 * @param value Object Parameter Value
	 * @return boolean boolean to see if it was successful in setting the parameter
	 * value.
	 */
	public boolean setParameter(String name, Object value);

	/**
	 * get the adjustable parameters for this forecast
	 *
	 * @return
	 */
	public ListIterator<ParameterAPI> getAdjustableParamsIterator();

	/**
	 * Gets the Adjustable parameter list for the ERF
	 * @return
	 */
	public ParameterList getAdjustableParameterList();


	/**
	 * This function finds whether a particular location lies in applicable
	 * region of the forecast
	 *
	 * @param loc : location
	 * @return: True if this location is within forecast's applicable region, else false
	 */
	public boolean isLocWithinApplicableRegion(Location loc);


	/**
	 * Get the region for which this forecast is applicable
	 * @return : Geographic region object specifying the applicable region of forecast
	 */
	public Region getApplicableRegion();


	/**
	 * This specifies what types of Tectonic Regions are included in the ERF
	 * @return : ArrayList<TectonicRegionType>
	 */
	public ArrayList<TectonicRegionType> getIncludedTectonicRegionTypes();



}
