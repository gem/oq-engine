package org.opensha.sra.gui.portfolioeal.gui;

import java.awt.Color;
import java.awt.Container;
import java.awt.Dimension;
import java.awt.GridBagLayout;
import java.awt.event.ActionListener;
import java.awt.event.ItemListener;
import java.util.ArrayList;
import java.util.EventListener;

import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JComboBox;
import javax.swing.JComponent;
import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.JScrollBar;
import javax.swing.JScrollPane;
import javax.swing.JSplitPane;
import javax.swing.JTabbedPane;
import javax.swing.JTextArea;
import javax.swing.JTextField;

import org.opensha.sha.gui.beans.Site_GuiBean;
import org.opensha.sha.gui.controls.SetMinSourceSiteDistanceControlPanel;
import org.opensha.sha.gui.controls.SetSiteParamsFromWebServicesControlPanel;

/**
 * The view of the Portfolio EAL Calculator.  This class defines the interface to 
 * interact with the calculator.  It used beans to define the ERF, IMR, and Site
 * sections.
 * 
 * @author Jeremy Leakakos
 * @see    ERFPanel
 * @see    IMRPanel
 * @see    SitePanel
 */
public class PortfolioEALCalculatorView extends JFrame {

	private static final long serialVersionUID = -6117101906743764287L;
	private static PortfolioEALCalculatorView view;
	private final int WIDTH = 1100;
	private final int HEIGHT = 780;
	private ERFPanel erf;
	private IMRPanel imr;
	private SitePanel site;
	private JTextArea IO;
	private JScrollPane IOContainer;
	private JTabbedPane tabbedPane;
	private JPanel bottomPane;
	private SetMinSourceSiteDistanceControlPanel distanceControlPanel;
	private SetSiteParamsFromWebServicesControlPanel cvmControlPanel;
	private Site_GuiBean siteBean = new Site_GuiBean();
	private JTextField portfolioField;
	private JButton computeButton;
	private JButton cancelButton;
	private JButton clearButton;
	private boolean progressBarChecked = false;
	private ArrayList<JComponent> componentList = new ArrayList<JComponent>();
	public static final boolean CHECKED_YES = true;
	public static final boolean CHECKED_NO = false;

	
	/**
	 * The constructor for the view of the Portfolio EAL calculator
	 * 
	 * @param name 		 The name of the window
	 */
	private PortfolioEALCalculatorView(String name) {
		super(name);
		
		// Set up the erf and imr panes; access each ones's JPanel with a call to getPanel()
		erf = new ERFPanel();
		imr = new IMRPanel();
		site = new SitePanel(imr.getIMRBean().getSelectedIMR_Instance());
		
		
		// Set up the distance control panel for access to the value for calculations, but don't
		// set it visible yet
		distanceControlPanel = new SetMinSourceSiteDistanceControlPanel(getContentPane());
		
		// The I/O pane; a JTextArea with the I/O of the system
		setupIOPane();
		
		// The portfolio selection tab and erf/imr tab; a JTabbed pane with two tabs for the portfolio
		//												selection and erf/imr panels
		setupTabs();
		
		// The bottom pane; a JPanel with program controls
		setupBottomPane();
		
		// Set up the layout of the view
		setupLayout(getContentPane());
		setSize(WIDTH, HEIGHT);
	}

	public static PortfolioEALCalculatorView getView() {
		if ( view == null ) view = new PortfolioEALCalculatorView("Portfolio EAL Calculator");
		return view;
	}
	/**
	 * This method is used to setup the layout of the application<br>
	 * <Strong>Top Pane:</Strong> A JSplitPane, with test I/O on the left, and the options on the right.<br>
	 * <Strong>Bottom Pane:</Strong> The bottom pane contains the controls of the application
	 * @param contentPane The frames content pane; used to add components to the frame
	 */
	private void setupLayout(Container contentPane) {
		// The main splitPane; the pane that the the other components fit into
		JSplitPane mainSplitPane = new JSplitPane(JSplitPane.VERTICAL_SPLIT);
		mainSplitPane.setDividerLocation(9  * HEIGHT / 12 );
		
		// The top splitPane; the pane the I/O window and options windows fit into
		JSplitPane topPane = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT, this.IOContainer, this.tabbedPane);
		topPane.setDividerLocation(WIDTH - (2 * HEIGHT / 3));
		
		// Set the location inside mainSplitPane
		mainSplitPane.setTopComponent(topPane);
		mainSplitPane.setBottomComponent(bottomPane);
		
