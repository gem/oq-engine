package org.opensha.sra.gui.portfolioeal.gui;

import java.util.Iterator;

import org.opensha.commons.param.ParameterList;
import org.opensha.sha.gui.beans.Site_GuiBean;

/**
 * This class is a facade to Site_GuiBean.  It is used to allow access to only part of Site_GuiBean,
 * and change functionality where necessary.
 * 
 * @author Jeremy Leakakos
 *
 */
@SuppressWarnings("serial")
public class SiteGuiBeanFacade extends Site_GuiBean {

	private ParameterList parameterList = new ParameterList();
	
	/**
	 * The default constructor for SiteGuiBeanFacade.  It mirrors the functionality of Site_GuiBean 
	 * by calling super.
	 * 
	 * @see Site_GuiBean
	 */
	public SiteGuiBeanFacade() {
		super();		
	}
	
	/**
	 * This function removes the previous site parameters and adds as passed in iterator
	 * Longitude and Latitude are not changed, and they are forced to be non-editable.
	 * 
	 * Overrides <code>replaceSiteParams</code> in Site_GuiBean
	 *
	 * @param it The iterator for the selected IMR
	 */
	@SuppressWarnings("unchecked")
	public void replaceSiteParams(Iterator it) {

	  // first remove all the parameters ewxcept latitude and longitude
	  Iterator siteIt = parameterList.getParameterNamesIterator();
	  while(siteIt.hasNext()) { // remove all the parameters except latitdue and longitude
	    String paramName = (String)siteIt.next();
	    if(!paramName.equalsIgnoreCase(LATITUDE) &&
	       !paramName.equalsIgnoreCase(LONGITUDE)){
	      parameterList.removeParameter(paramName);
	    }
	  }
	  // Add the rest of the parameters to the list
	  addSiteParams(it);
	  
	  // Make the Latitute and Longitude parameters non-editable
	  getParameterListEditor().getParameterEditor("Latitude").setEnabled(false);
	  getParameterListEditor().getParameterEditor("Longitude").setEnabled(false);
	  getParameterListEditor().getParameterEditor("Vs30").setEnabled(false);
	 }
}
