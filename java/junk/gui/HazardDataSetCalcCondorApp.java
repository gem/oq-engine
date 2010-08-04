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

package junk.gui;

import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.MouseEvent;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.lang.reflect.InvocationTargetException;
import java.net.URL;
import java.net.URLConnection;
import java.util.ArrayList;
import java.util.ListIterator;

import javax.swing.ImageIcon;
import javax.swing.JApplet;
import javax.swing.JButton;
import javax.swing.JComboBox;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JSplitPane;
import javax.swing.JTabbedPane;
import javax.swing.JTextField;
import javax.swing.Timer;
import javax.swing.UIManager;
import javax.swing.border.Border;
import javax.swing.border.EtchedBorder;

import org.apache.commons.lang.SystemUtils;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.region.SitesInGriddedRegion;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.exceptions.RegionConstraintException;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.calc.HazardCurveCalculator;
import org.opensha.sha.gui.beans.ERF_GuiBean;
import org.opensha.sha.gui.beans.IMR_GuiBean;
import org.opensha.sha.gui.beans.IMR_GuiBeanAPI;
import org.opensha.sha.gui.beans.IMT_GuiBean;
import org.opensha.sha.gui.beans.SitesInGriddedRectangularRegionGuiBean;
import org.opensha.sha.gui.controls.CurveDisplayAppAPI;
import org.opensha.sha.gui.controls.RegionsOfInterestControlPanel;
import org.opensha.sha.gui.controls.SetMinSourceSiteDistanceControlPanel;
import org.opensha.sha.gui.controls.X_ValuesInCurveControlPanel;
import org.opensha.sha.gui.infoTools.ApplicationVersionInfoWindow;
import org.opensha.sha.gui.infoTools.CalcProgressBar;
import org.opensha.sha.gui.infoTools.ExceptionWindow;
import org.opensha.sha.gui.infoTools.IMT_Info;
import org.opensha.sha.gui.infoTools.UserAuthorizationCheckWindow;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;

/**
 * <p>Title: HazardDataSetCalcCondorApp</p>
 * <p>Description: This application allows the user to calculate the hazard map
 * dataset using the condor pool at USC. Once the dataset is computed an email
 * will be sent to the user that computation have been completed.
 * This application is smart enough to check if the calculation that you are trying
 * to do have already been done. If the computation have already been done, rather
 * then doing the computation again it will return dataset id of already computed
 * dataset.</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author: Ned Field & Nitin Gupta & Vipin Gupta
 * @created : March 15,2004
 * @version 1.0
 */

