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

package org.opensha.sha.gui;

import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.GridLayout;
import java.awt.Insets;
import java.awt.SystemColor;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.lang.reflect.InvocationTargetException;
import java.net.URL;
import java.util.ArrayList;

import javax.swing.JButton;
import javax.swing.JComboBox;
import javax.swing.JFrame;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JSplitPane;
import javax.swing.JTabbedPane;
import javax.swing.Timer;
import javax.swing.UIManager;
import javax.swing.border.Border;
import javax.swing.border.EtchedBorder;

import org.opensha.commons.data.XYZ_DataSetAPI;
import org.opensha.commons.data.region.SitesInGriddedRegion;
import org.opensha.commons.data.siteData.OrderedSiteDataProviderList;
import org.opensha.commons.data.siteData.gui.beans.OrderedSiteDataGUIBean;
import org.opensha.commons.data.siteData.impl.CVM4BasinDepth;
import org.opensha.commons.data.siteData.impl.WaldAllenGlobalVs30;
import org.opensha.commons.data.siteData.impl.WillsMap2006;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.exceptions.RegionConstraintException;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.commons.util.FileUtils;
import org.opensha.commons.util.ListUtils;
import org.opensha.sha.calc.ScenarioShakeMapCalculator;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.gui.beans.AttenuationRelationshipGuiBean;
import org.opensha.sha.gui.beans.AttenuationRelationshipSiteParamsRegionAPI;
import org.opensha.sha.gui.beans.EqkRupSelectorGuiBean;
import org.opensha.sha.gui.beans.IMLorProbSelectorGuiBean;
import org.opensha.sha.gui.beans.MapGuiBean;
import org.opensha.sha.gui.beans.SitesInGriddedRectangularRegionGuiBean;
import org.opensha.sha.gui.controls.GMTMapCalcOptionControl;
import org.opensha.sha.gui.controls.CalculationSettingsControlPanel;
import org.opensha.sha.gui.controls.CalculationSettingsControlPanelAPI;
import org.opensha.sha.gui.controls.ControlPanel;
import org.opensha.sha.gui.controls.CyberShakePlotFromDBControlPanel;
import org.opensha.sha.gui.controls.CyberShakeSiteSetterControlPanel;
import org.opensha.sha.gui.controls.DisaggregationControlPanel;
import org.opensha.sha.gui.controls.GenerateHazusControlPanelForSingleMultipleIMRs;
import org.opensha.sha.gui.controls.IM_EventSetCEA_ControlPanel;
import org.opensha.sha.gui.controls.PEER_TestCaseSelectorControlPanel;
import org.opensha.sha.gui.controls.PlottingOptionControl;
import org.opensha.sha.gui.controls.PuenteHillsScenarioControlPanel;
import org.opensha.sha.gui.controls.PuenteHillsScenarioControlPanelUsingEqkRuptureCreation;
import org.opensha.sha.gui.controls.RegionsOfInterestControlPanel;
import org.opensha.sha.gui.controls.RunAll_PEER_TestCasesControlPanel;
import org.opensha.sha.gui.controls.SanAndreasScenarioControlPanel;
import org.opensha.sha.gui.controls.SiteDataControlPanel;
import org.opensha.sha.gui.controls.SitesOfInterestControlPanel;
import org.opensha.sha.gui.controls.XY_ValuesControlPanel;
import org.opensha.sha.gui.controls.X_ValuesInCurveControlPanel;
import org.opensha.sha.gui.infoTools.ApplicationVersionInfoWindow;
import org.opensha.sha.gui.infoTools.CalcProgressBar;
import org.opensha.sha.gui.infoTools.ExceptionWindow;
import org.opensha.sha.gui.infoTools.IMT_Info;
import org.opensha.sha.imr.event.ScalarIMRChangeEvent;
import org.opensha.sha.imr.event.ScalarIMRChangeListener;

/**
 * <p>Title: ScenarioShakeMapApp</p>
 * <p>Description: This application provides the flexibility to plot shakemaps
 *  using the single Attenuation as well as the multiple attenuation relationships.</p>
 *  TESTS PERFORMED:<p>
 * 1) the Wills site-class servlet and site-type translator were checked independently.<p>
 * 2) All attenuation-relationship parameter settings were checked using the debugging
 * option in the ScenarioShakeMapCalculator (e.g., three different events with different
 * focal mechanisms checked - src #s 136, 232, and 61 in the USGS/CGS_2002 ERF). Thus, the
 * values should be correct as long as the attenuation-relationships are working properly,
 * which has been checked independently using the AttenuationRelationshipApplet.<p>
 * 3) Various IML@prob or prob@iml with various truncations were checked against calculations
 * with the AttenuationRelationshipApplet. <p>
 * 4) ShakeMaps computed here were compared with those at the offical USGS archive (more details later). <p>
 * 5) The wted-averages in multi-attenuation-relationship mode were checked, as well as the fact that
 * log-averages are taken over probabilities and IMLs where appropriate. <p>
 * 6) That the HAZUS files are generated correctly was checked.
 * @author : Edward (Ned) Field, Nitin Gupta and Vipin Gupta
 * @version 1.0
 */

