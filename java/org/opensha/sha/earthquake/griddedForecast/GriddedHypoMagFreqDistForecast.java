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

package org.opensha.sha.earthquake.griddedForecast;

import java.util.ArrayList;
import java.util.EventObject;
import java.util.ListIterator;

import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.Region;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.sha.earthquake.EqkRupForecastBaseAPI;
import org.opensha.sha.util.TectonicRegionType;

/**
 * <p>
 * Title: GriddedHypoMagFreqForecast
 * </p>
 * 
 * <p>
 * Description: This constitutes a Poissonian hypocenter forecast.
 * 
 * Are locations unique?.
 * </p>
 *<p>
 * Note : The rate provided by this forecast are always yearly rate.
 *</p>
 * 
 * @author Nitin Gupta , Edward (Ned) Field, Vipin Gupta
 * @version 1.0
 */
public abstract class GriddedHypoMagFreqDistForecast implements
		EqkRupForecastBaseAPI,
		HypoMagFreqDistAtMultLocsAPI,
		ParameterChangeListener {

	// TODO why abstract? no abstract methods; just lacks constructoirs

	// Timespan for the given forecast
	private TimeSpan timeSpan;
	// number of hypocenter location.
	// private int numHypoLocation;
	// Adjustable parameters fro the given forecast model
	private ParameterList adjustableParameters;
	// Only update the forecast if parameters have been changed.
	protected boolean parameterChangeFlag = true;

	// EvenlyGriddedGeographicAPI region
	protected GriddedRegion region;

	private ArrayList listenerList = new ArrayList();

	/**
	 * This function finds whether a particular location lies in applicable
	 * region of the forecast
	 * 
	 * @param loc : location
	 * @return: True if this location is within forecast's applicable region,
	 *          else false
	 */
	public boolean isLocWithinApplicableRegion(Location loc) {
		return region.contains(loc);
	}

	/**
	 * Gets the EvenlyGriddedGeographic Region
	 * 
	 * @return EvenlyGriddedGeographicRegionAPI
	 */
	public GriddedRegion getRegion() {
		return region;
	}

	public void setRegion(GriddedRegion region) {
		this.region = region;
	}
	
	/**
			 * Get the region for which this forecast is applicable
			 * @return : Geographic region object specifying the applicable region of forecast
			 */
	public Region getApplicableRegion() {
		return region;
	}

	/**
	 * Returns the adjustable parameters list
	 * 
	 * @return ParameterList
	 */
	public ParameterList getAdjustableParameterList() {
		return adjustableParameters;
	}

	/**
	 * Returns the adjustable parameters as the ListIterator
	 * 
	 * @return ListIterator
	 */
	public ListIterator getAdjustableParamsIterator() {
		return adjustableParameters.getParametersIterator();
	}

	/**
	 * Return the name for this class
	 * 
	 * @return : return the name for this class
	 */
	public String getName() {
		return null;
	}

	/**
	 * Update and save the serialized forecast into the file
	 */
	public String updateAndSaveForecast() {
		throw new UnsupportedOperationException(
				"updateAndSaveForecast() not supported");
	}

	/**
	 * getNumHypoLocation
	 * 
	 * @return int
	 * @todo Implement this org.opensha.sha.earthquake.HypoMagFreqDistAtLocAPI
	 *       method
	 */
	public int getNumHypoLocs() {
		return region.getNodeCount();
	}

	/**
	 * Function that must be implemented by all Timespan Listeners for
	 * ParameterChangeEvents.
	 * 
	 * @param event The Event which triggered this function call
	 */
	public void timeSpanChange(EventObject event) {
		this.parameterChangeFlag = true;
	}

	/**
	 * This is the main function of this interface. Any time a control paramater
	 * or independent paramater is changed by the user in a GUI this function is
	 * called, and a paramater change event is passed in.
	 * 
	 * This sets the flag to indicate that the sources need to be updated
	 * 
	 * @param event
	 */
	public void parameterChange(ParameterChangeEvent event) {
		parameterChangeFlag = true;
	}

	/**
	 * Allows the user to get the Timespan for this
	 * GriddedHypoMagFreqDistForecast
	 * 
	 * @return TimeSpan
	 */
	public TimeSpan getTimeSpan() {
		return timeSpan;
	}

	/**
	 * Loops over all the adjustable parameters and set parameter with the given
	 * name to the given value. First checks if the parameter is contained
	 * within the ERF adjustable parameter list or TimeSpan adjustable
	 * parameters list. If not then return false.
	 * 
	 * @param name String Name of the Adjustable Parameter
	 * @param value Object Parameeter Value
	 * @return boolean boolean to see if it was successful in setting the
	 *         parameter value.
	 */
	public boolean setParameter(String name, Object value) {
		if (getAdjustableParameterList().containsParameter(name)) {
			getAdjustableParameterList().getParameter(name).setValue(value);
			return true;
		} else if (timeSpan.getAdjustableParams().containsParameter(name)) {
			timeSpan.getAdjustableParams().getParameter(name).setValue(value);
			return true;
		}
		return false;
	}

	/**
	 * Allows the user to set the Timespan for this
	 * GriddedHypoMagFreqDistForecast
	 * 
	 * @param timeSpan TimeSpan
	 */
	public void setTimeSpan(TimeSpan timeSpan) {
		this.timeSpan = timeSpan;
	}

	/**
	 * If any parameter has been changed then update the forecast. NOTE : Not
	 * implemented
	 */
	public void updateForecast() {
		if (parameterChangeFlag) {

		}
	}
	
	  /**
	   * This specifies what types of Tectonic Regions are included in the ERF.
	   * This default implementation includes only ACTIVE_SHALLOW, so it should 
	   * be overridden in subclasses if other types are used
	   * @return : ArrayList<TectonicRegionType>
	   */
	  public ArrayList<TectonicRegionType> getIncludedTectonicRegionTypes(){
		  ArrayList<TectonicRegionType> list = new ArrayList<TectonicRegionType>();
		  list.add(TectonicRegionType.ACTIVE_SHALLOW);
		  return list;
	  }


}
