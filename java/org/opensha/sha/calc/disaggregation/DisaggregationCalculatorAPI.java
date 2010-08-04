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

package org.opensha.sha.calc.disaggregation;

import java.rmi.Remote;
import java.rmi.RemoteException;
import java.util.Map;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.util.TectonicRegionType;

/**
 * <p>Title: DisaggregationCalculatorAPI</p>
 * <p>Description: This class defines interface for Disaggregation calculator.
 * Implementation of this interface disaggregates a hazard curve based on the
 * input parameters imr, site and eqkRupforecast.  See Bazzurro and Cornell
 * (1999, Bull. Seism. Soc. Am., 89, pp. 501-520) for a complete discussion
 * of disaggregation.  The Dbar computed here is for rupture distance.</p>
 * @author : Nitin Gupta
 * @created Oct 01,2004
 * @version 1.0
 */
public interface DisaggregationCalculatorAPI extends Remote{

	/**
	 * Sets the Max Z Axis Range value fro the plotting purposes
	 * @param zMax
	 * @throws java.rmi.RemoteException
	 */
	public void setMaxZAxisForPlot(double zMax) throws
	java.rmi.RemoteException ; 

	/**
	 * this function performs the disaggregation.
	 * Returns true if it was succesfully able to disaggregate above
	 * a given IML else return false
	 *
	 * @param iml: the intensity measure level to disaggregate
	 * @param site: site parameter
	 * @param imr: selected IMR object
	 * @param eqkRupForecast: selected Earthquake rup forecast
	 * @return boolean
	 */
	public boolean disaggregate(double iml, Site site,
			ScalarIntensityMeasureRelationshipAPI imr,
			EqkRupForecast eqkRupForecast,
			double maxDist,ArbitrarilyDiscretizedFunc 
			magDistFilter) throws java.rmi.RemoteException;

	/**
	 * this function performs the disaggregation.
	 * Returns true if it was succesfully able to disaggregate above
	 * a given IML else return false
	 *
	 * @param iml: the intensity measure level to disaggregate
	 * @param site: site parameter
	 * @param imrMap: mapping of tectonic regions to IMR objects
	 * @param eqkRupForecast: selected Earthquake rup forecast
	 * @return boolean
	 */
	public boolean disaggregate(double iml, Site site,
			Map<TectonicRegionType, ScalarIntensityMeasureRelationshipAPI> imrMap,
			EqkRupForecast eqkRupForecast,
			double maxDist,ArbitrarilyDiscretizedFunc 
			magDistFilter) throws java.rmi.RemoteException;

	/**
	 * Sets the number of sources to be shown in the Disaggregation.
	 * @param numSources int
	 * @throws RemoteException
	 */
	public void setNumSourcestoShow(int numSources)throws
	java.rmi.RemoteException ;
	
	/**
	 * Enables/disables calculation and display of source distances in source data list.
	 * 
	 * @param showDistances
	 * @throws RemoteException 
	 */
	public void setShowDistances(boolean showDistances) throws RemoteException;

	/**
	 * This sets the maximum distance of sources to be considered in the calculation
	 * (as determined by the getMinDistance(Site) method of ProbEqkSource subclasses).
	 * Sources more than this distance away are ignored.
	 * Default value is 250 km.
	 *
	 * @param distance: the maximum distance in km
	 */
	//public void setMaxSourceDistance(double distance) throws java.rmi.RemoteException;

	/**
	 *
	 * Returns the disaggregated source list with following info ( in each line)
	 * 1)Source Id as given by OpenSHA
	 * 2)Name of the Source
	 * 3)Rate Contributed by that source
	 * 4)Percentage Contribution of the source in Hazard at the site.
	 *
	 * @return String
	 * @throws RemoteException
	 */
	public String getDisaggregationSourceInfo() throws java.rmi.RemoteException;

	/**
	 * gets the number of current rupture being processed
	 * @return
	 */
	public int getCurrRuptures() throws java.rmi.RemoteException;


	/**
	 * gets the total number of ruptures
	 * @return
	 */
	public int getTotRuptures() throws java.rmi.RemoteException;


	/**
	 * Checks to see if disaggregation calculation for the selected site
	 * have been completed.
	 * @return
	 */
	public boolean done() throws java.rmi.RemoteException;


	/**
	 * Creates the disaggregation plot using the GMT and return Disaggregation plot
	 * image web address as the URL string.
	 * @param metadata String
	 * @return String
	 * @throws RemoteException
	 */
	public String getDisaggregationPlotUsingServlet(String metadata) throws java.
	rmi.RemoteException;


	/**
	 * Setting up the Mag Range
	 * @param minMag double
	 * @param numMags int
	 * @param deltaMag double
	 */
	public void setMagRange(double minMag, int numMags, double deltaMag) throws
	java.rmi.RemoteException ;

	/**
	 * Setting up the Distance Range
	 * @param minDist double
	 * @param numDist int
	 * @param deltaDist double
	 */
	public void setDistanceRange(double minDist, int numDist, double deltaDist) throws
	java.rmi.RemoteException;

	/**
	 * Setting up custom distance bins
	 * @param distBinEdges - a double array of the distance-bin edges (in correct order, from low to high)
	 */
	public void setDistanceRange(double[] distBinEdges) throws
	java.rmi.RemoteException;

	/**
	 * Returns the Bin Data in the String format
	 * @return String
	 * @throws RemoteException
	 */
	public String getBinData()throws java.rmi.RemoteException;

	/**
	 *
	 * @returns resultant disaggregation in a String format.
	 * @throws java.rmi.RemoteException
	 */
	public String getMeanAndModeInfo() throws java.rmi.RemoteException;
}
