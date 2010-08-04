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

package org.opensha.commons.gui.plot.jfreechart.logTest;

import java.awt.AWTEvent;
import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.Frame;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.KeyEvent;
import java.awt.event.WindowEvent;
import java.util.ArrayList;
import java.util.Iterator;

import javax.swing.BorderFactory;
import javax.swing.ButtonGroup;
import javax.swing.JApplet;
import javax.swing.JButton;
import javax.swing.JComboBox;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JRadioButton;
import javax.swing.JSplitPane;
import javax.swing.JTextField;
import javax.swing.border.EtchedBorder;

import org.jfree.chart.ChartPanel;
import org.jfree.chart.JFreeChart;
import org.jfree.chart.axis.LogarithmicAxis;
import org.jfree.chart.axis.NumberAxis;
import org.jfree.chart.labels.StandardXYToolTipGenerator;
import org.jfree.chart.renderer.xy.StandardXYItemRenderer;
import org.jfree.data.Range;
import org.jfree.data.xy.XYSeries;
import org.jfree.data.xy.XYSeriesCollection;
import org.jfree.ui.RectangleInsets;




/**

 * <p>Title: JFreeLogPlotTesterApp</p>
 * <p>Description: This Applet checks for the log-plots</p>
 *
 * @author: Nitin Gupta & Vipin Gupta
 * @date:November 13,2002
 * @version 1.0
 */

public class JFreeLogPlotTesterApp extends JApplet  {

  // for debug purposes
  protected final static String C = "JFreeLogPlotTesterApp";
  protected final static boolean D = false;

  //auto scales the graph
  private boolean autoScale =true;

  private boolean isStandalone = false;
  private JSplitPane jSplitPane1 = new JSplitPane();
  private JPanel innerPlotPanel = new JPanel();
  private JPanel jPanel2 = new JPanel();
  private JLabel jLabel1 = new JLabel();
  private JComboBox rangeCombo = new JComboBox();
  private JLabel jLabel2 = new JLabel();
  private JLabel jLabel3 = new JLabel();
  private JLabel jLabel4 = new JLabel();
  private JLabel jLabel5 = new JLabel();
  private JTextField minXText = new JTextField();
  private JTextField maxXText = new JTextField();
  private JTextField minYText = new JTextField();
  private JTextField maxYText = new JTextField();
  private JButton addButton = new JButton();
  private JButton clearButton = new JButton();

  //this vector stores the different plot ranges text string
  private ArrayList logRanges = new ArrayList();

  //static string declaration for the test cases
  private static final String TEST_0= new String("Auto Scale"); // draws the graph according to the given default values
  private static final String TEST_1= new String("Preset-1");
  private static final String TEST_2= new String("Preset-2");
  private static final String TEST_3= new String("Preset-3");
  private static final String TEST_4= new String("Preset-4");
  private static final String TEST_5= new String("Preset-5");
  private static final String TEST_6= new String("Preset-6");
  private static final String TEST_7= new String("Preset-7");
  private static final String TEST_8= new String("Preset-8");
  private static final String TEST_9= new String("Preset-9");
  private static final String TEST_10= new String("Preset-10");
  private static final String TEST_11= new String("Preset-11");
  private static final String TEST_12= new String("Preset-12");
  private static final String TEST_13= new String("Preset-13");
  private static final String TEST_14= new String("Preset-14");
  private static final String TEST_15= new String("Preset-15");
  private static final String CUSTOM_SCALE = new String("Custom Scale");

  //static string to choose the type of Axis
  private static final String LOG = "Log Scale";
  private static final String LINEAR = "Linear Scale";

  // title for the chart
  private static final String TITLE = "Log-Log Testing";



  //Static Strings that determine the selection in the Set DataSet Combo selection
  private static final String USE_DEFAULT = "Use Default";
  private static final String NEW_DATASET = "Enter New Data";

  // chart Panel

  //variables that determine the window size
  protected final static int W = 820;
  protected final static int H = 670;


  /**
   * for Y-log, 0 values will be converted to this small value
   */
  private double Y_MIN_VAL = 1e-8;

