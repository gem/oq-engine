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

package org.opensha.sra.gui;

import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Component;
import java.awt.Dimension;
import java.awt.FlowLayout;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.SystemColor;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.rmi.RemoteException;
import java.util.ArrayList;

import javax.swing.BorderFactory;
import javax.swing.ImageIcon;
import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JCheckBoxMenuItem;
import javax.swing.JComboBox;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JMenu;
import javax.swing.JMenuBar;
import javax.swing.JMenuItem;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JSplitPane;
import javax.swing.JTabbedPane;
import javax.swing.JToolBar;
import javax.swing.Timer;
import javax.swing.UIManager;
import javax.swing.border.BevelBorder;
import javax.swing.border.Border;

import org.apache.commons.lang.SystemUtils;
import org.jfree.data.Range;
import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.calc.HazardCurveCalculator;
import org.opensha.sha.calc.HazardCurveCalculatorAPI;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.earthquake.EqkRupForecastBaseAPI;
import org.opensha.sha.gui.beans.ERF_GuiBean;
import org.opensha.sha.gui.beans.IMR_GuiBean;
import org.opensha.sha.gui.beans.IMR_GuiBeanAPI;
import org.opensha.sha.gui.beans.Site_GuiBean;
import org.opensha.sha.gui.controls.CurveDisplayAppAPI;
import org.opensha.sha.gui.controls.PEER_TestCaseSelectorControlPanel;
import org.opensha.sha.gui.controls.PlotColorAndLineTypeSelectorControlPanel;
import org.opensha.sha.gui.controls.SetMinSourceSiteDistanceControlPanel;
import org.opensha.sha.gui.controls.SetSiteParamsFromWebServicesControlPanel;
import org.opensha.sha.gui.controls.SitesOfInterestControlPanel;
import org.opensha.sha.gui.controls.XY_ValuesControlPanel;
import org.opensha.sha.gui.infoTools.ButtonControlPanel;
import org.opensha.sha.gui.infoTools.ButtonControlPanelAPI;
import org.opensha.sha.gui.infoTools.CalcProgressBar;
import org.opensha.sha.gui.infoTools.ExceptionWindow;
import org.opensha.sha.gui.infoTools.GraphPanel;
import org.opensha.sha.gui.infoTools.GraphPanelAPI;
import org.opensha.sha.gui.infoTools.GraphWindow;
import org.opensha.sha.gui.infoTools.GraphWindowAPI;
import org.opensha.sha.gui.infoTools.IMT_Info;
import org.opensha.sha.gui.infoTools.PlotCurveCharacterstics;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;

import org.opensha.sra.calc.LossCurveCalculator;
import org.opensha.sra.vulnerability.AbstractVulnerability;
import org.opensha.sra.gui.components.GuiBeanAPI;
import org.opensha.sra.gui.components.VulnerabilityBean;



/**
 * <p>Title: HazardCurveServerModeApplication</p>
 * <p>Description: This application computes Hazard Curve for selected
 * AttenuationRelationship model , Site and Earthquake Rupture Forecast (ERF)model.
 * This computed Hazard curve is shown in a panel using JFreechart.
 * This application works with/without internet connection.  If user using this
 * application has network connection then it creates the instances of ERF on server
 * and make all calls to server for any forecast updation. All the computation
 * in this application is done using the server. Once the computations complete, it
 * returns back the result.
 * All the server client relationship has been established using RMI, which allows
 * to make simple calls to the server similar to if things are existing on user's
 * own machine.
 * If network connection is not available to user then it will create all the
 * objects on users local machine and do all computation there itself.</p>
 * @author Nitin Gupta and Vipin Gupta
 * Date : Sept 23 , 2002
 * @version 1.0
 */

