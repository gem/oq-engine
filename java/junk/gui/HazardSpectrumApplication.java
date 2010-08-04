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
import java.awt.FlowLayout;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.SystemColor;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.MouseEvent;
import java.lang.reflect.InvocationTargetException;
import java.net.URL;
import java.rmi.RemoteException;
import java.util.ArrayList;
import java.util.ListIterator;

import javax.swing.BorderFactory;
import javax.swing.ImageIcon;
import javax.swing.JApplet;
import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JComboBox;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JSplitPane;
import javax.swing.JTabbedPane;
import javax.swing.Timer;
import javax.swing.UIManager;
import javax.swing.border.BevelBorder;
import javax.swing.border.Border;

import org.jfree.data.Range;
import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.data.function.DiscretizedFuncList;
import org.opensha.commons.gui.plot.jfreechart.DiscretizedFunctionXYDataSet;
import org.opensha.commons.param.DependentParameterAPI;
import org.opensha.commons.param.DoubleDiscreteParameter;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.calc.HazardCurveCalculator;
import org.opensha.sha.calc.disaggregation.DisaggregationCalculator;
import org.opensha.sha.earthquake.ERF_EpistemicList;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.EqkRupForecastBaseAPI;
import org.opensha.sha.gui.beans.ERF_GuiBean;
import org.opensha.sha.gui.beans.EqkRupSelectorGuiBean;
import org.opensha.sha.gui.beans.IMLorProbSelectorGuiBean;
import org.opensha.sha.gui.beans.IMR_GuiBean;
import org.opensha.sha.gui.beans.IMR_GuiBeanAPI;
import org.opensha.sha.gui.beans.Site_GuiBean;
import org.opensha.sha.gui.controls.AxisLimitsControlPanelAPI;
import org.opensha.sha.gui.controls.CurveDisplayAppAPI;
import org.opensha.sha.gui.controls.DisaggregationControlPanel;
import org.opensha.sha.gui.controls.ERF_EpistemicListControlPanel;
import org.opensha.sha.gui.controls.PEER_TestCaseSelectorControlPanel;
import org.opensha.sha.gui.controls.PlotColorAndLineTypeSelectorControlPanel;
import org.opensha.sha.gui.controls.PlottingOptionControl;
import org.opensha.sha.gui.controls.RunAll_PEER_TestCasesControlPanel;
import org.opensha.sha.gui.controls.SetMinSourceSiteDistanceControlPanel;
import org.opensha.sha.gui.controls.SetSiteParamsFromWebServicesControlPanel;
import org.opensha.sha.gui.controls.SitesOfInterestControlPanel;
import org.opensha.sha.gui.controls.X_ValuesInCurveControlPanel;
import org.opensha.sha.gui.infoTools.ButtonControlPanel;
import org.opensha.sha.gui.infoTools.ButtonControlPanelAPI;
import org.opensha.sha.gui.infoTools.CalcProgressBar;
import org.opensha.sha.gui.infoTools.GraphPanel;
import org.opensha.sha.gui.infoTools.GraphPanelAPI;
import org.opensha.sha.gui.infoTools.GraphWindow;
import org.opensha.sha.gui.infoTools.GraphWindowAPI;
import org.opensha.sha.gui.infoTools.IMT_Info;
import org.opensha.sha.gui.infoTools.PlotCurveCharacterstics;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;

/**
 * <p>Title: HazardSpectrumApplication</p>
 * <p>Description: </p>
 * @author Nitin Gupta and Vipin Gupta
 * Date : Sept 23 , 2002
 * @version 1.0
 */