public class HazardDataSetCalcCondorApp extends JApplet
implements ParameterChangeListener, IMR_GuiBeanAPI, Runnable, CurveDisplayAppAPI {


	/**
	 * Name of the class
	 */
	protected final static String C = "HazardMapApplet";
	// for debug purpose
	protected final static boolean D = false;
	public static String SERVLET_URL  = "http://gravity.usc.edu/OpenSHA/servlet/HazardMapCalcServlet";
	public static String DATASET_CHECK_SERVLET_URL = "http://gravity.usc.edu/OpenSHA/servlet/DatasetIdAndMetadataCheckServlet";


	protected final static String version = "0.0.8";

	protected final static String versionURL = "http://www.opensha.org/applications/hazMapApps/HazMapApps_Version.txt";
	protected final static String appURL = "http://gravity.usc.edu/OpenSHA/HazardDataSetCalcCondorApp.jar";
	protected final static String versionUpdateInfoURL = "http://www.opensha.org/applications/hazMapApps/versionUpdate.html";


	//variables that determine the width and height of the frame
	private static final int W=600;
	private static final int H=820;

	// default insets
	private Insets defaultInsets = new Insets( 4, 4, 4, 4 );

	//store the site values for each site in the griddded region
	private SitesInGriddedRegion griddedRegionSites;

	//gets the instance of the selected AttenuationRelationship
	private AttenuationRelationship attenRel;
	private boolean useCustomX_Values = false;


	/**
	 *  The object class names for all the supported Eqk Rup Forecasts
	 */
	public final static String RMI_FRANKEL_ADJ_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.remoteERF_Clients.Frankel96_AdjustableEqkRupForecastClient";
	public final static String RMI_STEP_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.remoteERF_Clients.STEP_EqkRupForecastClient";
	public final static String RMI_STEP_ALASKAN_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.remoteERF_Clients.STEP_AlaskanPipeForecastClient";
	public final static String RMI_FRANKEL02_ADJ_FORECAST_CLASS_NAME="org.opensha.sha.earthquake.rupForecastImpl.remoteERF_Clients.Frankel02_AdjustableEqkRupForecastClient";
	public final static String RMI_WG02_ADJ_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.remoteERF_Clients.WG02_EqkRupForecastClient";
	public final static String RMI_FLOATING_POISSON_FAULT_ERF_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.remoteERF_Clients.FloatingPoissonFaultERF_Client";
	public final static String RMI_WGCEP_UCERF1_ERF_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.remoteERF_Clients.WGCEP_UCERF1_EqkRupForecastClient";

	// Strings for control pick list
	private final static String CONTROL_PANELS = "Control Panels";
	private final static String REGIONS_OF_INTEREST_CONTROL = "Regions of Interest";
	private final static String X_VALUES_CONTROL = "Set X values for Hazard Curve Calc.";
	private final static String DISTANCE_CONTROL = "Max Source-Site Distance";


	// objects for control panels
	private RegionsOfInterestControlPanel regionsOfInterest;
	private X_ValuesInCurveControlPanel xValuesPanel;
	private SetMinSourceSiteDistanceControlPanel distanceControlPanel;
	//private HazardMapSubmissionMethods mapSubmissionMethods;


	// instances of the GUI Beans which will be shown in this applet
	private ERF_GuiBean erfGuiBean;
	private IMR_GuiBean imrGuiBean;
	private IMT_GuiBean imtGuiBean;
	private SitesInGriddedRectangularRegionGuiBean sitesGuiBean;

	private boolean isStandalone = false;
	private JPanel mainPanel = new JPanel();
	private Border border1;
	private JSplitPane mainSplitPane = new JSplitPane();
	private JPanel buttonPanel = new JPanel();
	private JPanel eqkRupPanel = new JPanel();
	private JSplitPane imr_IMTSplit = new JSplitPane();
	private JTabbedPane parameterTabbedPanel = new JTabbedPane();
	private JPanel imrPanel = new JPanel();
	private JPanel imtPanel = new JPanel();
	private BorderLayout borderLayout2 = new BorderLayout();
	private GridBagLayout gridBagLayout = new GridBagLayout();
	private JPanel gridRegionSitePanel = new JPanel();


	private JPanel imrSelectionPanel = new JPanel();

	BorderLayout borderLayout1 = new BorderLayout();

	//holds the ArbitrarilyDiscretizedFunc
	private ArbitrarilyDiscretizedFunc function;
	//instance to get the default IMT X values for the hazard Curve
	private IMT_Info imtInfo = new IMT_Info();


	//images for the OpenSHA
	private final static String POWERED_BY_IMAGE = "logos/PoweredByOpenSHA_Agua.jpg";

	//static string for the OPENSHA website
	private final static String OPENSHA_WEBSITE="http://www.OpenSHA.org";


	//keeps track of the step in the application to update the user of the progress.
	private int step;
	//timer to show thw progress bar
	Timer timer;
	//instance of Progress Bar
	private CalcProgressBar calcProgress;
	private JPanel dataPanel = new JPanel();
	private JPanel imgPanel = new JPanel();
	private JLabel imgLabel = new JLabel(new ImageIcon(FileUtils.loadImage(this.POWERED_BY_IMAGE)));
	private JButton addButton = new JButton();
	private JComboBox controlComboBox = new JComboBox();
	private GridBagLayout gridBagLayout7 = new GridBagLayout();
	private BorderLayout borderLayout3 = new BorderLayout();
	private JTextField datasetIdText = new JTextField();
	private JLabel emailLabel = new JLabel();
	private JLabel datasetLabel = new JLabel();
	private JTextField emailText = new JTextField();


	//Maximum source site Distance
	private Double maxDistance;
	private GridBagLayout gridBagLayout4 = new GridBagLayout();

	//Construct the applet
	public HazardDataSetCalcCondorApp() {}
	//Initialize the applet
	public void init() {

		//Checking for the Authentic user
		//This pops up a user login window and only authentic user will be able
		//to use HazardMap Calculation application.
		UserAuthorizationCheckWindow loginWin = new UserAuthorizationCheckWindow();
		while (!loginWin.isLoginSuccess()) {
			if (!loginWin.isVisible())
				loginWin.setVisible(true);
		}
		loginWin.dispose();
		try {
			// initialize the control pick list
			initControlList();
			jbInit();
		}
		catch(Exception e) {
			ExceptionWindow bugWindow = new ExceptionWindow(this,e,"Exception occured while initializing the application "+
			"Parameters values have not been set yet.");
			bugWindow.setVisible(true);
			bugWindow.pack();
		}
		try{
			initIMRGuiBean();
		}catch(RuntimeException e){
			JOptionPane.showMessageDialog(this,"Invalid parameter value",e.getMessage(),JOptionPane.ERROR_MESSAGE);
			return;
		}
		try {
			this.initGriddedRegionGuiBean();
		}
		catch (RegionConstraintException ex) {
			ExceptionWindow bugWindow = new ExceptionWindow(this,ex,
					"Exception occured while initializing the  region parameters in Hazard Dataset Calc App"+
			" Parameters values have not been set yet.");
			bugWindow.setVisible(true);
			bugWindow.pack();

		}
		this.initIMTGuiBean();
		try{
			this.initERFSelector_GuiBean();
		}catch(RuntimeException e){
			JOptionPane.showMessageDialog(this,"Could not connect with ERF's","Error occur in ERF",
					JOptionPane.OK_OPTION);
			return;
		}

	}


	//Component initialization
	private void jbInit() throws Exception {
		border1 = new EtchedBorder(EtchedBorder.RAISED,new Color(248, 254, 255),new Color(121, 124, 136));
		this.setSize(new Dimension(564, 834));
		this.getContentPane().setLayout(borderLayout1);
		mainPanel.setBorder(border1);
		mainPanel.setLayout(gridBagLayout);
		mainSplitPane.setOrientation(JSplitPane.VERTICAL_SPLIT);
		buttonPanel.setLayout(borderLayout3);
		eqkRupPanel.setLayout(gridBagLayout);
		imr_IMTSplit.setOrientation(JSplitPane.VERTICAL_SPLIT);
		imrPanel.setLayout(borderLayout2);
		imtPanel.setLayout(gridBagLayout);
		buttonPanel.setMinimumSize(new Dimension(391, 50));
		gridRegionSitePanel.setLayout(gridBagLayout);
		imrSelectionPanel.setLayout(gridBagLayout);
		//controlComboBox.setBackground(Color.white);
		dataPanel.setLayout(gridBagLayout4);
		imgPanel.setLayout(gridBagLayout7);
		addButton.setBorder(null);
		addButton.setText("Start Calc");
		addButton.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				addButton_actionPerformed(e);
			}
		});
		controlComboBox.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				controlComboBox_actionPerformed(e);
			}
		});
		emailLabel.setText("Email:");
		datasetLabel.setText("Dataset Id:");
		emailText.setText("");
		dataPanel.setMinimumSize(new Dimension(548, 150));
		dataPanel.setPreferredSize(new Dimension(549, 150));
		this.getContentPane().add(mainPanel, BorderLayout.CENTER);
		mainPanel.add(mainSplitPane,  new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(1, 1, 2, 3), 0, 431));
		mainSplitPane.add(buttonPanel, JSplitPane.BOTTOM);
		buttonPanel.add(dataPanel, BorderLayout.CENTER);
		dataPanel.add(datasetIdText,  new GridBagConstraints(1, 1, 1, 1, 1.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(34, 19, 81, 0), 162, 7));
		dataPanel.add(datasetLabel,  new GridBagConstraints(0, 1, 1, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(34, 7, 81, 0), 28, 10));
		dataPanel.add(emailText,  new GridBagConstraints(1, 0, 1, 1, 1.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(43, 19, 0, 0), 162, 7));
		dataPanel.add(controlComboBox,  new GridBagConstraints(2, 0, 1, 1, 1.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL, new Insets(43, 48, 0, 24), 35, 2));
		dataPanel.add(emailLabel,  new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(43, 7, 0, 15), 43, 12));
		dataPanel.add(addButton,  new GridBagConstraints(2, 1, 1, 1, 0.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(27, 51, 81, 24), 79, 12));
		buttonPanel.add(imgPanel, BorderLayout.SOUTH);
		imgPanel.add(imgLabel,  new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(15, 235, 3, 246), 57, 28));
		mainSplitPane.add(parameterTabbedPanel, JSplitPane.TOP);
		imr_IMTSplit.add(imtPanel, JSplitPane.BOTTOM);
		imr_IMTSplit.add(imrSelectionPanel, JSplitPane.TOP);
		imrPanel.add(imr_IMTSplit, BorderLayout.CENTER);
		parameterTabbedPanel.addTab("Intensity-Measure Relationship", imrPanel);
		parameterTabbedPanel.addTab("Region & Site Params", gridRegionSitePanel);
		parameterTabbedPanel.addTab( "Earthquake Rupture Forecast", eqkRupPanel );
		mainSplitPane.setDividerLocation(550);
		imr_IMTSplit.setDividerLocation(300);
		imgLabel.addMouseListener(new java.awt.event.MouseAdapter() {
			public void mouseClicked(MouseEvent e) {
				imgLabel_mouseClicked(e);
			}
		});

	}


	/**
	 * Checks if the current version of the application is latest else direct the
	 * user to the latest version on the website.
	 */
	protected void checkAppVersion(){
		ArrayList hazCurveVersion = null;
		try {
			hazCurveVersion = FileUtils.loadFile(new URL(versionURL));
		}
		catch (Exception ex1) {
			return;
		}
		String appVersionOnWebsite = (String)hazCurveVersion.get(0);
		if(!appVersionOnWebsite.trim().equals(version.trim())){
			try{
				ApplicationVersionInfoWindow messageWindow =
					new ApplicationVersionInfoWindow(appURL,
							this.versionUpdateInfoURL,
							"App Version Update", this);
				Dimension dim = Toolkit.getDefaultToolkit().getScreenSize();
				messageWindow.setLocation( (dim.width -
						messageWindow.getSize().width) / 2,
						(dim.height -
								messageWindow.getSize().height) / 2);
				messageWindow.setVisible(true);
			}catch(Exception e){
				e.printStackTrace();
			}
		}

		return;

	}


	/**
	 * Returns the Application version
	 * @return String
	 */
	public static String getAppVersion(){
		return version;
	}



	//Main method
	public static void main(String[] args) {
		HazardDataSetCalcCondorApp application = new HazardDataSetCalcCondorApp();
		application.isStandalone = true;
		JFrame frame = new JFrame();
		//EXIT_ON_CLOSE == 3
		frame.setDefaultCloseOperation(3);
		frame.setTitle("HazardMapDataCalc App ("+getAppVersion()+" )");
		frame.getContentPane().add(application, BorderLayout.CENTER);
		application.init();
		frame.setSize(W,H);
		Dimension d = Toolkit.getDefaultToolkit().getScreenSize();
		frame.setLocation((d.width - frame.getSize().width) / 2, (d.height - frame.getSize().height) / 2);
		frame.setVisible(true);
	}

	//static initializer for setting look & feel
	static {
		String osName = System.getProperty("os.name");
		try {
			UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
		}
		catch(Exception e) {
		}
	}




	/**
	 * Initialise the Gridded Region sites gui bean
	 *
	 */
	private void initGriddedRegionGuiBean() throws RegionConstraintException {
		// get the selected IMR
		attenRel = (AttenuationRelationship)imrGuiBean.getSelectedIMR_Instance();
		// create the Site Gui Bean object
		sitesGuiBean = new SitesInGriddedRectangularRegionGuiBean();
		sitesGuiBean.addSiteParams(attenRel.getSiteParamsIterator());
		// show the sitebean in JPanel
		gridRegionSitePanel.add(this.sitesGuiBean, new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0,
				GridBagConstraints.CENTER, GridBagConstraints.BOTH, defaultInsets, 0, 0 ));
	}

	/**
	 * Initialise the IMT gui Bean
	 */
	private void initIMTGuiBean(){
		// get the selected IMR
		attenRel = (AttenuationRelationship)imrGuiBean.getSelectedIMR_Instance();
		/**
		 * Initialize the IMT Gui Bean
		 */

		// create the IMT Gui Bean object
		imtGuiBean = new IMT_GuiBean(attenRel,attenRel.getSupportedIntensityMeasuresIterator());

		imtPanel.add(imtGuiBean, new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0,
				GridBagConstraints.CENTER, GridBagConstraints.BOTH, defaultInsets, 0, 0 ));
	}

	/**
	 * Initialize the IMR Gui Bean
	 */
	private void initIMRGuiBean() {

		imrGuiBean = new IMR_GuiBean(this);
		imrGuiBean.getParameterEditor(imrGuiBean.IMR_PARAM_NAME).getParameter().addParameterChangeListener(this);

		// show this IMRgui bean the Panel
		imrSelectionPanel.add(this.imrGuiBean,new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0,
				GridBagConstraints.CENTER, GridBagConstraints.BOTH, defaultInsets, 0, 0 ));

	}

	/**
	 * Initialize the ERF Gui Bean
	 */
	private void initERFSelector_GuiBean() {
		// create the ERF Gui Bean object
		ArrayList erf_Classes = new ArrayList();

		erf_Classes.add(RMI_FRANKEL02_ADJ_FORECAST_CLASS_NAME);
		erf_Classes.add(RMI_FLOATING_POISSON_FAULT_ERF_CLASS_NAME);
		erf_Classes.add(RMI_FRANKEL_ADJ_FORECAST_CLASS_NAME);
		erf_Classes.add(RMI_STEP_FORECAST_CLASS_NAME);
		erf_Classes.add(RMI_STEP_ALASKAN_FORECAST_CLASS_NAME);
		erf_Classes.add(RMI_WG02_ADJ_FORECAST_CLASS_NAME);
		erf_Classes.add(RMI_WGCEP_UCERF1_ERF_CLASS_NAME);
		try{
			erfGuiBean = new ERF_GuiBean(erf_Classes);
		}catch(InvocationTargetException e){
			throw new RuntimeException("Connection to ERF servlets failed");
		}
		eqkRupPanel.add(erfGuiBean, new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0,
				GridBagConstraints.CENTER,GridBagConstraints.BOTH, defaultInsets, 0, 0 ));
	}






	/**
	 *  Any time a control paramater or independent paramater is changed
	 *  by the user in a GUI this function is called, and a paramater change
	 *  event is passed in. This function then determines what to do with the
	 *  information ie. show some paramaters, set some as invisible,
	 *  basically control the paramater lists.
	 *
	 * @param  event
	 */
	public void parameterChange(ParameterChangeEvent event){

		String S = C + ": parameterChange(): ";

		String name1 = event.getParameterName();

		// if IMR selection changed, update the site parameter list and supported IMT
		if ( name1.equalsIgnoreCase(imrGuiBean.IMR_PARAM_NAME)) {
			attenRel = (AttenuationRelationship)imrGuiBean.getSelectedIMR_Instance();
			imtGuiBean.setIM(attenRel,attenRel.getSupportedIntensityMeasuresIterator());
			imtGuiBean.validate();
			imtGuiBean.repaint();
			sitesGuiBean.replaceSiteParams(attenRel.getSiteParamsIterator());
			sitesGuiBean.validate();
			sitesGuiBean.repaint();
		}


	}

	/**
	 * Initialize the items to be added to the control list
	 */
	private void initControlList() {
		controlComboBox.addItem(CONTROL_PANELS);
		controlComboBox.addItem(REGIONS_OF_INTEREST_CONTROL);
		controlComboBox.addItem(X_VALUES_CONTROL);
		controlComboBox.addItem(DISTANCE_CONTROL);
		//controlComboBox.addItem(MAP_CALC_CONTROL);
	}




	/**
	 * Initialize the Interesting regions control panel
	 * It will provide a pick list of interesting regions
	 */
	private void initRegionsOfInterestControl() {
		if(this.regionsOfInterest==null)
			regionsOfInterest = new RegionsOfInterestControlPanel(this, this.sitesGuiBean);
		regionsOfInterest.getComponent().pack();
		regionsOfInterest.getComponent().setVisible(true);
	}

	/**
	 * initialize the X values for the Hazard Map
	 * It will enable the user to set the X values
	 */
	private void initX_ValuesControl(){
		if(xValuesPanel == null)
			xValuesPanel = new X_ValuesInCurveControlPanel(this,this);
		if(!useCustomX_Values) xValuesPanel.useDefaultX_Values();
		else xValuesPanel.setX_Values(function);
		xValuesPanel.getComponent().pack();
		xValuesPanel.getComponent().setVisible(true);
	}

	/**
	 * Initialize the Min Source and site distance control.
	 * This function is called when user selects "Source Site Distance Control"
	 * from controls pick list
	 */
	private void initDistanceControl() {
		if (this.distanceControlPanel == null)
			distanceControlPanel = new SetMinSourceSiteDistanceControlPanel(this);
		distanceControlPanel.pack();
		distanceControlPanel.setVisible(true);
	}

	/**
	 * Initialize the MapSubmission Calculation option .By default the option is
	 * Grid Based mode of generating the Hazard Map Calculation but this control
	 * panel allows user to choose from other options too.
	 */
	//private void initMapCalculationModeControl() {
	//if (mapSubmissionMethods == null)
	//mapSubmissionMethods = new HazardMapSubmissionMethods();
	// mapSubmissionMethods.pack();
	//mapSubmissionMethods.setVisible(true);
	//}

	/**
	 *
	 * @returns the selected IMT
	 */
	public String getSelectedIMT() {
		return imtGuiBean.getSelectedIMT();
	}


	/**
	 * This forces use of default X-axis values (according to the selected IMT)
	 */
	public void setCurveXValues() {
		useCustomX_Values = false;
	}

	/**
	 * Sets the hazard curve x-axis values (if user wants custom values x-axis values).
	 * Note that what's passed in is not cloned (the y-axis values will get modified).
	 * @param func
	 */
	public void setCurveXValues(ArbitrarilyDiscretizedFunc func) {
		useCustomX_Values = true;
		function = func;
	}



	/**
	 *
	 * @returns the selected Attenuationrelationship model
	 */
	public AttenuationRelationship getSelectedAttenuationRelationship(){
		return attenRel;
	}


	/**
	 * This function is called when controls pick list is chosen
	 * @param e
	 */
	void controlComboBox_actionPerformed(ActionEvent e) {
		if(controlComboBox.getItemCount()<=0) return;
		String selectedControl = controlComboBox.getSelectedItem().toString();
		if(selectedControl.equalsIgnoreCase(this.REGIONS_OF_INTEREST_CONTROL))
			initRegionsOfInterestControl();
		else if(selectedControl.equalsIgnoreCase(this.X_VALUES_CONTROL))
			initX_ValuesControl();
		else if(selectedControl.equalsIgnoreCase(this.DISTANCE_CONTROL))
			initDistanceControl();
		//else if(selectedControl.equalsIgnoreCase(this.MAP_CALC_CONTROL))
		//initMapCalculationModeControl();
		controlComboBox.setSelectedItem(this.CONTROL_PANELS);
	}


	/**
	 * This function is called when user submits the calculation
	 * @param e
	 */
	void addButton_actionPerformed(ActionEvent e) {
		calcProgress = new CalcProgressBar("HazardMap Application","Initializing Calculation ...");
		// check that user has entered a valid email address
		String email = emailText.getText();
		if(email.trim().equalsIgnoreCase("")) {
			JOptionPane.showMessageDialog(this, "Please Enter email Address");
			return;
		}
		if(email.indexOf("@") ==-1 || email.indexOf(".") ==-1) {
			JOptionPane.showMessageDialog(this, "Please Enter valid email Address");
			return;
		}
		timer = new Timer(100, new ActionListener() {
			public void actionPerformed(ActionEvent evt) {
				if(step ==1)
					calcProgress.setProgressMessage("Checking if calculation have been done earlier ...");
				else if(step ==2)
					calcProgress.setProgressMessage("Setting ERF on server ...");
				else if(step == 3)
					calcProgress.setProgressMessage("Submitting Calculations , Please wait ...");
				else if(step ==0){
					addButton.setEnabled(true);
					timer.stop();
					calcProgress.dispose();
					calcProgress = null;
				}
			}
		});
		Thread t = new Thread(this);
		t.start();
	}

	/**
	 *
	 */
	public void run(){
		timer.start();
		try{
			step =1;
			//use the default values for IML's if user does not specifies any custom values.
			if(!useCustomX_Values)
				function = imtInfo.getDefaultHazardCurve(imtGuiBean.getSelectedIMT());
			//this connects to the servlet on web server to check if dataset name already exists
			//or computation have already been for these parameter settings.
			if(distanceControlPanel == null ) maxDistance = new Double(HazardCurveCalculator.MAX_DISTANCE_DEFAULT);
			else maxDistance = new Double(distanceControlPanel.getDistance());
			Object obj= checkForHazardMapComputation();
			if(obj instanceof String){
				JOptionPane.showMessageDialog(this, (String)obj);
				step =0;
				return;
			}
			else if(obj instanceof Boolean){ // if it is the instance of boolean which return true always
				//meaning it is safe to proceeed with the calculation and the name of the dataset that user
				//has specified.
				// get the selected IMR
				ScalarIntensityMeasureRelationshipAPI imr = imrGuiBean.getSelectedIMR_Instance();
				step =2;
				//gets the instance of the selected ERF
				String eqkRupForecastLocation =  erfGuiBean.saveSelectedERF();
				// this function will get the selected IMT parameter and set it in IMT
				imtGuiBean.setIMT();
				SitesInGriddedRegion griddedRegionSites = sitesGuiBean.getGriddedRegionSite();
				step =3;
				sendParametersToServlet(griddedRegionSites, imr, eqkRupForecastLocation);
				step =0;
			}
		}catch(ParameterException ee){
			ee.printStackTrace();
			step =0;
			JOptionPane.showMessageDialog(this,ee.getMessage(),"Invalid Parameters",JOptionPane.ERROR_MESSAGE);
			return;
		}
		catch(Exception ee){
			ee.printStackTrace();
			step =0;
			JOptionPane.showMessageDialog(this,ee.getMessage(),"Input Error",JOptionPane.INFORMATION_MESSAGE);
			return;
		}

	}

	/**
	 * this connects to the servlet on web server to check if dataset name already exists
	 * or computation have already been for these parameter settings.
	 * @return
	 */
	private Object checkForHazardMapComputation(){

		try{
			if(D) System.out.println("starting to make connection with servlet");
			URL hazardMapServlet = new URL(DATASET_CHECK_SERVLET_URL);


			URLConnection servletConnection = hazardMapServlet.openConnection();
			if(D) System.out.println("connection established");

			// inform the connection that we will send output and accept input
			servletConnection.setDoInput(true);
			servletConnection.setDoOutput(true);

			// Don't use a cached version of URL connection.
			servletConnection.setUseCaches (false);
			servletConnection.setDefaultUseCaches (false);
			// Specify the content type that we will send binary data
			servletConnection.setRequestProperty ("Content-Type","application/octet-stream");

			ObjectOutputStream toServlet = new
			ObjectOutputStream(servletConnection.getOutputStream());

			//sending the parameters info. to the servlet
			toServlet.writeObject(getParametersInfo());

			//sending the dataset id to the servlet
			toServlet.writeObject(datasetIdText.getText());


			toServlet.flush();
			toServlet.close();

			// Receive the datasetnumber from the servlet after it has received all the data
			ObjectInputStream fromServlet = new ObjectInputStream(servletConnection.getInputStream());
			Object obj=fromServlet.readObject();
			//if(D) System.out.println("Receiving the Input from the Servlet:"+success);
			fromServlet.close();
			return obj;

		}catch (Exception e) {
			ExceptionWindow bugWindow = new ExceptionWindow(this,e,getParametersInfo());
			bugWindow.setVisible(true);
			bugWindow.pack();

		}
		return null;
	}

	/**
	 * sets up the connection with the servlet on the server (gravity.usc.edu)
	 */
	private void sendParametersToServlet(SitesInGriddedRegion regionSites,
			ScalarIntensityMeasureRelationshipAPI imr,
			String eqkRupForecastLocation) {

		try{
			if(D) System.out.println("starting to make connection with servlet");
			URL hazardMapServlet = new URL(SERVLET_URL);


			URLConnection servletConnection = hazardMapServlet.openConnection();
			if(D) System.out.println("connection established");

			// inform the connection that we will send output and accept input
			servletConnection.setDoInput(true);
			servletConnection.setDoOutput(true);

			// Don't use a cached version of URL connection.
			servletConnection.setUseCaches (false);
			servletConnection.setDefaultUseCaches (false);
			// Specify the content type that we will send binary data
			servletConnection.setRequestProperty ("Content-Type","application/octet-stream");

			ObjectOutputStream toServlet = new
			ObjectOutputStream(servletConnection.getOutputStream());

			//sending the object of the gridded region sites to the servlet
			toServlet.writeObject(regionSites);
			//sending the IMR object to the servlet
			toServlet.writeObject(imr);
			//sending the EQK forecast object to the servlet
			toServlet.writeObject(eqkRupForecastLocation);
			//send the X values in a arraylist
			ArrayList list = new ArrayList();
			for(int i = 0; i<function.getNum(); ++i) list.add(new String(""+function.getX(i)));
			toServlet.writeObject(list);
			// send the MAX DISTANCE
			toServlet.writeObject(maxDistance);

			//sending email address to the servlet
			toServlet.writeObject(emailText.getText());
			//sending the parameters info. to the servlet
			toServlet.writeObject(getParametersInfo());

			//sending the dataset id to the servlet
			toServlet.writeObject(datasetIdText.getText());


			toServlet.flush();
			toServlet.close();

			// Receive the datasetnumber from the servlet after it has received all the data
			ObjectInputStream fromServlet = new ObjectInputStream(servletConnection.getInputStream());
			String dataset=fromServlet.readObject().toString();
			JOptionPane.showMessageDialog(this, dataset);
			if(D) System.out.println("Receiving the Input from the Servlet:"+dataset);
			fromServlet.close();

		}catch (Exception e) {
			ExceptionWindow bugWindow = new ExceptionWindow(this,e,getParametersInfo());
			bugWindow.setVisible(true);
			bugWindow.pack();
		}
	}

	/**
	 * Returns the metadata associated with this calculation
	 *
	 * @returns the String containing the values selected for different parameters
	 */
	public String getParametersInfo() {
		String lf = SystemUtils.LINE_SEPARATOR;
		String metadata = "IMR Param List:" + lf +
		"---------------" + lf +
		this.imrGuiBean.getVisibleParametersCloned().
		getParameterListMetadataString() + lf +
		lf +
		"Region Param List: " + lf +
		"----------------" + lf +
		sitesGuiBean.getVisibleParametersCloned().
		getParameterListMetadataString() + lf +
		lf + "IMT Param List: " +
		lf +
		"---------------" + lf +
		imtGuiBean.getVisibleParametersCloned().getParameterListMetadataString() +
		lf +
		lf + "Forecast Param List: " +
		lf +
		"--------------------" + lf +
		erfGuiBean.getERFParameterList().getParameterListMetadataString() +
		lf +
		lf + "TimeSpan Param List: " +
		lf +
		"--------------------" + lf +
		erfGuiBean.getSelectedERFTimespanGuiBean().getParameterListMetadataString() + lf+
		lf + "Miscellaneous Metadata:"+
		lf +
		"--------------------" + lf+
		"Maximum Site Source Distance = "+maxDistance+lf+
		lf+
		"X Values = ";

		//getting the X values used to generate the metadata.
		ListIterator it = function.getXValuesIterator();
		String xVals="";
		while(it.hasNext())
			xVals +=(Double)it.next()+" , ";
		xVals = xVals.substring(0,xVals.lastIndexOf(","));

		//adding the X Vals used to the Metadata.
		metadata +=xVals;
		return metadata;
	}

	void imgLabel_mouseClicked(MouseEvent e) {
		try{
			this.getAppletContext().showDocument(new URL(OPENSHA_WEBSITE), "new_peer_win");
		}catch(java.net.MalformedURLException ee){
			JOptionPane.showMessageDialog(this,new String("No Internet Connection Available"),
					"Error Connecting to Internet",JOptionPane.OK_OPTION);

		}
	}


	/**
	 * Updates the IMT_GuiBean to reflect the chnaged IM for the selected AttenuationRelationship.
	 * This method is called from the IMR_GuiBean to update the application with the Attenuation's
	 * supported IMs.
	 *
	 */
	public void updateIM() {
		//get the selected IMR
		ScalarIntensityMeasureRelationshipAPI imr = imrGuiBean.getSelectedIMR_Instance();
		imtGuiBean.setIM(imr,imr.getSupportedIntensityMeasuresIterator()) ;
	}

	/**
	 * Updates the SitesInGriddedRegionGuiBean to reflect the chnaged SiteParams for the selected AttenuationRelationship.
	 * This method is called from the IMR_GuiBean to update the application with the Attenuation's
	 * Site Params.
	 *
	 */
	public void updateSiteParams() {
		//get the selected IMR
		ScalarIntensityMeasureRelationshipAPI imr = imrGuiBean.getSelectedIMR_Instance();
		sitesGuiBean.replaceSiteParams(imr.getSiteParamsIterator());
		sitesGuiBean.validate();
		sitesGuiBean.repaint();
	}
	
	@Override
	public void addCurve(ArbitrarilyDiscretizedFunc function) {}

}