		// Add the panes to the frame
		contentPane.add(mainSplitPane);
	}
	
	/**
	 * This method sets up the tabs that will be put in the TabbedPane<br>
	 * <Strong>Tab 1:</Strong> "Portfolio and Vulnerability"; set the portfolio file to use<br>
	 * <Strong>Tab 2:</Strong> "Set Hazard Curve"; set the hazard options
	 * 
	 */
	private void setupTabs() {
		// The tabbed pane; a JTabbedPane with two tabs for the portfolio selection and for the erf/imr
		// panels
		tabbedPane = new JTabbedPane(JTabbedPane.TOP);

		// Create a panel that has a JTextField and a file chooser w/ button to chose a portfolio file
		JPanel portfolioSelectionTab = new JPanel();
		portfolioSelectionTab.setLayout(new GridBagLayout());
		portfolioField = new JTextField("Enter Portfolio URL");
		portfolioField.setPreferredSize(new Dimension(250, 22));
		portfolioField.setEditable( false );
		portfolioField.setBackground(Color.WHITE);
		JButton portfolioOpenButton = new JButton("Open Portfolio");
		componentList.add(portfolioOpenButton);
		portfolioSelectionTab.add(portfolioField);
		portfolioSelectionTab.add(portfolioOpenButton);
		
		// Create a JSplitPane for the erf and imr/site panels that will be shown
		JSplitPane optionsTab = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT);
		JSplitPane imrSitePane = new JSplitPane(JSplitPane.VERTICAL_SPLIT);
		
	
		// Add the imr and the site to the split pane
		imrSitePane.add(imr.getPanel());
		imrSitePane.add(site.getPanel());
		imrSitePane.setDividerLocation((5 * WIDTH / 11)/2 + 32);
		
		// Add the imr/site split pane and erf panel to the SplitPane in the second tab
		optionsTab.add(imrSitePane);
		optionsTab.add(erf.getPanel());
		optionsTab.setDividerLocation((7 * HEIGHT / 11)/2);
		
		// Add the tabs to the JTabbedPane
		tabbedPane.add(portfolioSelectionTab, "Portfolio and Vulnerability");
		tabbedPane.add(optionsTab, "Set Hazard Curve");
	}
	
	/**
	 * This method sets up the I/O pane that displays the output from the computations of the EAL
	 * 
	 */
	private void setupIOPane() {
		IO = new JTextArea();
		IOContainer = new JScrollPane();
		IOContainer.setHorizontalScrollBarPolicy(JScrollPane.HORIZONTAL_SCROLLBAR_AS_NEEDED);
		IOContainer.setVerticalScrollBarPolicy(JScrollPane.VERTICAL_SCROLLBAR_AS_NEEDED);
		IOContainer.setBorder( BorderFactory.createEtchedBorder() );
		IO.setEditable(false);
		IO.setLineWrap(true);
		IO.setBorder(BorderFactory.createLineBorder(Color.WHITE, 5));
		IOContainer.getViewport().add(IO);
	}
	
	/**
	 * This method sets up the bottom pane<br><br>
	 * <Strong>Control Panels:</Strong> The drop down box with optional settings<br>
	 * <Strong>Compute Button:</Strong> Hit this to start EAL computation<br>
	 * <Strong>Clear Button:</Strong> Hit this to clear the I/O pane<br>
	 * <Strong>Progress Checkbox:</Strong> Select this to show a progress bar while computing<br>
	 */
	private void setupBottomPane() {
		bottomPane = new JPanel();
		
		// The list that will be shown in the dropdown box
		String[] array = { "Control Panels", 
						   "Max site-source distance",
						   "Portfolios of interest",
						   "Set Site Params from Web Services" };
		// The dropdown box with optional settings
		JComboBox controlPanels = new JComboBox(array);
		// The compute EAL button
		computeButton = new JButton("Compute");
		// The cancel button to stop computations
		// It starts not visible, but becomes visible when the "Compute" button is hit
		cancelButton = new JButton("Cancel");
		cancelButton.setVisible(false);
		// The clear I/O screen button
		clearButton = new JButton("Clear Results");
		JCheckBox progressCheckBox = new JCheckBox("Show Progress Bar");
		
		// Add action/item listeners to the objects.
		// This occurs by all of them being added to a list of components.
		// This list will get iterated over and that is when the listeners get added
		// to the components.
		componentList.add(controlPanels);
		componentList.add(computeButton);
		componentList.add(cancelButton);
		componentList.add(clearButton);
		componentList.add(progressCheckBox);
		
		bottomPane.add(controlPanels);
		bottomPane.add(computeButton);
		bottomPane.add(cancelButton);
		bottomPane.add(clearButton);
		bottomPane.add(progressCheckBox);
	}
	
	/**
	 * @return The IMRPanel that holds the IMR_GuiBean
	 */
	public IMRPanel getIMR() {
		return imr;
	}
	
	/**
	 * @return The ERFPanel that holds the ERF_GuiBean
	 */
	public ERFPanel getERF() {
		return erf;
	}
	
	/**
	 * @return The SitePanel that holds the Site_GuiBean
	 */
	public SitePanel getSite() {
		return site;
	}
	
	/**
	 * @return The distance control panel for "Max site-source distance"
	 */
	public SetMinSourceSiteDistanceControlPanel getDistanceControlPanel() {
		return distanceControlPanel;	
	}
	
	/**
	 * @return A boolean telling whether the progress bar box has been checked or not
	 */
	public boolean getProgressBarChecked() {
		return progressBarChecked;
	}
	
	public void setProgressBarChecked( boolean checked ) {
		progressBarChecked = checked;
	}	
	
	/**
	 * This method sets the I/O pane's text.
	 * 
	 * @param text The text that will be displayed in the I/O pane.
	 */
	public void setIO(String text) {
		IO.setText(text);

			try {
				Thread.sleep(100);
			} 
			catch (InterruptedException e) {
				e.printStackTrace();
			}
			
		JScrollBar bar = IOContainer.getVerticalScrollBar();
		bar.setValue(bar.getMaximum());
		
	}

	/**
	 * This registers the UI components with appropriate listeners.
	 * 
	 * @param listener The instance of the ItemListener/ActionListener that the
	 * components in the UI will listen on.
	 */
	public void registerUI( EventListener listener  ) {
		for( JComponent component: componentList ) {
			if (component.getClass().toString().equals("class javax.swing.JButton")) {
				((JButton) component).addActionListener( (ActionListener) listener );
			}
			else if ( component.getClass().toString().equals("class javax.swing.JComboBox")) {
				((JComboBox) component).addActionListener( (ActionListener) listener );
			}
			else if ( component.getClass().toString().equals("class javax.swing.JCheckBox")) {
				((JCheckBox) component).addItemListener( (ItemListener) listener );
			}
		}
	}
	
	/**
	 * This is the method called when the JComboBox is changed.<br><br>
	 * 
	 * <b>"Max site-source distance"</b>  calls <code>initDistanceControl()</code><br>
	 * <b>"Set Site Params from Web Services"</b>  calls <code>initCVMControl()</code><br>
	 * <b>"Portfolios of interest"</b>
	 * 
	 * @param selection The selected option from the ComboBox
	 */
	public void comboBoxSelection(String selection) {
		if ( selection.equals("Max site-source distance") ) initDistanceControl();
		if ( selection.equals("Set Site Params from Web Services") ) initCVMControl();
		if ( selection.equals("Portfolios of interest") ) System.out.println("Portfolios of interest");
	}
	
	/**
	 * Set the buttons up when the "Compute" button is hit.<br>
	 * "Cancel": set visible<br>
	 * "Compute": set disabled<br>
	 * "Clear": set disabled<br>
	 */
	public void setButtonsOnCompute() {
		cancelButton.setVisible(true);
		computeButton.setEnabled(false);
		clearButton.setEnabled(false);
	}
	
	/**
	 * Set the buttons up when the "Cancel" button is hit.<br>
	 * "Cancel": set invisible<br>
	 * "Compute": set enabled<br>
	 * "Clear": set enabled<br>
	 */
	public void setButtonsOnCancel() {
		cancelButton.setVisible(false);
		computeButton.setEnabled(true);
		clearButton.setEnabled(true);
	}
	
	/**
	 * Set the portfolio field text area to the name of the portfolio file.
	 * @param fileName The name of the portfolio file
	 */
	public void setPortfolioField( String fileName ) {
		portfolioField.setText( fileName );
	}
	
	/**
	 * This creates a new window to set the Max source site distance
	 *
	 */
	private void initDistanceControl() {
		
		SetMinSourceSiteDistanceControlPanel distanceControlPanel = new SetMinSourceSiteDistanceControlPanel(this.getGlassPane());
		distanceControlPanel.pack();
		distanceControlPanel.setVisible(true);
	}
	
	/**
	 * This creates a new window to get IMR parameters from an online site.
	 * 
	 */
	private void initCVMControl() {
		cvmControlPanel = new SetSiteParamsFromWebServicesControlPanel(getContentPane(), imr.getIMRBean(), siteBean);
		cvmControlPanel.pack();
		cvmControlPanel.setVisible(true);
	}
}