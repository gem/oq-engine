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

package org.opensha.commons.data.region;

import java.io.IOException;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.ListIterator;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.siteData.OrderedSiteDataProviderList;
import org.opensha.commons.data.siteData.SiteDataAPI;
import org.opensha.commons.data.siteData.SiteDataValue;
import org.opensha.commons.data.siteData.SiteDataValueList;
import org.opensha.commons.data.siteData.impl.CVM4BasinDepth;
import org.opensha.commons.data.siteData.impl.WillsMap2006;
import org.opensha.commons.exceptions.RegionConstraintException;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.sha.util.SiteTranslator;

/**
 * <p>Title: SitesInGriddedRegion</p>
 * <p>Description: This Class adds and replace the site params to each site for a gridded
 * region. This class fills in the site params for each site in the rectangular gridded
 * region. Right now all the sites have same site-type params, but later each site
 * will be getting the different values once plugged into CVM(community Velocity Model.
 * The Advantage of this class is that one does not have to create the iterator of all
 * sites which consumes a lot od memory to store all those sit, but we can just get one
 * site at a time and perform computation for that site.</p>
 * @author: Nitin Gupta & Vipin Gupta
 * @created : March 15,2003
 * @version 1.0
 */
// implements SitesInGriddedRegionAPI
// extends GriddedRegion
public class SitesInGriddedRegion implements Serializable {

	//Debug parameter
	public static final boolean D= false;

	//definition for the Siet Object
	Site site = new Site();

	ArrayList<SiteDataValueList<?>> siteDataValueLists = null;

	//set the same site type for each site
	private boolean setSameSiteParams = true;

	//ArrayList that contains the default Values for the Site parameters if CVM do not cover that site
	private ArrayList defaultSiteParams;

	//Instance of the site TransLator class
	SiteTranslator siteTranslator = new SiteTranslator();
	
	private GriddedRegion region;

	public SitesInGriddedRegion(GriddedRegion region) {
		this.region = region;
	}
	
	public GriddedRegion getRegion() {
		return region;
	}
//	public SitesInGriddedRegion(LocationList locList, double gridSpacing) {
//		super(locList,gridSpacing);
//	}

//	public SitesInGriddedRegion(double minLat,double maxLat,double minLon,double maxLon,
//			double gridSpacing) throws
//			RegionConstraintException {
//		super(minLat,maxLat,minLon,maxLon,gridSpacing);
//	}

//	public SitesInGriddedRegion(Region geo,
//			double gridSpacing) throws
//			RegionConstraintException {
//		super(geo.getMinLat(), geo.getMaxLat(), geo.getMinLon(), geo.getMaxLon(), gridSpacing);
//	}

	/**
	 * Gets the list for Site Params for region from application called this function.
	 * @param willsSiteClass : String Array of Wills Site Class Values
	 * @param bd : double Array of Basin Depth Values
	 */
	@Deprecated
	public void setSiteParamsForRegion(String[] willsSiteClass, double[] bd){

		//as we are getting the values from application and want to set the site params
		if(willsSiteClass != null && bd != null && willsSiteClass.length != bd.length)
			throw new RuntimeException("Invalid Range Site Type Values, both Wills "+
			"Site Class and Basindepth should have same number of values");
		
		siteDataValueLists = new ArrayList<SiteDataValueList<?>>();

		//if either wills site class or basin depth are not null
		if(willsSiteClass !=null || bd!=null){
			//either wills site class or basin depth are not null then each site needs
			//to be filled up with actaul site type parameters.
			setSameSiteParams = false;
			//if wills site class vlaues are not null then fill their values
			if(willsSiteClass !=null){
				ArrayList<String> willsData = new ArrayList<String>();
				for (String wills : willsSiteClass) {
					willsData.add(wills);
				}
				siteDataValueLists.add(new SiteDataValueList<String>(SiteDataAPI.TYPE_WILLS_CLASS,
						SiteDataAPI.TYPE_FLAG_MEASURED, willsData, null));
			}
			//If basin depth Values are not null, then fill in their values
			if(bd !=null){
				ArrayList<Double> basinData = new ArrayList<Double>();
				for (double basin : bd) {
					basinData.add(basin);
				}
				siteDataValueLists.add(new SiteDataValueList<Double>(SiteDataAPI.TYPE_DEPTH_TO_2_5,
						SiteDataAPI.TYPE_FLAG_MEASURED, basinData, null));
			}
		}
	}

	public void setSiteParamsForRegion(OrderedSiteDataProviderList providers) throws IOException {
		setSameSiteParams = false;
		//getting the list of Locations in the region
		LocationList locList = region.getNodeList();
		
		siteDataValueLists = new ArrayList<SiteDataValueList<?>>();
		
		for (int i=0; i<providers.size(); i++) {
			if (!providers.isEnabled(i)) {
				continue;
			}
			SiteDataAPI<?> provider = providers.getProvider(i);
			
			ArrayList<?> vals = provider.getValues(locList);
			siteDataValueLists.add(new SiteDataValueList(vals, provider));
		}
	}
	
	public void setSiteDataValueLists(ArrayList<SiteDataValueList<?>> siteDataValueLists) {
		setSameSiteParams = false;
		this.siteDataValueLists = siteDataValueLists;
	}
	
	public ArrayList<SiteDataValueList<?>> getSiteDataValueLists() {
		return siteDataValueLists;
	}