public class LossEstimationApplication extends JFrame
implements Runnable,  ParameterChangeListener,
ButtonControlPanelAPI,GraphPanelAPI,GraphWindowAPI,CurveDisplayAppAPI,
IMR_GuiBeanAPI{

	/**
	 * Name of the class
	 */
	private final static String C = "LossEstimationApplication";
	// for debug purpose
	protected final static boolean D = false;



	/**
	 *  The object class names for all the supported Eqk Rup Forecasts
	 */
	public final static String WGCEP_AVG_UCERF_2_CLASS_NAME="org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.MeanUCERF2.MeanUCERF2";
	public final static String FRANKEL_ADJ_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.Frankel96.Frankel96_AdjustableEqkRupForecast";
	public final static String FRANKEL02_ADJ_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.Frankel02.Frankel02_AdjustableEqkRupForecast";
	public final static String WGCEP_UCERF1_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF1.WGCEP_UCERF1_EqkRupForecast";
	public final static String WGCEP_UCERF_2_Final_CLASS_NAME="org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.UCERF2";
	//public final static String STEP_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.step.STEP_EqkRupForecast";
	//public final static String STEP_ALASKA_ERF_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.step.STEP_AlaskanPipeForecast";
	public final static String POISSON_FAULT_ERF_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.FloatingPoissonFaultERF";
	public final static String SIMPLE_FAULT_ERF_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.PoissonFaultERF";
	public final static String POINT_SRC_FORECAST_CLASS_NAME="org.opensha.sha.earthquake.rupForecastImpl.PointSourceERF";
	public final static String POINT2MULT_VSS_FORECAST_CLASS_NAME="org.opensha.sha.earthquake.rupForecastImpl.Point2MultVertSS_Fault.Point2MultVertSS_FaultERF";
	public final static String WG02_ERF_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.WG02.WG02_EqkRupForecast";




	// instances of the GUI Beans which will be shown in this applet
	protected ERF_GuiBean erfGuiBean;
	protected IMR_GuiBean imrGuiBean;
	protected Site_GuiBean siteGuiBean;
	protected VulnerabilityBean vulnBean;



	//instance for the ButtonControlPanel
	ButtonControlPanel buttonControlPanel;

	//instance of the GraphPanel (window that shows all the plots)
	GraphPanel graphPanel;

	//instance of the GraphWindow to pop up when the user wants to "Peel-Off" curves;
	GraphWindow graphWindow;

	//X and Y Axis  when plotting tha Curves Name
	protected String xAxisName;
	protected String yAxisName;


	// Strings for control pick list
	protected final static String CONTROL_PANELS = "Control Panels";

	protected final static String DISTANCE_CONTROL = "Max Source-Site Distance";
	protected final static String SITES_OF_INTEREST_CONTROL = "Sites of Interest";
	protected final static String CVM_CONTROL = "Set Site Params from Web Services";

	protected final static String XY_Values_Control = "Set external XY dataset";


	// objects for control panels
	protected PEER_TestCaseSelectorControlPanel peerTestsControlPanel;
	protected SetMinSourceSiteDistanceControlPanel distanceControlPanel;
	protected SitesOfInterestControlPanel sitesOfInterest;
	protected SetSiteParamsFromWebServicesControlPanel cvmControlPanel;

	protected XY_ValuesControlPanel xyPlotControl;


	private Insets plotInsets = new Insets( 4, 10, 4, 4 );

	private Border border1;


	//log flags declaration
	private boolean xLog =false;
	private boolean yLog =false;

	// default insets
	protected Insets defaultInsets = new Insets( 4, 4, 4, 4 );

	// height and width of the applet
	protected final static int W = 1100;
	protected final static int H = 820;

	/**
	 * List of ArbitrarilyDiscretized functions and Weighted funstions
	 */
	protected ArrayList functionList = new ArrayList();


	/**
	 * these four values save the custom axis scale specified by user
	 */
	private double minXValue;
	private double maxXValue;
	private  double minYValue;
	private double maxYValue;
	private boolean customAxis = false;



	// PEER Test Cases
	protected String TITLE = new String("Loss Curves");


	private JPanel jPanel1 = new JPanel();
	private Border border2;
	private final static Dimension COMBO_DIM = new Dimension( 180, 30 );
	private final static Dimension BUTTON_DIM = new Dimension( 80, 20 );
	private Border border3;
	private Border border4;
	private Border border5;
	private Border border6;
	private Border border7;
	private Border border8;



	private JLabel openshaImgLabel = new JLabel(new ImageIcon(FileUtils.loadImage("logos/PoweredByOpenSHA_Agua.jpg")));
	private JLabel usgsImgLabel = new JLabel(new ImageIcon(FileUtils.loadImage("logos/usgs_resrisk.gif")));
	private JLabel riskAgoraImgLabel = new JLabel(new ImageIcon(FileUtils.loadImage("logos/AgoraOpenRisk.jpg")));

	//static string for the OPENSHA website
	private final static String OPENSHA_WEBSITE="http://www.OpenSHA.org";

	JSplitPane topSplitPane = new JSplitPane();
	JButton clearButton = new JButton();
	JPanel buttonPanel = new JPanel();
	JCheckBox progressCheckBox = new JCheckBox();
	JButton addButton = new JButton();
	JComboBox controlComboBox = new JComboBox();
	JSplitPane chartSplit = new JSplitPane();
	JPanel panel = new JPanel();
	GridBagLayout gridBagLayout9 = new GridBagLayout();
	GridBagLayout gridBagLayout8 = new GridBagLayout();
	JSplitPane imrSplitPane = new JSplitPane();
	GridBagLayout gridBagLayout5 = new GridBagLayout();

	JPanel sitePanel = new JPanel();
	JPanel vulPanel = new JPanel();
	JSplitPane controlsSplit = new JSplitPane();
	JTabbedPane paramsTabbedPane = new JTabbedPane();
	JPanel erfPanel = new JPanel();
	GridBagLayout gridBagLayout15 = new GridBagLayout();
	GridBagLayout gridBagLayout13 = new GridBagLayout();
	GridBagLayout gridBagLayout12 = new GridBagLayout();
	JPanel imrPanel = new JPanel();
	GridBagLayout gridBagLayout10 = new GridBagLayout();
	BorderLayout borderLayout1 = new BorderLayout();

	//instances of various calculators
	HazardCurveCalculatorAPI calc;
	CalcProgressBar progressClass;
	protected CalcProgressBar startAppProgressClass;
	//timer threads to show the progress of calculations
	Timer timer;
	//calculation thead
	Thread calcThread;
	//checks to see if HazardCurveCalculations are done
	boolean isHazardCalcDone= false;
	private JButton peelOffButton = new JButton();
	JMenuBar menuBar = new JMenuBar();
	JMenu fileMenu = new JMenu();

	JMenuItem fileExitMenu = new JMenuItem();
	JMenuItem fileSaveMenu = new JMenuItem();
	JMenuItem filePrintMenu = new JCheckBoxMenuItem();
	JToolBar jToolBar = new JToolBar();

	JButton closeButton = new JButton();
	ImageIcon closeFileImage = new ImageIcon(FileUtils.loadImage("icons/closeFile.png"));

	JButton printButton = new JButton();
	ImageIcon printFileImage = new ImageIcon(FileUtils.loadImage("icons/printFile.jpg"));

	JButton saveButton = new JButton();
	ImageIcon saveFileImage = new ImageIcon(FileUtils.loadImage("icons/saveFile.jpg"));




	/**this boolean keeps track when to plot the new data on top of other and when to
	 *add to the existing data.
	 * If it is true then add new data on top of existing data, but if it is false
	 * then add new data to the existing data(this option only works if it is ERF_List).
	 * */
	boolean addData= true;
	protected JButton cancelCalcButton = new JButton();
	private FlowLayout flowLayout1 = new FlowLayout();

	protected final static String version = "0.0.12";

	protected final static String versionURL = "http://www.opensha.org/applications/hazCurvApp/HazardCurveApp_Version.txt";
	protected final static String appURL = "http://www.opensha.org/applications/hazCurvApp/HazardCurveServerModeApp.jar";
	protected final static String versionUpdateInfoURL = "http://www.opensha.org/applications/hazCurvApp/versionUpdate.html";




	//Initialize the applet
	public void init() {
		try {

			// initialize the control pick list
			initControlList();
			// initialize the GUI components
			startAppProgressClass = new CalcProgressBar("Starting Application", "Initializing Application .. Please Wait");
			jbInit();


			// initialize the various GUI beans
			initVulnerabilityGuiBean();
			initIMR_GuiBean();
			this.initSiteGuiBean();
			try{
				initERF_GuiBean();
			}catch(RuntimeException e){
				JOptionPane.showMessageDialog(this,"Connection to ERF's failed","Internet Connection Problem",
						JOptionPane.OK_OPTION);
				e.printStackTrace();
				startAppProgressClass.dispose();
				System.exit(0);
			}
		}
		catch(Exception e) {
			ExceptionWindow bugWindow = new ExceptionWindow(this,e,"Exception occured while creating the GUI.\n"+
			"No Parameters have been set");
			bugWindow.setVisible(true);
			bugWindow.pack();
			//e.printStackTrace();
		}
		startAppProgressClass.dispose();
		((JPanel)getContentPane()).updateUI();
	}

	//Component initialization
	protected void jbInit() throws Exception {
		border1 = BorderFactory.createLineBorder(SystemColor.controlText,1);
		border2 = BorderFactory.createLineBorder(SystemColor.controlText,1);
		border3 = BorderFactory.createEmptyBorder();
		border4 = BorderFactory.createLineBorder(SystemColor.controlText,1);
		border5 = BorderFactory.createLineBorder(SystemColor.controlText,1);
		border6 = BorderFactory.createBevelBorder(BevelBorder.RAISED,Color.white,Color.white,new Color(98, 98, 112),new Color(140, 140, 161));
		border7 = BorderFactory.createBevelBorder(BevelBorder.RAISED,Color.white,Color.white,new Color(98, 98, 112),new Color(140, 140, 161));
		border8 = BorderFactory.createBevelBorder(BevelBorder.RAISED,Color.white,Color.white,new Color(98, 98, 112),new Color(140, 140, 161));

		this.getContentPane().setLayout(borderLayout1);



		fileMenu.setText("File");
		fileExitMenu.setText("Exit");
		fileSaveMenu.setText("Save");
		filePrintMenu.setText("Print");

		fileExitMenu.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				fileExitMenu_actionPerformed(e);
			}
		});

		fileSaveMenu.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				fileSaveMenu_actionPerformed(e);
			}
		});

		filePrintMenu.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				filePrintMenu_actionPerformed(e);
			}
		});

		closeButton.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent actionEvent) {
				closeButton_actionPerformed(actionEvent);
			}
		});
		printButton.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent actionEvent) {
				printButton_actionPerformed(actionEvent);
			}
		});
		saveButton.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent actionEvent) {
				saveButton_actionPerformed(actionEvent);
			}
		});


		menuBar.add(fileMenu);
		fileMenu.add(fileSaveMenu);
		fileMenu.add(filePrintMenu);
		fileMenu.add(fileExitMenu);

		setJMenuBar(menuBar);
		closeButton.setIcon(closeFileImage);
		closeButton.setToolTipText("Exit Application");
		Dimension d = closeButton.getSize();
		jToolBar.add(closeButton);
		printButton.setIcon(printFileImage);
		printButton.setToolTipText("Print Graph");
		printButton.setSize(d);
		jToolBar.add(printButton);
		saveButton.setIcon(saveFileImage);
		saveButton.setToolTipText("Save Graph as image");
		saveButton.setSize(d);
		jToolBar.add(saveButton);
		jToolBar.setFloatable(false);

		this.getContentPane().add(jToolBar, BorderLayout.NORTH);

		jPanel1.setLayout(gridBagLayout10);

		//creating the Object the GraphPaenl class
		graphPanel = new GraphPanel(this);

		jPanel1.setBackground(Color.white);
		jPanel1.setBorder(border4);
		jPanel1.setMinimumSize(new Dimension(959, 600));
		jPanel1.setPreferredSize(new Dimension(959, 600));

		//loading the OpenSHA Logo

		topSplitPane.setOrientation(JSplitPane.VERTICAL_SPLIT);

		clearButton.setText("Clear Plot");
		clearButton.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				clearButton_actionPerformed(e);
			}
		});

		buttonPanel.setMinimumSize(new Dimension(568, 20));
		buttonPanel.setLayout(flowLayout1);

		progressCheckBox.setFont(new java.awt.Font("Dialog", 1, 12));

		progressCheckBox.setSelected(true);
		progressCheckBox.setText("Show Progress Bar");

		addButton.setText("Compute");
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
		panel.setLayout(gridBagLayout9);
		panel.setBackground(Color.white);
		panel.setBorder(border5);
		panel.setMinimumSize(new Dimension(0, 0));
		imrSplitPane.setOrientation(JSplitPane.VERTICAL_SPLIT);
		imrSplitPane.setBottomComponent(imrPanel);
		imrSplitPane.setTopComponent(vulPanel);

		sitePanel.setLayout(gridBagLayout13);
		sitePanel.setBackground(Color.white);
		vulPanel.setLayout(gridBagLayout8);
		vulPanel.setBackground(Color.white);
		controlsSplit.setDividerSize(5);
		erfPanel.setLayout(gridBagLayout5);
		erfPanel.setBackground(Color.white);
		erfPanel.setBorder(border2);
		erfPanel.setMaximumSize(new Dimension(2147483647, 10000));
		erfPanel.setMinimumSize(new Dimension(2, 300));
		erfPanel.setPreferredSize(new Dimension(2, 300));
		imrPanel.setLayout(gridBagLayout15);
		imrPanel.setBackground(Color.white);
		chartSplit.setLeftComponent(panel);
		chartSplit.setRightComponent(paramsTabbedPane);


		peelOffButton.setText("Peel Off");
		peelOffButton.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				peelOffButton_actionPerformed(e);
			}
		});


		/*imgLabel.addMouseListener(new java.awt.event.MouseAdapter() {
      public void mouseClicked(MouseEvent e) {
        imgLabel_mouseClicked(e);
      }
    });*/
		cancelCalcButton.setText("Cancel");
		cancelCalcButton.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				cancelCalcButton_actionPerformed(e);
			}
		});
		this.getContentPane().add(jPanel1, BorderLayout.CENTER);
		jPanel1.add(topSplitPane,  new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(11, 4, 5, 6), 243, 231));

		//object for the ButtonControl Panel
		buttonControlPanel = new ButtonControlPanel(this);


		buttonPanel.add(controlComboBox, 0);
		buttonPanel.add(addButton, 1);
		buttonPanel.add(cancelCalcButton, 2);
		buttonPanel.add(clearButton, 3);
		buttonPanel.add(peelOffButton, 4);
		buttonPanel.add(progressCheckBox, 5);
		buttonPanel.add(buttonControlPanel, 6);
		buttonPanel.add(usgsImgLabel, 7);
		buttonPanel.add(openshaImgLabel, 8);
		buttonPanel.add(riskAgoraImgLabel,9);
		//making the cancel button not visible until user has started to do the calculation
		cancelCalcButton.setVisible(false);

		topSplitPane.add(chartSplit, JSplitPane.TOP);
		chartSplit.add(panel, JSplitPane.LEFT);
		chartSplit.add(paramsTabbedPane, JSplitPane.RIGHT);
		imrSplitPane.add(vulPanel, JSplitPane.TOP);
		imrSplitPane.add(imrPanel, JSplitPane.BOTTOM);
		controlsSplit.add(imrSplitPane, JSplitPane.LEFT);
		paramsTabbedPane.add(controlsSplit, "Vulnerabilty,IMR & Site");
		controlsSplit.add(sitePanel, JSplitPane.RIGHT);
		paramsTabbedPane.add(erfPanel, "ERF & Time Span");
		topSplitPane.add(buttonPanel, JSplitPane.BOTTOM);
		topSplitPane.setDividerLocation(590);
		imrSplitPane.setDividerLocation(100);

		controlsSplit.setDividerLocation(230);
		erfPanel.setLayout(gridBagLayout5);
		erfPanel.validate();
		erfPanel.repaint();
		chartSplit.setDividerLocation(590);
		this.setSize(W,H);
		Dimension dim = Toolkit.getDefaultToolkit().getScreenSize();
		this.setLocation((dim.width - this.getSize().width) / 2, 0);
		//EXIT_ON_CLOSE == 3
		this.setDefaultCloseOperation(3);
		this.setTitle("Loss Estimation Curve Application ");

	}

	//Main method
	public static void main(String[] args) {
		LossEstimationApplication applet = new LossEstimationApplication();

		applet.init();
		applet.setVisible(true);
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
	 *  Adds a feature to the GraphPanel attribute of the EqkForecastApplet object
	 */
	private void addGraphPanel() {

		// Starting
		String S = C + ": addGraphPanel(): ";
		graphPanel.drawGraphPanel(xAxisName,yAxisName,functionList,xLog,yLog,customAxis,TITLE,buttonControlPanel);
		togglePlot();
		//this.isIndividualCurves = false;
	}

	//checks if the user has plot the data window or plot window
	public void togglePlot(){
		panel.removeAll();
		graphPanel.togglePlot(buttonControlPanel);
		panel.add(graphPanel, new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ));
		panel.validate();
		panel.repaint();
	}

	/**
	 * this function is called when Add Graph button is clicked
	 * @param e
	 */
	void addButton_actionPerformed(ActionEvent e) {

		addButton();

	}


	/**
	 * Implementing the run method in the Runnable interface that creates a new thread
	 * to do Hazard Curve Calculation, this thread created is seperate from the
	 * timer thread, so that progress bar updation does not conflicts with Calculations.
	 */
	public void run() {
		try{
			computeHazardCurve();
			cancelCalcButton.setVisible(false);
			//disaggCalc = null;
			calcThread = null;
		}catch(Exception e){
			e.printStackTrace();
			ExceptionWindow bugWindow = new ExceptionWindow(this,e,getParametersInfoAsString());
			bugWindow.setVisible(true);
			bugWindow.pack();
		}

	}

	/**
	 * This method creates the HazardCurveCalc and Disaggregation Calc(if selected) instances.
	 * If the internet connection is available then it creates a remote instances of
	 * the calculators on server where the calculations take place, else
	 * calculations are performed on the user's own machine.
	 */
	protected void createCalcInstance(){
		try {
			calc = new HazardCurveCalculator();
		}
		catch (Exception ex) {
			ExceptionWindow bugWindow = new ExceptionWindow(this,
					ex, this.getParametersInfoAsString());
			bugWindow.setVisible(true);
			bugWindow.pack();
		}
	}

	/**
	 * this function is called to draw the graph
	 */
	protected void addButton() {
		setButtonsEnable(false);
		// do not show warning messages in IMR gui bean. this is needed
		// so that warning messages for site parameters are not shown when Add graph is clicked
		imrGuiBean.showWarningMessages(false);

		try{
			createCalcInstance();
		}catch(Exception e){
			setButtonsEnable(true);
			ExceptionWindow bugWindow = new ExceptionWindow(this,e,getParametersInfoAsString());
			bugWindow.setVisible(true);
			bugWindow.pack();
			e.printStackTrace();
		}

		// check if progress bar is desired and set it up if so
		if(this.progressCheckBox.isSelected())  {
			calcThread = new Thread(this);
			calcThread.start();
			timer = new Timer(200, new ActionListener() {
				public void actionPerformed(ActionEvent evt) {
					try{

						int totRupture = calc.getTotRuptures();
						int currRupture = calc.getCurrRuptures();
						boolean totCurCalculated = true;
						if(currRupture ==-1){
							progressClass.setProgressMessage("Please wait, calculating total rutures ....");
							totCurCalculated = false;
						}
						if(!isHazardCalcDone && totCurCalculated)
							progressClass.updateProgress(currRupture, totRupture);

						if (isHazardCalcDone) {
							timer.stop();
							progressClass.dispose();
							drawGraph();
						}
					}catch(Exception e){
						//e.printStackTrace();
						timer.stop();
						setButtonsEnable(true);
						ExceptionWindow bugWindow = new ExceptionWindow(getApplicationComponent(),e,getParametersInfoAsString());
						bugWindow.setVisible(true);
						bugWindow.pack();
					}
				}
			});
		}
		else {
			this.computeHazardCurve();
			this.drawGraph();
		}
	}


	/**
	 *
	 * @returns the application component
	 */
	protected Component getApplicationComponent(){
		return this;
	}

	/**
	 * to draw the graph
	 */
	protected void drawGraph() {
		// you can show warning messages now
		imrGuiBean.showWarningMessages(true);
		addGraphPanel();

	}

	/**
	 * plots the curves with defined color,line width and shape.
	 *
	 */
	public void plotGraphUsingPlotPreferences(){
		drawGraph();
	}


	/**
	 * this function is called when "clear plot" is selected
	 *
	 * @param e
	 */
	void clearButton_actionPerformed(ActionEvent e) {
		clearPlot(true);
	}

	/**
	 *  Clears the plot screen of all traces
	 */
	private void clearPlot(boolean clearFunctions) {

		if ( D )
			System.out.println( "Clearing plot area" );

		int loc = this.chartSplit.getDividerLocation();
		int newLoc = loc;

		if( clearFunctions){
			graphPanel.removeChartAndMetadata();
			panel.removeAll();
			functionList.clear();
		}
		customAxis = false;
		chartSplit.setDividerLocation( newLoc );
	}

	/**
	 * sets the range for X and Y axis
	 * @param xMin : minimum value for X-axis
	 * @param xMax : maximum value for X-axis
	 * @param yMin : minimum value for Y-axis
	 * @param yMax : maximum value for Y-axis
	 *
	 */
	public void setAxisRange(double xMin,double xMax, double yMin, double yMax) {
		minXValue=xMin;
		maxXValue=xMax;
		minYValue=yMin;
		maxYValue=yMax;
		this.customAxis=true;
		drawGraph();

	}

	/**
	 * set the auto range for the axis. This function is called
	 * from the AxisLimitControlPanel
	 */
	public void setAutoRange() {
		this.customAxis=false;
		drawGraph();
	}

	/*void imgLabel_mouseClicked(MouseEvent e) {
    try{
      this.getAppletContext().showDocument(new URL(OPENSHA_WEBSITE), "new_peer_win");
    }catch(java.net.MalformedURLException ee){
      JOptionPane.showMessageDialog(this,new String("No Internet Connection Available"),
                                    "Error Connecting to Internet",JOptionPane.OK_OPTION);
      return;
    }
  }*/


	/**
	 *  Any time a control paramater or independent paramater is changed
	 *  by the user in a GUI this function is called, and a paramater change
	 *  event is passed in. This function then determines what to do with the
	 *  information ie. show some paramaters, set some as invisible,
	 *  basically control the paramater lists.
	 *
	 * @param  event
	 */
	public void parameterChange( ParameterChangeEvent event ) {

		String S = C + ": parameterChange(): ";
		if ( D )  System.out.println( "\n" + S + "starting: " );

		String name1 = event.getParameterName();

		// if IMR selection changed, update the site parameter list and supported IMT
		if ( name1.equalsIgnoreCase(imrGuiBean.IMR_PARAM_NAME)) {
			ScalarIntensityMeasureRelationshipAPI imr = imrGuiBean.getSelectedIMR_Instance();
			siteGuiBean.replaceSiteParams(imr.getSiteParamsIterator());
			siteGuiBean.validate();
			siteGuiBean.repaint();
		}
		if(name1.equalsIgnoreCase(vulnBean.getParameter().getName())){
			AbstractVulnerability currentModel = vulnBean.getCurrentModel();
			String currentIMT = currentModel.getIMT();
			double currentPeriod = 0;
			if(currentIMT.equals(SA_Param.NAME))
				currentPeriod = currentModel.getPeriod();
			imrGuiBean.setIMRParamListAndEditor(currentIMT, currentIMT, currentPeriod, currentPeriod);
			ScalarIntensityMeasureRelationshipAPI imr = imrGuiBean.getSelectedIMR_Instance();
			siteGuiBean.replaceSiteParams(imr.getSiteParamsIterator());
			siteGuiBean.validate();
			siteGuiBean.repaint();
		} 
	}



	/**
	 * Function to make the buttons enable or disable in the application.
	 * It is used in application to disable the button in the buttons panel
	 * if some computation is already going on.
	 * @param b
	 */
	protected void setButtonsEnable(boolean b){
		addButton.setEnabled(b);
		clearButton.setEnabled(b);
		peelOffButton.setEnabled(b);
		buttonControlPanel.setEnabled(b);
		progressCheckBox.setEnabled(b);
	}




	/**
	 * Gets the probabilities functiion based on selected parameters
	 * this function is called when add Graph is clicked
	 */
	protected void computeHazardCurve() {

		//starting the calculation
		isHazardCalcDone = false;

		EqkRupForecastBaseAPI forecast = null;

		// get the selected forecast model
		try {

			// whether to show progress bar in case of update forecast
			erfGuiBean.showProgressBar(this.progressCheckBox.isSelected());
			//get the selected ERF instance
			forecast = erfGuiBean.getSelectedERF();
		}
		catch (Exception e) {
			e.printStackTrace();
			JOptionPane.showMessageDialog(this, e.getMessage(), "Incorrect Values",
					JOptionPane.ERROR_MESSAGE);
			setButtonsEnable(true);
			return;
		}
		if (this.progressCheckBox.isSelected()) {
			progressClass = new CalcProgressBar("Hazard-Curve Calc Status",
			"Beginning Calculation ");
			progressClass.displayProgressBar();
			timer.start();
		}

		AbstractVulnerability currentModel = this.vulnBean.getCurrentModel();
		String currentIMT = currentModel.getIMT();
		double currentPeriod = 0;
		if(currentIMT.equals(SA_Param.NAME))
			currentPeriod = currentModel.getPeriod();
		//    ArrayList<Double> currentIMLs = currentModel.getIMLVals();
		double[] currentIMLs = currentModel.getIMLValues();


		// get the selected IMR
		ScalarIntensityMeasureRelationshipAPI imr = imrGuiBean.getSelectedIMR_Instance();

		// make a site object to pass to IMR
		Site site = siteGuiBean.getSite();

		// calculate the hazard curve
		try {
			if (distanceControlPanel != null) calc.setMaxSourceDistance(
					distanceControlPanel.getDistance());
		}
		catch (Exception e) {
			setButtonsEnable(true);
			ExceptionWindow bugWindow = new ExceptionWindow(this, e,
					getParametersInfoAsString());
			bugWindow.setVisible(true);
			bugWindow.pack();
			e.printStackTrace();
		}

		ArbitrarilyDiscretizedFunc currentHazardCurve = calcHazardCurve(currentIMT,currentPeriod,currentIMLs,site,forecast,imr);
		/*ArbitrarilyDiscretizedFunc currentAnnualizedRates= null;
    try {
		currentAnnualizedRates = 
			(ArbitrarilyDiscretizedFunc)calc.getAnnualizedRates(currentHazardCurve, 
					forecast.getTimeSpan().getDuration());
		getAnnualizedPE(currentAnnualizedRates);
	} catch (RemoteException e) {
		e.printStackTrace();
	}*/
		LossCurveCalculator lCalc = new LossCurveCalculator();
		ArbitrarilyDiscretizedFunc lossFunc = lCalc.getLossCurve(currentHazardCurve, vulnBean.getCurrentModel());
		lossFunc.setInfo(this.getParametersInfoAsString());
		lossFunc.setName(vulnBean.getCurrentModel().getName());
		// set the X-axis label
		String imt = currentIMT;
		xAxisName = "Fractional Loss";
		yAxisName = "Prob. of Exceed.";

		this.functionList.add(lossFunc);
		isHazardCalcDone = true;
		setButtonsEnable(true);

	}

	/**
	 * Converts the Annualized Rate into Annualized Prob. exceed
	 * @param function
	 */
	private void getAnnualizedPE(ArbitrarilyDiscretizedFunc function){
		int num = function.getNum();
		for(int i=0;i<num;++i){
			double rate = function.getY(i);
			double pe = 1-Math.exp(-1*rate);
			function.set(i,pe);
		}
	}

	//  private ArbitrarilyDiscretizedFunc calcHazardCurve(String imt, double period, ArrayList<Double> imls,
	//		  Site site,EqkRupForecastBaseAPI forecast,ScalarIntensityMeasureRelationshipAPI imr){
	private ArbitrarilyDiscretizedFunc calcHazardCurve(String imt, double period, double[] imls,
			Site site,EqkRupForecastBaseAPI forecast,ScalarIntensityMeasureRelationshipAPI imr){
		// initialize the values in condProbfunc with log values as passed in hazFunction
		// intialize the hazard function
		ArbitrarilyDiscretizedFunc hazFunction = new ArbitrarilyDiscretizedFunc();
		initX_Values(hazFunction,imls,imt);
		imr.setIntensityMeasure(imt);
		imr.getParameter(PeriodParam.NAME).setValue(period);
		//	    ((AttenuationRelationship)imr).setIntensityMeasure(imt,period);
		//System.out.println("22222222HazFunction: "+hazFunction.toString());
		try {
			// calculate the hazard curve
			//eqkRupForecast = (EqkRupForecastAPI)FileUtils.loadObject("erf.obj");
			try {

				hazFunction = (ArbitrarilyDiscretizedFunc) calc.getHazardCurve(
						hazFunction, site,imr, (EqkRupForecastAPI) forecast);
			}
			catch (Exception e) {
				e.printStackTrace();
				setButtonsEnable(true);
			}
			hazFunction = toggleHazFuncLogValues(hazFunction,imls);
			hazFunction.setInfo(getParametersInfoAsString());
		}
		catch (RuntimeException e) {
			JOptionPane.showMessageDialog(this, e.getMessage(),
					"Parameters Invalid",
					JOptionPane.INFORMATION_MESSAGE);
			e.printStackTrace();
			setButtonsEnable(true);
			return null;
		}	
		return hazFunction;
	}

	/**
	 * set x values in log space for Hazard Function to be passed to IMR
	 * if the selected IMT are SA , PGA , PGV or FaultDispl
	 * It accepts 1 parameters
	 *
	 * @param originalFunc :  this is the function with X values set
	 */
	//  private void initX_Values(DiscretizedFuncAPI arb,ArrayList<Double> imls, String imt){
	private void initX_Values(DiscretizedFuncAPI arb,double[] imls, String imt){

		IMT_Info imtInfo = new IMT_Info();
		if (imtInfo.isIMT_LogNormalDist(imt)) {
			for(int i=0;i<imls.length;++i)
				arb.set(Math.log(imls[i]),1);

			//System.out.println("11111111111HazFunction: "+arb.toString());
		}
		else
			throw new RuntimeException("Unsupported IMT");
	}  

	/**
	 * set x values back from the log space to the original linear values
	 * for Hazard Function after completion of the Hazard Calculations
	 * if the selected IMT are SA , PGA or PGV
	 * It accepts 1 parameters
	 *
	 * @param hazFunction :  this is the function with X values set
	 */
	//  private ArbitrarilyDiscretizedFunc toggleHazFuncLogValues(ArbitrarilyDiscretizedFunc hazFunc,ArrayList<Double> imls){
	private ArbitrarilyDiscretizedFunc toggleHazFuncLogValues(ArbitrarilyDiscretizedFunc hazFunc,double[] imls){
		int numPoints = hazFunc.getNum();
		DiscretizedFuncAPI tempFunc = hazFunc.deepClone();
		hazFunc = new ArbitrarilyDiscretizedFunc();
		// take log only if it is PGA, PGV ,SA or FaultDispl
		for(int i=0;i<tempFunc.getNum();++i)
			hazFunc.set(imls[i],tempFunc.getY(i));

		return hazFunc;
	}



	/**
	 * Initialize the IMR Gui Bean
	 */
	protected void initIMR_GuiBean() {

		AbstractVulnerability currentModel = vulnBean.getCurrentModel();
		String currentIMT = currentModel.getIMT();
		double currentPeriod = 0;
		if(currentIMT.equals(SA_Param.NAME))
			currentPeriod = currentModel.getPeriod();

		imrPanel.removeAll();
		imrGuiBean = new IMR_GuiBean(this,currentIMT,currentIMT,currentPeriod,currentPeriod);
		imrGuiBean.getParameterEditor(imrGuiBean.IMR_PARAM_NAME).getParameter().addParameterChangeListener(this);
		// show this gui bean the JPanel
		imrPanel.add(this.imrGuiBean,new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0,
				GridBagConstraints.CENTER, GridBagConstraints.BOTH, defaultInsets, 0, 0 ));
		imrPanel.updateUI();
	}

	/**
	 * Initialize the Vulnerability Gui Bean
	 */
	private void initVulnerabilityGuiBean() {

		// create the Vulnerability Gui Bean object
		vulnBean = new VulnerabilityBean();
		vulnBean.getParameter().addParameterChangeListener(this);
		vulPanel.setLayout(gridBagLayout8);
		vulPanel.add((Component) vulnBean.getVisualization(GuiBeanAPI.APPLICATION),
				new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0,
						GridBagConstraints.CENTER,
						GridBagConstraints.BOTH,
						defaultInsets, 0, 0));
		vulPanel.updateUI();

	}

	/**
	 * Initialize the site gui bean
	 */
	protected void initSiteGuiBean() {

		// get the selected IMR
		ScalarIntensityMeasureRelationshipAPI imr = imrGuiBean.getSelectedIMR_Instance();
		// create the Site Gui Bean object
		siteGuiBean = new Site_GuiBean();
		siteGuiBean.addSiteParams(imr.getSiteParamsIterator());
		// show the sitebean in JPanel
		sitePanel.add(this.siteGuiBean, new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0,
				GridBagConstraints.CENTER, GridBagConstraints.BOTH, defaultInsets, 0, 0));
		sitePanel.updateUI();

	}


	/**
	 * Initialize the ERF Gui Bean
	 */
	protected void initERF_GuiBean() {

		if (erfGuiBean == null) {
			try {
				// create the ERF Gui Bean object
				ArrayList erf_Classes = new ArrayList();
				//adding the RMI based ERF's to the application
				//adding the client based ERF's to the application
				erf_Classes.add(FRANKEL_ADJ_FORECAST_CLASS_NAME);
				erf_Classes.add(WGCEP_AVG_UCERF_2_CLASS_NAME);
				erf_Classes.add(FRANKEL02_ADJ_FORECAST_CLASS_NAME);
				erf_Classes.add(WGCEP_UCERF1_CLASS_NAME);
				erf_Classes.add(WGCEP_UCERF_2_Final_CLASS_NAME);
				erf_Classes.add(POISSON_FAULT_ERF_CLASS_NAME);
				erf_Classes.add(SIMPLE_FAULT_ERF_CLASS_NAME);
				erf_Classes.add(POINT_SRC_FORECAST_CLASS_NAME);
				erf_Classes.add(POINT2MULT_VSS_FORECAST_CLASS_NAME);

				erfGuiBean = new ERF_GuiBean(erf_Classes);
				erfGuiBean.getParameter(erfGuiBean.ERF_PARAM_NAME).
				addParameterChangeListener(this);
			}
			catch (InvocationTargetException e) {
				e.printStackTrace();
				//throw new RuntimeException("Connection to ERF's failed");
			}
		}
		erfPanel.add(this.erfGuiBean, new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0,
				GridBagConstraints.CENTER, GridBagConstraints.BOTH, defaultInsets, 0, 0));
		erfPanel.updateUI();
	}






	/**
	 * Initialize the items to be added to the control list
	 */
	protected void initControlList() {
		controlComboBox.addItem(CONTROL_PANELS);
		controlComboBox.addItem(DISTANCE_CONTROL);
		controlComboBox.addItem(SITES_OF_INTEREST_CONTROL);
		controlComboBox.addItem(CVM_CONTROL);
		controlComboBox.addItem(XY_Values_Control);
	}

	/**
	 * This function is called when controls pick list is chosen
	 * @param e
	 */
	void controlComboBox_actionPerformed(ActionEvent e) {
		if(controlComboBox.getItemCount()<=0) return;
		String selectedControl = controlComboBox.getSelectedItem().toString();
		if(selectedControl.equalsIgnoreCase(this.DISTANCE_CONTROL))
			initDistanceControl();
		else if(selectedControl.equalsIgnoreCase(this.SITES_OF_INTEREST_CONTROL))
			initSitesOfInterestControl();
		else if(selectedControl.equalsIgnoreCase(this.CVM_CONTROL))
			initCVMControl();

		else if(selectedControl.equalsIgnoreCase(XY_Values_Control))
			this.initXYPlotSelectionControl();

		controlComboBox.setSelectedItem(this.CONTROL_PANELS);
	}




	/*
	 * This function allows user to specify the XY values to be added to the existing
	 * plot.
	 */
	private void initXYPlotSelectionControl(){
		if(xyPlotControl==null){
			xyPlotControl = new XY_ValuesControlPanel(this,this);
		}
		xyPlotControl.getComponent().setVisible(true);
	}

	/**
	 * Updates the IMT_GuiBean to reflect the chnaged IM for the selected AttenuationRelationship.
	 * This method is called from the IMR_GuiBean to update the application with the Attenuation's
	 * supported IMs.
	 *
	 */
	public void updateIM() {

	}



	/**
	 * Initialize the Min Source and site distance control.
	 * This function is called when user selects "Source Site Distance Control"
	 * from controls pick list
	 */
	private void initDistanceControl() {
		if(this.distanceControlPanel==null)
			distanceControlPanel = new SetMinSourceSiteDistanceControlPanel(this);
		distanceControlPanel.pack();
		distanceControlPanel.setVisible(true);
	}


	/**
	 * Initialize the Interesting sites control panel
	 * It will provide a pick list of interesting sites
	 */
	private void initSitesOfInterestControl() {
		if(this.sitesOfInterest==null)
			sitesOfInterest = new SitesOfInterestControlPanel(this, this.siteGuiBean);
		sitesOfInterest.getComponent().pack();
		sitesOfInterest.getComponent().setVisible(true);
	}

	/**
	 * Initialize the Interesting sites control panel
	 * It will provide a pick list of interesting sites
	 */
	private void initCVMControl() {
		if(this.cvmControlPanel==null)
			cvmControlPanel = new SetSiteParamsFromWebServicesControlPanel(this, this.imrGuiBean, this.siteGuiBean);
		cvmControlPanel.pack();
		cvmControlPanel.setVisible(true);
	}




	/**
	 *
	 * @returns the Range for the X-Axis
	 */
	public Range getX_AxisRange(){
		return graphPanel.getX_AxisRange();
	}

	/**
	 *
	 * @returns the Range for the Y-Axis
	 */
	public Range getY_AxisRange(){
		return graphPanel.getY_AxisRange();
	}



	/**
	 * Sets ArbitraryDiscretizedFunc inside list containing all the functions.
	 * @param function ArbitrarilyDiscretizedFunc
	 */
	public void addCurve(ArbitrarilyDiscretizedFunc function){
		functionList.add(function);
		ArrayList plotFeaturesList = getPlottingFeatures();
		plotFeaturesList.add(new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.CROSS_SYMBOLS,
				Color.BLACK,4.0,1));
		addGraphPanel();
	}



	/**
	 * tells the application if the xLog is selected
	 * @param xLog : boolean
	 */
	public void setX_Log(boolean xLog){
		this.xLog = xLog;
		drawGraph();
	}

	/**
	 * tells the application if the yLog is selected
	 * @param yLog : boolean
	 */
	public void setY_Log(boolean yLog){
		this.yLog = yLog;
		drawGraph();
	}


	/**
	 *
	 * @returns the boolean: Log for X-Axis Selected
	 */
	public boolean getXLog(){
		return xLog;
	}

	/**
	 *
	 * @returns the boolean: Log for Y-Axis Selected
	 */
	public boolean getYLog(){
		return yLog;
	}

	/**
	 *
	 * @returns boolean: Checks if Custom Axis is selected
	 */
	public boolean isCustomAxis(){
		return customAxis;
	}

	/**
	 *
	 * @returns the Min X-Axis Range Value, if custom Axis is choosen
	 */
	public double getMinX(){
		return minXValue;
	}

	/**
	 *
	 * @returns the Max X-Axis Range Value, if custom axis is choosen
	 */
	public double getMaxX(){
		return maxXValue;
	}

	/**
	 *
	 * @returns the Min Y-Axis Range Value, if custom axis is choosen
	 */
	public double getMinY(){
		return minYValue;
	}

	/**
	 *
	 * @returns the Max Y-Axis Range Value, if custom axis is choosen
	 */
	public double getMaxY(){
		return maxYValue;
	}


	/**
	 *
	 * @returns the X Axis Label
	 */
	public String getXAxisLabel(){
		return xAxisName;
	}

	/**
	 *
	 * @returns Y Axis Label
	 */
	public String getYAxisLabel(){
		return yAxisName;
	}

	/**
	 *
	 * @returns plot Title
	 */
	public String getPlotLabel(){
		return TITLE;
	}


	/**
	 *
	 * sets  X Axis Label
	 */
	public void setXAxisLabel(String xAxisLabel){
		xAxisName = xAxisLabel;
	}

	/**
	 *
	 * sets Y Axis Label
	 */
	public void setYAxisLabel(String yAxisLabel){
		yAxisName = yAxisLabel;
	}

	/**
	 *
	 * sets plot Title
	 */
	public void setPlotLabel(String plotTitle){
		TITLE = plotTitle;
	}

	/**
	 *
	 * @returns the String containing the values selected for different parameters
	 */
	public String getParametersInfoAsString(){
		return getMapParametersInfoAsHTML().replaceAll(
				"<br>",SystemUtils.LINE_SEPARATOR);
	}


	/**
	 *
	 * @returns the String containing the values selected for different parameters
	 */
	public String getMapParametersInfoAsHTML(){
		String imrMetadata;
		//for visible parameters
		imrMetadata = imrGuiBean.getVisibleParametersCloned().getParameterListMetadataString();

		double maxSourceSiteDistance;
		if (distanceControlPanel != null)
			maxSourceSiteDistance = distanceControlPanel.getDistance();
		else
			maxSourceSiteDistance = HazardCurveCalculator.MAX_DISTANCE_DEFAULT;

		return "<br>"+ "IMR Param List:" +"<br>"+
		"---------------"+"<br>"+
		imrMetadata+"<br><br>"+
		"Site Param List: "+"<br>"+
		"----------------"+"<br>"+
		siteGuiBean.getParameterListEditor().getVisibleParametersCloned().getParameterListMetadataString()+"<br><br>"+

		"Forecast Param List: "+"<br>"+
		"--------------------"+"<br>"+
		erfGuiBean.getERFParameterList().getParameterListMetadataString()+"<br><br>"+
		"TimeSpan Param List: "+"<br>"+
		"--------------------"+"<br>"+
		erfGuiBean.getSelectedERFTimespanGuiBean().getParameterListMetadataString()+"<br><br>"+
		"Max. Source-Site Distance = "+maxSourceSiteDistance;

	}

	/**
	 *
	 * @returns the List for all the ArbitrarilyDiscretizedFunctions and Weighted Function list.
	 */
	public ArrayList getCurveFunctionList(){
		return functionList;
	}



	/**
	 * Actual method implementation of the "Peel-Off"
	 * This function peels off the window from the current plot and shows in a new
	 * window. The current plot just shows empty window.
	 */
	protected void peelOffCurves(){
		graphWindow = new GraphWindow(this);
		clearPlot(true);
		graphWindow.setVisible(true);
	}



	/**
	 * Action method to "Peel-Off" the curves graph window in a seperate window.
	 * This is called when the user presses the "Peel-Off" window.
	 * @param e
	 */
	void peelOffButton_actionPerformed(ActionEvent e) {
		peelOffCurves();
	}

	/**
	 *
	 * @returns the list PlotCurveCharacterstics that contain the info about
	 * plotting the curve like plot line color , its width and line type.
	 */
	public ArrayList getPlottingFeatures(){
		return graphPanel.getCurvePlottingCharacterstic();
	}


	/**
	 * File | Exit action performed.
	 *
	 * @param actionEvent ActionEvent
	 */
	private void fileExitMenu_actionPerformed(ActionEvent actionEvent) {
		close();
	}

	/**
	 *
	 */
	private void close() {
		int option = JOptionPane.showConfirmDialog(this,
				"Do you really want to exit the application?\n" +
				"You will loose all unsaved data.",
				"Exit App",
				JOptionPane.OK_CANCEL_OPTION);
		if (option == JOptionPane.OK_OPTION)
			System.exit(0);
	}

	/**
	 * File | Exit action performed.
	 *
	 * @param actionEvent ActionEvent
	 */
	private void fileSaveMenu_actionPerformed(ActionEvent actionEvent) {
		try {
			save();
		}
		catch (IOException e) {
			JOptionPane.showMessageDialog(this, e.getMessage(), "Save File Error",
					JOptionPane.OK_OPTION);
			return;
		}
	}

	/**
	 * File | Exit action performed.
	 *
	 * @param actionEvent ActionEvent
	 */
	private void filePrintMenu_actionPerformed(ActionEvent actionEvent) {
		print();
	}

	/**
	 * Opens a file chooser and gives the user an opportunity to save the chart
	 * in PNG format.
	 *
	 * @throws IOException if there is an I/O error.
	 */
	public void save() throws IOException {
		graphPanel.save();
	}

	/**
	 * Creates a print job for the chart.
	 */
	public void print() {
		graphPanel.print(this);
	}

	public void closeButton_actionPerformed(ActionEvent actionEvent) {
		close();
	}

	public void printButton_actionPerformed(ActionEvent actionEvent) {
		print();
	}

	public void saveButton_actionPerformed(ActionEvent actionEvent) {
		try {
			save();
		}
		catch (IOException e) {
			JOptionPane.showMessageDialog(this, e.getMessage(), "Save File Error",
					JOptionPane.OK_OPTION);
			return;
		}
	}


	/**
	 * This function stops the hazard curve calculation if started, so that user does not
	 * have to wait for the calculation to finish.
	 * Note: This function has one advantage , it starts over the calculation again, but
	 * if user has not changed any other parameter for the forecast, that won't
	 * be updated, so saves time and memory for not updating the forecast everytime,
	 * cancel is pressed.
	 * @param e
	 */
	void cancelCalcButton_actionPerformed(ActionEvent e) {
		//stopping the Hazard Curve calculation thread
		calcThread.stop();
		calcThread = null;
		//close the progress bar for the ERF GuiBean that displays "Updating Forecast".
		erfGuiBean.closeProgressBar();
		//stoping the timer thread that updates the progress bar
		if(timer !=null && progressClass !=null){
			timer.stop();
			timer = null;
			progressClass.dispose();
		}
		//stopping the Hazard Curve calculations on server
		if(calc !=null){
			try{
				calc.stopCalc();
				calc = null;
			}catch(RemoteException ee){
				ExceptionWindow bugWindow = new ExceptionWindow(this,ee,getParametersInfoAsString());
				bugWindow.setVisible(true);
				bugWindow.pack();
			}
		}
		this.isHazardCalcDone = false;
		//making the buttons to be visible
		setButtonsEnable(true);
		cancelCalcButton.setVisible(false);
	}



	/**
	 * This returns the Earthquake Forecast GuiBean which allows the the cybershake
	 * control panel to set the forecast parameters from cybershake control panel,
	 * similar to what they are set when calculating cybershaks curves.
	 */
	public ERF_GuiBean getEqkRupForecastGuiBeanInstance(){
		return erfGuiBean;

	}


	/**
	 * This returns the Site Guibean using which allows to set the site locations
	 * in the OpenSHA application from cybershake control panel.
	 */
	public Site_GuiBean getSiteGuiBeanInstance() {
		return siteGuiBean;
	}

	/**
	 * Updates the Site_GuiBean to reflect the chnaged SiteParams for the selected AttenuationRelationship.
	 * This method is called from the IMR_GuiBean to update the application with the Attenuation's
	 * Site Params.
	 *
	 */
	public void updateSiteParams() {
		//get the selected IMR
		ScalarIntensityMeasureRelationshipAPI imr = imrGuiBean.getSelectedIMR_Instance();
		siteGuiBean.replaceSiteParams(imr.getSiteParamsIterator());
		siteGuiBean.validate();
		siteGuiBean.repaint();
	}

	@Override
	public String getSelectedIMT() {
		return null;
	}

	@Override
	public void setCurveXValues(ArbitrarilyDiscretizedFunc func) {
		throw new RuntimeException("Not applicable for application");
	}

	@Override
	public void setCurveXValues() {
		throw new RuntimeException("Not applicable for application");
	}
}
