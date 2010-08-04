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

import java.io.IOException;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.ListIterator;
import java.util.logging.Level;
import java.util.logging.Logger;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.siteData.SiteDataValue;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.commons.param.DependentParameterAPI;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.util.SiteTranslator;

public abstract class IM_EventSetOutputWriter {
	
	protected static Logger logger = IM_EventSetCalc_v3_0.logger;
	
	protected IM_EventSetCalc_v3_0_API calc;
	private static SiteTranslator siteTrans = new SiteTranslator();
	
	private float sourceCutOffDistance = 0;
	private Site siteForSourceCutOff = null;
	
	public static final DecimalFormat meanSigmaFormat = new DecimalFormat("0.####");
	public static final DecimalFormat distFormat = new DecimalFormat("0.###");
	public static final DecimalFormat rateFormat = new DecimalFormat("####0E0");
	
	public IM_EventSetOutputWriter(IM_EventSetCalc_v3_0_API calc) {
		this.calc = calc;
	}
	
	public abstract void writeFiles(ArrayList<EqkRupForecastAPI> erfs, ArrayList<ScalarIntensityMeasureRelationshipAPI> attenRels,
			ArrayList<String> imts) throws IOException;
	
	public void writeFiles(EqkRupForecastAPI erf, ArrayList<ScalarIntensityMeasureRelationshipAPI> attenRels,
			ArrayList<String> imts) throws IOException {
		ArrayList<EqkRupForecastAPI> erfs = new ArrayList<EqkRupForecastAPI>();
		erfs.add(erf);
		writeFiles(erfs, attenRels, imts);
	}
	
	public void writeFiles(EqkRupForecastAPI erf, ScalarIntensityMeasureRelationshipAPI imr,
			String imt) throws IOException {
		ArrayList<ScalarIntensityMeasureRelationshipAPI> imrs = new ArrayList<ScalarIntensityMeasureRelationshipAPI>();
		imrs.add(imr);
		ArrayList<String> imts = new ArrayList<String>();
		imts.add(imt);
		writeFiles(erf, imrs, imts);
	}
	
	public abstract String getName();
	
	public static String getHAZ01IMTString(ParameterAPI<?> param) {
		String imt = param.getName();
		
		if (param instanceof DependentParameterAPI) {
			DependentParameterAPI<?> depParam = (DependentParameterAPI<?>)param;
			ListIterator<ParameterAPI<?>> it = depParam.getIndependentParametersIterator();
			while (it.hasNext()) {
				ParameterAPI<?> dep = it.next();
				if (dep.getName().equals(PeriodParam.NAME)) {
					double period = (Double)dep.getValue();
					int p10 = (int)(period * 10.0 + 0.5);
					String p10Str = p10 + "";
					if (p10Str.length() < 2)
						p10Str = "0" + p10Str;
					imt += p10Str;
					break;
				}
			}
		}
		return imt;
	}
	
	public static String getRegularIMTString(ParameterAPI<?> param) {
		String imt = param.getName();
		
		if (param instanceof DependentParameterAPI) {
			DependentParameterAPI<?> depParam = (DependentParameterAPI<?>)param;
			ListIterator<ParameterAPI<?>> it = depParam.getIndependentParametersIterator();
			while (it.hasNext()) {
				ParameterAPI<?> dep = it.next();
				if (dep.getName().equals(PeriodParam.NAME)) {
					double period = (Double)dep.getValue();
					imt += " " + (float)period;
					break;
				}
			}
		}
		return imt;
	}
	
	/**
	 * Sets the IMT from the string specification
	 * 
	 * @param imtLine
	 * @param attenRel
	 */
	public static void setIMTFromString(String imtStr, ScalarIntensityMeasureRelationshipAPI attenRel) {
		String imt = imtStr.trim();
		if ((imt.startsWith("SA") || imt.startsWith("SD"))) {
			logger.log(Level.FINE, "Parsing IMT with Period: " + imt);
			// this is SA/SD
			String perSt = imt.substring(2);
			String theIMT = imt.substring(0, 2);
			double period;
			if (perSt.startsWith(" ") || perSt.startsWith("\t")) {
				// this is a 'SA period' format IMT
				logger.log(Level.FINEST, "Split into IMT: " + theIMT + ", Period portion: " + perSt);
				period = Double.parseDouble(perSt.trim());
				
			} else {
				// this is a HAZ01 style IMT
				logger.log(Level.FINEST, "Split into IMT: " + theIMT + ", Period portion (HAZ01 style): " + perSt);
				period = Double.parseDouble(perSt) / 10;
			}
			attenRel.setIntensityMeasure(theIMT);
			DependentParameterAPI imtParam = (DependentParameterAPI)attenRel.getIntensityMeasure();
			imtParam.getIndependentParameter(PeriodParam.NAME).setValue(period);
			logger.log(Level.FINE, "Parsed IMT with Period: " + imt + " => " + theIMT + ", period: " + period);
//			System.out.println("imtstr: " + imt + ", " + attenRel.getIntensityMeasure().getName()
//						+ ": " + attenRel.getParameter(PeriodParam.NAME).getValue());
		} else {
			logger.log(Level.FINE, "Setting IMT  from String");
			attenRel.setIntensityMeasure(imt);
		}
	}
	