public class HazardSpectrumApplication extends JApplet
implements Runnable, ParameterChangeListener, AxisLimitsControlPanelAPI,CurveDisplayAppAPI,
ButtonControlPanelAPI,GraphPanelAPI,GraphWindowAPI, IMR_GuiBeanAPI{

	/**
	 * Name of the class
	 */
	private final static String C = "Hazard Spectrum Applet";
	// for debug purpose
	private final static boolean D = false;


	/**
	 *  The object class names for all the supported Eqk Rup Forecasts
	 */
	public final static String POISSON_FAULT_ERF_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.FloatingPoissonFaultERF";
	public final static String PEER_AREA_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.PEER_TestCases.PEER_AreaForecast";
	public final static String PEER_NON_PLANAR_FAULT_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.PEER_TestCases.PEER_NonPlanarFaultForecast";
	public final static String PEER_MULTI_SOURCE_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.PEER_TestCases.PEER_MultiSourceForecast";
	public final static String PEER_LOGIC_TREE_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.PEER_TestCases.PEER_LogicTreeERF_List";
	public final static String FRANKEL_ADJ_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.Frankel96.Frankel96_AdjustableEqkRupForecast";
	public final static String FRANKEL2000_ADJ_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.Frankel02.Frankel02_AdjustableEqkRupForecast";
	public final static String STEP_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.step.STEP_EqkRupForecast";
	public final static String WG02_ERF_LIST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.WG02.WG02_ERF_Epistemic_List";
	public final static String STEP_ALASKA_ERF_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.step.STEP_AlaskanPipeForecast";
	public final static String WG02_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.WG02.WG02_EqkRupForecast";

	// instances of the GUI Beans which will be shown in this applet
	private ERF_GuiBean erfGuiBean;
	private IMR_GuiBean imrGuiBean;
	private IMLorProbSelectorGuiBean imlProbGuiBean;
	private Site_GuiBean siteGuiBean;
	private EqkRupSelectorGuiBean erfRupSelectorGuiBean;

	// Strings for control pick list
	private final static String CONTROL_PANELS = "Control Panels";
	//private final static String PEER_TEST_CONTROL = "PEER Test Case Selector";
	//private final static String DISAGGREGATION_CONTROL = "Disaggregation";
	private final static String EPISTEMIC_CONTROL = "ERF Epistemic Control";
	private final static String AXIS_CONTROL = "Axis Control";
	private final static String DISTANCE_CONTROL = "Max Source-Site Distance";
	private final static String SITES_OF_INTEREST_CONTROL = "Sites of Interest";
	private final static String CVM_CONTROL = "Set Site Params from CVM";
	private final static String X_VALUES_CONTROL = "Set X values for Hazard Spectrum Calc.";
	private final static String PLOTTING_OPTION = "Set new dataset plotting option";


	//Strings for choosing ERFGuiBean or ERF_RupSelectorGUIBean
	private final static String PROBABILISTIC = "Probabilistic";
	private final static String DETERMINISTIC = "Deterministic";

	//Static String to tell the IMT as the SA becuase it is the only supported IMT for this Application
	protected static String SA_NAME = "SA";
	private static String SA_PERIOD = "SA Period";


	//Axis Labels
	private static final String IML = "SA (g)";
	private static final String PROB_AT_EXCEED = "Probability of Exceedance";
	private static final String X_AXIS_LABEL = "Period (sec)";

	//ArrayList that stores the SA Period values for the IMR
	private ArrayList saPeriodVector ;
	//Total number of the SA Period Values
	private int numSA_PeriodVals;
	//Total number of the values for which we have ran the Hazard Curve
	private int numSA_PeriodValDone=0;

	//flag to check whether calculation for the Deterministic Model completed
	private boolean deterministicCalcDone=false;
	//flag to check whether Hazrda Curve Calc are done
	private boolean hazCalcDone = false;


	// objects for control panels
	private PEER_TestCaseSelectorControlPanel peerTestsControlPanel;
	private DisaggregationControlPanel disaggregationControlPanel;
	private ERF_EpistemicListControlPanel epistemicControlPanel;
	private SetMinSourceSiteDistanceControlPanel distanceControlPanel;
	private SitesOfInterestControlPanel sitesOfInterest;
	private SetSiteParamsFromWebServicesControlPanel cvmControlPanel;
	private X_ValuesInCurveControlPanel xValuesPanel;
	private RunAll_PEER_TestCasesControlPanel runAllPEER_Tests;
	private PlottingOptionControl plotOptionControl;

	// message string to be dispalayed if user chooses Axis Scale
	// without first clicking on "Add Graph"
	private final static String AXIS_RANGE_NOT_ALLOWED =
		new String("First Choose Add Graph. Then choose Axis Scale option");



	// mesage needed in case of show data if plot is not available
	private final static String NO_PLOT_MSG = "No Plot Data Available";

	private Insets plotInsets = new Insets( 4, 10, 4, 4 );

	private boolean isStandalone = false;
	private Border border1;


	//instance for the ButtonControlPanel
	ButtonControlPanel buttonControlPanel;

	//instance of the GraphPanel (window that shows all the plots)
	GraphPanel graphPanel;
	//instance of the GraphWindow to pop up when the user wants to "Peel-Off" curves;
	GraphWindow graphWindow;


	//X and Y Axis  when plotting tha Curves Name
	private String xAxisName;
	private String yAxisName;



	//log flags declaration
	private boolean xLog =false;
	private boolean yLog =false;

	// default insets
	private Insets defaultInsets = new Insets( 4, 4, 4, 4 );

	// height and width of the applet
	private final static int W = 1200;
	private final static int H = 750;

	/**
	 * FunctionList declared
	 */
	private DiscretizedFuncList totalProbFuncs = new DiscretizedFuncList();
	private DiscretizedFunctionXYDataSet data = new DiscretizedFunctionXYDataSet();

	/**
	 * List of ArbitrarilyDiscretized functions and Weighted funstions
	 */
	private ArrayList functionList = new ArrayList();

	//holds the ArbitrarilyDiscretizedFunc
	private ArbitrarilyDiscretizedFunc function;

	//instance to get the default IMT X values for the hazard Curve
	private IMT_Info imtInfo = new IMT_Info();

	// Create the x-axis and y-axis - either normal or log
	private org.jfree.chart.axis.NumberAxis xAxis = null;
	private org.jfree.chart.axis.NumberAxis yAxis = null;


	// variable needed for plotting Epistemic list
	private boolean isEqkList = false; // whther we are plottin the Eqk List
	private boolean isIndividualCurves = false; //to keep account that we are first drawing the individual curve for erf in the list
	private boolean isAllCurves = true; // whether to plot all curves

	// whether user wants to plot custom fractile
	private String fractileOption ;

	// whether avg is selected by the user
	private boolean avgSelected = false;

	//Variables required to update progress bar if ERF List is selected
	//total number of ERF's in list
	private int numERFsInEpistemicList =0;
	//index number of ERF for which Hazard Curve is being calculated
	private int currentERFInEpistemicListForHazardCurve =0;


	/**
	 * these four values save the custom axis scale specified by user
	 */
	private double minXValue;
	private double maxXValue;
	private  double minYValue;
	private double maxYValue;
	private boolean customAxis = false;

	//flags to check which X Values the user wants to work with: default or custom
	boolean useCustomX_Values = false;


	private GridBagLayout gridBagLayout4 = new GridBagLayout();
	private GridBagLayout gridBagLayout6 = new GridBagLayout();
	private GridBagLayout gridBagLayout7 = new GridBagLayout();
	private GridBagLayout gridBagLayout3 = new GridBagLayout();



	//flag to check for the disaggregation functionality
	private boolean disaggregationFlag= false;
	private String disaggregationString;

	// PEER Test Cases
	private String TITLE = new String("Hazard Spectra");

	// light blue color
	private Color lightBlue = new Color( 200, 200, 230 );

	/**
	 * for Y-log, 0 values will be converted to this small value
	 */
	private double Y_MIN_VAL = 1e-16;

	private boolean graphOn = false;
	private GridBagLayout gridBagLayout11 = new GridBagLayout();
	private JPanel jPanel1 = new JPanel();
	private GridBagLayout gridBagLayout2 = new GridBagLayout();
	private GridBagLayout gridBagLayout1 = new GridBagLayout();
	private Border border2;
	private final static String AUTO_SCALE = "Auto Scale";
	private final static String CUSTOM_SCALE = "Custom Scale";
	private final static Dimension COMBO_DIM = new Dimension( 180, 30 );
	private final static Dimension BUTTON_DIM = new Dimension( 80, 20 );
	private Border border3;
	private Border border4;
	private GridBagLayout gridBagLayout16 = new GridBagLayout();
	private Border border5;
	private Border border6;
	private Border border7;
	private Border border8;



	//images for the OpenSHA
	private final static String FRAME_ICON_NAME = "openSHA_Aqua_sm.gif";
	private final static String POWERED_BY_IMAGE = "PoweredBy.gif";

	//static string for the OPENSHA website
	private final static String OPENSHA_WEBSITE="http://www.OpenSHA.org";

	JSplitPane topSplitPane = new JSplitPane();
	JButton clearButton = new JButton();
	JLabel imgLabel = new JLabel();
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
	JSplitPane erfSplitPane = new JSplitPane();
	JPanel sitePanel = new JPanel();
	JPanel imtPanel = new JPanel();
	JSplitPane controlsSplit = new JSplitPane();
	JTabbedPane paramsTabbedPane = new JTabbedPane();
	JPanel erfPanel = new JPanel();
	GridBagLayout gridBagLayout15 = new GridBagLayout();
	GridBagLayout gridBagLayout13 = new GridBagLayout();
	GridBagLayout gridBagLayout12 = new GridBagLayout();
	JPanel imrPanel = new JPanel();
	GridBagLayout gridBagLayout10 = new GridBagLayout();
	BorderLayout borderLayout1 = new BorderLayout();
	HazardCurveCalculator calc;
	DisaggregationCalculator disaggCalc;
	CalcProgressBar progressClass;
	//CalcProgressBar disaggProgressClass;
	Timer timer;
	//Timer disaggTimer;
	JComboBox probDeterSelection = new JComboBox();
	private JButton peelOffButton = new JButton();
	private FlowLayout flowLayout1 = new FlowLayout();


	//Get command-line parameter value
	public String getParameter(String key, String def) {
		return isStandalone ? System.getProperty(key, def) :
			(getParameter(key) != null ? getParameter(key) : def);
	}

	//Construct the applet
	public HazardSpectrumApplication() {
		data.setFunctions(this.totalProbFuncs);
		// for Y-log, convert 0 values in Y axis to this small value
		data.setConvertZeroToMin(true,Y_MIN_VAL);
	}
	//Initialize the applet
	public void init() {
		try {

			// initialize the control pick list
			initControlList();
			//initialise the list to make selection whether to show ERF_GUIBean or ERF_RupSelectorGuiBean
			initProbOrDeterList();
			// initialize the GUI components
			jbInit();

			// initialize the various GUI beans
			initIMR_GuiBean();
			initSiteGuiBean();
			initImlProb_GuiBean();
			try{
				this.initERFSelector_GuiBean();
			}catch(RuntimeException e){
				JOptionPane.showMessageDialog(this,"Connection to ERF failed","Internet Connection Problem",
						JOptionPane.OK_OPTION);
				return;
			}
		}
		catch(Exception e) {
			e.printStackTrace();
		}
	}

	//Component initialization
	private void jbInit() throws Exception {
		border1 = BorderFactory.createLineBorder(SystemColor.controlText,1);
		border2 = BorderFactory.createLineBorder(SystemColor.controlText,1);
		border3 = BorderFactory.createEmptyBorder();
		border4 = BorderFactory.createLineBorder(SystemColor.controlText,1);
		border5 = BorderFactory.createLineBorder(SystemColor.controlText,1);
		border6 = BorderFactory.createBevelBorder(BevelBorder.RAISED,Color.white,Color.white,new Color(98, 98, 112),new Color(140, 140, 161));
		border7 = BorderFactory.createBevelBorder(BevelBorder.RAISED,Color.white,Color.white,new Color(98, 98, 112),new Color(140, 140, 161));
		border8 = BorderFactory.createBevelBorder(BevelBorder.RAISED,Color.white,Color.white,new Color(98, 98, 112),new Color(140, 140, 161));
		//this.getContentPane().setBackground(Color.white);
		this.setSize(new Dimension(1100, 670));
		this.getContentPane().setLayout(borderLayout1);


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
		imgLabel.setText("");
		imgLabel.setIcon(new ImageIcon(FileUtils.loadImage(this.POWERED_BY_IMAGE)));
		imgLabel.addMouseListener(new java.awt.event.MouseAdapter() {
			public void mouseClicked(MouseEvent e) {
				imgLabel_mouseClicked(e);
			}
		});
		//jCheckylog.setBackground(Color.white);
		//jCheckylog.setForeground(new Color(80, 80, 133));
		//buttonPanel.setBackground(Color.white);
		buttonPanel.setMinimumSize(new Dimension(568, 20));
		buttonPanel.setLayout(flowLayout1);
		//progressCheckBox.setBackground(Color.white);
		progressCheckBox.setFont(new java.awt.Font("Dialog", 1, 12));
		//progressCheckBox.setForeground(new Color(80, 80, 133));
		progressCheckBox.setSelected(true);
		progressCheckBox.setText("Show Progress Bar");
		addButton.setText("Compute");
		addButton.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				addButton_actionPerformed(e);
			}
		});
		// jCheckxlog.setBackground(Color.white);
		//jCheckxlog.setForeground(new Color(80, 80, 133));
		//controlComboBox.setBackground(new Color(200, 200, 230));
		//controlComboBox.setForeground(new Color(80, 80, 133));
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
		imrSplitPane.setBottomComponent(imtPanel);
		imrSplitPane.setTopComponent(imrPanel);
		erfSplitPane.setTopComponent(erfPanel);
		sitePanel.setLayout(gridBagLayout13);
		sitePanel.setBackground(Color.white);
		imtPanel.setLayout(gridBagLayout8);
		imtPanel.setBackground(Color.white);
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
		probDeterSelection.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				probDeterSelection_actionPerformed(e);
			}
		});
		peelOffButton.setText("Peel Off");
		peelOffButton.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				peelOffButton_actionPerformed(e);
			}
		});
		this.getContentPane().add(jPanel1, BorderLayout.CENTER);
		jPanel1.add(topSplitPane,  new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(11, 4, 5, 6), 243, 231));
		buttonPanel.add(probDeterSelection, null);
		buttonPanel.add(controlComboBox, null);
		buttonPanel.add(addButton, null);
		buttonPanel.add(clearButton, null);
		buttonPanel.add(peelOffButton, null);
		buttonPanel.add(progressCheckBox, null);
		buttonPanel.add(imgLabel, null);
		topSplitPane.add(chartSplit, JSplitPane.TOP);
		chartSplit.add(panel, JSplitPane.LEFT);
		chartSplit.add(paramsTabbedPane, JSplitPane.RIGHT);
		imrSplitPane.add(imrPanel, JSplitPane.TOP);
		imrSplitPane.add(imtPanel, JSplitPane.BOTTOM);
		controlsSplit.add(imrSplitPane, JSplitPane.LEFT);
		paramsTabbedPane.add(controlsSplit, "IMR, IML/Prob, & Site");
		controlsSplit.add(sitePanel, JSplitPane.RIGHT);
		paramsTabbedPane.add(erfSplitPane, "ERF & Time Span");
		erfSplitPane.add(erfPanel, JSplitPane.LEFT);
		topSplitPane.add(buttonPanel, JSplitPane.BOTTOM);
		topSplitPane.setDividerLocation(600);
		imrSplitPane.setDividerLocation(300);
		erfSplitPane.setDividerLocation(260);
		controlsSplit.setDividerLocation(260);
		erfPanel.validate();
		erfPanel.repaint();
		chartSplit.setDividerLocation(600);


	}
	//Start the applet
	public void start() {
	}

	//Stop the applet
	public void stop() {
	}

	//Destroy the applet
	public void destroy() {
	}

	//Get Applet information
	public String getAppletInfo() {
		return "Applet Information";
	}

	//Get parameter info
	public String[][] getParameterInfo() {
		return null;
	}

	//Main method
	public static void main(String[] args) {
		HazardSpectrumApplication applet = new HazardSpectrumApplication();
		applet.isStandalone = true;
		JFrame frame = new JFrame();
		//EXIT_ON_CLOSE == 3
		frame.setDefaultCloseOperation(3);
		frame.setTitle("Hazard Spectrum Applet");
		frame.getContentPane().add(applet, BorderLayout.CENTER);
		applet.init();
		applet.start();
		frame.setSize(W,H);
		Dimension d = Toolkit.getDefaultToolkit().getScreenSize();
		frame.setLocation((d.width - frame.getSize().width) / 2, (d.height - frame.getSize().height) / 2);
		frame.setVisible(true);
	}

	//static initializer for setting look & feel
	static {
		try {
			UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
			//UIManager.setLookAndFeel(UIManager.getCrossPlatformLookAndFeelClassName());
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


	public void run() {
		computeHazardCurve();
	}


	/**
	 * this function is called to draw the graph
	 */
	private void addButton() {
		// do not show warning messages in IMR gui bean. this is needed
		// so that warning messages for site parameters are not shown when Add graph is clicked
		imrGuiBean.showWarningMessages(false);
		try{
			calc = new HazardCurveCalculator();
		}catch(Exception e){
			e.printStackTrace();
		}
		// check if progress bar is desired and set it up if so
		if(this.progressCheckBox.isSelected())  {
			Thread t = new Thread(this);
			t.start();

			timer = new Timer(200, new ActionListener() {
				public void actionPerformed(ActionEvent evt) {
					try{
						if(calc.getCurrRuptures()!=-1){
							progressClass.updateProgress(numSA_PeriodValDone,numSA_PeriodVals);
						}
					}catch(Exception e){
						e.printStackTrace();
					}
					if(isIndividualCurves) {
						drawGraph();
						//isIndividualCurves = false;
					}
					if (hazCalcDone) {
						timer.stop();
						progressClass.dispose();
						drawGraph();
					}
				}
			});

			// timer for disaggregation progress bar
			/*disaggTimer = new Timer(500, new ActionListener() {
          public void actionPerformed(ActionEvent evt) {
            if(disaggCalc.getCurrRuptures()!=-1)
              disaggProgressClass.updateProgress(disaggCalc.getCurrRuptures(), disaggCalc.getTotRuptures());
            if (disaggCalc.done()) {
          // Toolkit.getDefaultToolkit().beep();
              disaggTimer.stop();
              disaggProgressClass.dispose();
            }
          }
        });*/
		}
		else {
			this.computeHazardCurve();
			this.drawGraph();
		}
	}

	/**
	 * to draw the graph
	 */
	private void drawGraph() {
		// you can show warning messages now
		imrGuiBean.showWarningMessages(true);
		addGraphPanel();
		setButtonsEnable(true);
	}

	/**
	 * plots the curves with defined color,line width and shape.
	 *
	 */
	public void plotGraphUsingPlotPreferences(){
		drawGraph();
	}




	/**
	 * when "show data" button is clicked
	 *
	 * @param e
	 */
	void toggleButton_actionPerformed(ActionEvent e) {
		this.togglePlot();
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
		graphPanel.removeChartAndMetadata();
		panel.removeAll();
		if( clearFunctions) {
			this.totalProbFuncs.clear();
		}

		chartSplit.setDividerLocation( newLoc );
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
		addGraphPanel();

	}

	/**
	 * set the auto range for the axis. This function is called
	 * from the AxisLimitControlPanel
	 */
	public void setAutoRange() {
		this.customAxis=false;
		addGraphPanel();
	}

	/**
	 * This function to specify whether disaggregation is selected or not
	 * @param isSelected : True if disaggregation is selected , else false
	 */
	public void setDisaggregationSelected(boolean isSelected) {
		disaggregationFlag = isSelected;
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
			//set the intensity measure for the IMR
			imr.setIntensityMeasure(SA_Param.NAME);
			//gets the SA Period Values for the IMR
			this.getSA_PeriodForIMR(imr);
			siteGuiBean.replaceSiteParams(imr.getSiteParamsIterator());
			siteGuiBean.validate();
			siteGuiBean.repaint();
		}
		if(name1.equalsIgnoreCase(ERF_GuiBean.ERF_PARAM_NAME)) {
			/* get the selected ERF
      NOTE : We have used erfGuiBean.getSelectedERF_Instance()INSTEAD OF
      erfGuiBean.getSelectedERF.
      Difference is that erfGuiBean.getSelectedERF_Instance() does not update
      the forecast while erfGuiBean.getSelectedERF updates the
			 */
			if(erfGuiBean !=null){

				controlComboBox.removeAllItems();
				this.initControlList();
				// add the Epistemic control panel option if Epistemic ERF is selected
				if(erfGuiBean.isEpistemicList()) {
					this.controlComboBox.addItem(EPISTEMIC_CONTROL);
					controlComboBox.setSelectedItem(EPISTEMIC_CONTROL);
				}
			}
		}
	}


	/**
	 * Gets the probabilities functiion based on selected parameters
	 * this function is called when add Graph is clicked
	 */
	private void computeHazardCurve() {

		//flag to initialise if Deterministic Model Calc have been completed
		deterministicCalcDone=false;

		//checks how many SA Periods has been completed
		this.numSA_PeriodValDone =0;

		//flag to check whether Hazard Curve Calc are done
		hazCalcDone = false;

		//gets the Label for the Y-axis for the earlier grph
		String oldY_AxisLabel="";
		if(totalProbFuncs.getYAxisName() !=null)
			oldY_AxisLabel = totalProbFuncs.getYAxisName();

		// get the selected IMR
		AttenuationRelationship imr = (AttenuationRelationship)imrGuiBean.getSelectedIMR_Instance();

		// make a site object to pass to IMR
		Site site = siteGuiBean.getSite();

		// intialize the hazard function
		ArbitrarilyDiscretizedFunc hazFunction = new ArbitrarilyDiscretizedFunc();
		ArbitrarilyDiscretizedFunc tempHazFunction = new ArbitrarilyDiscretizedFunc();

		//what selection does the user have made, IML@Prob or Prob@IML
		String imlOrProb=imlProbGuiBean.getSelectedOption();
		//gets the IML or Prob value filled in by the user
		double imlProbValue=imlProbGuiBean.getIML_Prob();
		boolean imlAtProb = false, probAtIML = false;
		if(imlOrProb.equalsIgnoreCase(imlProbGuiBean.IML_AT_PROB)){
			//if the old Y axis Label not equal to the IML then clear plot and draw the chart again
			if(!this.IML.equalsIgnoreCase(oldY_AxisLabel))
				this.clearPlot(true);
			totalProbFuncs.setYAxisName(this.IML);
			imlAtProb=true;
		}
		else{
			//if the old Y axis Label not equal to the Prob then clear plot and draw the chart again
			if(!this.PROB_AT_EXCEED.equalsIgnoreCase(oldY_AxisLabel))
				this.clearPlot(true);
			totalProbFuncs.setYAxisName(this.PROB_AT_EXCEED);
			probAtIML=true;
		}

		//If the user has chosen the Probabilistic
		if(((String)probDeterSelection.getSelectedItem()).equalsIgnoreCase(this.PROBABILISTIC)){
			this.isEqkList = false;
			// whwther to show progress bar in case of update forecast
			erfGuiBean.showProgressBar(this.progressCheckBox.isSelected());
			// get the selected forecast model
			EqkRupForecastBaseAPI eqkRupForecast = null;
			try{
				//gets the instance of the selected ERF
				eqkRupForecast = erfGuiBean.getSelectedERF();
			}catch(Exception e){
				e.printStackTrace();
			}
			if(this.progressCheckBox.isSelected())  {
				progressClass = new CalcProgressBar("Hazard-Curve Calc Status", "Beginning Calculation ");
				progressClass.displayProgressBar();
				timer.start();
			}

			// check whether this forecast is a Forecast List
			// if this is forecast list , handle it differently
			boolean isEqkForecastList = false;
			if(eqkRupForecast instanceof ERF_EpistemicList)  {
				handleForecastList(site, imr, eqkRupForecast,imlProbValue,imlAtProb,probAtIML);
				this.hazCalcDone = true;
				return;
			}

			// this is not a eqk list
			this.isEqkList = false;

			try{
				// set the value for the distance from the distance control panel
				if(distanceControlPanel!=null)  calc.setMaxSourceDistance(distanceControlPanel.getDistance());
			}catch(RemoteException e){
				e.printStackTrace();
			}
			// initialize the values in condProbfunc with log values as passed in hazFunction
			initX_Values(tempHazFunction,imlProbValue,imlAtProb,probAtIML);

			try {
				//iterating over all the SA Periods for the IMR's
				for(int i=0;i< numSA_PeriodVals;++i){
					double saPeriodVal = ((Double)this.saPeriodVector.get(i)).doubleValue();
					imr.getParameter(this.SA_PERIOD).setValue(this.saPeriodVector.get(i));
					try{
						// calculate the hazard curve for each SA Period
						calc.getHazardCurve(tempHazFunction, site, imr, (EqkRupForecast)eqkRupForecast);
					}catch(RemoteException e){
						e.printStackTrace();
					}
					//number of SA Periods for which we have ran the Hazard Curve
					this.numSA_PeriodValDone =i;
					hazFunction.setInfo("\n"+getCurveParametersInfo()+"\n");
					double val = getHazFuncIML_ProbValues(tempHazFunction,imlProbValue,imlAtProb,probAtIML);
					hazFunction.set(saPeriodVal,val);
				}
			}catch (RuntimeException e) {
				JOptionPane.showMessageDialog(this, e.getMessage(),
						"Parameters Invalid", JOptionPane.INFORMATION_MESSAGE);
				return;
			}
		}
		else{ //If the Deterministic has been chosen by the user
			imr.setSite(site);
			try{
				imr.setEqkRupture(this.erfRupSelectorGuiBean.getRupture());
			}catch (Exception ex) {
				timer.stop();
				JOptionPane.showMessageDialog(this, "Rupture not allowed for the chosen IMR: "+ex.getMessage());
				this.repaint();
				this.validate();
				return;
			}

			if(this.progressCheckBox.isSelected())  {
				progressClass = new CalcProgressBar("Hazard-Curve Calc Status", "Beginning Calculation ");
				progressClass.displayProgressBar();
				timer.start();
			}

			//if the user has selectde the Prob@IML
			if(probAtIML)
				//iterating over all the SA Periods for the IMR's
				for(int i=0;i< this.numSA_PeriodVals;++i){
					double saPeriodVal = ((Double)this.saPeriodVector.get(i)).doubleValue();
					imr.getParameter(this.SA_PERIOD).setValue(this.saPeriodVector.get(i));
					double imlLogVal = Math.log(imlProbValue);
					//double val = 0.4343*Math.log(imr.getExceedProbability(imlLogVal));
					double val = imr.getExceedProbability(imlLogVal);
					//adding values to the hazard function
					hazFunction.set(saPeriodVal,val);
					//number of SA Periods for which we have ran the Hazard Curve
					this.numSA_PeriodValDone =i;
				}
			else  //if the user has selected IML@prob
				//iterating over all the SA Periods for the IMR
				for(int i=0;i<this.numSA_PeriodVals;++i){
					double saPeriodVal = ((Double)(saPeriodVector.get(i))).doubleValue();
					imr.getParameter(this.SA_PERIOD).setValue(this.saPeriodVector.get(i));
					imr.getParameter(imr.EXCEED_PROB_NAME).setValue(new Double(imlProbValue));
					//double val = 0.4343*imr.getIML_AtExceedProb();
					//adding values to the Hazard Function
					double val = Math.exp(imr.getIML_AtExceedProb());
					hazFunction.set(saPeriodVal,val);
					//number of SA Periods for which we have ran the Hazard Curve
					this.numSA_PeriodValDone =i;
				}
			this.deterministicCalcDone = true;
		}

		// add the function to the function list
		totalProbFuncs.add(hazFunction);
		//checks whether the Hazard Curve Calculation are complete
		hazCalcDone = true;
		// set the X-axis label
		totalProbFuncs.setXAxisName(X_AXIS_LABEL);

	}


	/**
	 * Gets the SA Period Values for the IMR
	 * @param imr
	 */
	private void getSA_PeriodForIMR(ScalarIntensityMeasureRelationshipAPI imr){
		ListIterator it =imr.getSupportedIntensityMeasuresIterator();
		while(it.hasNext()){
			DependentParameterAPI  tempParam = (DependentParameterAPI)it.next();
			if(tempParam.getName().equalsIgnoreCase(this.SA_NAME)){
				ListIterator it1 = tempParam.getIndependentParametersIterator();
				while(it1.hasNext()){
					ParameterAPI independentParam = (ParameterAPI)it1.next();
					if(independentParam.getName().equalsIgnoreCase(this.SA_PERIOD)){
						saPeriodVector = ((DoubleDiscreteParameter)independentParam).getAllowedDoubles();
						numSA_PeriodVals = saPeriodVector.size();
					}
				}
			}
		}
	}



	/**
	 * Handle the Eqk Forecast List.
	 * @param site : Selected site
	 * @param imr : selected IMR
	 * @param eqkRupForecast : List of Eqk Rup forecasts
	 */
	private void handleForecastList(Site site,
			ScalarIntensityMeasureRelationshipAPI imr,
			EqkRupForecastBaseAPI eqkRupForecast,
			double imlProbValue,boolean imlAtProb,
			boolean probAtIML) {

		ERF_EpistemicList erfList  = (ERF_EpistemicList)eqkRupForecast;

		//checks how many SA Periods has been completed
		this.numSA_PeriodValDone =0;

		int numERFs = erfList.getNumERFs(); // get the num of ERFs in the list

		// clear the function list
		totalProbFuncs.clear();
		// calculate the hazard curve
		try{
			if(distanceControlPanel!=null) calc.setMaxSourceDistance(distanceControlPanel.getDistance());
		}catch(RemoteException e){
			e.printStackTrace();
		}
		// do not show progress bar if not desired by user
		//calc.showProgressBar(this.progressCheckBox.isSelected());
		//check if the curves are to shown in the same black color for each erf.
		this.isEqkList = true; // set the flag to indicate thatwe are dealing with Eqk list
		// calculate hazard curve for each ERF within the list
		if(!this.progressCheckBox.isSelected()) this.isIndividualCurves = false;
		else this.isIndividualCurves = true;

		//fixing the value for the Y Axis
		if(probAtIML)
			totalProbFuncs.setYAxisName(this.PROB_AT_EXCEED);
		else
			totalProbFuncs.setYAxisName(this.IML);

		for(int i=0; i<numERFs; ++i) {
			ArbitrarilyDiscretizedFunc hazFunction = new ArbitrarilyDiscretizedFunc();
			ArbitrarilyDiscretizedFunc tempHazFunction = new ArbitrarilyDiscretizedFunc();
			if(this.progressCheckBox.isSelected()) while(isIndividualCurves);
			// intialize the hazard function
			initX_Values(tempHazFunction,imlProbValue,imlAtProb,probAtIML);
			try {
				//iterating over all the SA Periods for the IMR's
				for(int j=0;j< this.numSA_PeriodVals;++j){
					double saPeriodVal = ((Double)this.saPeriodVector.get(j)).doubleValue();
					imr.getParameter(this.SA_PERIOD).setValue(this.saPeriodVector.get(j));
					try{
						// calculate the hazard curve for each SA Period
						calc.getHazardCurve(tempHazFunction, site, imr, erfList.getERF(i));
					}catch(RemoteException e){
						e.printStackTrace();
					}
					//number of SA Periods for which we have ran the Hazard Curve
					this.numSA_PeriodValDone =j;
					hazFunction.setInfo("\n"+getCurveParametersInfo()+"\n");
					double val= getHazFuncIML_ProbValues(tempHazFunction,imlProbValue,imlAtProb,probAtIML);
					hazFunction.set(saPeriodVal,val);
				}
			}catch (RuntimeException e) {
				JOptionPane.showMessageDialog(this, e.getMessage(),
						"Parameters Invalid", JOptionPane.INFORMATION_MESSAGE);
				e.printStackTrace();
				return;
			}
			totalProbFuncs.add(hazFunction);
			this.isIndividualCurves = true;
		}


		// if fractile or average needs to be calculated
		if(!this.fractileOption.equalsIgnoreCase
				(ERF_EpistemicListControlPanel.NO_PERCENTILE) || this.avgSelected) {
			// set the function list and weights in the calculator
			/*if (fractileCalc==null)
       fractileCalc = new FractileCurveCalculator(totalProbFuncs,
           erfList.getRelativeWeightsList());
     else  fractileCalc.set(totalProbFuncs, erfList.getRelativeWeightsList());*/
		}

		if(!isAllCurves) totalProbFuncs.clear(); //if all curves are not needed to be drawn

		// if 5th, 50 and 95th percetile need to be plotted
		/*if(this.fractileOption.equalsIgnoreCase
      (ERF_EpistemicListControlPanel.FIVE_50_95_PERCENTILE)) {
     totalProbFuncs.add(fractileCalc.getFractile(.05)); // 5th fractile
     totalProbFuncs.add(fractileCalc.getFractile(.5)); // 50th fractile
     totalProbFuncs.add(fractileCalc.getFractile(.95)); // 95th fractile
   } else if(this.fractileOption.equalsIgnoreCase // for custom fractile
      (ERF_EpistemicListControlPanel.CUSTOM_PERCENTILE )) {
     double fractile = this.epistemicControlPanel.getCustomFractileValue();
     totalProbFuncs.add(fractileCalc.getFractile(fractile/100));
   }*/
		// calculate average
		//if(this.avgSelected) totalProbFuncs.add(fractileCalc.getMeanCurve());
		// set the X-axis label
		totalProbFuncs.setXAxisName(X_AXIS_LABEL);

		isIndividualCurves = false;
	}



	/**
	 * set x values in log space for Hazard Function to be passed to IMR as IMT is
	 * always SA
	 * It accepts 1 parameters
	 *
	 * @param originalFunc :  this is the function with X values set
	 */
	private void initX_Values(DiscretizedFuncAPI arb, double imlProbVal,boolean imlAtProb,
			boolean probAtIML){

		if(probAtIML) //prob@iml
			arb.set(Math.log(imlProbVal),1);
		else{ //iml@Prob then we have to interpolate over a range of X-Values
			if(!useCustomX_Values)
				function = imtInfo.getDefaultHazardCurve(SA_Param.NAME);

			if (imtInfo.isIMT_LogNormalDist(SA_Param.NAME)) {
				for(int i=0;i<function.getNum();++i)
					arb.set(Math.log(function.getX(i)),1);
			}
		}
	}

	/**
	 * set x values back from the log space to the original linear values
	 * for Hazard Function after completion of the Hazard Calculations
	 * and returns back to the user IML or Prob value
	 * It accepts 1 parameters
	 *
	 * @param hazFunction :  this is the function with X values set
	 */
	private double getHazFuncIML_ProbValues(ArbitrarilyDiscretizedFunc hazFunc,
			double imlProbVal,boolean imlAtProb, boolean probAtIML) {

		//gets the number of points in the function
		int numPoints = hazFunc.getNum();
		//prob at iml is selected just return the Y Value back
		if(probAtIML)
			return hazFunc.getY(numPoints-1);
		else{ //if iml at prob is selected just return the interpolated IML value.
			ArbitrarilyDiscretizedFunc tempFunc = new ArbitrarilyDiscretizedFunc();
			for(int i=0; i<numPoints; ++i)
				tempFunc.set(function.getX(i),hazFunc.getY(i));

			/*we are calling the function (getFirst InterpolatedX ) becuase x values for the PEER
			 * are the X values and the function we get from the Hazard Curve Calc are the
			 * Y Values for the Prob., now we have to find the interpolated IML which corresponds
			 * X value and imlProbVal is the Y value parameter which this function accepts
			 */
			//returns the interpolated IML value for the given prob.
			return tempFunc.getFirstInterpolatedX_inLogXLogYDomain(imlProbVal);

		}
	}

	/**
	 *
	 * @returns the list PlotCurveCharacterstics that contain the info about
	 * plotting the curve like plot line color , its width and line type.
	 */
	public ArrayList getCurvePlottingCharacterstic(){
		return graphPanel.getCurvePlottingCharacterstic();
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
	 * Function to make the buttons enable or disable in the application.
	 * It is used in application to disable the button in the buttons panel
	 * if some computation is already going on.
	 * @param b
	 */
	private void setButtonsEnable(boolean b){
		addButton.setEnabled(b);
		clearButton.setEnabled(b);
		peelOffButton.setEnabled(b);
		buttonControlPanel.setEnabled(b);
		progressCheckBox.setEnabled(b);
	}


	/**
	 *
	 * @returns the String containing the values selected for different parameters
	 */
	public String getCurveParametersInfo(){
		String paramInfo= null;
		if(erfGuiBean !=null)
			paramInfo="IMR Param List: " +this.imrGuiBean.getParameterList().toString()+"\n"+
			"Site Param List: "+siteGuiBean.getParameterListEditor().getParameterList().toString()+"\n"+
			"IML OR Prob Param List: "+this.imlProbGuiBean.getParameterList().toString()+"\n"+
			"Forecast Param List: "+erfGuiBean.getERFParameterList().toString();
		else
			paramInfo="IMR Param List: " +this.imrGuiBean.getParameterList().toString()+"\n"+
			"Site Param List: "+siteGuiBean.getParameterListEditor().getParameterList().toString()+"\n"+
			"IML OR Prob Param List: "+this.imlProbGuiBean.getParameterList().toString()+"\n"+
			"Forecast Param List: "+erfRupSelectorGuiBean.getParameterListMetadataString();
		return paramInfo;
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
	private void peelOffCurves(){
		graphWindow = new GraphWindow(this);
		clearPlot(true);
		graphWindow.setVisible(true);
	}


	/**
	 * Initialize the IMR Gui Bean
	 */
	private void initIMR_GuiBean() {

		imrGuiBean = new IMR_GuiBean(this);
		imrGuiBean.getParameterEditor(imrGuiBean.IMR_PARAM_NAME).getParameter().addParameterChangeListener(this);
		// show this gui bean the JPanel
		imrPanel.add(this.imrGuiBean,new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0,
				GridBagConstraints.CENTER, GridBagConstraints.BOTH, defaultInsets, 0, 0 ));
		//sets the Intensity measure for the IMR
		imrGuiBean.getSelectedIMR_Instance().setIntensityMeasure(this.SA_NAME);
		//initialise the SA Peroid values for the IMR
		this.getSA_PeriodForIMR(imrGuiBean.getSelectedIMR_Instance());
	}

	/**
	 * Initialize the site gui bean
	 */
	private void initSiteGuiBean() {

		// get the selected IMR
		ScalarIntensityMeasureRelationshipAPI imr = imrGuiBean.getSelectedIMR_Instance();
		// create the Site Gui Bean object
		siteGuiBean = new Site_GuiBean();
		siteGuiBean.replaceSiteParams(imr.getSiteParamsIterator());
		// show the sitebean in JPanel
		sitePanel.add(this.siteGuiBean, new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0,
				GridBagConstraints.CENTER, GridBagConstraints.BOTH, defaultInsets, 0, 0 ));

	}

	/**
	 * Initialise the IMT_Prob Selector Gui Bean
	 */
	private void initImlProb_GuiBean(){
		imlProbGuiBean = new IMLorProbSelectorGuiBean();
		this.imtPanel.add(imlProbGuiBean, new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0,
				GridBagConstraints.CENTER,GridBagConstraints.BOTH, defaultInsets, 0, 0 ));
	}


	/**
	 * Initialize the ERF Gui Bean
	 */
	private void initERF_GuiBean() {
		// create the ERF Gui Bean object
		ArrayList erf_Classes = new ArrayList();
		erf_Classes.add(FRANKEL2000_ADJ_FORECAST_CLASS_NAME);
		erf_Classes.add(FRANKEL_ADJ_FORECAST_CLASS_NAME);
		erf_Classes.add(STEP_FORECAST_CLASS_NAME);
		erf_Classes.add(WG02_ERF_LIST_CLASS_NAME);
		erf_Classes.add(STEP_ALASKA_ERF_CLASS_NAME);
		erf_Classes.add(POISSON_FAULT_ERF_CLASS_NAME);
		erf_Classes.add(PEER_AREA_FORECAST_CLASS_NAME);
		erf_Classes.add(PEER_NON_PLANAR_FAULT_FORECAST_CLASS_NAME);
		erf_Classes.add(PEER_MULTI_SOURCE_FORECAST_CLASS_NAME);
		erf_Classes.add(PEER_LOGIC_TREE_FORECAST_CLASS_NAME);

		try{
			if(erfGuiBean == null)
				erfGuiBean = new ERF_GuiBean(erf_Classes);
		}catch(InvocationTargetException e){
			throw new RuntimeException("Connection to ERF's  failed");
		}
		erfPanel.setLayout(gridBagLayout5);
		erfPanel.removeAll();
		erfPanel.add(erfGuiBean, new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0,
				GridBagConstraints.CENTER,GridBagConstraints.BOTH, defaultInsets, 0, 0 ));
		erfPanel.validate();
		erfPanel.repaint();
	}

	/**
	 * Initialize the ERF Rup Selector Gui Bean
	 */
	private void initERFSelector_GuiBean() {
		// create the ERF Gui Bean object
		ArrayList erf_Classes = new ArrayList();
		erf_Classes.add(FRANKEL_ADJ_FORECAST_CLASS_NAME);
		erf_Classes.add(FRANKEL2000_ADJ_FORECAST_CLASS_NAME);
		erf_Classes.add(STEP_FORECAST_CLASS_NAME);
		erf_Classes.add(WG02_FORECAST_CLASS_NAME);
		erf_Classes.add(POISSON_FAULT_ERF_CLASS_NAME);
		erf_Classes.add(PEER_AREA_FORECAST_CLASS_NAME);
		erf_Classes.add(PEER_NON_PLANAR_FAULT_FORECAST_CLASS_NAME);
		erf_Classes.add(PEER_MULTI_SOURCE_FORECAST_CLASS_NAME);
		erf_Classes.add(PEER_LOGIC_TREE_FORECAST_CLASS_NAME);

		try{
			if(erfRupSelectorGuiBean == null)
				erfRupSelectorGuiBean = new EqkRupSelectorGuiBean(erf_Classes);
		}catch(InvocationTargetException e){
			throw new RuntimeException("Connection to ERF's failed");
		}

		erfPanel.removeAll();
		//erfGuiBean = null;
		erfPanel.add(erfRupSelectorGuiBean, new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0,
				GridBagConstraints.CENTER,GridBagConstraints.BOTH, defaultInsets, 0, 0 ));
		erfRupSelectorGuiBean.getParameter(ERF_GuiBean.ERF_PARAM_NAME).addParameterChangeListener(this);
		erfPanel.validate();
		erfPanel.repaint();
	}






	/**
	 * Initialize the items to be added to the control list
	 */
	private void initControlList() {
		this.controlComboBox.addItem(CONTROL_PANELS);
		//this.controlComboBox.addItem(PEER_TEST_CONTROL);
		//this.controlComboBox.addItem(DISAGGREGATION_CONTROL);
		this.controlComboBox.addItem(AXIS_CONTROL);
		this.controlComboBox.addItem(DISTANCE_CONTROL);
		this.controlComboBox.addItem(SITES_OF_INTEREST_CONTROL);
		this.controlComboBox.addItem(CVM_CONTROL);
		this.controlComboBox.addItem(X_VALUES_CONTROL);
	}

	/**
	 * Initialise the item to be added to the Prob and Deter Selection
	 */
	private void initProbOrDeterList(){
		this.probDeterSelection.addItem(DETERMINISTIC);
		this.probDeterSelection.addItem(PROBABILISTIC);
	}

	/**
	 * This function is called when controls pick list is chosen
	 * @param e
	 */
	void controlComboBox_actionPerformed(ActionEvent e) {
		if(controlComboBox.getItemCount()<=0) return;
		String selectedControl = controlComboBox.getSelectedItem().toString();
		/*if(selectedControl.equalsIgnoreCase(this.PEER_TEST_CONTROL))
      initPEER_TestControl();
    else if(selectedControl.equalsIgnoreCase(this.DISAGGREGATION_CONTROL))
      initDisaggregationControl();*/
		if(selectedControl.equalsIgnoreCase(this.EPISTEMIC_CONTROL))
			initEpistemicControl();
		else if(selectedControl.equalsIgnoreCase(this.DISTANCE_CONTROL))
			initDistanceControl();
		else if(selectedControl.equalsIgnoreCase(this.DISTANCE_CONTROL))
			initDistanceControl();
		else if(selectedControl.equalsIgnoreCase(this.SITES_OF_INTEREST_CONTROL))
			initSitesOfInterestControl();
		else if(selectedControl.equalsIgnoreCase(this.CVM_CONTROL))
			initCVMControl();
		else if(selectedControl.equalsIgnoreCase(this.X_VALUES_CONTROL))
			initX_ValuesControl();
		controlComboBox.setSelectedItem(this.CONTROL_PANELS);
	}

	/**
	 * This function is to whether to plot ERF_GuiBean or ERF_RupSelectorGuiBean
	 * @param e
	 */
	void probDeterSelection_actionPerformed(ActionEvent e) {
		String selectedControl = this.probDeterSelection.getSelectedItem().toString();
		if(selectedControl.equalsIgnoreCase(this.PROBABILISTIC)){
			try{
				this.initERF_GuiBean();
			}catch(RuntimeException ee){
				JOptionPane.showMessageDialog(this,"Connection to ERF failed","Internet Connection Problem",
						JOptionPane.OK_OPTION);
				System.exit(0);
			}
		}
		else if(selectedControl.equalsIgnoreCase(this.DETERMINISTIC)){
			try{
				this.initERFSelector_GuiBean();
			}catch(RuntimeException ee){
				JOptionPane.showMessageDialog(this,"Connection to ERF failed","Internet Connection Problem",
						JOptionPane.OK_OPTION);
				System.exit(0);
			}
		}
	}


	/**
	 * Initialize the PEER Test control.
	 * This function is called when user selects "Select Test and site"
	 * from controls pick list
	 */
	/*private void initPEER_TestControl() {
    //creating the instance of the PEER_TestParamSetter class which is extended from the
    //JComboBox, so it is like a control panel for creating the JComboBox containing the
    //name of different sets and the test cases
    //peerTestsParamSetter takes the instance of the hazardCurveGuiBean as its instance
    // distance control panel is needed here so that distance can be set for PEER cases
    if(distanceControlPanel==null) distanceControlPanel= new SetMinSourceSiteDistanceControlPanel(this);
    if(peerTestsControlPanel==null)
      peerTestsControlPanel=new PEER_TestCaseSelectorControlPanel(this,
          imrGuiBean, siteGuiBean, imtGuiBean, erfGuiBean, timeSpanGuiBean,
          this.distanceControlPanel);
    peerTestsControlPanel.pack();
    peerTestsControlPanel.setVisible(true);
  }*/


	/**
	 * Initialize the Disaggregation control.
	 * This function is called when user selects "Disaggregation"
	 * from controls pick list
	 */
	/*private void initDisaggregationControl() {
    if(this.disaggregationControlPanel==null)
      disaggregationControlPanel = new DisaggregationControlPanel(this, this);
    disaggregationControlPanel.setVisible(true);
  }*/

	/**
	 * Initialize the Epistemic list control.
	 * This function is called when user selects "ERF Epistemic Control"
	 * from controls pick list
	 */
	private void initEpistemicControl() {
		throw new RuntimeException("Broken in old junk app");
//		if(this.epistemicControlPanel==null)
//			epistemicControlPanel = new ERF_EpistemicListControlPanel(this,this);
//		epistemicControlPanel.setVisible(true);
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
	 * initialize the X values for the Hazard Curve control Panel
	 * It will enable the user to set the X values
	 */
	private void initX_ValuesControl(){
		if(xValuesPanel == null)
			xValuesPanel = new X_ValuesInCurveControlPanel(this,this);
		if(!useCustomX_Values)
			xValuesPanel.useDefaultX_Values();
		else
			xValuesPanel.setX_Values(function);
		xValuesPanel.getComponent().pack();
		xValuesPanel.getComponent().setVisible(true);
	}


	/**
	 * This function sets whether all curves are to drawn or only fractiles are to drawn
	 * @param drawAllCurves :True if all curves are to be drawn else false
	 */
	public void setPlotAllCurves(boolean drawAllCurves) {
		this.isAllCurves = drawAllCurves;
	}

	/**
	 * This function sets the percentils option chosen by the user.
	 * User can choose "No Fractile", "5th, 50th and 95th Fractile" or
	 * "Custom Fractile"
	 *
	 * @param fractileOption : Option selected by the user. It can be set by
	 * various constant String values in ERF_EpistemicListControlPanel
	 */
	public void setFractileOption(String fractileOption) {
		this.fractileOption = fractileOption;
	}

	/**
	 * This function is needed to tell the applet whether avg is selected or not
	 * This is called from ERF_EpistemicListControlPanel
	 *
	 * @param isAvgSelected : true if avg is selected else false
	 */
	public void setAverageSelected(boolean isAvgSelected) {
		this.avgSelected = isAvgSelected;
	}

	/**
	 * This forces use of default X-axis values (according to the selected IMT)
	 */
	public void setCurveXValues(){
		useCustomX_Values = false;
	}

	/**
	 * Sets the hazard curve x-axis values (if user wants custom values x-axis values).
	 * Note that what's passed in is not cloned (the y-axis values will get modified).
	 * @param func
	 */
	public void setCurveXValues(ArbitrarilyDiscretizedFunc func){
		useCustomX_Values = true;
		function =func;
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
	 * @returns boolean: Checks if Custom Axis is selected
	 */
	public boolean isCustomAxis(){
		return customAxis;
	}

	/**
	 *
	 * @returns the selected IMT
	 */
	public String getSelectedIMT(){
		return SA_Param.NAME;
	}

	/**
	 *
	 * @returns the list PlotCurveCharacterstics that contain the info about
	 * plotting the curve like plot line color , its width and line type.
	 */
	public ArrayList getPlottingFeatures(){
		return graphPanel.getCurvePlottingCharacterstic();
	}

	void peelOffButton_actionPerformed(ActionEvent e) {
		peelOffCurves();
	}

	/**
	 * This method does nothing in the Hazard Spectrum application
	 *
	 */
	public void updateIM(){

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

	/**
	 * Sets ArbitraryDiscretizedFunc inside list containing all the functions.
	 * 
	 * @param function
	 *            ArbitrarilyDiscretizedFunc
	 */
	public void addCurve (
			ArbitrarilyDiscretizedFunc function) {
		functionList.add(function);
		ArrayList<PlotCurveCharacterstics> plotFeaturesList = getPlottingFeatures();
		plotFeaturesList.add(new PlotCurveCharacterstics(
				PlotColorAndLineTypeSelectorControlPanel.CROSS_SYMBOLS,
				Color.BLACK, 4.0, 1));
		addGraphPanel();
	}

}






