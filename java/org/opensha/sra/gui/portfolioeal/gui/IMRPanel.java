package org.opensha.sra.gui.portfolioeal.gui;

import java.awt.Color;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;

import javax.swing.JPanel;

import org.opensha.sha.gui.beans.IMR_GuiBean;

/**
 * This class creates an instance of <code>IMR_GuiBean</code>, and implements 
 * it as a JPanel.
 * 
 * @author Jeremy Leakakos
 */
public class IMRPanel {

	private IMR_GuiBean imr;
	private JPanel imrGUIPanel = new JPanel();
	public BCR_ApplicationFacade bcr;

	/**
	 * The default constructor.  An IMR_GuiPanel is created to be used in the main view.  Since
	 * IMR_GuiPanel is NOT already a JPanel, UI formatting must be done in this class.
	 */
	@SuppressWarnings("static-access")
	public IMRPanel(){

		// Set up the BCR
		BCR_ApplicationFacade bcr = BCR_ApplicationFacade.getBCR();
		imr = new IMR_GuiBean( bcr );
		imr.getParameterEditor(imr.IMR_PARAM_NAME).getParameter().addParameterChangeListener(bcr);
		
		bcr.setImrGuiBean(imr);
		
		// Setup the layout to the actual panel used in the application
		GridBagLayout gridbag = new GridBagLayout();
		GridBagConstraints gridbagc = setGridBagConstraints();
	    imrGUIPanel.setLayout(gridbag);
	    imrGUIPanel.setBackground(Color.white);
		imrGUIPanel.add(imr, gridbagc);
		
		gridbagc.anchor = GridBagConstraints.PAGE_END;
		gridbagc.fill = GridBagConstraints.BOTH;
		imrGUIPanel.add(new JPanel(), gridbagc);
		imrGUIPanel.updateUI();
	}

	/** 
	 * @return The JPanel that holds the view for the IMR_GuiBean 
	 * */
	public JPanel getPanel() {
		return imrGUIPanel;
	}
	
	/**
	 * @return The IMR_GuiBean; this is the actual instance of the IMR_GuiBean
	 */
	public IMR_GuiBean getIMRBean() {
		return imr;
	}
	
	/**
	 * @return GridBagConstraints are used to set up a GridBagLayout
	 */
	private GridBagConstraints setGridBagConstraints() {
		Insets defaultInsets = new Insets( 4, 4, 2, 2 );
		return new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0, GridBagConstraints.NORTH, 
									  GridBagConstraints.BOTH, defaultInsets, 0, 0 );
	}	
}