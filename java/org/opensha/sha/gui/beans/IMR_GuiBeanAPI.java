/**
 * 
 */
package org.opensha.sha.gui.beans;



/**
 * @author nitingupta
 *
 */
public interface  IMR_GuiBeanAPI {

	/**
	 * Updates the application using the IMR_GuiBean to update its Supported IM and show the correct 
	 * IM in the IMT Gui.
	 */
	public void updateIM();
	
    /**
     * Update the Site Params for the selected AttenutionRelationship, so the similar can be shown by the application and shown by 
     * siteGuiBean.
     */	
    public void updateSiteParams();
}
