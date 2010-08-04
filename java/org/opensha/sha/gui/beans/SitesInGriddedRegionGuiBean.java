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

package org.opensha.sha.gui.beans;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.ListIterator;

import javax.swing.JOptionPane;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.region.CaliforniaRegions;
import org.opensha.commons.data.region.SitesInGriddedRegion;
import org.opensha.commons.exceptions.RegionConstraintException;
import org.opensha.commons.geo.BorderType;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.Region;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.IntegerParameter;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterConstraintAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ParameterListEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeFailEvent;
import org.opensha.commons.param.event.ParameterChangeFailListener;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.sha.util.SiteTranslator;


/**
 * <p>SitesInGriddedRegionGuiBean </p>
 * <p>Description: This creates the Gridded Region parameter Editor with Site Params
 * for the selected Attenuation Relationship in the Application.
 * </p>
 * @author Kevin Milner
 * @date March 4, 2009
 * @version 1.0
 */



public class SitesInGriddedRegionGuiBean extends ParameterListEditor implements
ParameterChangeFailListener, ParameterChangeListener, Serializable {

	// for debug purposes
	protected final static String C = "SiteParamList";

	/**
	 * Latitude and longitude are added to the site attenRelImplmeters
	 */
	public final static String MIN_LONGITUDE = "Min Longitude";
	public final static String MAX_LONGITUDE = "Max Longitude";
	public final static String MIN_LATITUDE =  "Min  Latitude";
	public final static String MAX_LATITUDE =  "Max  Latitude";
	public final static String GRID_SPACING =  "Grid Spacing";
	public final static String SITE_PARAM_NAME = "Set Site Params";
	public final static String REGION_SELECT_NAME = "Region Type/Preset";
	public final static String NUM_SITES_NAME = "Number Of Sites";

	public final static String DEFAULT = "Default ";

	// title for site paramter panel
	public final static String GRIDDED_SITE_PARAMS = "Set Gridded Region Params";

	//Site Params ArrayList
	ArrayList<ParameterAPI> siteParams = new ArrayList<ParameterAPI>();

	//Static String for setting the site Params
	public final static String SET_ALL_SITES = "Apply same site parameter(s) to all locations";
	public final static String USE_SITE_DATA = "Use site data providers";

	/**
	 * Longitude and Latitude paramerts to be added to the site params list
	 */
	private DoubleParameter minLon = new DoubleParameter(MIN_LONGITUDE,
			new Double(-360), new Double(360),new Double(-119.5));
	private DoubleParameter maxLon = new DoubleParameter(MAX_LONGITUDE,
			new Double(-360), new Double(360),new Double(-117));
	private DoubleParameter minLat = new DoubleParameter(MIN_LATITUDE,
			new Double(-90), new Double(90), new Double(33.5));
	private DoubleParameter maxLat = new DoubleParameter(MAX_LATITUDE,
			new Double(-90), new Double(90), new Double(34.7));
	private DoubleParameter gridSpacing = new DoubleParameter(GRID_SPACING,
			new Double(.001),new Double(1.0),new String("Degrees"),new Double(.1));
	private IntegerParameter numSites = new IntegerParameter(NUM_SITES_NAME);


	//StringParameter to set site related params
	private StringParameter siteParam;

	//SiteTranslator
	private SiteTranslator siteTrans = new SiteTranslator();

	//instance of class EvenlyGriddedRectangularGeographicRegion
	private SitesInGriddedRegion gridRegion;

	public final static String RECTANGULAR_NAME = "Rectangular Region";
	public final static String CUSTOM_NAME = "Custom Region";

	// names for defaults
	public final static String RELM_TESTING_NAME = "RELM Testing Region";
	public final static String RELM_COLLECTION_NAME = "RELM Collection Region";
	public final static String SO_CAL_NAME = "Southern California Region";
	public final static String NO_CAL_NAME = "Northern Caliofnia Region";

	ArrayList<Region> presets;

	private StringParameter regionSelect;

	public SitesInGriddedRegionGuiBean(ArrayList<Region> presets) throws RegionConstraintException {
		ArrayList<String> presetsStr = new ArrayList<String>();
		presetsStr.add(SitesInGriddedRegionGuiBean.RECTANGULAR_NAME);
		//		presetsStr.add(SitesInGriddedRegionGuiBean.CUSTOM_NAME);
		for (Region preset : presets) {
			presetsStr.add(preset.getName());
		}

		this.presets = presets;

		regionSelect = new StringParameter(REGION_SELECT_NAME, presetsStr);
		regionSelect.setValue(SitesInGriddedRegionGuiBean.RECTANGULAR_NAME);
		regionSelect.addParameterChangeListener(this);

		//defaultVs30.setInfo(this.VS30_DEFAULT_INFO);
		//parameterList.addParameter(defaultVs30);
		minLat.addParameterChangeFailListener(this);
		minLon.addParameterChangeFailListener(this);
		maxLat.addParameterChangeFailListener(this);
		maxLon.addParameterChangeFailListener(this);
		gridSpacing.addParameterChangeFailListener(this);

		minLat.addParameterChangeListener(this);
		minLon.addParameterChangeListener(this);
		maxLat.addParameterChangeListener(this);
		maxLon.addParameterChangeListener(this);
		gridSpacing.addParameterChangeListener(this);

		//creating the String Param for user to select how to get the site related params
		ArrayList<String> siteOptions = new ArrayList<String>();
		siteOptions.add(SET_ALL_SITES);
		siteOptions.add(USE_SITE_DATA);
		siteParam = new StringParameter(SITE_PARAM_NAME,siteOptions,(String)siteOptions.get(0));
		siteParam.addParameterChangeListener(this);

		// add the longitude and latitude paramters
		parameterList = new ParameterList();
		parameterList.addParameter(regionSelect);
		parameterList.addParameter(minLon);
		parameterList.addParameter(maxLon);
		parameterList.addParameter(minLat);
		parameterList.addParameter(maxLat);
		parameterList.addParameter(gridSpacing);
		parameterList.addParameter(numSites);
		parameterList.addParameter(siteParam);

		updateNumSites();

		editorPanel.removeAll();
		addParameters();
		createAndUpdateSites();

		try {
			jbInit();
		}catch(Exception e) {
			e.printStackTrace();
		}
	}

	/**
	 * constuctor which builds up mapping between IMRs and their related sites
	 */
	public SitesInGriddedRegionGuiBean() throws RegionConstraintException {
		this(generateDefaultRegions());
	}

	public static ArrayList<Region> generateDefaultRegions() {
		ArrayList<Region> regions = new ArrayList<Region>();

		// TODO these are circular see namedGeoRegion
		Region region;
		
		region = new Region(
				new CaliforniaRegions.RELM_TESTING().getBorder(), BorderType.MERCATOR_LINEAR);
		region.setName(RELM_TESTING_NAME);
		regions.add(region);
		
		region = new Region(
				new CaliforniaRegions.RELM_COLLECTION().getBorder(), BorderType.MERCATOR_LINEAR);
		region.setName(RELM_COLLECTION_NAME);
		regions.add(region);
		
		region = new Region(
				new CaliforniaRegions.RELM_SOCAL().getBorder(), BorderType.MERCATOR_LINEAR);
		region.setName(SO_CAL_NAME);
		regions.add(region);
		
		region = new Region(
				new CaliforniaRegions.RELM_NOCAL().getBorder(), BorderType.MERCATOR_LINEAR);
		region.setName(NO_CAL_NAME);
		regions.add(region);

		return regions;
	}
	
	private void reloadSiteParams() {
		boolean useData = this.isUseSiteData();
		
		Iterator<ParameterAPI<?>> it = parameterList.getParametersIterator();
		
		while (it.hasNext()) {
			ParameterAPI<?> param = it.next();
			
			if (isSiteParam(param)) {
				parameterList.removeParameter(param);
				String name = param.getName();
				
				if (useData) {
					if (!name.startsWith(DEFAULT))
						param.setName(DEFAULT + name);
				} else {
					if (name.startsWith(DEFAULT))
						param.setName(name.replaceFirst(DEFAULT, ""));
				}
				System.out.println("Reloaded: " + name);
				parameterList.addParameter(param);
			}
		}
		
		// now make sure they're all there...
		for (ParameterAPI param : siteParams) {
			if (!parameterList.containsParameter(param)) {
				if (isSiteParam(param)) {
					String name = param.getName();
					if (useData) {
						if (!name.startsWith(DEFAULT))
							param.setName(DEFAULT + name);
					} else {
						if (name.startsWith(DEFAULT))
							param.setName(name.replaceFirst(DEFAULT, ""));
					}
//					System.out.println("Reloaded: " + name);
					parameterList.addParameter(param);
				}
			}
		}
		
		this.refreshParamEditor();
		editorPanel.removeAll();
		addParameters();
		editorPanel.validate();
		editorPanel.repaint();
		setTitle(GRIDDED_SITE_PARAMS);
	}

	/**
	 * This function removes the previous site parameters and adds as passed in iterator
	 *
	 * @param it
	 */
	public void replaceSiteParams(Iterator<ParameterAPI<?>> it) {
		boolean useData = this.isUseSiteData();
		
		// first remove all the parameters except latitude and longitude
		Iterator<ParameterAPI<?>> siteIt = parameterList.getParametersIterator();
		while(siteIt.hasNext()) { // remove all the parameters except latitude and longitude and gridSpacing
			ParameterAPI<?> param = siteIt.next();
			if(isSiteParam(param)) {
				parameterList.removeParameter(param);
				System.out.println("Removed: " + param.getName());
			}
		}
		
		siteParams.clear();

		// now add all the new params
		while (it.hasNext()) {
			ParameterAPI param = (ParameterAPI)it.next().clone();
			String name = param.getName();
			if (useData) {
				if (!name.startsWith(DEFAULT))
					param.setName(DEFAULT + name);
			} else {
				if (name.startsWith(DEFAULT))
					param.setName(name.replaceFirst(DEFAULT, ""));
			}
			parameterList.addParameter(param);
			siteParams.add(param);
			System.out.println("Added: " + param.getName());
		}
		
		editorPanel.removeAll();
		addParameters();
		editorPanel.validate();
		editorPanel.repaint();
		setTitle(GRIDDED_SITE_PARAMS);
	}



	/**
	 * gets the iterator of all the sites
	 *
	 * @return
	 */ // not currently used TODO clean
//	public Iterator<Site> getAllSites() {
//		return gridRegion.getSitesIterator();
//	}


	/**
	 * get the clone of site object from the site params
	 *
	 * @return
	 */
	public Iterator<Site> getSitesClone() {
		Iterator<Location> lIt = gridRegion.getRegion().getNodeList().iterator();
		ArrayList<Site> newSiteVector=new ArrayList<Site>();
		while(lIt.hasNext())
			newSiteVector.add(new Site(lIt.next()));

		ListIterator it  = parameterList.getParametersIterator();
		// clone the paramters
		while(it.hasNext()){
			ParameterAPI tempParam= (ParameterAPI)it.next();
			for(int i=0;i<newSiteVector.size();++i){
				if(!((Site)newSiteVector.get(i)).containsParameter(tempParam))
					((Site)newSiteVector.get(i)).addParameter((ParameterAPI)tempParam.clone());
			}
		}
		return newSiteVector.iterator();
	}

	/**
	 * this function updates the GriddedRegion object after checking with the latest
	 * lat and lons and gridSpacing
	 * So, we update the site object as well
	 *
	 */
	private void updateGriddedSiteParams() throws
	RegionConstraintException {

		ArrayList<ParameterAPI> v= new ArrayList<ParameterAPI>();
		createAndUpdateSites();
		//getting the site params for the first element of the siteVector
		//becuase all the sites will be having the same site Parameter
		Iterator<ParameterAPI> it = siteParams.iterator();
		while(it.hasNext())
			v.add((ParameterAPI)it.next());
		gridRegion.addSiteParams(v.iterator());
	}


	public ArrayList<ParameterAPI> getSiteParams() {
		return siteParams;
	}


	/**
	 * Shown when a Constraint error is thrown on a ParameterEditor
	 *
	 * @param  e  Description of the Parameter
	 */
	public void parameterChangeFailed( ParameterChangeFailEvent e ) {


		String S = C + " : parameterChangeFailed(): ";



		StringBuffer b = new StringBuffer();

		ParameterAPI param = ( ParameterAPI ) e.getSource();


		ParameterConstraintAPI constraint = param.getConstraint();
		String oldValueStr = e.getOldValue().toString();
		String badValueStr = e.getBadValue().toString();
		String name = param.getName();

		b.append( "The value ");
		b.append( badValueStr );
		b.append( " is not permitted for '");
		b.append( name );
		b.append( "'.\n" );
		b.append( "Resetting to ");
		b.append( oldValueStr );
		b.append( ". The constraints are: \n");
		b.append( constraint.toString() );

		JOptionPane.showMessageDialog(
				this, b.toString(),
				"Cannot Change Value", JOptionPane.INFORMATION_MESSAGE
		);
	}

	private boolean updateNumSites() {
		try {
			createAndUpdateSites();
		} catch (RegionConstraintException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		if (gridRegion != null) {
			numSites.setValue(gridRegion.getRegion().getNodeCount());
			LocationList locs = gridRegion.getRegion().getBorder();
			for (int i=0; i<locs.size(); i++) {
				Location loc = locs.get(i);
				System.out.println(loc.getLatitude() + " " + loc.getLongitude());
			}
			return true;
		}
		return false;
	}

	/**
	 * This function is called when value a parameter is changed
	 * @param e Description of the parameter
	 */
	public void parameterChange(ParameterChangeEvent e){
		ParameterAPI param = ( ParameterAPI ) e.getSource();

		boolean update = false;

		if (param == regionSelect || param == minLat || param == maxLat || param == minLon || param == maxLon || param == gridSpacing) {
			update = updateNumSites();
		}

		if(param.getName().equals(SITE_PARAM_NAME))
			reloadSiteParams();
		else if (param == regionSelect || update) {
			String name = (String)(regionSelect.getValue());
			parameterList.clear();
			parameterList.addParameter(regionSelect);
			if (name.equals(SitesInGriddedRegionGuiBean.RECTANGULAR_NAME)) {
				parameterList.addParameter(minLon);
				parameterList.addParameter(maxLon);
				parameterList.addParameter(minLat);
				parameterList.addParameter(maxLat);
			} else if (name.equals(SitesInGriddedRegionGuiBean.CUSTOM_NAME)) {

			} else {

			}

			parameterList.addParameter(gridSpacing);
			parameterList.addParameter(numSites);
			parameterList.addParameter(siteParam);
			reloadSiteParams();
			refreshParamEditor();

			editorPanel.removeAll();
			addParameters();
			editorPanel.validate();
			editorPanel.repaint();
		}
	}

	/**
	 * This method creates the gridded region with the min -max Lat and Lon
	 * It also checks if the Max Lat is less than Min Lat and
	 * Max Lat is Less than Min Lonb then it throws an exception.
	 * @return
	 */
	private void createAndUpdateSites() throws RegionConstraintException {
		if (regionSelect == null)
			System.out.println("REGION SELECT NULL");
		if (regionSelect.getValue() == null)
			System.out.println("REGION SELECT VALUE NULL");
		String name = (String)(regionSelect.getValue());
		double gridSpacingD = ((Double)gridSpacing.getValue()).doubleValue();
		if (name.equalsIgnoreCase(SitesInGriddedRegionGuiBean.RECTANGULAR_NAME)) {
			double minLatitude= ((Double)minLat.getValue()).doubleValue();
			double maxLatitude= ((Double)maxLat.getValue()).doubleValue();
			double minLongitude=((Double)minLon.getValue()).doubleValue();
			double maxLongitude=((Double)maxLon.getValue()).doubleValue();
			//checkLatLonParamValues();
			  GriddedRegion eggr = 
				  new GriddedRegion(
						  new Location(minLatitude,minLongitude),
						  new Location(maxLatitude,maxLongitude),
						  gridSpacingD, new Location(0,0));
			gridRegion= new SitesInGriddedRegion(eggr);
		} else {
			for (Region region : presets) {
				if (name.equals(region.getName())) {
					GriddedRegion eggr = 
						new GriddedRegion(
								region.getBorder(), 
								BorderType.MERCATOR_LINEAR, 
								gridSpacingD, new Location(0,0));
					gridRegion = new SitesInGriddedRegion(eggr);
					break;
				}
			}
		}

	}

	/**
	 * 
	 * @return boolean specifying use of Wills Site Types from the CVM in calculation
	 */
	public boolean isUseSiteData() {
		return ((String)siteParam.getValue()).equals(USE_SITE_DATA);
	}

	/**
	 *
	 * @return the object for the SitesInGriddedRectangularRegion class
	 */
	public SitesInGriddedRegion getGriddedRegionSite() throws RuntimeException, RegionConstraintException {

		updateGriddedSiteParams();

		return gridRegion;
	}
	
	private boolean isSiteParam(ParameterAPI param) {
		String name = param.getName();
		
//		System.out.println("Is site param: " + name);
		
		if (name.equalsIgnoreCase(MAX_LATITUDE))
			return false;
		if (name.equalsIgnoreCase(MIN_LATITUDE))
			return false;
		if (name.equalsIgnoreCase(MAX_LONGITUDE))
			return false;
		if (name.equalsIgnoreCase(MIN_LONGITUDE))
			return false;
		if (name.equalsIgnoreCase(GRID_SPACING))
			return false;
		if (name.equalsIgnoreCase(SITE_PARAM_NAME))
			return false;
		if (name.equalsIgnoreCase(REGION_SELECT_NAME))
			return false;
		if (name.equalsIgnoreCase(NUM_SITES_NAME))
			return false;
//		System.out.println("YES!");
		return true;
	}

//	/**
//	 * Make the site params visible depending on the choice user has made to
//	 * set the site Params
//	 */
//	private void setSiteParamsVisible(){
//		Iterator<ParameterAPI> it = parameterList.getParametersIterator();
//		
//		siteParams.clear();
//		
//		//if the user decides to fill the values from the CVM
//		if(isUseSiteData()){
//			//editorPanel.getParameterEditor(this.VS30_DEFAULT).setVisible(true);
//			while(it.hasNext()){
//				//adds the default site Parameters becuase each site will have different site types and default value
//				//has to be given if site lies outside the bounds of CVM
//				ParameterAPI tempParam= (ParameterAPI)it.next();
//				if(isSiteParam(tempParam)){
//
//					//removing the existing site Params from the List and adding the
//					//new Site Param with site as being defaults
//					parameterList.removeParameter(tempParam.getName());
//
//					//creating the new Site Param, with "Default " added to its name, with existing site Params
//					ParameterAPI newParam = (ParameterAPI)tempParam.clone();
//					//If the parameterList already contains the site param with the "Default" name, then no need to change the existing name.
//					if(!newParam.getName().startsWith(this.DEFAULT))
//						newParam.setName(this.DEFAULT+newParam.getName());
//					//making the new parameter to uneditable same as the earlier site Param, so that
//					//only its value can be changed and not it properties
//					newParam.setNonEditable();
//					newParam.addParameterChangeFailListener(this);
//
//					//adding the parameter to the List if not already exists
//					if(!parameterList.containsParameter(newParam.getName()))
//						parameterList.addParameter(newParam);
//					siteParams.add(newParam);
//				}
//			}
//		}
//		//if the user decides to go in with filling all the sites with the same site parameter,
//		//then make that site parameter visible to te user
//		else {
//			while(it.hasNext()){
//				//removing the default Site Type Params if same site is to be applied to whole region
//				ParameterAPI tempParam= (ParameterAPI)it.next();
//				if(tempParam.getName().startsWith(this.DEFAULT))
//					parameterList.removeParameter(tempParam.getName());
//			}
//			//Adding the Site related params to the ParameterList
//			ListIterator it1 = siteParams.listIterator();
//			while(it1.hasNext()){
//				ParameterAPI tempParam = (ParameterAPI)it1.next();
//				if(!parameterList.containsParameter(tempParam.getName()))
//					parameterList.addParameter(tempParam);
//			}
//		}
//
//		//creating the ParameterList Editor with the updated ParameterList
//		editorPanel.removeAll();
//		addParameters();
//		editorPanel.validate();
//		editorPanel.repaint();
//		setTitle(GRIDDED_SITE_PARAMS);
//	}

}
