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

package org.opensha.sha.calc.IM_EventSet.v03;

import java.io.File;
import java.util.ArrayList;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.siteData.OrderedSiteDataProviderList;
import org.opensha.commons.data.siteData.SiteDataValue;
import org.opensha.commons.geo.Location;

public interface IM_EventSetCalc_v3_0_API {
	
	/**
	 * Returns the number of sites for the calculation
	 * 
	 * @return
	 */
	public int getNumSites();

	/**
	 * Returns the Location of the ith site.
	 * 
	 * @param i
	 * @return
	 */
	public Location getSiteLocation(int i);

	/**
	 * Returns the ordered site data provider list, or null to not use site data providers
	 * 
	 * @return
	 */
	public OrderedSiteDataProviderList getSiteDataProviders();

	/**
	 * Returns the user specified (in the input file) site data values for the site
	 * or null to try to use site data providers
	 * 
	 * @param i
	 * @return
	 */
	public ArrayList<SiteDataValue<?>> getUserSiteDataValues(int i);
	
	/**
	 * Returns the output directory for all results
	 * 
	 * @return
	 */
	public abstract File getOutputDir();
	
	/**
	 * This initializes the site data values for each site.
	 * 
	 * If there is user specified data for the specific site, that is given top
	 * priority. If there are also site data providers available, those will
	 * be used (but given lower priority than any user values).
	 * 
	 * @return
	 */
	public ArrayList<ArrayList<SiteDataValue<?>>> getSitesData();
	
	public ArrayList<Site> getSites();

}
