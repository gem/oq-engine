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
import java.lang.reflect.InvocationTargetException;
import java.rmi.RemoteException;
import java.text.DecimalFormat;
import java.util.ArrayList;

import javax.swing.BorderFactory;
import javax.swing.ImageIcon;
import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JComboBox;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JSplitPane;
import javax.swing.JTabbedPane;
import javax.swing.JTextArea;
import javax.swing.Timer;
import javax.swing.UIManager;
import javax.swing.border.BevelBorder;
import javax.swing.border.Border;

import org.apache.commons.lang.SystemUtils;
import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
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
import org.opensha.sha.gui.controls.SetMinSourceSiteDistanceControlPanel;
import org.opensha.sha.gui.controls.SetSiteParamsFromWebServicesControlPanel;
import org.opensha.sha.gui.controls.SitesOfInterestControlPanel;
import org.opensha.sha.gui.infoTools.CalcProgressBar;
import org.opensha.sha.gui.infoTools.ConnectToCVM;
import org.opensha.sha.gui.infoTools.ExceptionWindow;
import org.opensha.sha.gui.infoTools.IMT_Info;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;

import org.opensha.sra.calc.BenefitCostCalculator;
import org.opensha.sra.calc.EALCalculator;
import org.opensha.sra.vulnerability.AbstractVulnerability;
import org.opensha.sra.gui.components.BenefitCostBean;
import org.opensha.sra.gui.components.GuiBeanAPI;



/**
 * <p>Title: BCR_Application</p>
 * <p>Description: </p>
 * @author Nitin Gupta and Vipin Gupta
 * Date : Feb  , 2006
 * @version 1.0
 */

