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

import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.io.Serializable;
import java.net.URL;
import java.net.URLConnection;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.ListIterator;

import javax.swing.JOptionPane;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.region.SitesInGriddedRegion;
import org.opensha.commons.data.siteData.OrderedSiteDataProviderList;
import org.opensha.commons.data.siteData.SiteDataAPI;
import org.opensha.commons.data.siteData.SiteDataValueList;
import org.opensha.commons.data.siteData.gui.beans.OrderedSiteDataGUIBean;
import org.opensha.commons.exceptions.RegionConstraintException;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.Parameter;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterConstraintAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ParameterListEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeFailEvent;
import org.opensha.commons.param.event.ParameterChangeFailListener;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.sha.gui.infoTools.CalcProgressBar;
import org.opensha.sha.gui.servlets.GriddedRegionServlet;
import org.opensha.sha.util.SiteTranslator;


/**
 * <p>Title:SitesInGriddedRectangularRegionGuiBean </p>
 * <p>Description: This creates the Gridded Region parameter Editor with Site Params
 * for the selected Attenuation Relationship in the Application.
 * </p>
 * @author Nitin Gupta & Vipin Gupta
 * @date March 11, 2003
 * @version 1.0
 */



public class SitesInGriddedRectangularRegionGuiBean extends ParameterListEditor implements
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

	public final static String DEFAULT = "Default  ";

	// title for site paramter panel
	public final static String GRIDDED_SITE_PARAMS = "Set Gridded Region Params";

	//Site Params ArrayList
	ArrayList<ParameterAPI<?>> siteParams ;

	//Static String for setting the site Params
	public final static String SET_ALL_SITES = "Apply same site parameter(s) to all locations";
	public final static String USE_SITE_DATA = "Use site data providers";
	// these are kept for compatibility
	public final static String SET_SITE_USING_WILLS_SITE_TYPE = "Use the CGS Preliminary Site Conditions Map of CA (web service)";
	public final static String SET_SITES_USING_SCEC_CVM = "Use both CGS Map and SCEC Basin Depth (web services)";

	/**
	 * Longitude and Latitude parameters to be added to the site params list
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
			new Double(.01666),new Double(1.0),new String("Degrees"),new Double(.1));


	//StringParameter to set site related params
	private StringParameter siteParam;

	//SiteTranslator
	SiteTranslator siteTrans = new SiteTranslator();

	private OrderedSiteDataGUIBean dataGuiBean;
	private OrderedSiteDataProviderList defaultProviderList = null;

	//instance of class EvenlyGriddedRectangularGeographicRegion
	private SitesInGriddedRegion sites;

	/**
	 * constuctor which builds up mapping between IMRs and their related sites
	 */
	public SitesInGriddedRectangularRegionGuiBean() throws RegionConstraintException {
		this(null);
	}

	/**
	 * constuctor which builds up mapping between IMRs and their related sites
	 */
	public SitesInGriddedRectangularRegionGuiBean(OrderedSiteDataGUIBean dataGuiBean) throws RegionConstraintException {
		this.dataGuiBean = dataGuiBean;

		if (dataGuiBean == null) {
			defaultProviderList = OrderedSiteDataProviderList.createCompatibilityProviders(false);
		}

		//defaultVs30.setInfo(this.VS30_DEFAULT_INFO);
		//parameterList.addParameter(defaultVs30);
		minLat.addParameterChangeFailListener(this);
		minLon.addParameterChangeFailListener(this);
		maxLat.addParameterChangeFailListener(this);
		maxLon.addParameterChangeFailListener(this);
		gridSpacing.addParameterChangeFailListener(this);

		//creating the String Param for user to select how to get the site related params
		ArrayList siteOptions = new ArrayList();
		siteOptions.add(SET_ALL_SITES);
		if (dataGuiBean == null) {
			siteOptions.add(SET_SITE_USING_WILLS_SITE_TYPE);
			siteOptions.add(SET_SITES_USING_SCEC_CVM);
		} else {
			siteOptions.add(USE_SITE_DATA);
		}
		siteParam = new StringParameter(SITE_PARAM_NAME,siteOptions,(String)siteOptions.get(0));
		siteParam.addParameterChangeListener(this);

		// add the longitude and latitude paramters
		parameterList = new ParameterList();
		parameterList.addParameter(minLon);
		parameterList.addParameter(maxLon);
		parameterList.addParameter(minLat);
		parameterList.addParameter(maxLat);
		parameterList.addParameter(gridSpacing);
		parameterList.addParameter(siteParam);
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
	 * This function adds the site params to the existing list.
	 * Parameters are NOT cloned.
	 * If paramter with same name already exists, then it is not added
	 *
	 * @param it : Iterator over the site params in the IMR
	 */
	public void addSiteParams(Iterator it) {
		Parameter tempParam;
		ArrayList siteTempVector= new ArrayList();
		while(it.hasNext()) {
			tempParam = (Parameter)it.next();
			if(!parameterList.containsParameter(tempParam)) { // if this does not exist already
				parameterList.addParameter(tempParam);
				//adding the parameter to the vector,
				//ArrayList is used to pass the add the site parameters to the gridded region sites.
				siteTempVector.add(tempParam);
			}
		}
		//adding the Site Params to the ArrayList, so that we can add those later if we want to.
		siteParams = siteTempVector;
		sites.addSiteParams(siteTempVector.iterator());
		setSiteParamsVisible();
	}

	/**
	 * This function adds the site params to the existing list.
	 * Parameters are cloned.
	 * If paramter with same name already exists, then it is not added
	 *
	 * @param it : Iterator over the site params in the IMR
	 */
	public void addSiteParamsClone(Iterator it) {
		Parameter tempParam;
		ArrayList v= new ArrayList();
		while(it.hasNext()) {
			tempParam = (Parameter)it.next();
			if(!parameterList.containsParameter(tempParam)) { // if this does not exist already
				Parameter cloneParam = (Parameter)tempParam.clone();
				parameterList.addParameter(cloneParam);
				//adding the cloned parameter in the siteList.
				v.add(cloneParam);
			}
		}
		sites.addSiteParams(v.iterator());
		setSiteParamsVisible();
	}

	/**
	 * This function removes the previous site parameters and adds as passed in iterator
	 *
	 * @param it
	 */
	public void replaceSiteParams(Iterator it) {
		// first remove all the parameters except latitude and longitude
		Iterator siteIt = parameterList.getParameterNamesIterator();
		while(siteIt.hasNext()) { // remove all the parameters except latitude and longitude and gridSpacing
			String paramName = (String)siteIt.next();
			if(!paramName.equalsIgnoreCase(MIN_LATITUDE) &&
					!paramName.equalsIgnoreCase(MIN_LONGITUDE) &&
					!paramName.equalsIgnoreCase(MAX_LATITUDE) &&
					!paramName.equalsIgnoreCase(MAX_LONGITUDE) &&
					!paramName.equalsIgnoreCase(GRID_SPACING) &&
					!paramName.equalsIgnoreCase(SITE_PARAM_NAME))
				parameterList.removeParameter(paramName);
		}
		//removing the existing sites Params from the gridded Region sites
		sites.removeSiteParams();

		// now add all the new params
		addSiteParams(it);
	}



	/**
	 * gets the iterator of all the sites
	 *
	 * @return
	 */ // not currently used
//	public Iterator getAllSites() {
//		return gridRectRegion.getSitesIterator();
//	}


	/**
	 * get the clone of site object from the site params
	 *
	 * @return
	 */
	public Iterator<Site> getSitesClone() {
		Iterator<Location> lIt = sites.getRegion().getNodeList().iterator();
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

		ArrayList v= new ArrayList();
		createAndUpdateSites();
		//getting the site params for the first element of the siteVector
		//becuase all the sites will be having the same site Parameter
		Iterator it = siteParams.iterator();
		while(it.hasNext())
			v.add(((ParameterAPI)it.next()).clone());
		sites.addSiteParams(v.iterator());
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

	/**
	 * This function is called when value a parameter is changed
	 * @param e Description of the parameter
	 */
	public void parameterChange(ParameterChangeEvent e){
		ParameterAPI param = ( ParameterAPI ) e.getSource();

		if(param.getName().equals(SITE_PARAM_NAME))
			setSiteParamsVisible();
	}

	/**
	 * This method creates the gridded region with the min -max Lat and Lon
	 * It also checks if the Max Lat is less than Min Lat and
	 * Max Lat is Less than Min Lonb then it throws an exception.
	 * @return
	 */
	private void createAndUpdateSites() throws RegionConstraintException {

		double minLatitude= ((Double)minLat.getValue()).doubleValue();
		double maxLatitude= ((Double)maxLat.getValue()).doubleValue();
		double minLongitude=((Double)minLon.getValue()).doubleValue();
		double maxLongitude=((Double)maxLon.getValue()).doubleValue();
		//checkLatLonParamValues();
		GriddedRegion eggr = 
			new GriddedRegion(
					new Location(minLatitude,minLongitude),
					new Location(maxLatitude,maxLongitude),
					((Double)gridSpacing.getValue()).doubleValue(), 
					new Location(0,0));
		sites= new SitesInGriddedRegion(eggr);
	}


	/**
	 *
	 * @return the object for the SitesInGriddedRectangularRegion class
	 */
	public SitesInGriddedRegion getGriddedRegionSite() throws RuntimeException, RegionConstraintException {
		updateGriddedSiteParams();
		if(((String)siteParam.getValue()).equals(SET_ALL_SITES)) {
			//if the site params does not need to be set from the CVM
			sites.setSameSiteParams();
//			Site site = gridRectRegion.getSite(0);
//			ListIterator<ParameterAPI> it = site.getParametersIterator();
//			while (it.hasNext()) {
//				ParameterAPI param = it.next();
//				param.setValue(parameterList.getParameter(param.getName()).getValue());
//			}
		}

		//if the site Params needs to be set from the WILLS Site type and SCEC basin depth
		else{
			try{
				setSiteParamsFromCVM();
			}catch(Exception e){
				throw new RuntimeException("Server is down , please try again later");
			}
			ArrayList defaultSiteParams = new ArrayList();
			for(int i=0;i<siteParams.size();++i){
				ParameterAPI tempParam = (ParameterAPI)((ParameterAPI)siteParams.get(i)).clone();
				tempParam.setValue(parameterList.getParameter(this.DEFAULT+tempParam.getName()).getValue());
				defaultSiteParams.add(tempParam);
			}
			sites.setDefaultSiteParams(defaultSiteParams);
		}
		return sites;
	}


	/**
	 * Make the site params visible depending on the choice user has made to
	 * set the site Params
	 */
	private void setSiteParamsVisible(){

		//getting the Gridded Region site Object ParamList Iterator
		Iterator it = parameterList.getParametersIterator();

		//if the user decides to go in with filling all the sites with the same site parameter,
		//then make that site parameter visible to te user
		if(((String)siteParam.getValue()).equals(SET_ALL_SITES)){
			while(it.hasNext()){
				//removing the default Site Type Params if same site is to be applied to whole region
				ParameterAPI tempParam= (ParameterAPI)it.next();
				if(tempParam.getName().startsWith(this.DEFAULT))
					parameterList.removeParameter(tempParam.getName());
			}
			//Adding the Site related params to the ParameterList
			ListIterator it1 = siteParams.listIterator();
			while(it1.hasNext()){
				ParameterAPI tempParam = (ParameterAPI)it1.next();
				if(!parameterList.containsParameter(tempParam.getName()))
					parameterList.addParameter(tempParam);
			}
		}
		//if the user decides to fill the values from the CVM
		else {
			//editorPanel.getParameterEditor(this.VS30_DEFAULT).setVisible(true);
			while(it.hasNext()){
				//adds the default site Parameters becuase each site will have different site types and default value
				//has to be given if site lies outside the bounds of CVM
				ParameterAPI tempParam= (ParameterAPI)it.next();
				if(!tempParam.getName().equalsIgnoreCase(this.MAX_LATITUDE) &&
						!tempParam.getName().equalsIgnoreCase(this.MIN_LATITUDE) &&
						!tempParam.getName().equalsIgnoreCase(this.MAX_LONGITUDE) &&
						!tempParam.getName().equalsIgnoreCase(this.MIN_LONGITUDE) &&
						!tempParam.getName().equalsIgnoreCase(this.GRID_SPACING) &&
						!tempParam.getName().equalsIgnoreCase(this.SITE_PARAM_NAME)){

					//removing the existing site Params from the List and adding the
					//new Site Param with site as being defaults
					parameterList.removeParameter(tempParam.getName());
					if(!tempParam.getName().startsWith(this.DEFAULT))
						//getting the Site Param Value corresponding to the Will Site Class "DE" for the seleted IMR  from the SiteTranslator
						siteTrans.setParameterValue(tempParam,siteTrans.WILLS_DE,Double.NaN);

					//creating the new Site Param, with "Default " added to its name, with existing site Params
					ParameterAPI newParam = (ParameterAPI)tempParam.clone();
					//If the parameterList already contains the site param with the "Default" name, then no need to change the existing name.
					if(!newParam.getName().startsWith(this.DEFAULT))
						newParam.setName(this.DEFAULT+newParam.getName());
					//making the new parameter to uneditable same as the earlier site Param, so that
					//only its value can be changed and not it properties
					newParam.setNonEditable();
					newParam.addParameterChangeFailListener(this);

					//adding the parameter to the List if not already exists
					if(!parameterList.containsParameter(newParam.getName()))
						parameterList.addParameter(newParam);
				}
			}
		}
		
		if (dataGuiBean != null) {
			OrderedSiteDataProviderList list = dataGuiBean.getProviderList();
//			list.enableOnlyFirstForEachType();
//			System.out.println(list);
			dataGuiBean.refreshAll();
//			System.out.println(list);
		}

		//creating the ParameterList Editor with the updated ParameterList
		editorPanel.removeAll();
		addParameters();
		editorPanel.validate();
		editorPanel.repaint();
		setTitle(GRIDDED_SITE_PARAMS);
		this.refreshParamEditor();
	}

	/**
	 * set the Site Params from the CVM
	 */
	private void setSiteParamsFromCVM(){

		// give latitude and longitude to the servlet
		Double lonMin = (Double)parameterList.getParameter(MIN_LONGITUDE).getValue();
		Double lonMax = (Double)parameterList.getParameter(MAX_LONGITUDE).getValue();
		Double latMin = (Double)parameterList.getParameter(MIN_LATITUDE).getValue();
		Double latMax = (Double)parameterList.getParameter(MAX_LATITUDE).getValue();
		Double gridSpacing = (Double)parameterList.getParameter(GRID_SPACING).getValue();

		// if values in longitude and latitude are invalid
		if(lonMin == null || latMin == null) {
			JOptionPane.showMessageDialog(this,"Check the values in longitude and latitude");
			return ;
		}
		
		OrderedSiteDataProviderList dataProviders = null;
		if (dataGuiBean != null) {
			dataProviders = dataGuiBean.getProviderList();
		} else {
			dataProviders = defaultProviderList;
		}

		CalcProgressBar calcProgress = new CalcProgressBar("Setting Gridded Region sites","Getting the site paramters from the CVM");
		if(((String)siteParam.getValue()).equals(SET_SITE_USING_WILLS_SITE_TYPE)) {
			//if we are setting each site using the Wills site type. basin depth is taken as default.
			dataProviders = (OrderedSiteDataProviderList)dataProviders.clone();
			for (int i=0; i<dataProviders.size(); i++) {
				if (dataProviders.getProvider(i).getDataType().equals(SiteDataAPI.TYPE_DEPTH_TO_2_5))
					dataProviders.setEnabled(i, false);
			}
		}
		try {
			sites.setSiteParamsForRegion(dataProviders);
		} catch (IOException e) {
			throw new RuntimeException(e);
		}
		calcProgress.dispose();
	}

	/**
	 * This function makes sure that Lat and Lon params are within the
	 * range and min values are not greater than max values, ie. checks
	 * if the user has filled in the correct values.
	 */
	/*private void checkLatLonParamValues() throws ParameterException{

    double minLatitude= ((Double)minLat.getValue()).doubleValue();
    double maxLatitude= ((Double)maxLat.getValue()).doubleValue();
    double minLongitude=((Double)minLon.getValue()).doubleValue();
    double maxLongitude=((Double)maxLon.getValue()).doubleValue();

    if(maxLatitude <= minLatitude){
      throw new ParameterException("Max Lat. must be greater than Min Lat");
    }

    if(maxLongitude <= minLongitude){
      throw new ParameterException("Max Lon. must be greater than Min Lon");
    }

  }*/



	/**
	 * This function creates a Region object on the server and save it there. It then
	 * returns the path to the file where that gridded object is stored.
	 * @return
	 */
	public String openConnectionToServer() throws RegionConstraintException, RuntimeException{

		//checks the values of the Lat and Lon to see if user has filled in the values correctly.
		//checkLatLonParamValues();

		try{
			createAndUpdateSites();
			String regionSitesParamVal = (String)parameterList.getParameter(SitesInGriddedRectangularRegionGuiBean.SITE_PARAM_NAME).getValue();
			ArrayList<SiteDataValueList<?>> valsList;
			if (regionSitesParamVal.equals(USE_SITE_DATA)) {
				OrderedSiteDataProviderList dataProviders;
				if (dataGuiBean != null) {
					dataProviders = dataGuiBean.getProviderList();
				} else {
					dataProviders = defaultProviderList;
				}
				sites.setSiteParamsForRegion(dataProviders);
				valsList = sites.getSiteDataValueLists();
			} else {
				valsList = new ArrayList<SiteDataValueList<?>>();
			}
			

			if(D) System.out.println("starting to make connection with servlet");
			URL griddedRegionCalcServlet = new URL(GriddedRegionServlet.SERVLET_URL);


			URLConnection servletConnection = griddedRegionCalcServlet.openConnection();
			if(D) System.out.println("connection established");

			// inform the connection that we will send output and accept input
			servletConnection.setDoInput(true);
			servletConnection.setDoOutput(true);

			// Don't use a cached version of URL connection.
			servletConnection.setUseCaches (false);
			servletConnection.setDefaultUseCaches (false);
			// Specify the content type that we will send binary data
			servletConnection.setRequestProperty ("Content-Type","application/octet-stream");

			ObjectOutputStream outputToServlet = new
			ObjectOutputStream(servletConnection.getOutputStream());


			//sends the parameterList in the SitesInGriddedRectangularRegionGuiBean to the server
			outputToServlet.writeObject(parameterList);
			//sends the arraylist of site Param List to the server
			outputToServlet.writeObject(siteParams);
			
			System.out.println("Sending values list: " + valsList.size());
			outputToServlet.writeObject(valsList);

			outputToServlet.flush();
			outputToServlet.close();

			// Receive the "actual webaddress of all the gmt related files"
			// from the servlet after it has received all the data
			ObjectInputStream inputToServlet = new
			ObjectInputStream(servletConnection.getInputStream());

			//absolute path of the file where we have stored the file for the region object
			Object regionFilePath =(Object)inputToServlet.readObject();
			//if(D) System.out.println("Receiving the Input from the Servlet:"+webaddr);
			inputToServlet.close();

			if(regionFilePath instanceof RegionConstraintException)
				throw (RegionConstraintException)regionFilePath;
			else if(regionFilePath instanceof String)
				return (String)regionFilePath;
			else
				throw (Exception)regionFilePath;
		}
		catch(RegionConstraintException e){
			throw new RegionConstraintException(e.getMessage());
		}
		catch (Exception e) {
			e.printStackTrace();
			throw new RuntimeException("Server is down , please try again later");
		}

	}




}