	/**
	 * Gets all of the default site params from the attenuation relationship
	 * 
	 * @param attenRel
	 * @return
	 */
	@SuppressWarnings("unchecked")
	protected ArrayList<ParameterAPI> getDefaultSiteParams(ScalarIntensityMeasureRelationshipAPI attenRel) {
		logger.log(Level.FINE, "Storing default IMR site related params.");
		ListIterator<ParameterAPI<?>> siteParamsIt = attenRel.getSiteParamsIterator();
		ArrayList<ParameterAPI> defaultSiteParams = new ArrayList<ParameterAPI>();

		while (siteParamsIt.hasNext()) {
			defaultSiteParams.add((ParameterAPI) siteParamsIt.next().clone());
		}

		return defaultSiteParams;
	}

	/**
	 * Sets the site params for the given Attenuation Relationship to the value in the given params.
	 * @param attenRel
	 * @param defaultSiteParams
	 */
	@SuppressWarnings("unchecked")
	protected void setSiteParams(ScalarIntensityMeasureRelationshipAPI attenRel, ArrayList<ParameterAPI> defaultSiteParams) {
		logger.log(Level.FINE, "Restoring default IMR site related params.");
		for (ParameterAPI param : defaultSiteParams) {
			ParameterAPI attenParam = attenRel.getParameter(param.getName());
			attenParam.setValue(param.getValue());
		}
	}

	/**
	 * This goes through each site and makes sure that it has a parameter for each site
	 * param from the Attenuation Relationship. It then tries to set that parameter from
	 * its own data values, and if it can't, uses the attenuation relationship's default.
	 * 
	 * @param attenRel
	 * @return
	 */
	protected ArrayList<Site> getInitializedSites(ScalarIntensityMeasureRelationshipAPI attenRel) {
		logger.log(Level.FINE, "Retrieving and setting Site related params for IMR");
		// get the list of sites
		ArrayList<Site> sites = this.calc.getSites();
		ArrayList<ArrayList<SiteDataValue<?>>> sitesData = this.calc.getSitesData();

		// we need to make sure that the site has parameters for this atten rel
		ListIterator<ParameterAPI<?>> siteParamsIt = attenRel.getSiteParamsIterator();
		while (siteParamsIt.hasNext()) {
			ParameterAPI attenParam = siteParamsIt.next();
			for (int i=0; i<sites.size(); i++) {
				Site site = sites.get(i);
				ArrayList<SiteDataValue<?>> siteData = sitesData.get(i);
				ParameterAPI siteParam;
				if (site.containsParameter(attenParam.getName())) {
					siteParam = site.getParameter(attenParam.getName());
				} else {
					siteParam = (ParameterAPI)attenParam.clone();
					site.addParameter(siteParam);
				}
				// now try to set this parameter from the site data
				boolean success = siteTrans.setParameterValue(siteParam, siteData);
				// if we couldn't set it from our data, use the atten rel's default
				if (!success)
					siteParam.setValue(attenParam.getValue());
			}
		}
//		for (int i=0; i<sites.size(); i++) {
//			Site site = sites.get(i);
//			ArrayList<SiteDataValue<?>> siteData = sitesData.get(i);
//			printSiteParams(site, siteData);
//		}
		return sites;
	}
	
	private float getSourceCutOffDistance() {
		if (sourceCutOffDistance == 0) {
			createSiteList();
		}
		return sourceCutOffDistance;
	}
	
	private Site getSiteForSourceCutOff() {
		if (siteForSourceCutOff == null) {
			createSiteList();
		}
		return siteForSourceCutOff;
	}
	
	/**
	 * This method finds the location at the middle of the region encompassing all of
	 * the sites and gets a cutoff distance such that all ruptures within 200 km of any
	 * site are included in the output.
	 */
	protected void createSiteList() {
		logger.log(Level.FINE, "Calculating source cutoff site and distance");
		//gets the min lat, lon and max lat, lon from given set of locations.
		double minLon = Double.MAX_VALUE;
		double maxLon = Double.NEGATIVE_INFINITY;
		double minLat = Double.MAX_VALUE;
		double maxLat = Double.NEGATIVE_INFINITY;
		int numSites = calc.getNumSites();
		for (int i = 0; i < numSites; ++i) {

			Location loc = calc.getSiteLocation(i);
			double lon = loc.getLongitude();
			double lat = loc.getLatitude();
			if (lon > maxLon)
				maxLon = lon;
			if (lon < minLon)
				minLon = lon;
			if (lat > maxLat)
				maxLat = lat;
			if (lat < minLat)
				minLat = lat;
		}
		double middleLon = (minLon + maxLon) / 2;
		double middleLat = (minLat + maxLat) / 2;

		//getting the source-site cuttoff distance
		sourceCutOffDistance = (float) LocationUtils.horzDistance(
				new Location(middleLat, middleLon),
				new Location(minLat, minLon)) + 
				IM_EventSetCalc_v3_0.MIN_SOURCE_DIST;
		siteForSourceCutOff = new Site(new Location(middleLat, middleLon));

		return;
	}
	
	/**
	 * This method checks if the source is within 200 KM of any site
	 * 
	 * @param source
	 * @return
	 */
	public boolean shouldIncludeSource(ProbEqkSource source) {
		float sourceCutOffDistance = getSourceCutOffDistance();
		Site siteForSourceCutOff = getSiteForSourceCutOff();
		
		double sourceDistFromSite = source.getMinDistance(siteForSourceCutOff);
		if (sourceDistFromSite > sourceCutOffDistance) {
			logger.log(Level.FINEST, "Source outside of cutoff distance, skipping");
			return false;
		}
		return true;
	}

	@Override
	public String toString() {
		// TODO Auto-generated method stub
		return getName();
	}

}