public class ScenarioShakeMapApp extends JFrame implements ParameterChangeListener,
AttenuationRelationshipSiteParamsRegionAPI,CalculationSettingsControlPanelAPI,Runnable, ScalarIMRChangeListener{

	/**
	 * Name of the class
	 */
	protected final static String C = "ScenarioShakeMapApp";
	// for debug purpose
	protected final static boolean D = false;


	protected final static String version = "0.0.16";

	protected final static String versionURL = "http://www.opensha.org/applications/scenShakeMapApp/ScenarioShakeMapApp_Version.txt";
	protected final static String appURL = "http://www.opensha.org/applications/scenShakeMapApp/ScenarioShakeMapApp.jar";
	protected final static String versionUpdateInfoURL = "http://www.opensha.org/applications/scenShakeMapApp/versionUpdate.html";



	//variables that determine the width and height of the frame
	protected static final int W=550;
	protected static final int H=760;

	// default insets
	protected Insets defaultInsets = new Insets( 4, 4, 4, 4 );


	//the path to the file where gridded region is stored if calculation are to be
	// done on the server
	protected String serverRegionFilePath;
	//path to the file where the XYZ data file is stored
	protected String serverXYZDataSetFilePath;


	//reference to the  XYZ dataSet
	protected XYZ_DataSetAPI xyzDataSet;


	//store the site values for each site in the griddded region
	protected SitesInGriddedRegion griddedRegionSites;

	//stores the IML or Prob selection and their value for which we want to compute the
	//scenario shake map. Value we get from the respective guibeans.
	protected boolean probAtIML=false;
	protected double imlProbValue;

	//Eqkrupture Object
	protected EqkRupture eqkRupture;

	// stores the instances of the selected AttenuationRelationships
	protected ArrayList attenRel;
	//stores the instance of the selected AttenuationRelationships wts after normalization
	protected ArrayList attenRelWts;

	//Instance to the ShakeMap calculator to get the XYZ data for the selected scenario
	//making the object for the ScenarioShakeMapCalculator to get the XYZ data.
	protected ScenarioShakeMapCalculator shakeMapCalc = new ScenarioShakeMapCalculator();

	//timer to show thw progress bar
	protected Timer timer;

	//Metadata String
	protected String mapParametersInfo = null;


	//boolean to check if the calculation have to be done on the server
	protected boolean calculationFromServer = true;


	/**
	 *  The object class names for all the supported Eqk Rup Forecasts
	 */
	public final static String RMI_FRANKEL_ADJ_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.remoteERF_Clients.Frankel96_AdjustableEqkRupForecastClient";
	public final static String RMI_STEP_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.remoteERF_Clients.STEP_EqkRupForecastClient";
	public final static String RMI_STEP_ALASKA_ERF_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.remoteERF_Clients.STEP_AlaskanPipeForecastClient";
	public final static String RMI_FLOATING_POISSON_FAULT_ERF_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.remoteERF_Clients.FloatingPoissonFaultERF_Client";
	public final static String RMI_FRANKEL02_ADJ_FORECAST_CLASS_NAME="org.opensha.sha.earthquake.rupForecastImpl.remoteERF_Clients.Frankel02_AdjustableEqkRupForecastClient";
	public final static String RMI_PEER_AREA_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.remoteERF_Clients.PEER_AreaForecastClient";
	public final static String RMI_PEER_NON_PLANAR_FAULT_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.remoteERF_Clients.PEER_NonPlanarFaultForecastClient";
	public final static String RMI_PEER_MULTI_SOURCE_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.remoteERF_Clients.PEER_MultiSourceForecastClient";
	public final static String RMI_POINT2MULT_VSS_FORECAST_CLASS_NAME="org.opensha.sha.earthquake.rupForecastImpl.Point2MultVertSS_Fault.Point2MultVertSS_FaultERF";
	public final static String RMI_POISSON_FAULT_ERF_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.remoteERF_Clients.PoissonFaultERF_Client";
	public final static String RMI_WG02_ERF_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.remoteERF_Clients.WG02_EqkRupForecastClient";
	public final static String RMI_WGCEP_UCERF1_ERF_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.remoteERF_Clients.WGCEP_UCERF1_EqkRupForecastClient";

	// Strings for control pick list
	protected final static String CONTROL_PANELS = "Control Panels";
	
	private ArrayList<ControlPanel> controlPanels;

	// objects for control panels
	protected RegionsOfInterestControlPanel regionsOfInterest;
	protected PuenteHillsScenarioControlPanelUsingEqkRuptureCreation puenteHillsControlUsingEqkRupture;
	protected SanAndreasScenarioControlPanel  sanAndreasControlUsingEqkRupture;
	protected IM_EventSetCEA_ControlPanel imSetScenarioControl;
	//protected PuenteHillsScenarioControlPanelForSingleMultipleAttenRel puenteHillsControl;
	protected GenerateHazusControlPanelForSingleMultipleIMRs hazusControl;
	private GMTMapCalcOptionControl calcControl;
	protected CalculationSettingsControlPanel calcParamsControl;
	//private SF_BayAreaScenarioControlPanel bayAreaControl;

	// instances of the GUI Beans which will be shown in this applet
	protected EqkRupSelectorGuiBean erfGuiBean;
	protected AttenuationRelationshipGuiBean imrGuiBean;
	protected SitesInGriddedRectangularRegionGuiBean sitesGuiBean;
	protected OrderedSiteDataGUIBean siteDataGUIBean;
	protected IMLorProbSelectorGuiBean imlProbGuiBean;
	protected MapGuiBean mapGuiBean;


	//Adding the Menu to the application
	//JMenuBar menuBar = new JMenuBar();
	//JMenu helpMenu = new JMenu();
	//JMenuItem helpLaunchMenu = new JMenuItem();


	protected boolean isStandalone = false;
	protected JPanel mainPanel = new JPanel();
	protected Border border1;
	protected JSplitPane mainSplitPane = new JSplitPane();
	protected JPanel buttonPanel = new JPanel();
	protected JPanel eqkRupPanel = new JPanel();
	protected GridBagLayout gridBagLayout3 = new GridBagLayout();
	protected GridBagLayout gridBagLayout2 = new GridBagLayout();
	protected JPanel gmtPanel = new JPanel();
	protected JTabbedPane parameterTabbedPanel = new JTabbedPane();
	protected JPanel imrPanel = new JPanel();
	protected JPanel imtPanel = new JPanel();
	protected JPanel prob_IMLPanel = new JPanel();
	protected BorderLayout borderLayout2 = new BorderLayout();
	protected GridBagLayout gridBagLayout9 = new GridBagLayout();
	protected GridBagLayout gridBagLayout8 = new GridBagLayout();
	protected JButton addButton = new JButton();
	protected JPanel gridRegionSitePanel = new JPanel();
	protected GridLayout gridLayout1 = new GridLayout();
	protected GridBagLayout gridBagLayout1 = new GridBagLayout();
	protected GridBagLayout gridBagLayout5 = new GridBagLayout();
	protected JComboBox controlComboBox = new JComboBox();
	protected GridBagLayout gridBagLayout6 = new GridBagLayout();
	protected BorderLayout borderLayout1 = new BorderLayout();
	protected CalcProgressBar calcProgress;
	protected int step;


	protected GridBagLayout gridBagLayout4 = new GridBagLayout();

	//Construct the applet
	public ScenarioShakeMapApp() {
	}
	//Initialize the applet
	public void init() {
		try {
			this.initSiteDataGuiBean();
		}
		catch (RuntimeException ex) {
			step = 0;
			ExceptionWindow bugWindow = new ExceptionWindow(this,ex,
					"Exception occured while initializing the Site Data providers in ScenarioShakeMap application."+
			"Parameters values have not been set yet.");
			bugWindow.setVisible(true);
			bugWindow.pack();
			ex.printStackTrace();

		}
		try {
			jbInit();
		}
		catch(Exception e) {
			step = 0;
			ExceptionWindow bugWindow = new ExceptionWindow(this,e,"Exception during initializing the application.\n"+
			"Parameters values not yet set.");
			e.printStackTrace();
			bugWindow.setVisible(true);
			bugWindow.pack();
		}
		try{
			//initialises the IMR and IMT Gui Bean
			initIMRGuiBean();
		}catch(RuntimeException e){
			//e.printStackTrace();
			step = 0;
			ExceptionWindow bugWindow = new ExceptionWindow(this,e, "Exception occured initializing the IMR with "+
			"default parameters value");
			e.printStackTrace();
			bugWindow.setVisible(true);
			bugWindow.pack();
			//JOptionPane.showMessageDialog(this,"Invalid parameter value",e.getMessage(),JOptionPane.ERROR_MESSAGE);
			//return;
		}
		try {
			this.initGriddedRegionGuiBean();
		}
		catch (RegionConstraintException ex) {
			step = 0;
			ExceptionWindow bugWindow = new ExceptionWindow(this,ex,
					"Exception occured while initializing the  region parameters in ScenarioShakeMap application."+
			"Parameters values have not been set yet.");
			bugWindow.setVisible(true);
			bugWindow.pack();
			ex.printStackTrace();

		}
		try{
			this.initERFSelector_GuiBean();

		}catch(RuntimeException e){
			e.printStackTrace();
			step =0;
			JOptionPane.showMessageDialog(this,"Could not create ERF Object","Error occur in ERF",
					JOptionPane.OK_OPTION);
			System.exit(0);
			//return;
		}
		this.initImlProb_GuiBean();
		this.initMapGuiBean();
		// initialize the control pick list
		initControlList();
	}

	/**
	 * Checks if the current version of the application is latest else direct the
	 * user to the latest version on the website.
	 */
	protected void checkAppVersion(){
		ArrayList scenarioShakeVersion = null;
		try {
			scenarioShakeVersion = FileUtils.loadFile(new URL(versionURL));
		}
		catch (Exception ex1) {
			return;
		}
		String appVersionOnWebsite = (String)scenarioShakeVersion.get(0);
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




	//Component initialization
	protected void jbInit() throws Exception {
		border1 = new EtchedBorder(EtchedBorder.RAISED,new Color(248, 254, 255),new Color(121, 124, 136));
		this.setSize(new Dimension(564, 752));
		this.getContentPane().setLayout(borderLayout1);
		mainPanel.setBorder(border1);
		mainPanel.setLayout(gridBagLayout6);
		mainSplitPane.setOrientation(JSplitPane.VERTICAL_SPLIT);
		mainSplitPane.setLastDividerLocation(610);
		buttonPanel.setLayout(gridBagLayout4);
		eqkRupPanel.setLayout(gridBagLayout1);
		gmtPanel.setLayout(gridBagLayout9);

		imrPanel.setLayout(borderLayout2);
		imtPanel.setLayout(gridBagLayout8);
		prob_IMLPanel.setLayout(gridBagLayout2);
		addButton.setText("Make Map");
		addButton.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				addButton_actionPerformed(e);
			}
		});
		buttonPanel.setMinimumSize(new Dimension(391, 50));
		gridRegionSitePanel.setLayout(gridLayout1);
		imrPanel.setLayout(gridBagLayout5);
		controlComboBox.setBackground(SystemColor.control);
		controlComboBox.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				controlComboBox_actionPerformed(e);
			}
		});
		this.getContentPane().add(mainPanel, BorderLayout.CENTER);
		mainPanel.add(mainSplitPane,  new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(1, 1, 2, 3), 0, 431));
		mainSplitPane.add(buttonPanel, JSplitPane.BOTTOM);
		buttonPanel.add(controlComboBox,  new GridBagConstraints(0, 0, 1, 1, 1.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL, new Insets(48, 41, 47, 0), 5, 2));
		buttonPanel.add(addButton,  new GridBagConstraints(1, 0, 1, 1, 0.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(48, 88, 39, 139), 26, 9));
		mainSplitPane.add(parameterTabbedPanel, JSplitPane.TOP);


		parameterTabbedPanel.addTab("Intensity-Measure Relationship", imrPanel);
		parameterTabbedPanel.addTab("Region & Site Params", gridRegionSitePanel);
		JPanel panel = new JPanel(new BorderLayout());
		panel.add(siteDataGUIBean, BorderLayout.CENTER);
		parameterTabbedPanel.addTab("Site Data Providers", panel);
		parameterTabbedPanel.addTab("Earthquake Rupture", eqkRupPanel );
		parameterTabbedPanel.addTab( "Exceedance Level/Probability", prob_IMLPanel);
		parameterTabbedPanel.addTab("Map Attributes", gmtPanel);

		mainSplitPane.setDividerLocation(630);

		//applet.createHelpMenu();
		this.setSize(W,H);
		Dimension dim = Toolkit.getDefaultToolkit().getScreenSize();
		this.setLocation((dim.width - getSize().width) / 2, (dim.height - getSize().height) / 2);
		//EXIT_ON_CLOSE == 3
		this.setDefaultCloseOperation(3);
		this.setTitle("ScenarioShakeMap Application ("+getAppVersion()+" )");

		//adding the Menu to the application
		/*helpMenu.setText("Help");
    helpLaunchMenu.setText("Help Application");
    menuBar.add(helpMenu);
    helpMenu.add(helpLaunchMenu);
    setJMenuBar(menuBar);*/
		//createHelpMenu();
	}


	/*private void createHelpMenu(){
    LaunchHelpFromMenu helpMenu = new LaunchHelpFromMenu();
    HelpBroker hb = helpMenu.createHelpMenu("file:///Users/nitingupta/projects/sha/OpenSHA_docs/ScenarioShakeMap_UserManual/shaHelp.xml");
    helpLaunchMenu.addActionListener(new CSH.DisplayHelpFromSource(hb));
  }*/

	//Main method
	public static void main(String[] args) {
		ScenarioShakeMapApp applet = new ScenarioShakeMapApp();
		applet.checkAppVersion();
		applet.init();
		applet.setVisible(true);
	}

	//static initializer for setting look & feel
	static {
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
	protected void initGriddedRegionGuiBean() throws RegionConstraintException {

		// create the Site Gui Bean object
		sitesGuiBean = new SitesInGriddedRectangularRegionGuiBean(siteDataGUIBean);

		//sets the site parameters in the gridded region gui bean.
		setGriddedRegionSiteParams();
		// show the sitebean in JPanel
		gridRegionSitePanel.add(this.sitesGuiBean, new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0,
				GridBagConstraints.CENTER, GridBagConstraints.BOTH, defaultInsets, 0, 0 ));
	}

	protected void initSiteDataGuiBean() {
		OrderedSiteDataProviderList provs = OrderedSiteDataProviderList.createSiteDataProviderDefaults();
		// just leave CVM, Global Vs30, and Wills 2006 enabled
		for (int i=0; i<provs.size(); i++) {
			String name = provs.getProvider(i).getName();
			if (name.equals(CVM4BasinDepth.NAME))
				provs.setEnabled(i, true);
			else if (name.equals(WillsMap2006.NAME))
				provs.setEnabled(i, true);
			else if (name.equals(WaldAllenGlobalVs30.NAME))
				provs.setEnabled(i, true);
			else
				provs.setEnabled(i, false);
		}
		siteDataGUIBean = new OrderedSiteDataGUIBean(provs);
	}



	/**
	 * Initialize the IMR Gui Bean
	 */
	protected void initIMRGuiBean() {
		imrGuiBean = new AttenuationRelationshipGuiBean(this);
		imrGuiBean.getIntensityMeasureParamEditor().getParameterEditor(imrGuiBean.IMT_PARAM_NAME).getParameter().addParameterChangeListener(this);
		// show this IMRgui bean the Panel
		imrPanel.add(imrGuiBean,new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0,
				GridBagConstraints.CENTER, GridBagConstraints.BOTH, defaultInsets, 0, 0 ));
		imrGuiBean.addAttenuationRelationshipChangeListener(this);
		siteDataGUIBean.setIMR(imrGuiBean.getSelectedIMR_Instance());
	}

	/**
	 * Initialize the ERF Gui Bean
	 */
	protected void initERFSelector_GuiBean() {
		// create the ERF Gui Bean object
		ArrayList erf_Classes = new ArrayList();

		/**
		 *  The object class names for all the supported Eqk Rup Forecasts
		 */
		erf_Classes.add(RMI_POISSON_FAULT_ERF_CLASS_NAME);
		erf_Classes.add(RMI_FRANKEL_ADJ_FORECAST_CLASS_NAME);
		//erf_Classes.add(RMI_STEP_FORECAST_CLASS_NAME);
		//   erf_Classes.add(RMI_STEP_ALASKA_ERF_CLASS_NAME);
		erf_Classes.add(RMI_FLOATING_POISSON_FAULT_ERF_CLASS_NAME);
		erf_Classes.add(RMI_FRANKEL02_ADJ_FORECAST_CLASS_NAME);
		//   erf_Classes.add(RMI_PEER_AREA_FORECAST_CLASS_NAME);
		//   erf_Classes.add(RMI_PEER_NON_PLANAR_FAULT_FORECAST_CLASS_NAME);
		//   erf_Classes.add(RMI_PEER_MULTI_SOURCE_FORECAST_CLASS_NAME);
		erf_Classes.add(RMI_WG02_ERF_CLASS_NAME);
		erf_Classes.add(RMI_WGCEP_UCERF1_ERF_CLASS_NAME);


		try{
			erfGuiBean = new EqkRupSelectorGuiBean(erf_Classes);
		}catch(InvocationTargetException e){
			throw new RuntimeException("Connection to ERF's failed");
		}
		eqkRupPanel.add(erfGuiBean, new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0,
				GridBagConstraints.CENTER,GridBagConstraints.BOTH, defaultInsets, 0, 0 ));
	}

	/**
	 * Initialise the IMT_Prob Selector Gui Bean
	 */
	protected void initImlProb_GuiBean(){
		imlProbGuiBean = new IMLorProbSelectorGuiBean();
		imlProbGuiBean.setIMLConstraintBasedOnSelectedIMT(imrGuiBean.getSelectedIMT());
		prob_IMLPanel.add(imlProbGuiBean, new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0,
				GridBagConstraints.CENTER,GridBagConstraints.BOTH, defaultInsets, 0, 0 ));
	}





	/**
	 * Sets the GMT Params
	 */
	protected void initMapGuiBean(){
		mapGuiBean = new MapGuiBean();
		mapGuiBean.showRegionParams(false);
		gmtPanel.add(mapGuiBean, new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0,
				GridBagConstraints.CENTER, GridBagConstraints.BOTH, defaultInsets, 0, 0 ));
		double minLat=((Double)sitesGuiBean.getParameterList().getParameter(sitesGuiBean.MIN_LATITUDE).getValue()).doubleValue();
		double maxLat=((Double)sitesGuiBean.getParameterList().getParameter(sitesGuiBean.MAX_LATITUDE).getValue()).doubleValue();
		double minLon=((Double)sitesGuiBean.getParameterList().getParameter(sitesGuiBean.MIN_LONGITUDE).getValue()).doubleValue();
		double maxLon=((Double)sitesGuiBean.getParameterList().getParameter(sitesGuiBean.MAX_LONGITUDE).getValue()).doubleValue();
		double gridSpacing=((Double)sitesGuiBean.getParameterList().getParameter(sitesGuiBean.GRID_SPACING).getValue()).doubleValue();
		mapGuiBean.setRegionParams(minLat,maxLat,minLon,maxLon,gridSpacing);
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


		if(name1.equalsIgnoreCase(AttenuationRelationshipGuiBean.IMT_PARAM_NAME))
			imlProbGuiBean.setIMLConstraintBasedOnSelectedIMT(imrGuiBean.getSelectedIMT());


	}

	/**
	 *
	 */
	public void run(){

		try{
			addButton();
		}catch(ParameterException ee){
			//ee.printStackTrace();
			step =0;
			JOptionPane.showMessageDialog(this,ee.getMessage(),"Invalid Parameters",JOptionPane.ERROR_MESSAGE);
			return;
		}
		catch(RegionConstraintException ee){
			//ee.printStackTrace();
			step =0;
			JOptionPane.showMessageDialog(this,ee.getMessage(),"Invalid Site",JOptionPane.ERROR_MESSAGE);
			return;
		}
		catch(RuntimeException ee){
			step =0;
			JOptionPane.showMessageDialog(this,ee.getMessage(),"Input Error",JOptionPane.ERROR_MESSAGE);
			ee.printStackTrace();
			return;

		}
		catch(Exception ee){
			step = 0;
			ExceptionWindow bugWindow = new ExceptionWindow(this,ee,mapParametersInfo);
			bugWindow.setVisible(true);
			bugWindow.pack();
			ee.printStackTrace();
			return;
		}
	}



	/**
	 * sets the Site Params from the AttenuationRelationships in the GriddedRegion
	 * Gui Bean.
	 */
	public void setGriddedRegionSiteParams(){
		if(sitesGuiBean !=null){
			sitesGuiBean.replaceSiteParams(imrGuiBean.getSelectedAttenRelSiteParams());
			sitesGuiBean.refreshParamEditor();
		}
	}


	/**
	 * Updates the Sites Values for each site in the region chosen by the user
	 *
	 */
	protected void getGriddedRegionSites() throws RuntimeException, RegionConstraintException {
		//if calculation have to be done on the local system
		if(!calculationFromServer)
			griddedRegionSites = sitesGuiBean.getGriddedRegionSite();
		else //if calculation have to done on the server
			serverRegionFilePath = sitesGuiBean.openConnectionToServer();

	}

	/**
	 * gets the IML or Prob selected option and its value from the respective guiBean
	 */
	protected void getIMLorProb(){
		imlProbValue=imlProbGuiBean.getIML_Prob();
		String imlOrProb=imlProbGuiBean.getSelectedOption();
		if(imlOrProb.equalsIgnoreCase(imlProbGuiBean.PROB_AT_IML))
			probAtIML=true;
		else
			probAtIML = false;
	}


	/**
	 * If the calculation have to be done on server then returns true else
	 * retun false
	 * @return
	 */
	public boolean doCalculationOnServer(){
		return calculationFromServer;
	}


	/**
	 * This method calculates the probablity or the IML for the selected Gridded Region
	 * and stores the value in each vectors(lat-ArrayList, Lon-ArrayList and IML or Prob ArrayList)
	 * The IML or prob vector contains value based on what the user has selected in the Map type
	 * @param attenRel : Selected AttenuationRelationships
	 * @param imt : Selected IMT
	 */
	public Object generateShakeMap(ArrayList attenRel, ArrayList attenRelWts, String imt) throws ParameterException,RuntimeException, RegionConstraintException {
		try {
			double value=imlProbValue;
			//if the IMT selected is Log supported then take the log if Prob @ IML
			if(IMT_Info.isIMT_LogNormalDist(imrGuiBean.getSelectedIMT()) && probAtIML)
				value = Math.log(imlProbValue);
			if(!calculationFromServer){
				//does the calculation for the ScenarioShakeMap Calc and gives back a XYZ dataset
				xyzDataSet = shakeMapCalc.getScenarioShakeMapData(attenRel,attenRelWts,
						griddedRegionSites,eqkRupture,probAtIML,value);
				//if the IMT is log supported then take the exponential of the Value if IML @ Prob
				if(IMT_Info.isIMT_LogNormalDist(imt) && !probAtIML){
					ArrayList zVals = xyzDataSet.getZ_DataSet();
					int size = zVals.size();
					for(int i=0;i<size;++i){
						double val = ((Double)(zVals.get(i))).doubleValue();
						double tempVal = Math.exp(val);
						zVals.set(i,new Double(tempVal));
					}
				}
				return xyzDataSet;
			}
			else{ //if the calculation have to be done on the server
				//calls the scenario shakemap calculator to generate the map data file on the server
				serverXYZDataSetFilePath = shakeMapCalc.getScenarioShakeMapDataUsingServer(attenRel,attenRelWts,
						serverRegionFilePath,eqkRupture,probAtIML,value,imt);
				return serverXYZDataSetFilePath;
			}
		}catch(ParameterException e){
			//e.printStackTrace();
			throw new ParameterException(e.getMessage());
		}
	}


	/**
	 * Gets the EqkRupture object from the Eqk Rupture GuiBean
	 */
	public void getEqkRupture(){
		eqkRupture = erfGuiBean.getRupture();
	}



	/**
	 * Sets the GMT Region coordinates
	 */
	protected void setRegionForGMT(){
		double minLat=((Double)sitesGuiBean.getParameterList().getParameter(sitesGuiBean.MIN_LATITUDE).getValue()).doubleValue();
		double maxLat=((Double)sitesGuiBean.getParameterList().getParameter(sitesGuiBean.MAX_LATITUDE).getValue()).doubleValue();
		double minLon=((Double)sitesGuiBean.getParameterList().getParameter(sitesGuiBean.MIN_LONGITUDE).getValue()).doubleValue();
		double maxLon=((Double)sitesGuiBean.getParameterList().getParameter(sitesGuiBean.MAX_LONGITUDE).getValue()).doubleValue();
		double gridSpacing=((Double)sitesGuiBean.getParameterList().getParameter(sitesGuiBean.GRID_SPACING).getValue()).doubleValue();
		mapGuiBean.setRegionParams(minLat,maxLat,minLon,maxLon,gridSpacing);
	}


	/**
	 * Returns the selected IM in the IMR GuiBean
	 * @return
	 */
	public ParameterAPI getSelectedIntensityMeasure(){
		return imrGuiBean.getSelectedIntensityMeasure();
	}


	/**
	 * Creating the map for the Hazus.
	 * This creates the map and info for the SA-1sec, SA-0.3sec, PGA and PGV, all
	 * required as part calculation in Hazus. This will only generate the map and all the
	 * related information of the map but won't generate the shapefiles until the user
	 * has asked it to do so in the map parameters.
	 * Note : This method will always generate the Linear plot, whether the user has
	 * selected log plot in the map parameters, because Hazus only takes data in linearr
	 * space. So this method will always compute maps and its data in the linear space
	 * as Hazus does not accepts the log values in the map data.
	 */
	public void makeMapForHazus(Object datasetForSA_03,Object datasetForSA_1,
			Object datasetForPGA,Object datasetForPGV){
		//sets the region coordinates for the GMT using the MapGuiBean
		setRegionForGMT();


		//sets the some GMT param to specific value for computation for Hazus files.
		mapGuiBean.setGMT_ParamsForHazus();
		//gets the map parameters info.
		mapParametersInfo = getMapParametersInfoAsHTML();

		if(!calculationFromServer) //if the calc are to be done on the local system
			//creates the maps and information that goes into the Hazus.
			mapGuiBean.makeHazusShapeFilesAndMap((XYZ_DataSetAPI)datasetForSA_03,(XYZ_DataSetAPI)datasetForSA_1,
					(XYZ_DataSetAPI)datasetForPGA,(XYZ_DataSetAPI)datasetForPGV,eqkRupture,mapParametersInfo);
		else //if the calc are to be done on server
			//creates the maps and information that goes into the Hazus.
			mapGuiBean.makeHazusShapeFilesAndMap((String)datasetForSA_03,(String)datasetForSA_1,
					(String)datasetForPGA,(String)datasetForPGV,eqkRupture,mapParametersInfo);

		//sets the GMT parameters changed for Hazus files generation to their original value.
		mapGuiBean.setGMT_ParamsChangedForHazusToOriginalValue();
		//make sures that next time user wants to generate the shapefiles for hazus
		//he would have to pull up the control panel again and punch the button.
		hazusControl.setGenerateShapeFilesForHazus(false);
		//running the garbage collector to collect the objects
		System.gc();
	}


	/**
	 * This function sets the Gridded region Sites and the type of plot user wants to see
	 * IML@Prob or Prob@IML and it value.
	 * This function also gets the selected AttenuationRelationships in a ArrayList and their
	 * corresponding relative wts.
	 * This function also gets the mode of map calculation ( on server or on local machine)
	 */
	public void getGriddedSitesMapTypeAndSelectedAttenRels() throws
	RegionConstraintException, RuntimeException {
		//gets the IML or Prob selected value
		getIMLorProb();

		//gets the map data calc option
		if (calcControl != null) {
			String mapCalcOption = calcControl.getMapCalculationOption();
			//checks if the user wants to do the calc. on his local system or on the server.
			if (mapCalcOption.equals(GMTMapCalcOptionControl.USE_LOCAL))
				calculationFromServer = false;
			else
				calculationFromServer = true;
		}
		//get the site values for each site in the gridded region
		getGriddedRegionSites();

		//selected IMRs Wts
		attenRelWts = imrGuiBean.getSelectedIMR_Weights();
		//selected IMR's
		attenRel = imrGuiBean.getSelectedIMRs();
	}

	protected void addButton_actionPerformed(ActionEvent e) {


		addButton.setEnabled(false);
		calcProgress = new CalcProgressBar("ScenarioShakeMapApp","Initializing ShakeMap Calculation");
		//get the updated EqkRupture from Rupture Gui Bean
		getEqkRupture();
		//gets the metadata as soon as the user presses the button to make map.
		mapParametersInfo = getMapParametersInfoAsHTML();

		//sets the Gridded region Sites and the type of plot user wants to see
		//IML@Prob or Prob@IML and it value.


		try {
			getGriddedSitesMapTypeAndSelectedAttenRels();
		}
		catch (RegionConstraintException ee) {
			step = 0;
			/*ExceptionWindow bugWindow = new ExceptionWindow(this, ee,
          mapParametersInfo);
      bugWindow.setVisible(true);
      bugWindow.pack();*/

			JOptionPane.showMessageDialog(this, ee.getMessage(), "Input Error",
					JOptionPane.ERROR_MESSAGE);
			ee.printStackTrace();
			addButton.setEnabled(true);
			return;
		}
		catch (RuntimeException ee) {
			JOptionPane.showMessageDialog(this, ee.getMessage(), "Server Problem",
					JOptionPane.INFORMATION_MESSAGE);
			addButton.setEnabled(true);
			return;
		}




		// this function will get the selected IMT parameter and set it in IMT
		imrGuiBean.setIMT();

		timer = new Timer(200, new ActionListener() {
			public void actionPerformed(ActionEvent evt) {
				if(step == 1)
					calcProgress.setProgressMessage("Computing the ShakeMap Data ...");
				else if(step == 2)
					calcProgress.setProgressMessage("Generating the ShakeMap Image ...");
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
	 * when the generate Map button is pressed
	 */
	protected void addButton() throws RegionConstraintException, ParameterException,
	RuntimeException {
		timer.start();
		step = 1;
		generateShakeMap(attenRel,attenRelWts,imrGuiBean.getSelectedIMT());
		//sets the region coordinates for the GMT using the MapGuiBean
		setRegionForGMT();
		++step;

		String label = getMapLabel();
		if(!calculationFromServer) //if the calculation are to be done on the local system
			mapGuiBean.makeMap(xyzDataSet,eqkRupture,label,mapParametersInfo);
		else //if calculation are to be done on the server
			mapGuiBean.makeMap(serverXYZDataSetFilePath,eqkRupture,label,mapParametersInfo);
		//running the garbage collector to collect the objects
		System.gc();
		step =0;
	}

	/**
	 *
	 * @returns the Map label based on the selected Map Type( Prob@IML or IML@Prob)
	 */
	protected String getMapLabel(){
		//making the map
		String label;

		if(probAtIML)
			label="Prob";
		else
			label=imrGuiBean.getSelectedIMT();
		return label;
	}


	/**
	 *
	 * @returns the Adjustable parameters for the ScenarioShakeMap calculator
	 */
	public ParameterList getCalcAdjustableParams(){
		return shakeMapCalc.getAdjustableParams();
	}


	/**
	 *
	 * @returns the Metadata string for the Calculation Settings Adjustable Params
	 */
	public String getCalcParamMetadataString(){
		return getCalcAdjustableParams().getParameterListMetadataString();
	}


	/**
	 * Initialize the items to be added to the control list
	 */
	protected void initControlList() {
		controlPanels = new ArrayList<ControlPanel>();
		
		controlComboBox.addItem(CONTROL_PANELS);
		
		/*		Regions of Interest Control		*/
		controlComboBox.addItem(RegionsOfInterestControlPanel.NAME);
		controlPanels.add(new RegionsOfInterestControlPanel(this, this.sitesGuiBean));
		
		/*		Hazus Control					*/
		controlComboBox.addItem(GenerateHazusControlPanelForSingleMultipleIMRs.NAME);
		controlPanels.add(new GenerateHazusControlPanelForSingleMultipleIMRs(this,this));
		
		/*		Puente Hills Control			*/
		controlComboBox.addItem(PuenteHillsScenarioControlPanelUsingEqkRuptureCreation.NAME);
		controlPanels.add(new PuenteHillsScenarioControlPanelUsingEqkRuptureCreation(erfGuiBean,imrGuiBean,
						sitesGuiBean,mapGuiBean, this));
		
		/*		San Andreas Control				*/
		controlComboBox.addItem(SanAndreasScenarioControlPanel.NAME);
		controlPanels.add(new SanAndreasScenarioControlPanel(erfGuiBean,imrGuiBean,
				sitesGuiBean,mapGuiBean, this));
		
		/*		IM Event Set Scen Control		*/
		controlComboBox.addItem(IM_EventSetCEA_ControlPanel.NAME);
		controlPanels.add(new IM_EventSetCEA_ControlPanel(erfGuiBean,imrGuiBean,
				sitesGuiBean,mapGuiBean, this));
		
		/*		Map Calc Control				*/
		// this really isn't applicable anymore
//		controlComboBox.addItem(GMTMapCalcOptionControl.NAME);
//		controlPanels.add(new GMTMapCalcOptionControl(this));
		
		/*		Calc Params Control				*/
		controlComboBox.addItem(CalculationSettingsControlPanel.NAME);
		controlPanels.add(new CalculationSettingsControlPanel(this,this));
	}
	
	protected void showControlPanel(String controlName) {
		ControlPanel control = (ControlPanel)ListUtils.getObjectByName(controlPanels, controlName);
		if (control == null)
			throw new NullPointerException("Control Panel '" + controlName + "' not found!");
		showControlPanel(control);
	}
	
	protected void showControlPanel(ControlPanel control) {
		control.showControlPanel();
	}

	/**
	 * This function is called when controls pick list is chosen
	 * @param e
	 */
	protected void controlComboBox_actionPerformed(ActionEvent e) {
		if (controlComboBox.getItemCount() <= 0)
			return;
		if (controlComboBox.getSelectedIndex() == 0)
			return;
		String selectedControl = controlComboBox.getSelectedItem().toString();
		showControlPanel(selectedControl);
		
		controlComboBox.setSelectedItem(CONTROL_PANELS);
	}

	/**
	 *
	 * @returns the selected Attenuationrelationship model
	 */
	public ArrayList getSelectedAttenuationRelationships(){
		attenRel = imrGuiBean.getSelectedIMRs();
		return attenRel;
	}

	/**
	 *
	 * @returns the selected AttenuationRelationship wts
	 */
	public ArrayList getSelectedAttenuationRelationshipsWts(){
		attenRelWts = imrGuiBean.getSelectedIMR_Weights();
		return attenRelWts;
	}

	/**
	 *
	 * @returns the String containing the values selected for different parameters
	 */
	public String getMapParametersInfoAsHTML(){

		String imrMetadata = "IMR Param List:<br>\n " +
		"---------------<br>\n";


		//if the Hazus Control for Sceario is selected the get the metadata for IMT from there
		if(hazusControl!=null && hazusControl.isGenerateShapeFilesForHazus())
			imrMetadata +=imrGuiBean.getIMR_ParameterListMetadataString()+hazusControl.getIMT_Metadata()+"\n";
		else
			imrMetadata += imrGuiBean.getIMR_ParameterListMetadataString()+imrGuiBean.getIMT_ParameterListMetadataString()+"\n";

		//getting the metadata for the Calculation setting Params
		String calculationSettingsParamsMetadata = "<br><br>Calculation Param List:<br>\n "+
		"------------------<br>\n"+getCalcParamMetadataString()+"\n";

		return imrMetadata+
		"<br><br>Region Param List: <br>\n"+
		"----------------<br>\n"+
		sitesGuiBean.getVisibleParameters().getParameterListMetadataString()+"\n"+
		erfGuiBean.getParameterListMetadataString()+"\n"+
		"<br><br>TimeSpan Param List: <br>\n"+
		"--------------------<br>\n"+
		erfGuiBean.getTimespanMetadataString()+"\n"+
		"<br><br>GMT Param List: <br>\n"+
		"--------------------<br>\n"+
		mapGuiBean.getVisibleParameters().getParameterListMetadataString()+"\n"+
		calculationSettingsParamsMetadata;
	}
	
	public void imrChange(
			ScalarIMRChangeEvent event) {
		siteDataGUIBean.setIMR(event.getNewIMRs());
	}



}
