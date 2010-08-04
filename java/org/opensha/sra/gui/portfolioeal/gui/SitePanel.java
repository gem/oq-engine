package org.opensha.sra.gui.portfolioeal.gui;

import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;

import javax.swing.JPanel;

import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;

/**
 * This class creates an instance of <code>SiteGuiBeanFacade</code>.
 * 
 * 
 * @author Jeremy Leakakos
 * @see SiteGuiBeanFacade
 *
 */
public class SitePanel {

	//private Site_GuiBean siteBean;
	private JPanel sitePanel = new JPanel();
	private SiteGuiBeanFacade siteBean;
	
	/**
	 * The constructor for the SitePanel.  It creates a SiteGuiBeanFacade, which is a facade of
	 * Site_GuiBean.  It sets the parameters in the site bean from the initial imr.
	 * 
	 * @param imr The intensity measure relationship used; gotten from the view
	 */
	public SitePanel(ScalarIntensityMeasureRelationshipAPI imr) {
		BCR_ApplicationFacade bcr = BCR_ApplicationFacade.getBCR();
		//siteBean = new Site_GuiBean();
		siteBean = new SiteGuiBeanFacade();
		siteBean.addSiteParams(imr.getSiteParamsIterator());
		siteBean.getParameterListEditor().getParameterEditor("Latitude").setEnabled(false);
		siteBean.getParameterListEditor().getParameterEditor("Longitude").setEnabled(false);
//		siteBean.getParameterListEditor().getParameterEditor("Vs30").setEnabled(false);
		GridBagLayout gridbag = new GridBagLayout();
		GridBagConstraints gridbagc = setGridBagConstraints();
		sitePanel.setLayout(gridbag);
		sitePanel.add(siteBean, gridbagc);
		bcr.setSiteGuiBean(siteBean);
	}
	
	/**
	 * 
	 * @return The underlying SiteGuiBeanFacade
	 */
	public SiteGuiBeanFacade getSiteBean() {
		return siteBean;
	}
	
	/**
	 * @return The JPanel created to show to the view.
	 */
	public JPanel getPanel() {
		return sitePanel;
	}
	
	/**
	 * @return GridBagConstraints are used to set up a GridBagLayout
	 */
	private GridBagConstraints setGridBagConstraints() {
		Insets defaultInsets = new Insets( 4, 4, 2, 2 );
		return new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0, GridBagConstraints.SOUTH, 
									  GridBagConstraints.BOTH, defaultInsets, 0, 0 );
	}
}
