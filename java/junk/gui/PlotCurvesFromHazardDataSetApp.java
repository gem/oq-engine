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
import java.awt.event.MouseEvent;
import java.net.URL;
import java.util.ArrayList;

import javax.swing.BorderFactory;
import javax.swing.ImageIcon;
import javax.swing.JApplet;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JSplitPane;
import javax.swing.UIManager;
import javax.swing.border.BevelBorder;
import javax.swing.border.Border;

import org.jfree.data.Range;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.gui.beans.HazardDataSiteSelectionGuiBean;
import org.opensha.sha.gui.infoTools.ButtonControlPanel;
import org.opensha.sha.gui.infoTools.ButtonControlPanelAPI;
import org.opensha.sha.gui.infoTools.ExceptionWindow;
import org.opensha.sha.gui.infoTools.GraphPanel;
import org.opensha.sha.gui.infoTools.GraphPanelAPI;
import org.opensha.sha.gui.infoTools.GraphWindow;
import org.opensha.sha.gui.infoTools.GraphWindowAPI;


/**
 * <p>Title: PlotCurvesFromHazardDataSetApp</p>
 * <p>Description: Plot the curves from the Hazard Dataset.
 * This application allows the user to select from the existing hazard map dataset,
 * then for that dataset, fill in the latitude and longitude for which curve needs
 * to be plotted.</p>
 * @author Nitin Gupta and Vipin Gupta
 * Date : Sept 23 , 2002
 * @version 1.0
 */

