package org.opensha.sra.gui.portfolioeal.gui;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.sha.gui.beans.IMR_GuiBean;
import org.opensha.sha.gui.beans.Site_GuiBean;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sra.gui.BCR_Application;

/**
 *	This class is a facade of the BCR_Application which limits the view of 
 *	functionality taken from it.
 * 
 * 	@author Jeremy Leakakos
 */


@SuppressWarnings("serial")
public class BCR_ApplicationFacade extends BCR_Application {
	
	private IMR_GuiBean imrGuiBean;
	private Site_GuiBean siteGuiBean;
	private static BCR_ApplicationFacade BCR = new BCR_ApplicationFacade();

	
	/**
	 * Public constructor for BCR_Application subclass.
	 * It is a singleton, as there should only be at most one type of this class.
	 */
	private BCR_ApplicationFacade() {
		super();
	}
	
	/**
	 * The singleton method that returns a single instance of a BCR_ApplicationFacade
	 * 
	 * @return The only instance of the BCR_ApplicaionFacade
	 */
	public static BCR_ApplicationFacade getBCR() {
		if (BCR == null) {
			BCR = new BCR_ApplicationFacade();
		}
		return BCR;
	}
	/**
	 * This method does nothing, but still must exist.  It overwrites the updateSiteParams in
	 * <code>BCR_Application</code>.  There are no site params in the Portfolio EAL program, but this 
	 * method is still called because of coupling in other classes.
	 */
	public void updateSiteParams() {
		ScalarIntensityMeasureRelationshipAPI imr = imrGuiBean.getSelectedIMR_Instance();
		siteGuiBean.replaceSiteParams(imr.getSiteParamsIterator());
		siteGuiBean.validate();
	    siteGuiBean.repaint();
	}
	
	/**
	 * Update the IMR_GuiBean
	 * 
	 * @param bean the current IMR_GuiBean
	 */
	public void setImrGuiBean(IMR_GuiBean bean) {
		imrGuiBean = bean;
	}
	
	/**
	 * Update the Site_GuiBean
	 * 
	 * @param bean the current Site_GuiBean
	 */
	public void setSiteGuiBean( Site_GuiBean bean ) {
		siteGuiBean = bean;
	}
	/**
	 *  Any time a control paramater or independent paramater is changed
	 *  by the user in a GUI this function is called, and a paramater change
	 *  event is passed in. This function then determines what to do with the
	 *  information ie. show some paramaters, set some as invisible,
	 *  basically control the paramater lists.
	 *
	 * @param  event The event fired when a parameter is changed.
	 */
	@SuppressWarnings("static-access")
	public void parameterChange( ParameterChangeEvent event ) {
	  
	  String name = event.getParameterName();

	  if ( name.equalsIgnoreCase(imrGuiBean.IMR_PARAM_NAME)) {
		  ScalarIntensityMeasureRelationshipAPI imr = imrGuiBean.getSelectedIMR_Instance();
	      siteGuiBean.replaceSiteParams(imr.getSiteParamsIterator());
	      siteGuiBean.validate();
	      siteGuiBean.repaint();
	  }
	}
}