public class BCR_Application extends JFrame
    implements Runnable, ParameterChangeListener,
    IMR_GuiBeanAPI{

	private static final long serialVersionUID = 0x1B8589F;
	/**
   * Name of the class
   */
  private final static String C = "BCR_Application";
  // for debug purpose 
  protected final static boolean D = false;



  /**
   *  The object class names for all the supported Eqk Rup Forecasts
   */
  public final static String FRANKEL_ADJ_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.Frankel96.Frankel96_AdjustableEqkRupForecast";
  public final static String FRANKEL02_ADJ_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.Frankel02.Frankel02_AdjustableEqkRupForecast";
  public final static String WGCEP_UCERF1_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF1.WGCEP_UCERF1_EqkRupForecast";
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


  private JLabel openshaImgLabel = new JLabel(new ImageIcon(FileUtils.loadImage("logos/PoweredByOpenSHA_Agua.jpg")));
  private JLabel usgsImgLabel = new JLabel(new ImageIcon(FileUtils.loadImage("logos/usgs_resrisk.gif")));
  private JLabel riskAgoraImgLabel = new JLabel(new ImageIcon(FileUtils.loadImage("logos/AgoraOpenRisk.jpg")));


  // Strings for control pick list
  protected final static String CONTROL_PANELS = "Control Panels";
    protected final static String DISTANCE_CONTROL = "Max Source-Site Distance";
  protected final static String SITES_OF_INTEREST_CONTROL = "Sites of Interest";
  protected final static String CVM_CONTROL = "Set Site Params from Web Services";


  // objects for control panels

  protected SetMinSourceSiteDistanceControlPanel distanceControlPanel;
  protected SitesOfInterestControlPanel sitesOfInterest;
  protected SetSiteParamsFromWebServicesControlPanel cvmControlPanel;
  
  private Insets plotInsets = new Insets( 4, 10, 4, 4 );

  private Border border1;



  // default insets
  protected Insets defaultInsets = new Insets( 4, 4, 4, 4 );

  // height and width of the applet
  protected final static int W = 1100;
  protected final static int H = 770;


  //holds the ArbitrarilyDiscretizedFunc
  protected ArbitrarilyDiscretizedFunc function;


  protected String TITLE = new String("BCR Calculator");


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




  JSplitPane topSplitPane = new JSplitPane();
  JButton clearButton = new JButton();
  JPanel buttonPanel = new JPanel();
  JCheckBox progressCheckBox = new JCheckBox();
  JButton addButton = new JButton();
  JComboBox controlComboBox = new JComboBox();
  JSplitPane chartSplit = new JSplitPane();
  JPanel panel = new JPanel();
  /**
   * adding scroll pane for showing data
   */
  private JScrollPane dataScrollPane = new JScrollPane();

  // text area to show the data values
  private JTextArea pointsTextArea = new JTextArea();
  
  
  GridBagLayout gridBagLayout9 = new GridBagLayout();
  GridBagLayout gridBagLayout8 = new GridBagLayout();
  JSplitPane imrSplitPane = new JSplitPane();
  GridBagLayout gridBagLayout5 = new GridBagLayout();

  JPanel erfTimespanPanel = new JPanel();
  JPanel siteLocPanel = new JPanel();
  JSplitPane controlsSplit = new JSplitPane();
  JTabbedPane paramsTabbedPane = new JTabbedPane();
  JPanel structuralPanel = new JPanel();
  private BenefitCostBean bcbean ;
  private JPanel bcPanel;
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
 
  //counts the number of computation done till now
  private int computationDisplayCount =0;
  
  private DecimalFormat bcrFormat = new DecimalFormat("0.00");
 
  /**this boolean keeps track when to plot the new data on top of other and when to
  *add to the existing data.
  * If it is true then add new data on top of existing data, but if it is false
  * then add new data to the existing data(this option only works if it is ERF_List).
  * */
  boolean addData= true;
  protected JButton cancelCalcButton = new JButton();
  private FlowLayout flowLayout1 = new FlowLayout();



  //Construct the applet
  public BCR_Application() {

  }
  //Initialize the applet
  public void init() {
    try {

      // initialize the control pick list
      initControlList();
      // initialize the GUI components
      startAppProgressClass = new CalcProgressBar("Starting Application", "Initializing Application .. Please Wait");
      jbInit();
//    initialize the various GUI beans
      initBenefitCostBean();
      initIMR_GuiBean();
      initSiteGuiBean();
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
     e.printStackTrace();
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

    
    jPanel1.setLayout(gridBagLayout10);


    jPanel1.setBackground(Color.white);
    jPanel1.setBorder(border4);
    jPanel1.setMinimumSize(new Dimension(959, 600));
    jPanel1.setPreferredSize(new Dimension(959, 600));

    //loading the OpenSHA Logo

    topSplitPane.setOrientation(JSplitPane.VERTICAL_SPLIT);

    clearButton.setText("Clear Results");
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
    
    dataScrollPane.setHorizontalScrollBarPolicy(JScrollPane.HORIZONTAL_SCROLLBAR_AS_NEEDED);
    dataScrollPane.setVerticalScrollBarPolicy(JScrollPane.VERTICAL_SCROLLBAR_AS_NEEDED);
    dataScrollPane.setBorder( BorderFactory.createEtchedBorder() );
    dataScrollPane.getViewport().add( pointsTextArea, null );
    pointsTextArea.setEditable(false);
    pointsTextArea.setLineWrap(true);
    panel.add(dataScrollPane,new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0
            , GridBagConstraints.CENTER, GridBagConstraints.BOTH, plotInsets, 0, 0 ) );
    erfTimespanPanel.setLayout(gridBagLayout13);
    erfTimespanPanel.setBackground(Color.white);
    siteLocPanel.setLayout(gridBagLayout8);
    siteLocPanel.setBackground(Color.white);
    controlsSplit.setDividerSize(5);
    structuralPanel.setLayout(gridBagLayout5);
    structuralPanel.setBackground(Color.white);
    structuralPanel.setBorder(border2);
    structuralPanel.setMaximumSize(new Dimension(2147483647, 10000));
    structuralPanel.setMinimumSize(new Dimension(2, 300));
    structuralPanel.setPreferredSize(new Dimension(2, 300));
    imrPanel.setLayout(gridBagLayout15);
    imrPanel.setBackground(Color.white);
    chartSplit.setLeftComponent(panel);
    chartSplit.setRightComponent(paramsTabbedPane);

    cancelCalcButton.setText("Cancel");
    cancelCalcButton.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        cancelCalcButton_actionPerformed(e);
      }
    });
    this.getContentPane().add(jPanel1, BorderLayout.CENTER);
    jPanel1.add(topSplitPane,  new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
            ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(11, 4, 5, 6), 243, 231));
    
    buttonPanel.add(controlComboBox, 0);
    buttonPanel.add(addButton, 1);
    buttonPanel.add(cancelCalcButton, 2);
    buttonPanel.add(clearButton, 3);
    buttonPanel.add(progressCheckBox, 4);
    buttonPanel.add(usgsImgLabel, 5);
    buttonPanel.add(openshaImgLabel, 6);
    buttonPanel.add(riskAgoraImgLabel,7);
    

    //making the cancel button not visible until user has started to do the calculation
    cancelCalcButton.setVisible(false);

    topSplitPane.add(chartSplit, JSplitPane.TOP);
    chartSplit.add(panel, JSplitPane.LEFT);
    chartSplit.add(paramsTabbedPane, JSplitPane.RIGHT);
    imrSplitPane.add(imrPanel, JSplitPane.TOP);
    imrSplitPane.add(siteLocPanel, JSplitPane.BOTTOM);
    controlsSplit.add(imrSplitPane, JSplitPane.LEFT);
    controlsSplit.add(erfTimespanPanel, JSplitPane.RIGHT);
    paramsTabbedPane.add(structuralPanel, "Set Structural Type");
    
    paramsTabbedPane.add(controlsSplit, "Set Hazard Curve");
    topSplitPane.add(buttonPanel, JSplitPane.BOTTOM);
    topSplitPane.setDividerLocation(590);
    imrSplitPane.setDividerLocation(300);

    controlsSplit.setDividerLocation(230);
    structuralPanel.setLayout(gridBagLayout5);
    chartSplit.setDividerLocation(590);
    this.setSize(W,H);
    Dimension dim = Toolkit.getDefaultToolkit().getScreenSize();
    this.setLocation((dim.width - this.getSize().width) / 2, 0);
    //EXIT_ON_CLOSE == 3
    this.setDefaultCloseOperation(3);
    this.setTitle("BCR Application ");

  }



	  //Main method
	  public static void main(String[] args) {
	    BCR_Application applet = new BCR_Application();
	    
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
     * this function is called when Add Graph button is clicked
     * @param e
     */
    void addButton_actionPerformed(ActionEvent e) {
        cancelCalcButton.setVisible(true);
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
        ExceptionWindow bugWindow = new ExceptionWindow(this,e.getStackTrace(),getParametersInfoAsString());
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
      try{
          calc = new HazardCurveCalculator();
        }
        catch (Exception ex) {
          ex.printStackTrace();
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
        ExceptionWindow bugWindow = new ExceptionWindow(this,e.getStackTrace(),getParametersInfoAsString());
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
              }
            }catch(Exception e){
              e.printStackTrace();
            }
           }
          });
        }

      else {
        this.computeHazardCurve();
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
   * this function is called when "clear plot" is selected
   *
   * @param e
   */
  void clearButton_actionPerformed(ActionEvent e) {
	  this.pointsTextArea.setText("");
	  computationDisplayCount = 0;
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
      siteGuiBean.replaceSiteParams(imr.getSiteParamsIterator());
      siteGuiBean.validate();
      siteGuiBean.repaint();
      }
    if(name1.equalsIgnoreCase(bcbean.getCurrentVulnParam().getName())){
     	AbstractVulnerability currentModel = bcbean.getVulnModel(bcbean.CURRENT);
        String currentIMT = currentModel.getIMT();
        double currentPeriod = 0;
        if(currentIMT.equals(SA_Param.NAME))
        	currentPeriod = currentModel.getPeriod();
        
        
        AbstractVulnerability newModel = bcbean.getVulnModel(bcbean.RETRO);
        String newIMT = newModel.getIMT();
        double newPeriod = 0;
        if(newIMT.equals(SA_Param.NAME))
        	newPeriod = newModel.getPeriod();
        
    	imrGuiBean.setIMRParamListAndEditor(currentIMT, newIMT, currentPeriod, newPeriod);
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

    AbstractVulnerability currentModel = bcbean.getVulnModel(bcbean.CURRENT);
    String currentIMT = currentModel.getIMT();
    double currentPeriod = 0;
    if(currentIMT.equals(SA_Param.NAME))
    	currentPeriod = currentModel.getPeriod();
//    ArrayList<Double> currentIMLs = currentModel.getIMLVals();
    double[] currentIMLs = currentModel.getIMLValues();
    
    AbstractVulnerability newModel = bcbean.getVulnModel(bcbean.RETRO);
    String newIMT = newModel.getIMT();
    double newPeriod = 0;
    if(newIMT.equals(SA_Param.NAME))
    	newPeriod = newModel.getPeriod();
//    ArrayList<Double> newIMLs = newModel.getIMLVals();
    double[] newIMLs = newModel.getIMLValues();
    
    // get the selected IMR
    ScalarIntensityMeasureRelationshipAPI imr = imrGuiBean.getSelectedIMR_Instance();

    // make a site object to pass to IMR
    Site site = siteGuiBean.getSite();
    LocationList locs = new LocationList();
    Location loc = site.getLocation();
    locs.add(loc);
//  getting the wills site class values from servlet
    String siteClass="";
    try {
		ArrayList willsSiteClassList = ConnectToCVM.getWillsSiteTypeFromCVM(locs);
		siteClass = (String)willsSiteClassList.get(0);
	} catch (Exception e1) {
		e1.printStackTrace();
	}

     // calculate the hazard curve
    try {
      if (distanceControlPanel != null) calc.setMaxSourceDistance(
          distanceControlPanel.getDistance());
    }
    catch (Exception e) {
      setButtonsEnable(true);
      ExceptionWindow bugWindow = new ExceptionWindow(this, e.getStackTrace(),
          getParametersInfoAsString());
      bugWindow.setVisible(true);
      bugWindow.pack();
      e.printStackTrace();
    }
   
    ArbitrarilyDiscretizedFunc currentHazardCurve = calcHazardCurve(currentIMT,currentPeriod,currentIMLs,site,forecast,imr);
    ArbitrarilyDiscretizedFunc currentAnnualizedRates= null;
    try {
		currentAnnualizedRates = 
			(ArbitrarilyDiscretizedFunc)calc.getAnnualizedRates(currentHazardCurve, 
					forecast.getTimeSpan().getDuration());
	} catch (RemoteException e) {
		
	}
    
    ArbitrarilyDiscretizedFunc retroHazardCurve = calcHazardCurve(newIMT,newPeriod,newIMLs,site,forecast,imr);
    ArbitrarilyDiscretizedFunc retroAnnualizedRates = null;
    try {
    	retroAnnualizedRates = 
			(ArbitrarilyDiscretizedFunc)calc.getAnnualizedRates(retroHazardCurve, 
					forecast.getTimeSpan().getDuration());
	} catch (RemoteException e) {
		
	}
    
    EALCalculator currentCalc = new EALCalculator(currentAnnualizedRates,currentModel.getDFVals(),
    		bcbean.getCurrentReplaceCost());
    double currentEALVal = currentCalc.computeEAL();
    EALCalculator retroCalc = new EALCalculator(retroAnnualizedRates,newModel.getDFVals(),bcbean.getRetroReplaceCost());
    double newEALVal = retroCalc.computeEAL();
    
    BenefitCostCalculator bcCalc = new BenefitCostCalculator(currentEALVal,newEALVal,bcbean.getDiscountRate(),
    		bcbean.getDesignLife(),bcbean.getRetroCost());
    double bcr = bcCalc.computeBCR();
    double benefit = bcCalc.computeBenefit();
    double cost = bcCalc.computeCost();
    isHazardCalcDone = true;
    displayData(siteClass,currentHazardCurve,retroHazardCurve,currentEALVal,newEALVal,bcr,benefit,cost);
    setButtonsEnable(true);
  }
  
  
  private void displayData(String siteClass,ArbitrarilyDiscretizedFunc currentHazardCurve,ArbitrarilyDiscretizedFunc retroHazardCurve,
		  double currentEALVal,double newEALVal,double bcr,double benefit,double cost){
	  ++computationDisplayCount;
	  String data = pointsTextArea.getText();
	  if(computationDisplayCount !=1)
		  data +="\n\n";
	  data +="Benefit Cost Ratio Calculation # "+computationDisplayCount+"\n";
	  data +="BCR Desc. = "+bcbean.getDescription()+"\n";
	  data +="Site Class = "+siteClass+"\n";
	  data +="Current EAL Val = "+currentEALVal+"\nRetrofitted EAL Val = "+newEALVal+"\n";
	  data +="Benefit = $"+bcrFormat.format(benefit)+"\nBenefit Cost Ratio = "+bcr+"\n";
	  data +="Curent Hazard Curve"+"\n"+currentHazardCurve.toString();
	  data +="Retrofitted Hazard Curve"+"\n"+retroHazardCurve.toString()+"\n\n";
	  pointsTextArea.setText(data);
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
  private void initX_Values(DiscretizedFuncAPI arb, double[] imls, String imt){

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
   * Initialize the IMR Gui Bean
   */
  protected void initIMR_GuiBean() {

	AbstractVulnerability currentModel = bcbean.getVulnModel(bcbean.CURRENT);
    String currentIMT = currentModel.getIMT();
    double currentPeriod = 0;
    if(currentIMT.equals(SA_Param.NAME))
    	currentPeriod = currentModel.getPeriod();
    
    
    AbstractVulnerability newModel = bcbean.getVulnModel(bcbean.RETRO);
    String newIMT = newModel.getIMT();
    double newPeriod = 0;
    if(newIMT.equals(SA_Param.NAME))
    	newPeriod = newModel.getPeriod();
    imrPanel.removeAll();
     imrGuiBean = new IMR_GuiBean(this,currentIMT,newIMT,currentPeriod,newPeriod);
     imrGuiBean.getParameterEditor(imrGuiBean.IMR_PARAM_NAME).getParameter().addParameterChangeListener(this);
     // show this gui bean the JPanel
     imrPanel.add(this.imrGuiBean,new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0,
         GridBagConstraints.CENTER, GridBagConstraints.BOTH, defaultInsets, 0, 0 ));
     imrPanel.updateUI();
  }

  /**
   * Initialize the site gui bean
   */
  private void initSiteGuiBean() {

     // get the selected IMR
     ScalarIntensityMeasureRelationshipAPI imr = imrGuiBean.getSelectedIMR_Instance();
     // create the IMT Gui Bean object
     siteGuiBean = new Site_GuiBean();
     siteGuiBean.addSiteParams(imr.getSiteParamsIterator());
     siteLocPanel.setLayout(gridBagLayout8);
     siteLocPanel.add(siteGuiBean, new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0,
                                                     GridBagConstraints.CENTER,
                                                     GridBagConstraints.BOTH,
                                                     defaultInsets, 0, 0));
     siteLocPanel.updateUI();

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
        erf_Classes.add(FRANKEL02_ADJ_FORECAST_CLASS_NAME);
        erf_Classes.add(WGCEP_UCERF1_CLASS_NAME);        
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
    erfTimespanPanel.add(this.erfGuiBean, new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0,
            GridBagConstraints.CENTER, GridBagConstraints.BOTH, defaultInsets, 0, 0));
    erfTimespanPanel.updateUI();
  }


  /**
   * Initialize the Benefit cost GUI bean
   *
   */
  protected void initBenefitCostBean(){
//	creates the instance of the BenefitCost bean
	 bcbean = new BenefitCostBean();
	 bcPanel = (JPanel) bcbean.getVisualization(GuiBeanAPI.APPLICATION);
	 bcbean.getRetroVulnParam().addParameterChangeListener(this);
	 bcbean.getCurrentVulnParam().addParameterChangeListener(this);	  
	 structuralPanel.add(bcPanel,  new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
	            ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(0, 0, 0, 0), 0, 0));
	 structuralPanel.validate();
	 structuralPanel.repaint();
  }
  


  /**
   * Initialize the items to be added to the control list
   */
  protected void initControlList() {
    controlComboBox.addItem(CONTROL_PANELS);
    
    controlComboBox.addItem(DISTANCE_CONTROL);
    controlComboBox.addItem(SITES_OF_INTEREST_CONTROL);
    controlComboBox.addItem(CVM_CONTROL);
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
    
    controlComboBox.setSelectedItem(this.CONTROL_PANELS);
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
   *
   * @returns the String containing the values selected for different parameters
   */
  public String getParametersInfoAsString(){
    return getMapParametersInfoAsHTML().replaceAll("<br>",SystemUtils.LINE_SEPARATOR);
  }


  /**
   *
   * @returns the String containing the values selected for different parameters
   */
  public String getMapParametersInfoAsHTML(){
    String imrMetadata;
    //if Probabilistic calculation then only add the metadata
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
        ExceptionWindow bugWindow = new ExceptionWindow(this,ee.getStackTrace(),getParametersInfoAsString());
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
   * Updates the IMT_GuiBean to reflect the chnaged IM for the selected AttenuationRelationship.
   * This method is called from the IMR_GuiBean to update the application with the Attenuation's
   * supported IMs.
   *
   */
  public void updateIM() {
 
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
}