  /**
   * these four values save the log axis scale specified by selection of different
   * test cases for the logPlot
   */
  protected double minXValue;
  protected double maxXValue;
  protected double minYValue;
  protected double maxYValue;

  // Create the x-axis and y-axis - either normal or log
  org.jfree.chart.axis.NumberAxis xAxis = null;
  org.jfree.chart.axis.NumberAxis yAxis = null;
  XYSeriesCollection functions = new XYSeriesCollection();
 // DiscretizedFunctionXYDataSet data = new DiscretizedFunctionXYDataSet();

  Color lightBlue = new Color( 200, 200, 230 );
  Insets defaultInsets = new Insets( 0, 0, 0, 0 );
  private JComboBox dataSetCombo = new JComboBox();
  private JLabel jLabel6 = new JLabel();
  //draws the XY Plot
  private ChartPanel panel;
  private GridBagLayout gridBagLayout2 = new GridBagLayout();
  private BorderLayout borderLayout1 = new BorderLayout();
  private JRadioButton log10CaretCheck = new JRadioButton();

  private JRadioButton log10AsECheck = new JRadioButton();

  private ButtonGroup group = new ButtonGroup();

  //declaration for the class that lets the user to enter his own data
  private XYDataWindow dataWindow ;
  private JLabel jLabel7 = new JLabel();
  private JComboBox axisCombo = new JComboBox();
  private GridBagLayout gridBagLayout1 = new GridBagLayout();

  //Get a parameter value
  public String getParameter(String key, String def) {
    return isStandalone ? System.getProperty(key, def) :
        (getParameter(key) != null ? getParameter(key) : def);
  }

  //Construct the applet
  public JFreeLogPlotTesterApp() {

    logRanges.add(TEST_0);
    logRanges.add(CUSTOM_SCALE);
    logRanges.add(TEST_1);
    logRanges.add(TEST_2);
    logRanges.add(TEST_3);
    logRanges.add(TEST_4);
    logRanges.add(TEST_5);
    logRanges.add(TEST_6);
    logRanges.add(TEST_7);
    logRanges.add(TEST_8);
    logRanges.add(TEST_9);
    logRanges.add(TEST_10);
    logRanges.add(TEST_11);
    logRanges.add(TEST_12);
    logRanges.add(TEST_13);
    logRanges.add(TEST_14);
    logRanges.add(TEST_15);
  }
  //Initialize the applet
  public void init() {
    try {
      jbInit();
    }
    catch(Exception e) {
      e.printStackTrace();
    }

    // initialize the current IMR
      initLogPlotGui();
  }


  /**
   *  This must be called before the logPlots are generated. This is what initializes the
   *  Gui
   */
  protected void initLogPlotGui() {

    // starting
    String S = C + ": initLogPlotGui(): ";

    //creating the axis Combo selection option
    axisCombo.addItem(LOG);
    axisCombo.addItem(LINEAR);
    axisCombo.setSelectedItem(LOG);

    //creating the dataSelection combo
    dataSetCombo.addItem(USE_DEFAULT);
    dataSetCombo.addItem(NEW_DATASET);
    dataSetCombo.setSelectedItem(USE_DEFAULT);

    Iterator it = this.logRanges.iterator();
    while ( it.hasNext() )
      rangeCombo.addItem(it.next());
    rangeCombo.setSelectedItem((String)rangeCombo.getItemAt(0));
  }