	/**
	 * Gets the list for Site Params for region from servlet hosted at web server.
	 *
	 * After calling this function one should also call setDefaultSiteParams() , in
	 * order to the default value for the site parameters, in case we don't get
	 * any value from servlet.
	 *
	 * @param connectForBasinDepth : boolean to know if basin depth also required along with
	 * Wills Site class values to the Site Parameters for each location in the region.
	 */
	@Deprecated
	public void setSiteParamsForRegionFromServlet(boolean connectForBasinDepth){
		ArrayList<SiteDataAPI<?>> providers = new ArrayList<SiteDataAPI<?>>();
		try {
			providers.add(new WillsMap2006());
		} catch (IOException e) {
			throw new RuntimeException(e);
		}
		if (connectForBasinDepth) {
			try {
				providers.add(new CVM4BasinDepth(SiteDataAPI.TYPE_DEPTH_TO_2_5));
			} catch (IOException e) {
				throw new RuntimeException(e);
			}
		}
		OrderedSiteDataProviderList providerList = new OrderedSiteDataProviderList(providers);
		try {
			setSiteParamsForRegion(providerList);
		} catch (IOException e) {
			throw new RuntimeException(e);
		}
	}




	/**
	 * Gets the site at specified index.
	 * 
	 * NOTE (IMP) : This class translates the willsSiteClass values to the site parameters of the AttenuationsRelationships.
	 * If it fails to translate any site parameters , either becuase there is no Wills class value for a given site or any other 
	 * reason, it then uses the default value provided by the user for that parameter or any other site parameter for that 
	 * AttenuationRelationship.
	 * @param index
	 * @returns site at the index
	 */
	public Site getSite(int index) throws RegionConstraintException {
		site.setLocation(region.locationForIndex(index));
		String siteInfo=null;
		if(!setSameSiteParams){
			//getting the Site Parameters Iterator
			Iterator<ParameterAPI<?>> it = site.getParametersIterator();
			//checking to see if we are getting the correct value for willsSiteClassList and basin depth.
			if(D){
				System.out.println(site.getLocation().toString());
			}
			while(it.hasNext()) {
				ParameterAPI tempParam = it.next();
				
				ArrayList<SiteDataValue<?>> datas = new ArrayList<SiteDataValue<?>>();
				for (SiteDataValueList<?> dataList : siteDataValueLists) {
					datas.add(dataList.getValue(index));
				}
				
				boolean flag = siteTranslator.setParameterValue(tempParam, datas);
				
				if (!flag) {
					Iterator<ParameterAPI> it1 = defaultSiteParams.iterator();
					while(it1.hasNext()){
						ParameterAPI param = it1.next();
						if(tempParam.getName().equals(param.getName()))
							tempParam.setValue(param.getValue());
					}
				}
			}
		}
		return site;
	}

	/**
	 * Add this site-type parameter to all the sites in the gridded region
	 * @param it
	 */
	public void addSiteParams(Iterator it) {
		//iterator of all the site types supported by the selecetd IMR for that gridded region
		while(it.hasNext()){
			ParameterAPI tempParam=(ParameterAPI)it.next();
			if(!site.containsParameter(tempParam))
				site.addParameter(tempParam);
		}
	}


	/**
	 * This function removes the site types params from the site
	 * @param it
	 */
	public void removeSiteParams(){

		ListIterator it1=site.getParametersIterator();
		while(it1.hasNext())
			site.removeParameter((ParameterAPI)it1.next());
	}

	/**
	 * This function craetes the iterator of all the site within that region and
	 * return its iterator
	 * @return
	 */
//	public Iterator getSitesIterator(){
//		ArrayList sitesVector=new ArrayList();
//		//get the iterator of all the locations within that region
//		ListIterator it=this.getGridLocationsIterator();
//		//get the iterator for all the site types
//		ListIterator siteParamsIt = site.getParametersIterator();
//		while(it.hasNext()){
//			//create the site object and add it to tbe ArrayList List
//			Site newSite = new Site((Location)it.next());
//			while(siteParamsIt.hasNext()){
//				ParameterAPI tempParam = (ParameterAPI)siteParamsIt.next();
//				if(!newSite.containsParameter(tempParam))
//					newSite.addParameter(tempParam);
//			}
//			sitesVector.add(newSite);
//		}
//		return sitesVector.iterator();
//	}



	/**
	 * This function is called if the site Params need to be set using WILLS site type
	 * and basin depth from the SCEC basin depth values.
	 */

	/**
	 * Calling this function will set the Site Params to whatever their value is currently.
	 * All sites will be having the same value for those Site Parameters.
	 */
	public void setSameSiteParams(){
		setSameSiteParams = true;
		siteDataValueLists = null;
	}

	/**
	 * Sets the default Site Parameters in case CVM don't cover the regions
	 * @param defaultSiteParamsIt : Iterator for the Site Params and their Values
	 */
	// TODO revisit set to make copy of params; probably ok
	public void setDefaultSiteParams(ArrayList defaultSiteParams){
		//this.defaultSiteParams = defaultSiteParams;
		if (this.defaultSiteParams != null)
			this.defaultSiteParams.clear();
		else
			this.defaultSiteParams = new ArrayList<ParameterAPI>();
		for (ParameterAPI param : (ArrayList<ParameterAPI>)defaultSiteParams) {
			this.defaultSiteParams.add((ParameterAPI)param.clone());
		}
	}

}
