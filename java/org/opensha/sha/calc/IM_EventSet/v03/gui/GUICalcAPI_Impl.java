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

package org.opensha.sha.calc.IM_EventSet.v03.gui;

import java.io.File;
import java.util.ArrayList;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.siteData.OrderedSiteDataProviderList;
import org.opensha.commons.data.siteData.SiteDataValue;
import org.opensha.commons.geo.Location;
import org.opensha.sha.calc.IM_EventSet.v03.IM_EventSetCalc_v3_0;
import org.opensha.sha.calc.IM_EventSet.v03.IM_EventSetCalc_v3_0_API;

public class GUICalcAPI_Impl implements IM_EventSetCalc_v3_0_API {
	
	private ArrayList<Site> sites;
	private ArrayList<ArrayList<SiteDataValue<?>>> userSitesData;
	private ArrayList<ArrayList<SiteDataValue<?>>> sitesData;
	private File outputDir;
	private OrderedSiteDataProviderList providers;
	
	public GUICalcAPI_Impl(ArrayList<Location> locs, ArrayList<ArrayList<SiteDataValue<?>>> userSitesData,
			File outputDir, OrderedSiteDataProviderList providers) {
		sites = new ArrayList<Site>();
		for (Location loc : locs) {
			sites.add(new Site(loc));
		}
		this.userSitesData = userSitesData;
		this.outputDir = outputDir;
		this.providers = providers;
	}

	public int getNumSites() {
		return sites.size();
	}

	public File getOutputDir() {
		return outputDir;
	}

	public OrderedSiteDataProviderList getSiteDataProviders() {
		return providers;
	}

	public Location getSiteLocation(int i) {
		return sites.get(i).getLocation();
	}

	public ArrayList<Site> getSites() {
		return sites;
	}

	public ArrayList<ArrayList<SiteDataValue<?>>> getSitesData() {
		if (sitesData == null) {
			sitesData = IM_EventSetCalc_v3_0.getSitesData(this);
		}
		return sitesData;
	}

	public ArrayList<SiteDataValue<?>> getUserSiteDataValues(int i) {
		return userSitesData.get(i);
	}

}
