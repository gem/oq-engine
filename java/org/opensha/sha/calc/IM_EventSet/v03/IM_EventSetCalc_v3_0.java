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

import java.util.ArrayList;
import java.util.logging.Handler;
import java.util.logging.Level;
import java.util.logging.Logger;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.siteData.OrderedSiteDataProviderList;
import org.opensha.commons.data.siteData.SiteDataValue;

public abstract class IM_EventSetCalc_v3_0 implements IM_EventSetCalc_v3_0_API {
	
	public static Logger logger = Logger.getLogger("IMv3Log");
	
	public static void initLogger(Level level) {
		Logger parent = logger;
		while (parent != null) {
			for (Handler handler : parent.getHandlers())
				handler.setLevel(level);
			parent.setLevel(level);
			parent = parent.getParent();
		}
		logger.setLevel(level);
	}
	
	public static final float MIN_SOURCE_DIST = 200;

	/**
	 * This should ONLY be accessed through the getter method as it may
	 * be uninitialized
	 */
	private ArrayList<Site> sites = null;

	private ArrayList<ArrayList<SiteDataValue<?>>> sitesData = null;

	public IM_EventSetCalc_v3_0() {

	}

	public final ArrayList<Site> getSites() {
		if (sites == null) {
			logger.log(Level.FINE, "Generating site list");
			sites = new ArrayList<Site>();
			for (int i=0; i<getNumSites(); i++) {
				Site site = new Site(getSiteLocation(i));
				sites.add(site);
			}
		}
		return sites;
	}
	
	public static ArrayList<ArrayList<SiteDataValue<?>>> getSitesData(IM_EventSetCalc_v3_0_API calc) {
		ArrayList<ArrayList<SiteDataValue<?>>> sitesData = new ArrayList<ArrayList<SiteDataValue<?>>>();
		ArrayList<Site> sites = calc.getSites();
		OrderedSiteDataProviderList providers = calc.getSiteDataProviders();
		for (int i=0; i<sites.size(); i++) {
			Site site = sites.get(i);
			ArrayList<SiteDataValue<?>> dataVals = calc.getUserSiteDataValues(i);
			if (dataVals == null) {
				dataVals = new ArrayList<SiteDataValue<?>>();
			}
			if (providers != null) {
				ArrayList<SiteDataValue<?>> provData = providers.getAllAvailableData(site.getLocation());
				if (provData != null)
					dataVals.addAll(provData);
			}
			sitesData.add(dataVals);
		}
		return sitesData;
	}

	public final ArrayList<ArrayList<SiteDataValue<?>>> getSitesData() {
		if (sitesData == null) {
			logger.log(Level.FINE, "Generating site data providers lists");
			sitesData = getSitesData(this);
		}

		return sitesData;
	}
	
}