public class PlotCurvesFromHazardDataSetApp extends JApplet
    implements ButtonControlPanelAPI,GraphPanelAPI, GraphWindowAPI{

  /**
   * Name of the class
   */
  private final static String C = "HazardDataSetPlotter";
  // for debug purpose
  private final static boolean D = false;

  //instance for the ButtonControlPanel
  ButtonControlPanel buttonControlPanel;

  //instance of the GraphPanel (window that shows all the plots)
  GraphPanel graphPanel;

  //instance of the GraphWindow to pop up when the user wants to "Peel-Off" curves;
  GraphWindow graphWindow;

  /**
   * List of ArbitrarilyDiscretized functions and Weighted funstions
   */
  private ArrayList functionList = new ArrayList();

  private Insets plotInsets = new Insets( 4, 10, 4, 4 );

  private boolean isStandalone = false;
  private Border border1;

  //log flags declaration
  private boolean xLog =false;
  private boolean yLog =false;

  // default insets
  private Insets defaultInsets = new Insets( 4, 4, 4, 4 );

  // height and width of the applet
  private final static int W = 1100;
  private final static int H = 750;


  //holds the ArbitrarilyDiscretizedFunc
  private ArbitrarilyDiscretizedFunc function;

  private HazardDataSiteSelectionGuiBean siteGuiBean;

  //X and Y Axis  when plotting tha Curves Name
  private String xAxisName = " ";
  private String yAxisName = " ";


  /**
   * these four values save the custom axis scale specified by user
   */
  private double minXValue;
  private double maxXValue;
  private  double minYValue;
  private double maxYValue;
  private boolean customAxis = false;


  private GridBagLayout gridBagLayout4 = new GridBagLayout();
  private GridBagLayout gridBagLayout6 = new GridBagLayout();
  private GridBagLayout gridBagLayout7 = new GridBagLayout();
  private GridBagLayout gridBagLayout3 = new GridBagLayout();



  //flags to check which X Values the user wants to work with: default or custom
  boolean useCustomX_Values = false;


  // Plot title
  private String TITLE = new String("Hazard Curves");

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
  private final static Dimension COMBO_DIM = new Dimension( 180, 30 );
  private final static Dimension BUTTON_DIM = new Dimension( 80, 20 );
  private Border border3;
  private Border border4;
  private Border border5;
  private Border border6;
  private Border border7;
  private Border border8;



  //images for the OpenSHA
   private final static String POWERED_BY_IMAGE = "logos/PoweredByOpenSHA_Agua.jpg";

  //static string for the OPENSHA website
  private final static String OPENSHA_WEBSITE="http://www.OpenSHA.org";

  JSplitPane topSplitPane = new JSplitPane();
  JButton clearButton = new JButton();
  JPanel buttonPanel = new JPanel();
  JButton addButton = new JButton();
  JSplitPane chartSplit = new JSplitPane();
  JPanel panel = new JPanel();
  GridBagLayout gridBagLayout9 = new GridBagLayout();
  JPanel paramsPanel = new JPanel();

  GridBagLayout gridBagLayout15 = new GridBagLayout();
  JPanel imrPanel = new JPanel();
  GridBagLayout gridBagLayout10 = new GridBagLayout();
  BorderLayout borderLayout1 = new BorderLayout();
  private JButton peelOffButton = new JButton();
  private JLabel imgLabel = new JLabel(new ImageIcon(FileUtils.loadImage(this.POWERED_BY_IMAGE)));
  private FlowLayout flowLayout1 = new FlowLayout();
  private GridBagLayout gridBagLayout14 = new GridBagLayout();


  //Get command-line parameter value
  public String getParameter(String key, String def) {
    return isStandalone ? System.getProperty(key, def) :
        (getParameter(key) != null ? getParameter(key) : def);
  }

  //Construct the applet
  public PlotCurvesFromHazardDataSetApp() {

  }
  //Initialize the applet
  public void init() {
    try {



      // initialize the GUI components
      jbInit();

      // initialize the various GUI beans
      initSiteGuiBean();
    }
    catch(Exception e) {
      ExceptionWindow bugWindow = new ExceptionWindow(this,e,
          "Exception occured while launching the application, not parameter value has been set yet");
      bugWindow.setVisible(true);
      bugWindow.pack();
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

    this.setSize(new Dimension(1060, 670));
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

    buttonPanel.setAlignmentX((float) 0.0);
    buttonPanel.setAlignmentY((float) 0.0);
    buttonPanel.setMinimumSize(new Dimension(568, 20));
    buttonPanel.setLayout(flowLayout1);


    addButton.setText("Add Plot");
    addButton.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        addButton_actionPerformed(e);
      }
    });


    panel.setLayout(gridBagLayout9);
    panel.setBackground(Color.white);
    panel.setBorder(border5);
    panel.setMinimumSize(new Dimension(0, 0));


    imrPanel.setLayout(gridBagLayout15);
    imrPanel.setBackground(Color.white);
    chartSplit.setLeftComponent(panel);
    chartSplit.setRightComponent(paramsPanel);



    peelOffButton.setText("Peel Off");
    peelOffButton.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        peelOffButton_actionPerformed(e);
      }
    });


    imgLabel.addMouseListener(new java.awt.event.MouseAdapter() {
      public void mouseClicked(MouseEvent e) {
        imgLabel_mouseClicked(e);
      }
    });
    paramsPanel.setLayout(gridBagLayout14);
    this.getContentPane().add(jPanel1, BorderLayout.CENTER);
    jPanel1.add(topSplitPane,  new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
            ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(11, 4, 5, 6), 243, 231));

    //object for the ButtonControl Panel
    buttonControlPanel = new ButtonControlPanel(this);
    buttonPanel.add(addButton, 0);
    buttonPanel.add(clearButton, 1);
    buttonPanel.add(peelOffButton, 2);
    buttonPanel.add(buttonControlPanel,3);
    buttonPanel.add(imgLabel, 4);
    topSplitPane.add(chartSplit, JSplitPane.TOP);
    topSplitPane.add(buttonPanel, JSplitPane.BOTTOM);
    chartSplit.add(panel, JSplitPane.LEFT);
    chartSplit.add(paramsPanel, JSplitPane.RIGHT);
    topSplitPane.setDividerLocation(600);
    chartSplit.setDividerLocation(600);

  }


  /**
   * Initialize the site gui bean
   */
  private void initSiteGuiBean() {

     // create the Site Gui Bean object
     siteGuiBean = new HazardDataSiteSelectionGuiBean();
     // show the sitebean in JPanel
     paramsPanel.add(siteGuiBean, new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0,
           GridBagConstraints.CENTER, GridBagConstraints.BOTH, defaultInsets, 0, 0 ));
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
    return "Hazard Data Set Plotter Applet";
  }


  //Main method
  public static void main(String[] args) {
    PlotCurvesFromHazardDataSetApp application = new PlotCurvesFromHazardDataSetApp();
    application.isStandalone = true;
    JFrame frame = new JFrame();
    //EXIT_ON_CLOSE == 3
    frame.setDefaultCloseOperation(3);
    frame.setTitle(application.getAppletInfo());
    frame.getContentPane().add(application, BorderLayout.CENTER);
    application.init();
    application.start();
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




    /**
     * this function is called to draw the graph
     */
    private void addButton() {
      String S = C + ": addButton(): ";
      if ( D ) System.out.println( S + "Starting" );


      DiscretizedFuncAPI function =null;
      try{
        //getting the function from the site for the selected site.
        function = siteGuiBean.getChoosenFunction();
      }catch(RuntimeException e){
        JOptionPane.showMessageDialog(this,e.getMessage(),"Incorrect Parameter Input",JOptionPane.ERROR_MESSAGE);
        return;
      }

      if ( D ) System.out.println( S + "New Function info = " + function.getInfo() );

      //functions.setYAxisName( attenRel.getGraphIMYAxisLabel() );
      //functions.setXAxisName( attenRel.getGraphXAxisLabel() );
      //if( !functions.contains( function ) )
      functionList.add(function);
      addGraphPanel();
      if ( D ) System.out.println( S + "Ending" );

    }

    /**
     * to draw the graph
     */
    private void drawGraph() {
      // you can show warning messages now
     // set the log values

     addGraphPanel();
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

    if( clearFunctions) {
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



  void imgLabel_mouseClicked(MouseEvent e) {
    try{
      this.getAppletContext().showDocument(new URL(OPENSHA_WEBSITE), "new_peer_win");
    }catch(java.net.MalformedURLException ee){
      JOptionPane.showMessageDialog(this,new String("No Internet Connection Available"),
                                    "Error Connecting to Internet",JOptionPane.OK_OPTION);
    }
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
   * @returns the instance to the JPanel showing the JFreechart adn metadata
   */
  public GraphPanel getGraphPanel(){
    return graphPanel;
  }


  /**
   *
   * @returns the DiscretizedFuncList for all the data curves
   */
  public ArrayList getCurveFunctionList(){
    return functionList;
  }

  /**
   * plots the curves with defined color,line width and shape.
   *
   */
  public void plotGraphUsingPlotPreferences(){
    drawGraph();
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
   * Action method to "Peel-Off" the curves graph window in a seperate window.
   * This is called when the user presses the "Peel-Off" window.
   * @param e
   */
  void peelOffButton_actionPerformed(ActionEvent e) {
    peelOffCurves();
  }

  /**
   *
   * @returns the plotting feature like width, color and shape type of each
   * curve in list.
   */
  public ArrayList getPlottingFeatures(){
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

}