  //Component initialization
  private void jbInit() throws Exception {
    this.getContentPane().setLayout(borderLayout1);
    jPanel2.setLayout(gridBagLayout1);
    jLabel1.setFont(new java.awt.Font("Dialog", 1, 12));
    jLabel1.setForeground(new Color(80, 80, 133));
    jLabel1.setText("Test Case:");
    jLabel2.setFont(new java.awt.Font("Dialog", 1, 12));
    jLabel2.setForeground(new Color(80, 80, 133));
    jLabel2.setText("Min X:");
    jLabel3.setFont(new java.awt.Font("Dialog", 1, 12));
    jLabel3.setForeground(new Color(80, 80, 133));
    jLabel3.setText("Max X:");
    jLabel4.setFont(new java.awt.Font("Dialog", 1, 12));
    jLabel4.setForeground(new Color(80, 80, 133));
    jLabel4.setText("Min Y:");
    jLabel5.setFont(new java.awt.Font("Dialog", 1, 12));
    jLabel5.setForeground(new Color(80, 80, 133));
    jLabel5.setText("Max Y:");
    addButton.setBackground(new Color(200, 200, 230));
    addButton.setFont(new java.awt.Font("Dialog", 1, 10));
    addButton.setForeground(new Color(80, 80, 133));
    addButton.setText("Add Plot");
    addButton.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        addButton_actionPerformed(e);
      }
    });
    clearButton.setBackground(new Color(200, 200, 230));
    clearButton.setFont(new java.awt.Font("Dialog", 1, 10));
    clearButton.setForeground(new Color(80, 80, 133));
    clearButton.setText("Clear Plot");
    clearButton.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        clearButton_actionPerformed(e);
      }
    });
    innerPlotPanel.setLayout(gridBagLayout2);
    jSplitPane1.setDividerSize(5);
    jPanel2.setBackground(Color.white);
    rangeCombo.setBackground(new Color(200, 200, 230));
    rangeCombo.setForeground(new Color(80, 80, 133));
    rangeCombo.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        rangeCombo_actionPerformed(e);
      }
    });
    innerPlotPanel.setBackground(Color.white);
    minXText.addKeyListener(new java.awt.event.KeyAdapter() {
      public void keyTyped(KeyEvent e) {
        minXText_keyTyped(e);
      }
    });
    maxXText.addKeyListener(new java.awt.event.KeyAdapter() {
      public void keyTyped(KeyEvent e) {
        maxXText_keyTyped(e);
      }
    });
    minYText.addKeyListener(new java.awt.event.KeyAdapter() {
      public void keyTyped(KeyEvent e) {
        minYText_keyTyped(e);
      }
    });
    maxYText.addKeyListener(new java.awt.event.KeyAdapter() {
      public void keyTyped(KeyEvent e) {
        maxYText_keyTyped(e);
      }
    });
    jLabel6.setFont(new java.awt.Font("Lucida Grande", 1, 13));
    jLabel6.setForeground(new Color(80, 80, 133));
    jLabel6.setText("Set DataSet:");
    log10CaretCheck.setText("Set tick as(10^N)");
    log10CaretCheck.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        log10CaretCheck_actionPerformed(e);
      }
    });

    log10AsECheck.setText("Set tick as (1e#)");
    log10AsECheck.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        log10AsECheck_actionPerformed(e);
      }
    });

    dataSetCombo.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        dataSetCombo_actionPerformed(e);
      }
    });
    jLabel7.setFont(new java.awt.Font("Lucida Grande", 1, 13));
    jLabel7.setForeground(new Color(80, 80, 133));
    jLabel7.setText("Axis:");


    axisCombo.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        axisCombo_actionPerformed(e);
      }
    });
    jSplitPane1.add(innerPlotPanel, JSplitPane.LEFT);
    jSplitPane1.add(jPanel2, JSplitPane.RIGHT);
    jPanel2.add(minXText,  new GridBagConstraints(1, 1, 3, 1, 1.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(0, 0, 0, 10), 131, 4));
    jPanel2.add(rangeCombo,  new GridBagConstraints(1, 0, 3, 1, 1.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL, new Insets(120, 0, 0, 10), -4, -2));
    jPanel2.add(maxXText,  new GridBagConstraints(1, 2, 3, 1, 1.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(0, 0, 0, 10), 131, 4));
    jPanel2.add(minYText,  new GridBagConstraints(1, 3, 3, 1, 1.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(0, 0, 0, 10), 131, 4));
    jPanel2.add(maxYText,  new GridBagConstraints(1, 4, 3, 1, 1.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(0, 0, 0, 10), 131, 4));
    jPanel2.add(jLabel2,  new GridBagConstraints(0, 1, 1, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(0, 15, 0, 0), 23, 9));
    jPanel2.add(jLabel1,  new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(120, 1, 0, 0), 17, 9));
    jPanel2.add(jLabel3,  new GridBagConstraints(0, 2, 1, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(0, 15, 0, 7), 17, 9));
    jPanel2.add(jLabel4,  new GridBagConstraints(0, 3, 1, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(0, 15, 0, 12), 17, 9));
    jPanel2.add(jLabel5,  new GridBagConstraints(0, 4, 1, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(0, 15, 0, 18), 7, 9));
    jPanel2.add(clearButton,  new GridBagConstraints(3, 11, 1, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(109, 0, 63, 10), 23, 6));
    jPanel2.add(addButton,  new GridBagConstraints(0, 11, 3, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(109, 8, 63, 0), 17, 6));
    jPanel2.add(log10CaretCheck,  new GridBagConstraints(0, 7, 4, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(24, 12, 0, 24), 65, 8));

    jPanel2.add(log10AsECheck,  new GridBagConstraints(0, 9, 4, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(21, 12, 0, 24), 72, 8));

    jPanel2.add(dataSetCombo,  new GridBagConstraints(2, 6, 2, 1, 1.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL, new Insets(12, 0, 0, 10), -13, 3));
    jPanel2.add(jLabel6,  new GridBagConstraints(0, 6, 2, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(12, 7, 0, 0), 6, 8));
    jPanel2.add(jLabel7,  new GridBagConstraints(0, 5, 1, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(19, 8, 0, 0), 35, 12));
    jPanel2.add(axisCombo,  new GridBagConstraints(2, 5, 2, 1, 1.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL, new Insets(19, 0, 0, 10), -13, 3));
    this.getContentPane().add(jSplitPane1, BorderLayout.CENTER);
    jSplitPane1.setDividerLocation(500);

    group.add(log10AsECheck);
    group.add(log10CaretCheck);
    group.setSelected(log10CaretCheck.getModel(),true);
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
    JFreeLogPlotTesterApp applet = new JFreeLogPlotTesterApp();
    applet.isStandalone = true;
    Frame frame;
    frame = new Frame() {
      protected void processWindowEvent(WindowEvent e) {
        super.processWindowEvent(e);
        if (e.getID() == WindowEvent.WINDOW_CLOSING) {
          System.exit(0);
        }
      }
      public synchronized void setTitle(String title) {
        super.setTitle(title);
        enableEvents(AWTEvent.WINDOW_EVENT_MASK);
      }
    };
    frame.setTitle("Log Plot Tester Applet");
    frame.add(applet, BorderLayout.CENTER);
    applet.init();
    applet.start();
    frame.setSize(W,H);
    Dimension d = Toolkit.getDefaultToolkit().getScreenSize();
    frame.setLocation((d.width - frame.getSize().width) / 2, (d.height - frame.getSize().height) / 2);
    frame.setVisible(true);
  }

  /**
   *  This causes the model data to be calculated and a plot trace added to
   *  the current plot
   *
   * @param  e  The feature to be added to the Button_mouseClicked attribute
   */
  void addButton_actionPerformed(ActionEvent e){
     addButton();
  }

  private void addButton(){
    String S = C + ": addButton(): ";
    if ( D ) System.out.println( S + "Starting" );
    clearPlot();
    if(((String)dataSetCombo.getSelectedItem()).equals(this.NEW_DATASET)){
      functions.addSeries(dataWindow.getDataSet());
      autoScale = true;
    }
    else
      fillValues(new XYSeries("Default Data"));

    //if ( D ) System.out.println( S + "New Function info = " + function.getInfo() );

    addGraphPanel();
    return;
  }

  /**
   * this method is the interface between the JFreechart plotting capability
   * and our added requirements.
   */

  void addGraphPanel() {

    // Starting
    String S = C + ": addGraphPanel(): ";


    if(!autoScale){
      // get the min and max Y values
      minYValue=Double.parseDouble(minYText.getText());
      maxYValue=Double.parseDouble(maxYText.getText());

      //get the min and max Y values
      minXValue=Double.parseDouble(minXText.getText());
      maxXValue=Double.parseDouble(maxXText.getText());
    }

    //create the standard ticks so that smaller values too can plotted on the chart
    //TickUnits units = MyTickUnits.createStandardTickUnits();
    this.setAxis();


    if(this.axisCombo.getSelectedItem().equals(LOG)){
      if(this.log10AsECheck.isSelected()) setLog10AsEFlag();
      else if(this.log10CaretCheck.isSelected()) setLog10AsCaretFlag();
    }



    int type = StandardXYItemRenderer.LINES;

    StandardXYItemRenderer renderer = new StandardXYItemRenderer(type, new StandardXYToolTipGenerator() );


    xAxis.setAutoRangeIncludesZero( false );
    //xAxis.setStandardTickUnits(units);
    xAxis.setTickMarksVisible(false);

    yAxis.setAutoRangeIncludesZero( false );
    //yAxis.setStandardTickUnits(units);
    yAxis.setTickMarksVisible(false);

    //If the first test case is not chosen then plot the graph acording to the default x and y axis values
    if(!autoScale){
      xAxis.setRange(minXValue,maxXValue);
      yAxis.setRange(minYValue,maxYValue);
    }


    // build the plot
    org.jfree.chart.plot.XYPlot plot =null;

    plot = new org.jfree.chart.plot.XYPlot(functions, xAxis, yAxis,renderer);
    plot.setBackgroundAlpha( .8f );
    plot.setRenderer( renderer );
    plot.setDomainCrosshairLockedOnData(false);
    plot.setDomainCrosshairVisible(false);
    plot.setRangeCrosshairLockedOnData(false);
    plot.setRangeCrosshairVisible(false);
    plot.setInsets(new RectangleInsets(0, 0, 0, 15));

    JFreeChart chart = new JFreeChart(TITLE, JFreeChart.DEFAULT_TITLE_FONT, plot,false);
    chart.setBackgroundPaint( lightBlue );
    panel = new ChartPanel(chart, true, true, true, true, true);

    panel.setBorder( BorderFactory.createEtchedBorder( EtchedBorder.LOWERED ) );
    panel.setMouseZoomable(true);
    panel.setDisplayToolTips(true);
    panel.setHorizontalAxisTrace(false);
    panel.setVerticalAxisTrace(false);
    innerPlotPanel.removeAll();
    // panel added here
    innerPlotPanel.add( panel, new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0
        , GridBagConstraints.CENTER, GridBagConstraints.BOTH, defaultInsets, 0, 0 )
        );


    //setting the range to reflect in the range Text fields.
    if(dataSetCombo.getItemCount()>0){
      if(((String)dataSetCombo.getSelectedItem()).equals(this.NEW_DATASET)){
        setXRange(xAxis.getLowerBound(),xAxis.getUpperBound());
        setYRange(yAxis.getLowerBound(),yAxis.getUpperBound());
      }
    }

    innerPlotPanel.validate();
    innerPlotPanel.repaint();
    if ( D ) System.out.println( S + "Done" );
  }




  /**
   * sets the range for X-axis
   * @param xMin : minimum value for X-axis
   * @param xMax : maximum value for X-axis
   */
  public void setXRange(double xMin,double xMax) {
    minXText.setText(""+xMin);
    maxXText.setText(""+xMax);
  }

  /**
   * sets the range for Y-axis
   * @param yMin : minimum value for Y-axis
   * @param yMax : maximum value for Y-axis
   */
  public void setYRange(double yMin,double yMax) {
    minYText.setText(""+yMin);
    maxYText.setText(""+yMax);
  }

  void clearButton_actionPerformed(ActionEvent e) {
    clearPlot();
  }

  void clearPlot(){
    functions.removeAllSeries();
    innerPlotPanel.removeAll();
    panel = null;

    validate();
    repaint();
  }



  /**
   * this function sets the initial X and Y values for which log plot has to be generated.
   * @param function : XYSeries Object
   */
  private  void fillValues(XYSeries function) {


   // function.set(0.0 , 0.3709240147258726);
    /*function.add(1.02, 0.3252989675766);
    function.add(2.03,0.28831584981256364);
    function.add(3.04, 0.25759059645019516);
    function.add(4.05 ,0.2317579929371139);
    function.add(5.06  , 0.2098100264835782);
    function.add(6.07 ,0.19098853513049038);
    function.add(7.08,0.17471387488216564);
    function.add(8.09 ,0.16053638059488);
    function.add(9.1 , 0.1481026319892149);
    function.add(10.11, 0.13713156153136677);
    function.add(11.12, 0.12739724227876123);
    function.add(12.13, 0.11871629546658767);
    function.add(13.14, 0.11093854783560243);
    function.add(14.15, 0.1039400106842495);
    function.add(15.16, 0.09761754132663052);
    function.add(16.17, 0.09188473966503793);
    function.add(17.18, 0.08666876245566242);
    function.add(18.19, 0.08190782703460522);
    function.add(19.2 , 0.07754923839501857);
    function.add(20.21, 0.07354781734946621);
    function.add(21.22, 0.06986463883316718);
    function.add(22.23, 0.06646601203555078);
    function.add(23.24, 0.06332265057486956);
    function.add(24.25, 0.06040899312057254);
    function.add(25.26, 0.0577026439432351);
    function.add(26.27, 0.055183909687492975);
    function.add(27.28, 0.05283541382461658);
    function.add(28.29, 0.050641774180271305);
    function.add(29.3 , 0.048589331961324214);
    function.add(30.31, 0.04666592305007844);
    function.add(31.32, 0.04486068416147701);
    function.add(32.33, 0.04316388789175837);
    function.add(33.34, 0.04156680181753229);
    function.add(34.35, 0.040061567701209534);
    function.add(35.36, 0.038641097574252305);
    function.add(36.37, 0.03729898404347587);
    function.add(37.38, 0.036029422627983136);
    function.add(38.39, 0.0348271443086532);
    function.add(39.4 , 0.03368735677655461);
    function.add(40.41, 0.03260569311533537);
    function.add(41.42, 0.03157816685661586);
    function.add(42.43, 0.03060113251538157);
    function.add(43.44, 0.02967125085122234);
    function.add(44.45, 0.02878545821647051);
    function.add(45.46, 0.027940939448209676);
    function.add(46.47, 0.027135103841264246);
    function.add(47.48, 0.026365563806454308);
    function.add(48.49, 0.025630115874880878);
    function.add(49.5 , 0.02492672375664805);
    function.add(50.51, 0.0242535032027259);
    function.add(51.52, 0.023608708452845288);
    function.add(52.53, 0.02299072008139646);
    function.add(53.54, 0.02239803407810713);
    function.add(54.55, 0.02182925202148683);
    function.add(55.56, 0.021283072221205696);
    function.add(56.57, 0.020758281721201435);
    function.add(57.58, 0.02025374906876637);
    function.add(58.59, 0.01976841776648345);
    function.add(59.6 , 0.01930130033393358);
    function.add(60.61, 0.018851472914810853);
    function.add(61.62, 0.01841807037265436);
    function.add(62.63, 0.018000281824998316);
    function.add(63.64, 0.01759734657149157);
    function.add(64.65, 0.017208550376563294);
    function.add(65.66, 0.01683322207161208);
    function.add(66.67, 0.016470730445554187);
    function.add(67.68, 0.016120481395959056);
    function.add(68.69, 0.01578191531598401);
    function.add(69.7,  0.015454504694952256);
    function.add(70.71, 0.01513775191274188);
    function.add(71.72, 0.014831187210208815);
    function.add(72.73, 0.014534366819687384);
    function.add(73.74, 0.014246871241227393);
    function.add(74.75, 0.01396830365166128);
    function.add(75.76, 0.013698288434872056);
    function.add(76.77, 0.013436469822769696);
    function.add(77.78, 0.013182510637499117);
    function.add(78.79, 0.012936091126308585);
    function.add(79.8 , 0.012696907881319344);
    function.add(80.81, 0.012464672837162585);
    function.add(81.82, 0.0122391123401022);
    function.add(82.83, 0.012019966282845403);
    function.add(83.84, 0.01180698729977027);
    function.add(84.85, 0.011599940017770862);
    function.add(85.86, 0.011398600358348401);
    function.add(86.87, 0.01120275488695998);
    function.add(87.88, 0.011012200205984302);
    function.add(88.89, 0.010826742387977394);
    function.add(89.9 , 0.010646196446175296);
    function.add(90.91, 0.010470385839457589);
    function.add(91.92, 0.010299142009219399);
    function.add(92.93, 0.010132303945810278);
    function.add(93.94, 0.009969717782391493);
    function.add(94.95, 0.009811236414237418);
    function.add(95.96, 0.009656719141666239);
    function.add(96.97, 0.00950603133492957);
    function.add(97.98, 0.00935904411952373);
    function.add(98.99, 0.00921563408050459);*/
    function.add(-20,-20);
    function.add(20, 20);

    functions.addSeries(function);
  }

  /**
   * if user types by hand in any of the fields, then do not autoscale
   * @param e
   */
  void minXText_keyTyped(KeyEvent e) {
    this.autoScale = false;
  }

  /**
   * if user types by hand in any of the fields, then do not autoscale
   * @param e
   */
  void maxXText_keyTyped(KeyEvent e) {
    this.autoScale = false;
  }

  /**
   * if user types by hand in any of the fields, then do not autoscale
   * @param e
   */
  void minYText_keyTyped(KeyEvent e) {
    this.autoScale = false;
  }

  /**
   * if user types by hand in any of the fields, then do not autoscale
   * @param e
   */
  void maxYText_keyTyped(KeyEvent e) {
    this.autoScale = false;
  }

  //sets the default range for the log Plots
  void rangeCombo_actionPerformed(ActionEvent e) {
    if(rangeCombo.getSelectedItem().toString().equalsIgnoreCase(TEST_0)){
      autoScale=true;
      addButton();
      Range rX = xAxis.getRange();
      Range rY= yAxis.getRange();
      setXRange(rX.getLowerBound(),rX.getUpperBound());
      setYRange(rY.getLowerBound(),rY.getUpperBound());
      showRangeFields(false);
    }
    else {
      autoScale=false;
      showRangeFields(true);
      if(rangeCombo.getSelectedItem().toString().equalsIgnoreCase(TEST_1)){
        setXRange(.5e-20,1e-20);
        setYRange(.5e-20,1e-20);
      }
      else if(rangeCombo.getSelectedItem().toString().equalsIgnoreCase(TEST_2)){
        setXRange(1e-20,1e-19);
        setYRange(1e-20,1e-19);
      }
      else if(rangeCombo.getSelectedItem().toString().equalsIgnoreCase(TEST_3)){
        setXRange(1e-20,1e-17);
        setYRange(1e-20,1e-17);
      }
      else if(rangeCombo.getSelectedItem().toString().equalsIgnoreCase(TEST_4)){
        setXRange(1e-20,1e-16);
        setYRange(1e-20,1e-16);
      }
      else if(rangeCombo.getSelectedItem().toString().equalsIgnoreCase(TEST_5)){
        setXRange(1e-20,1e-15);
        setYRange(1e-20,1e-15);
      }
      else if(rangeCombo.getSelectedItem().toString().equalsIgnoreCase(TEST_6)){
        setXRange(1e-11,1e-7);
        setYRange(1e-11,1e-7);
      }
      else if(rangeCombo.getSelectedItem().toString().equalsIgnoreCase(TEST_7)){
        setXRange(1e-2,10);
        setYRange(1e-2,10);
      }
      else if(rangeCombo.getSelectedItem().toString().equalsIgnoreCase(TEST_8)){
        setXRange(1e-2,100);
        setYRange(1e-2,100);
      }
      else if(rangeCombo.getSelectedItem().toString().equalsIgnoreCase(TEST_9)){
        setXRange(1e-2,1000);
        setYRange(1e-2,1000);
      }
      else if(rangeCombo.getSelectedItem().toString().equalsIgnoreCase(TEST_10)){
        setXRange(10,10000);
        setYRange(10,10000);
      }
      else if(rangeCombo.getSelectedItem().toString().equalsIgnoreCase(TEST_11)){
        setXRange(10,100000);
        setYRange(10,100000);
      }
      else if(rangeCombo.getSelectedItem().toString().equalsIgnoreCase(TEST_12)){
        setXRange(2,2);
        setYRange(2,2);
      }
      else if(rangeCombo.getSelectedItem().toString().equalsIgnoreCase(TEST_13)){
        setXRange(1,1);
        setYRange(1,1);
      }
      else if(rangeCombo.getSelectedItem().toString().equalsIgnoreCase(TEST_14)){
        setXRange(10e4,10e6);
        setYRange(10e4,10e6);
      }
      else if(rangeCombo.getSelectedItem().toString().equalsIgnoreCase(TEST_15)){
        setXRange(2,8);
        setYRange(2,8);
      }
      else if(rangeCombo.getSelectedItem().toString().equalsIgnoreCase(CUSTOM_SCALE)){
        minXText.setText("");
        maxXText.setText("");
        minYText.setText("");
        maxYText.setText("");
        return;
      }
    }
    this.addGraphPanel();

  }

  /**
   * This function enables or disable the ablity to enter the text in the
   * Range text fields.
   * @param flag
   */
  private void showRangeFields(boolean flag){
      minXText.setEnabled(flag);
      maxXText.setEnabled(flag);
      minYText.setEnabled(flag);
      maxYText.setEnabled(flag);
  }

  void dataSetCombo_actionPerformed(ActionEvent e) {
    if(((String)dataSetCombo.getSelectedItem()).equals(NEW_DATASET)){
      if(dataWindow ==null)
        dataWindow = new XYDataWindow(this,functions);
      dataWindow.setVisible(true);
      dataWindow.pack();
    }
  }

  void log10CaretCheck_actionPerformed(ActionEvent e) {
   setLog10AsCaretFlag();
   this.addGraphPanel();
  }

  private void setLog10AsCaretFlag(){
    if(log10CaretCheck.isSelected()){
      ((LogarithmicAxis)xAxis).setAllowNegativesFlag(true);
      ((LogarithmicAxis)yAxis).setAllowNegativesFlag(true);
      ((LogarithmicAxis)xAxis).setLog10TickLabelsFlag(true);
      ((LogarithmicAxis)yAxis).setLog10TickLabelsFlag(true);
    }
  }



  void log10AsECheck_actionPerformed(ActionEvent e) {
    setLog10AsEFlag();
    this.addGraphPanel();
  }

  private void setLog10AsEFlag(){
    if(log10AsECheck.isSelected()){
      ((LogarithmicAxis)xAxis).setAllowNegativesFlag(true);
      ((LogarithmicAxis)yAxis).setAllowNegativesFlag(true);
      ((LogarithmicAxis)xAxis).setLog10TickLabelsFlag(false);
      ((LogarithmicAxis)yAxis).setLog10TickLabelsFlag(false);
      ((LogarithmicAxis)xAxis).setExpTickLabelsFlag(true);
      ((LogarithmicAxis)yAxis).setExpTickLabelsFlag(true);
    }
  }




  private void setAxis(){
    String axisOption = (String)axisCombo.getSelectedItem();
    if(axisOption.equals(LOG)){
      xAxis = new LogarithmicAxis("X-Axis");
      yAxis = new LogarithmicAxis("Y-Axis");
      log10AsECheck.setVisible(true);
      log10CaretCheck.setVisible(true);
    }
    else {
      xAxis = new NumberAxis("X-Axis");
      yAxis = new NumberAxis("Y-Axis");
      log10AsECheck.setVisible(false);
      log10CaretCheck.setVisible(false);
    }
  }

  void axisCombo_actionPerformed(ActionEvent e) {
    setAxis();
    addGraphPanel();
  }
}
