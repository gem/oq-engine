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

package org.opensha.sha.magdist.gui;

import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.Paint;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.ItemEvent;
import java.awt.event.ItemListener;
import java.awt.event.MouseEvent;
import java.net.URL;
import java.util.ArrayList;

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
import javax.swing.JScrollPane;
import javax.swing.JSplitPane;
import javax.swing.JTextArea;
import javax.swing.JTextPane;
import javax.swing.SwingConstants;
import javax.swing.UIManager;
import javax.swing.border.Border;
import javax.swing.border.EtchedBorder;
import javax.swing.text.BadLocationException;
import javax.swing.text.Document;
import javax.swing.text.SimpleAttributeSet;
import javax.swing.text.StyleConstants;

import org.jfree.chart.ChartPanel;
import org.jfree.chart.JFreeChart;
import org.jfree.chart.axis.NumberAxis;
import org.jfree.chart.axis.TickUnits;
import org.jfree.chart.labels.StandardXYToolTipGenerator;
import org.jfree.chart.renderer.xy.StandardXYItemRenderer;
import org.jfree.data.Range;
import org.opensha.commons.data.function.DiscretizedFuncList;
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;
import org.opensha.commons.gui.OvalBorder;
import org.opensha.commons.gui.SidesBorder;
import org.opensha.commons.gui.plot.jfreechart.DiscretizedFunctionXYDataSet;
import org.opensha.commons.gui.plot.jfreechart.MyTickUnits;
import org.opensha.commons.param.editor.ParameterListEditor;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.magdist.GaussianMagFreqDist;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.magdist.SingleMagFreqDist;
import org.opensha.sha.magdist.SummedMagFreqDist;
import org.opensha.sha.magdist.YC_1985_CharMagFreqDist;
import org.opensha.sha.param.MagFreqDistParameter;
import org.opensha.sha.param.editor.MagFreqDistParameterEditor;

/**
 * <p>Title: MagFreqDistTesterApplet</p>
 * <p>Description: </p>
 *
 * @author : Nitin Gupta and Vipin Gupta  Date: Aug,9,2002
 * @version 1.0
 */

public class MagFreqDistTesterApplet extends JApplet
            implements ItemListener {


  protected final static String C = "MagFreqDistTesterApplet";
  private final static String version = "0.0.3";
  protected final static boolean D = false;


  /**
   * these four values save the custom axis scale specified by user
   */
  protected float minXValue;
  protected float maxXValue;
  protected float minYValue;
  protected float maxYValue;

  protected boolean incrCustomAxis = false;
  protected boolean cumCustomAxis = false;
  protected boolean moCustomAxis = false;

  protected String legend=null;
  protected final static int W = 870;
  protected final static int H = 730;
  protected final static int A1 = 360;
  protected final static int A2 = 430;
  protected final static Font BUTTON_FONT = new java.awt.Font( "Dialog", 1, 11 );
  final static Dimension BUTTON_DIM = new Dimension( 80, 20 );
  final static Dimension COMBO_DIM = new Dimension( 180, 20 );

  private final static String MAG_DIST_PARAM_NAME = "Mag Dist Param";

  final static String NO_PLOT_MSG = "No Plot Data Available";
  private final static String MAG = new  String("Magnitude");
  private final static String INCR_RATE = new String("Incremental Rate");
  private final static String CUM_RATE = new  String("Cumulative Rate");
  private final static String MO_RATE = new  String("Moment Rate");
  private SummedMagFreqDist summedMagFreqDist;

  private final static String AUTO_SCALE_ALL = new String("Auto Scale All");
  private final static String INCR_AUTO_SCALE = new String("Incr Auto Scale");
  private final static String CUM_AUTO_SCALE = new String("Cum Auto Scale");
  private final static String MO_AUTO_SCALE = new String("Mo Auto Scale");
  private final static String CUSTOM_SCALE = new String("Custom Scale");


  // Create the x-axis - either normal or log
   org.jfree.chart.axis.NumberAxis incrXAxis = null;
   org.jfree.chart.axis.NumberAxis cumXAxis = null;
   org.jfree.chart.axis.NumberAxis moXAxis = null;
   private double AUTO_RANGE_MINIMUM_SIZE = 1e-100;

  //Create the y-axis - either normal or log
   org.jfree.chart.axis.NumberAxis incrYAxis = null;
   org.jfree.chart.axis.NumberAxis cumYAxis = null;
   org.jfree.chart.axis.NumberAxis moYAxis = null;


   private double xIncrMin,xIncrMax,yIncrMin,yIncrMax;
   private double xCumMin,xCumMax,yCumMin,yCumMax;
   private double xMoMin,xMoMax,yMoMin,yMoMax;



  /**
   *  Used to determine if should switch to new MagDist, and for display purposes
   */
  public String currentMagDistName = "";
  boolean isStandalone = false;
  protected boolean inParameterChangeWarning = false;


  Insets plotInsets = new Insets( 4, 10, 4, 4 );
  Insets defaultInsets = new Insets( 4, 4, 4, 4 );
  Insets emptyInsets = new Insets( 0, 0, 0, 0 );

  private JPanel mainPanel = new JPanel();
  private GridBagLayout GBL = new GridBagLayout();
  private JComboBox rangeComboBox = new JComboBox();
  private JCheckBox plotColorCheckBox = new JCheckBox();
  private JButton clearButton = new JButton();
  private JLabel jIncrAxisScale = new JLabel();
  private JCheckBox jCheckylog = new JCheckBox();
  private JButton toggleButton = new JButton();
  private JPanel buttonPanel = new JPanel();

  private JButton addButton = new JButton();
  private JPanel outerPanel = new JPanel();
  private JSplitPane mainSplitPane = new JSplitPane();
  private GridBagLayout gridBagLayout1 = new GridBagLayout();


  protected javax.swing.JFrame frame;

  private ChartPanel incrPanel;
  private ChartPanel cumPanel;
  private ChartPanel moPanel;

  private JTextPane legendPane= new JTextPane();
  private JScrollPane legendScrollPane=new JScrollPane();
  private JPanel legendPanel =new JPanel();
  private SimpleAttributeSet setLegend;
  private JScrollPane dataScrollPane = new JScrollPane();
  private JTextArea pointsTextArea = new JTextArea();
  private JLabel titleLabel = new JLabel();
  private JPanel plotPanel = new JPanel();
  private JPanel titlePanel = new JPanel();
  private JPanel innerPlotPanel = new JPanel();

  Color[] legendColor = new Color[11];
  Paint[] legendPaint = new Paint[11];

  Color darkBlue = new Color( 80, 80, 133 );
  Color lightBlue = new Color( 200, 200, 230 );
  protected boolean graphOn = false;
  boolean isWhite = true;
  Color background = Color.white;
  SidesBorder topBorder = new SidesBorder( darkBlue, background, background, background );
  SidesBorder bottomBorder = new SidesBorder( background, darkBlue, background, background );
  OvalBorder oval = new OvalBorder( 12, 4, darkBlue, darkBlue );

  int titleSize = 0;
  private Paint[] paint;

   /**
     *  Currently selected IMR and related information needed for the gui to
     *  work
     */
  MagFreqDistParameter magDist = null;
  MagFreqDistParameterEditor magDistEditor;

  // protected MagDistGuiList magDists = new MagDistGuiList();

  /**
   * For 3 different plots we are using the different objects to refer for incrRate Data,
   * total Cum Rate Data and total Moment Rate Data.
   */

  DiscretizedFuncList incrFunctions = new DiscretizedFuncList();
  DiscretizedFuncList toCumFunctions = new DiscretizedFuncList();
  DiscretizedFuncList toMoFunctions = new DiscretizedFuncList();

  DiscretizedFunctionXYDataSet incrData = new DiscretizedFunctionXYDataSet();
  DiscretizedFunctionXYDataSet toCumData = new DiscretizedFunctionXYDataSet();
  DiscretizedFunctionXYDataSet toMoData = new DiscretizedFunctionXYDataSet();


  private boolean yLog = false;
  JCheckBox jCheckSumDist = new JCheckBox();
  private JLabel imgLabel = new JLabel();


  //images for the OpenSHA
  private final static String FRAME_ICON_NAME = "openSHA_Aqua_sm.gif";
  private final static String POWERED_BY_IMAGE = "PoweredBy.gif";

  //static string for the OPENSHA website
  private final static String OPENSHA_WEBSITE="http://www.OpenSHA.org";
  private JLabel jLabel1 = new JLabel();
  private Border border1;


 static {

    try { UIManager.setLookAndFeel( UIManager.getSystemLookAndFeelClassName() ); }
    catch ( Exception e ) {}
}

   /**
     *  Construct the applet
     */

  public MagFreqDistTesterApplet() {
      incrData.setFunctions(incrFunctions);
      toCumData.setFunctions(toCumFunctions);
      toMoData.setFunctions(toMoFunctions);
      incrFunctions.setXAxisName(MAG);
      toCumFunctions.setXAxisName(MAG);
      toMoFunctions.setXAxisName(MAG);
      incrFunctions.setYAxisName(INCR_RATE);
      toCumFunctions.setYAxisName(CUM_RATE);
      toMoFunctions.setYAxisName(MO_RATE);
      incrData.setConvertZeroToMin(true,.0000001);
      toCumData.setConvertZeroToMin(true,.0000001);
      toMoData.setConvertZeroToMin(true,1);

      //default setting the legend and plot colors
      int k=0;
      legendColor[k]= Color.blue;
      legendPaint[k++]= Color.blue;
      legendColor[k]= Color.green;
      legendPaint[k++]= Color.green;
      legendColor[k]= Color.orange;
      legendPaint[k++]= Color.orange;
      legendColor[k]= Color.magenta;
      legendPaint[k++]= Color.magenta;
      legendColor[k]= Color.cyan;
      legendPaint[k++]= Color.cyan;

      legendColor[k]= Color.pink;
      legendPaint[k++]= Color.pink;

      legendColor[k]= Color.yellow;
      legendPaint[k++]= Color.yellow;

      legendColor[k]= Color.darkGray;
      legendPaint[k++]= Color.darkGray;
  }

  /**
   *  Initialize the applet
   */
    public void init() {

        try {
            jbInit();
            initMagDistGui();
        }
        catch ( Exception e ) {
            e.printStackTrace();
        }
    }


  private void jbInit() throws Exception {
    border1 = BorderFactory.createLineBorder(new Color(80, 80, 133),3);
    mainPanel.setLayout(GBL);
    mainPanel.setBorder(border1 );

    this.getContentPane().setLayout(GBL);

    rangeComboBox.setBackground(new Color(200, 200, 230));
    rangeComboBox.setFont(new java.awt.Font("Lucida Grande", 0, 11));
    rangeComboBox.setForeground(new Color(80, 80, 133));
    rangeComboBox.setMaximumSize(new Dimension(125, 22));
    rangeComboBox.setMinimumSize(new Dimension(125, 22));
    rangeComboBox.setPreferredSize(new Dimension(125, 22));
    rangeComboBox.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        rangeComboBox_actionPerformed(e);
      }
    });
    plotColorCheckBox.setBackground(Color.white);
    plotColorCheckBox.setFont(new java.awt.Font("Dialog", 1, 11));
    plotColorCheckBox.setForeground(new Color(80, 80, 133));
    plotColorCheckBox.setText("Black Background");
    plotColorCheckBox.addItemListener(this);
    clearButton.setBackground(new Color(200, 200, 230));
    clearButton.setFont(BUTTON_FONT);
    clearButton.setForeground(new Color(80, 80, 133));
    clearButton.setFocusPainted(false);
    clearButton.setText("Clear Plot");
    clearButton.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        clearButton_actionPerformed(e);
      }
    });
    clearButton.setPreferredSize(BUTTON_DIM);
    clearButton.setMinimumSize(BUTTON_DIM);
    jIncrAxisScale.setFont(new java.awt.Font("Dialog", 1, 12));
    jIncrAxisScale.setForeground(new Color(80, 80, 133));
    jIncrAxisScale.setToolTipText("");
    jIncrAxisScale.setText("Axis Scales: ");
    jCheckylog.setBackground(Color.white);
    jCheckylog.setFont(new java.awt.Font("Dialog", 1, 11));
    jCheckylog.setForeground(new Color(80, 80, 133));
    jCheckylog.setText("Y-Log");
    jCheckylog.addItemListener(this);
    toggleButton.setBackground(new Color(200, 200, 230));
    toggleButton.setFont(BUTTON_FONT);
    toggleButton.setForeground(new Color(80, 80, 133));
    toggleButton.setFocusPainted(false);
    toggleButton.setText("Show Data");
    toggleButton.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        toggleButton_actionPerformed(e);
      }
    });
    toggleButton.setPreferredSize(BUTTON_DIM);
    toggleButton.setMinimumSize(BUTTON_DIM);
    buttonPanel.setLayout(GBL);
    addButton.setBackground(new Color(200, 200, 230));
    addButton.setFont(BUTTON_FONT);
    addButton.setForeground(new Color(80, 80, 133));
    addButton.setFocusPainted(false);
    addButton.setText("Add Dist");
    addButton.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        addButton_actionPerformed(e);
      }
    });
    addButton.setPreferredSize(BUTTON_DIM);
    addButton.setActionCommand("Add Dist");
    addButton.setMinimumSize(BUTTON_DIM);
    outerPanel.setLayout(GBL);
    mainSplitPane.setOrientation(JSplitPane.HORIZONTAL_SPLIT);
    mainSplitPane.setBorder(null);
    mainSplitPane.setDividerSize(5);
    mainSplitPane.setOneTouchExpandable(false);

    dataScrollPane.setHorizontalScrollBarPolicy(JScrollPane.HORIZONTAL_SCROLLBAR_NEVER);
    dataScrollPane.setBorder(BorderFactory.createEtchedBorder());
    legendScrollPane.setBorder(BorderFactory.createEtchedBorder());
    legendPane.setBorder(BorderFactory.createEtchedBorder());
    pointsTextArea.setBorder(BorderFactory.createEtchedBorder());
    pointsTextArea.setText(NO_PLOT_MSG);
    pointsTextArea.setLineWrap(true);
    titleLabel.setHorizontalAlignment(SwingConstants.CENTER);
    titleLabel.setFont(new java.awt.Font( "Dialog", 1, 16 ));
    plotPanel.setLayout(GBL);
    titlePanel.setLayout(GBL);
    titlePanel.setBorder( bottomBorder );
    innerPlotPanel.setLayout(GBL);
    innerPlotPanel.setBorder(null);
    this.getContentPane().setBackground(Color.white);
    outerPanel.setBackground(Color.white);
    mainPanel.setBackground(Color.white);
    buttonPanel.setBackground(Color.white);
    buttonPanel.setBorder( topBorder );
    jCheckSumDist.setBackground(Color.white);
    jCheckSumDist.setForeground(Color.red);
    jCheckSumDist.setText("Summed Dist");
    jCheckSumDist.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        jCheckSumDist_actionPerformed(e);
      }
    });

    //loading the OpenSHA Logo
   imgLabel.setText("");
    imgLabel.setIcon(new ImageIcon(FileUtils.loadImage(this.POWERED_BY_IMAGE)));
    imgLabel.addMouseListener(new java.awt.event.MouseAdapter() {
      public void mouseClicked(MouseEvent e) {
        imgLabel_mouseClicked(e);
      }
    });
    jLabel1.setFont(new java.awt.Font("Dialog", 0, 18));
    jLabel1.setForeground(new Color(80, 80, 133));
    jLabel1.setText("Magnitude-Frequency Distribution GUI");
    mainPanel.add(mainSplitPane,  new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
            ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(2, 4, 4, 4), 0, 0));
    mainPanel.add(buttonPanel,         new GridBagConstraints(0, 1, GridBagConstraints.REMAINDER, GridBagConstraints.REMAINDER, 1.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL, new Insets(1, 1, 1, 1), 0, 0));
    this.getContentPane().add(outerPanel,         new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
            ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(9, 9, 0, 9), 109, 399));
    outerPanel.add(mainPanel,       new GridBagConstraints(0, 1, 1, 1, 1.0, 1.0
            ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(0, 5, 5, 5), 0, 0));
    buttonPanel.add(toggleButton,                         new GridBagConstraints(5, 0, 1, 2, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(2, 5, 0, 1), 11, 7));
    buttonPanel.add(clearButton,                  new GridBagConstraints(4, 0, 1, 3, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(2, 0, 0, 0), 8, 7));
    buttonPanel.add(plotColorCheckBox,                           new GridBagConstraints(7, 0, 1, 1, 0.0, 0.0
            ,GridBagConstraints.EAST, GridBagConstraints.NONE, new Insets(4, 3, 0, 0), 0, 0));
  /*  buttonPanel.add(magDistLabel,                                  new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(0, 0, 0, 0), 0, 0));*/
    buttonPanel.add(addButton,                        new GridBagConstraints(3, 0, 1, 4, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(2, 0, 0, 5), 12, 7));
    buttonPanel.add(jCheckylog,     new GridBagConstraints(6, 0, 1, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(5, 5, 0, 2), 0, 0));
   /* buttonPanel.add(magDistComboBox,         new GridBagConstraints(1, 0, 1, 1, 0.0, 0.0
            ,GridBagConstraints.EAST, GridBagConstraints.NONE, new Insets(0, 0, 0, 0), -5, 0));*/
    buttonPanel.add(jCheckSumDist,    new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(4, 0, 0, 0), 0, 0));
    buttonPanel.add(jIncrAxisScale,   new GridBagConstraints(1, 0, 1, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(4, 4, 0, 0), 0, 0));
    buttonPanel.add(rangeComboBox,    new GridBagConstraints(2, 0, 1, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(4, 0, 0, 4), 0, 0));
    outerPanel.add(jLabel1,  new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(5, 5, 5, 5), 0, 0));
    this.getContentPane().add(imgLabel,  new GridBagConstraints(0, 1, 1, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(2, 0, 0, 0), 0, 0));



    // make  the mag dist parameter
    ArrayList distNames = new ArrayList();
    distNames.add(SingleMagFreqDist.NAME);
    distNames.add(GutenbergRichterMagFreqDist.NAME);
    distNames.add(GaussianMagFreqDist.NAME);
    distNames.add(YC_1985_CharMagFreqDist.NAME);
    magDist =  new MagFreqDistParameter(MAG_DIST_PARAM_NAME, distNames);
    magDistEditor = new MagFreqDistParameterEditor();
    magDistEditor.setParameter(magDist);
    // make the magdist param button invisible instead display it as the panel in the window
    magDistEditor.setMagFreqDistParamButtonVisible(false);
    ParameterListEditor magDistPanel =  magDistEditor.getMagFreqDistParameterEditor();

    mainSplitPane.setBottomComponent( magDistPanel );
    mainSplitPane.setTopComponent( plotPanel );
    mainSplitPane.setDividerLocation(600);

    dataScrollPane.getViewport().add(pointsTextArea, null);
    legendScrollPane.getViewport().add(this.legendPane,null);


    plotPanel.add(titlePanel, new GridBagConstraints( 0, 0, 1, 1, 1.0, 0.0
                , GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL, new Insets( 4, 4, 2, 4 ), 0, 0 ));
    plotPanel.add(innerPlotPanel, new GridBagConstraints( 0, 1, 1, 1, 1.0, 1.0
                , GridBagConstraints.CENTER, GridBagConstraints.BOTH, defaultInsets, 0, 0 ));
    titlePanel.add(titleLabel, new GridBagConstraints( 0, 0, 1, 1, 1.0, 0.0
                , GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL, emptyInsets, 0, 0 ));


    titlePanel.setBackground( background );
    plotPanel.setBackground( background );
    innerPlotPanel.setBackground( background );

  }


    /**
     *  Sets the frame attribute of the IMRTesterApplet object
     *
     * @param  newFrame  The new frame value
     */
    public void setFrame( JFrame newFrame ) {
        frame = newFrame;
    }



     /**
      *  Main method
      *
      * @param  args  The command line arguments
      */
     public static void main( String[] args ) {

         MagFreqDistTesterApplet applet = new MagFreqDistTesterApplet();

         Color c = new Color( .9f, .9f, 1.0f, 1f );
         Font f = new Font( "Dialog", Font.PLAIN, 11 );

         UIManager.put( "ScrollBar.width", new Integer( 12 ) );
         UIManager.put( "ScrollPane.width", new Integer( 12 ) );

         UIManager.put( "PopupMenu.font", f );
         UIManager.put( "Menu.font", f );
         UIManager.put( "MenuItem.font", f );

         UIManager.put( "ScrollBar.border", BorderFactory.createEtchedBorder( 1 ) );

         UIManager.put( "PopupMenu.background", c );

         //UIManager.put("PopupMenu.selectionBackground", c );
         //UIManager.put("PopupMenu.border", BorderFactory.createLineBorder(Color.red, 1 ) );

         UIManager.put( "Menu.background", c );
         //UIManager.put("Menu.selectionBackground", c );

         UIManager.put( "MenuItem.background", c );
         UIManager.put( "MenuItem.disabledBackground", c );
         //UIManager.put("MenuItem.selectionBackground", c );

         // UIManager.put("MenuItem.borderPainted", new Boolean(false) );
         UIManager.put( "MenuItem.margin", new Insets( 0, 0, 0, 0 ) );

         UIManager.put( "ComboBox.background", c );
         //UIManager.put("ComboBox.selectionBackground", new Color(220, 230, 170));


         applet.isStandalone = true;
         JFrame frame = new JFrame();
         //EXIT_ON_CLOSE == 3
         frame.setDefaultCloseOperation( 3 );

         frame.getContentPane().add( applet, BorderLayout.CENTER );

         applet.init();
         applet.start();
         applet.setFrame( frame );

         frame.setTitle( applet.getAppletInfo() + " (Version:"+applet.version+")");

         frame.setSize( W, H );
         Dimension d = Toolkit.getDefaultToolkit().getScreenSize();
         frame.setLocation( ( d.width - frame.getSize().width ) / 2, ( d.height - frame.getSize().height ) / 2 );
         frame.setVisible( true );

    }




    /**
     *  THis must be called before the Mag Dist is used. This is what initializes the
     *  Mag dist
     */
    protected void initMagDistGui() {

        // starting
        String S = C + ": initMagDistGui(): ";
        rangeComboBox.addItem(AUTO_SCALE_ALL);
        rangeComboBox.addItem(INCR_AUTO_SCALE);
        rangeComboBox.addItem(CUM_AUTO_SCALE);
        rangeComboBox.addItem(MO_AUTO_SCALE);
        rangeComboBox.addItem(CUSTOM_SCALE);
  }



   /**
     *  Description of the Method
     *
     * @param  e  Description of the Parameter
     */
    public void itemStateChanged( ItemEvent e ) {

        // Starting
        String S = C + ": itemStateChanged(): ";
        if ( D ) System.out.println( S + "Starting" );


        if( e.getSource().equals( jCheckylog ) ){

            //String title = magDist.getGraphXYAxisTitle();

            clearPlot( false );
            inParameterChangeWarning = false;

            if( jCheckylog.isSelected() ) yLog = true;
            else yLog = false;


            if( incrFunctions != null && incrData != null && toCumFunctions!=null && toCumData!=null && toMoFunctions!=null && toMoData!=null) {
                incrData.setYLog(yLog);
                toCumData.setYLog(yLog);
                toMoData.setYLog(yLog);
                pointsTextArea.setText( "                   "+ ((IncrementalMagFreqDist)magDist.getValue()).getName()+"             ");
                pointsTextArea.setText("\n");
                pointsTextArea.append( MAG +" vs. "+ INCR_RATE + '\n' + incrFunctions.toString());
                pointsTextArea.append("\n\n");
                pointsTextArea.append( MAG +" vs. "+ CUM_RATE + '\n' + toCumFunctions.toString());
                pointsTextArea.append("\n\n");
                pointsTextArea.append( MAG +" vs. "+ MO_RATE + '\n' + toMoFunctions.toString());
                addGraphPanel();
            }
        }

        else if( e.getSource().equals( plotColorCheckBox ) ){

            if( isWhite ) {
                isWhite = false;
                if( incrPanel != null )
                    incrPanel.getChart().getPlot().setBackgroundPaint(Color.black);
                if( cumPanel != null )
                    cumPanel.getChart().getPlot().setBackgroundPaint(Color.black);
                if( moPanel != null )
                    moPanel.getChart().getPlot().setBackgroundPaint(Color.black);
                if(legendPane !=null)
                   legendPane.setBackground(Color.black);

            }
            else{
                isWhite = true;
                if( incrPanel != null )
                    incrPanel.getChart().getPlot().setBackgroundPaint(Color.white);
                if( cumPanel != null )
                    cumPanel.getChart().getPlot().setBackgroundPaint(Color.white);
                if( moPanel != null )
                    moPanel.getChart().getPlot().setBackgroundPaint(Color.white);
                if(legendPane !=null)
                    legendPane.setBackground(Color.white);
            }
        }

        // Ending
        if ( D ) System.out.println( S + "Ending" );

    }




  /**
   * Gets the currentMagDistName attribute of the MagFreqDistTesterApplet object
   *
   * @return    The currentMagDistName value
   */
    public String getCurrentMagDistName() {
        return currentMagDistName;
    }


    /**
     *  Clears the plot screen of all traces
     */
    void clearPlot(boolean clearFunctions) {

        if ( D )
            System.out.println( "Clearing plot area" );

        int loc = mainSplitPane.getDividerLocation();
        int newLoc = loc;
        titleSize = titlePanel.getHeight() + 6;

        innerPlotPanel.removeAll();
        //panel = null;

        pointsTextArea.setText( NO_PLOT_MSG );
        if( clearFunctions) {
           incrFunctions.clear();
           toCumFunctions.clear();
           toMoFunctions.clear();
           this.jCheckSumDist.setSelected(false);
        }


        if ( !titlePanel.isVisible() ) {
            titlePanel.setVisible( true );
            //newLoc = loc - titleSize;
        }

        if ( titleLabel != null ) {
            titleLabel.setText( currentMagDistName );
            titleLabel.validate();
            titleLabel.repaint();
        }


        validate();
        repaint();

        mainSplitPane.setDividerLocation( newLoc );
    }


   /**
    *  Get Applet information
    *
    * @return    The appletInfo value
    */
    public String getAppletInfo() {
        return "MagFreqDist Tester Applet";
    }


  /**
   * this function is called when "Add Dist" button is clicked
   * @param e
   */
  void addButton_actionPerformed(ActionEvent e) {
     addButton();
  }



    /**
     *  This causes the model data to be calculated and a plot trace added to
     *  the current plot
     *
     * @param  e  The feature to be added to the Button_mouseClicked attribute
     */
    protected void addButton(){

        String S = C + ": addButton(): ";
        if ( D ) System.out.println( S + "Starting" );

        try{
          this.magDistEditor.setMagDistFromParams();
          IncrementalMagFreqDist function= (IncrementalMagFreqDist)this.magDist.getValue();
          if(D) System.out.println(S+" after getting mag dist from editor");
          EvenlyDiscretizedFunc cumRate;
          EvenlyDiscretizedFunc moRate;

          // get the cumulative rate and moment rate distributions for this function
          cumRate=(EvenlyDiscretizedFunc)function.getCumRateDist();
          moRate=(EvenlyDiscretizedFunc)function.getMomentRateDist();

          // set the log values
          incrData.setYLog(yLog);
          toMoData.setYLog(yLog);
          toCumData.setYLog(yLog);


          /** @todo may have to be switched when different x/y axis choosen */
          if ( !incrFunctions.isFuncAllowed(function) ) {
             incrFunctions.clear();
          }
          if ( !toCumFunctions.isFuncAllowed(cumRate)) {
              toCumFunctions.clear();
          }
          if ( !toMoFunctions.isFuncAllowed(moRate)) {
              toMoFunctions.clear();
          }


        if(!this.jCheckSumDist.isSelected()) {
          // add the functions to the functionlist
          incrFunctions.add((EvenlyDiscretizedFunc)function);
          toCumFunctions.add(cumRate);
          toMoFunctions.add(moRate);
        } else { // if summed distribution is selected, add to summed distribution
             try {
               // add this distribution to summed distribution
               summedMagFreqDist.addIncrementalMagFreqDist(function);

               // previous sum is invalid in the function lists. so remove that
               incrFunctions.remove(0);
               toCumFunctions.remove(0);
               toMoFunctions.remove(0);

               // add the functions to the functionlist
               incrFunctions.add((EvenlyDiscretizedFunc)function);
               toCumFunctions.add(cumRate);
               toMoFunctions.add(moRate);
               // this function will insert summed distribution at top of function list
               insertSummedDistribution();
             }catch(Exception ex) {
               JOptionPane.showMessageDialog(this,
                                     "min, max, and num must be the same to sum the distributions."+
                                     "\n To add this distribution first deselect the Summed Dist option"
                                     );
               return;
             }
          }

        // Add points data to text area, people can see
          pointsTextArea.setText(INCR_RATE +" vs. "+ MAG + '\n' + "--------------------------" + '\n' + incrFunctions.toString());
          pointsTextArea.append('\n' + CUM_RATE +" vs. "+ MAG + '\n' + "-------------------------" + '\n' + toCumFunctions.toString());
          pointsTextArea.append('\n' + MO_RATE +" vs. "+ MAG + '\n' + "-----------------------" + '\n' + toMoFunctions.toString());

          // draw the graph
          addGraphPanel();

          // set the title label
          if ( titleLabel != null ) {
            titleLabel.setText( currentMagDistName );
            titleLabel.validate();
            titleLabel.repaint();
          }

        // catch the error and display messages in case of input error
        }catch(NumberFormatException e){
          JOptionPane.showMessageDialog(this,new String("Enter a Valid Numerical Value"),"Invalid Data Entered",JOptionPane.ERROR_MESSAGE);
        }catch(NullPointerException e) {
          //JOptionPane.showMessageDialog(this,new String(e.getMessage()),"Data Not Entered",JOptionPane.ERROR_MESSAGE);
          e.printStackTrace();
        }catch(Exception e) {
          JOptionPane.showMessageDialog(this,new String(e.getMessage()),"Invalid Data Entered",JOptionPane.ERROR_MESSAGE);
        }

       if ( D ) System.out.println( S + "Ending" );

    }


    /**
     *  Adds a feature to the GraphPanel attribute of the IMRTesterApplet object
     */
    protected void addGraphPanel() {

        // Starting
        String S = C + ": addGraphPanel(): ";
        if(this.jCheckylog.isSelected()) yLog=true;
        else yLog=false;


        // create a default chart based on some sample data...
        // Determine which labels to add to the axis labeling
        String incrXAxisLabel = incrFunctions.getXAxisName();
        String incrYAxisLabel = incrFunctions.getYAxisName();
        String cumXAxisLabel = toCumFunctions.getXAxisName();
        String cumYAxisLabel = toCumFunctions.getYAxisName();
        String moXAxisLabel = toMoFunctions.getXAxisName();
        String moYAxisLabel = toMoFunctions.getYAxisName();

        String title = this.getCurrentMagDistName();



        TickUnits units = MyTickUnits.createStandardTickUnits();
        // create X- axis for mag vs incremental rate
        incrXAxis = new NumberAxis( incrXAxisLabel );
        incrXAxis.setAutoRangeIncludesZero( false );
        incrXAxis.setStandardTickUnits(units);
        incrXAxis.setTickMarksVisible(false);

        // create X- axis for mag vs cum rate
        cumXAxis = new NumberAxis( cumXAxisLabel );
        cumXAxis.setAutoRangeIncludesZero( false );
        cumXAxis.setStandardTickUnits(units);
        cumXAxis.setTickMarksVisible(false);

        // create x- axis for mag vs moment rate
        moXAxis = new NumberAxis( moXAxisLabel );
        moXAxis.setAutoRangeIncludesZero( false );
        moXAxis.setStandardTickUnits(units);
        moXAxis.setTickMarksVisible(false);

        if (yLog)  {
          incrYAxis = new org.jfree.chart.axis.LogarithmicAxis(incrYAxisLabel);
          cumYAxis = new org.jfree.chart.axis.LogarithmicAxis(cumYAxisLabel);
          moYAxis = new org.jfree.chart.axis.LogarithmicAxis(moYAxisLabel);
        }
        else {
          incrYAxis = new NumberAxis(incrYAxisLabel);
          cumYAxis = new NumberAxis(cumYAxisLabel);
          moYAxis = new NumberAxis(moYAxisLabel);
       }

       try{
         // set properties for mag vs incremental rate Y- axis
         incrYAxis.setAutoRangeIncludesZero( true );
         incrYAxis.setStandardTickUnits(units);
         incrYAxis.setAutoRangeIncludesZero(false);
         incrYAxis.setAutoRangeStickyZero(true);
         incrYAxis.setAutoRangeMinimumSize(AUTO_RANGE_MINIMUM_SIZE);
         incrYAxis.setTickMarksVisible(false);


         // set properties for mag vs incremental rate Y- axis
         cumYAxis.setAutoRangeIncludesZero( true );
         cumYAxis.setStandardTickUnits(units);
         cumYAxis.setAutoRangeIncludesZero(false);
         cumYAxis.setAutoRangeStickyZero(true);
         cumYAxis.setAutoRangeMinimumSize(AUTO_RANGE_MINIMUM_SIZE);
         cumYAxis.setTickMarksVisible(false);

         // set properties for mag vs incremental rate Y- axis
         moYAxis.setAutoRangeIncludesZero( true );
         moYAxis.setStandardTickUnits(units);
         moYAxis.setAutoRangeIncludesZero(false);
         moYAxis.setAutoRangeStickyZero(true);
         moYAxis.setAutoRangeMinimumSize(AUTO_RANGE_MINIMUM_SIZE);
         moYAxis.setTickMarksVisible(false);


         int type = StandardXYItemRenderer.LINES;

         StandardXYItemRenderer renderer =
             new StandardXYItemRenderer( type, new StandardXYToolTipGenerator() );

        /* to set the range of the axis on the input from the user if the range combo box is selected*/
         if(this.incrCustomAxis) {
           incrXAxis.setRange(this.xIncrMin,this.xIncrMax);
           incrYAxis.setRange(this.yIncrMin,this.yIncrMax);
         }
         if(this.cumCustomAxis) {
           cumXAxis.setRange(this.xCumMin,this.xCumMax);
           cumYAxis.setRange(this.yCumMin,this.yCumMax);
         }
         if(this.moCustomAxis) {
           moXAxis.setRange(this.xMoMin,this.xMoMax);
           moYAxis.setRange(this.yMoMin,this.yMoMax);
         }


         // build the plot
         org.jfree.chart.plot.XYPlot incrPlot = new org.jfree.chart.plot.XYPlot(incrData, incrXAxis, incrYAxis, renderer);
         org.jfree.chart.plot.XYPlot cumPlot = new org.jfree.chart.plot.XYPlot(toCumData, cumXAxis, cumYAxis, renderer);
         org.jfree.chart.plot.XYPlot moPlot = new org.jfree.chart.plot.XYPlot(toMoData, moXAxis, moYAxis, renderer);


         incrPlot.setBackgroundAlpha( .8f );
         incrPlot.setDomainCrosshairLockedOnData(false);
         incrPlot.setDomainCrosshairVisible(false);
         incrPlot.setRangeCrosshairLockedOnData(false);
         incrPlot.setRangeCrosshairVisible(false);

         cumPlot.setBackgroundAlpha( .8f );
         cumPlot.setDomainCrosshairLockedOnData(false);
         cumPlot.setDomainCrosshairVisible(false);
         cumPlot.setRangeCrosshairLockedOnData(false);
         cumPlot.setRangeCrosshairVisible(false);

         moPlot.setBackgroundAlpha( .8f );
         moPlot.setDomainCrosshairLockedOnData(false);
         moPlot.setDomainCrosshairVisible(false);
         moPlot.setRangeCrosshairLockedOnData(false);
         moPlot.setRangeCrosshairVisible(false);

         int numSeries = legendPaint.length;
         for(int i=0; i < numSeries; ++i) renderer.setSeriesPaint(i,legendPaint[i]);
         if( isWhite ) {
           incrPlot.setBackgroundPaint( Color.white );
           cumPlot.setBackgroundPaint( Color.white );
           moPlot.setBackgroundPaint( Color.white );
           legendPane.setBackground(Color.white);
         }
         else {
           incrPlot.setBackgroundPaint( Color.black );
           cumPlot.setBackgroundPaint( Color.black );
           moPlot.setBackgroundPaint( Color.black );
           legendPane.setBackground(Color.black);
         }


         incrPlot.setRenderer( renderer );
         cumPlot.setRenderer( renderer );
         moPlot.setRenderer( renderer );


         JFreeChart incrChart = new JFreeChart(title, JFreeChart.DEFAULT_TITLE_FONT, incrPlot,false);
         JFreeChart cumChart = new JFreeChart(title, JFreeChart.DEFAULT_TITLE_FONT, cumPlot,false );
         JFreeChart moChart = new JFreeChart(title, JFreeChart.DEFAULT_TITLE_FONT, moPlot,false );


         // Graphics
         incrChart.setBackgroundPaint( lightBlue );
         cumChart.setBackgroundPaint( lightBlue );
         moChart.setBackgroundPaint( lightBlue );



         // Put into a panel
         incrPanel = new ChartPanel(incrChart, true, true, true, true, false);
         cumPanel = new ChartPanel(cumChart, true, true, true, true, false);
         moPanel = new ChartPanel(moChart, true, true, true, true, false);



         legendPane.removeAll();
         legendPane.setEditable(false);
         setLegend =new SimpleAttributeSet();
         setLegend.addAttribute(StyleConstants.CharacterConstants.Bold,
                                Boolean.TRUE);
         int numOfColors = incrPlot.getSeriesCount();
         Document doc = legendPane.getStyledDocument();
         try {

           doc.remove(0,doc.getLength());
           for(int i=0,j=0;i<numOfColors;++i,++j){
             if(j==legendColor.length)
               j=0;
             legend = new String(i+1+") "+this.incrFunctions.get(i).getName()+": "+this.incrFunctions.get(i).getInfo()+"\n\n");
             setLegend =new SimpleAttributeSet();
             StyleConstants.setFontSize(setLegend,12);
             StyleConstants.setForeground(setLegend,legendColor[j]);

             doc.insertString(doc.getLength(),legend,setLegend);
           }
         } catch (BadLocationException e) {
           return;
         }
         //panel.setMouseZoomable(true);


         // set panel properties for mag vs incremental rate chart
         incrPanel.setBorder( BorderFactory.createEtchedBorder( EtchedBorder.LOWERED ) );
         incrPanel.setMouseZoomable(true);
         incrPanel.setDisplayToolTips(true);
         incrPanel.setHorizontalAxisTrace(false);
         incrPanel.setVerticalAxisTrace(false);

         // set panel properties for mag vs cumulative rate chart
         cumPanel.setBorder( BorderFactory.createEtchedBorder( EtchedBorder.LOWERED ) );
         cumPanel.setMouseZoomable(true);
         cumPanel.setDisplayToolTips(true);
         cumPanel.setHorizontalAxisTrace(false);
         cumPanel.setVerticalAxisTrace(false);

         // set panel properties for mag vs moment rate chart
         moPanel.setBorder( BorderFactory.createEtchedBorder( EtchedBorder.LOWERED ) );
         moPanel.setMouseZoomable(true);
         moPanel.setDisplayToolTips(true);
         moPanel.setHorizontalAxisTrace(false);
         moPanel.setVerticalAxisTrace(false);

       }catch(Exception e){
         JOptionPane.showMessageDialog(this,e.getMessage(),"Invalid Plot",JOptionPane.OK_OPTION);
         return;
       }

        if ( D ) System.out.println( S + "Toggling plot on" );
        graphOn = false;
        togglePlot();
        if ( D ) System.out.println( S + "Done" );
     }




   /**
     *  Description of the Method
     */
    protected void togglePlot() {

        // Starting
        String S = C + ": togglePlot(): ";

        innerPlotPanel.removeAll();

        int loc = mainSplitPane.getDividerLocation();
        titleSize = titlePanel.getHeight() + 6;

        int newLoc = loc;
        if ( graphOn ) {
            if ( D )
                System.out.println( S + "Showing Data" );
            toggleButton.setText( "Show Plot" );
            graphOn = false;

            if ( !titlePanel.isVisible() ) {
                titlePanel.setVisible( true );
                // newLoc = loc - titleSize;
            }

            // dataScrollPane.setVisible(true);
            // innerPlotPanel.setBorder(oval);
            innerPlotPanel.add( dataScrollPane, new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0
                    , GridBagConstraints.CENTER, GridBagConstraints.BOTH, plotInsets, 0, 0 ) );
        }
        else {
            if ( D )
                System.out.println( S + "About to show Plot" );
            graphOn = true;
            // dataScrollPane.setVisible(false);
            toggleButton.setText( "Show Data" );
            if ( incrPanel != null ) {
                if ( D )
                    System.out.println( S + "Showing Plot" );


                if ( titlePanel.isVisible() ) {
                    titlePanel.setVisible( false );
                    //newLoc = loc + titleSize;
                }

                // panel for mag vs incremental-rate graph
                  innerPlotPanel.add( incrPanel, new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0
                        , GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ) );

                // panel for mag vs cumulative-rate graph
                innerPlotPanel.add( cumPanel, new GridBagConstraints( 1, 0, 1, 1, 1.0, 1.0
                        , GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ) );

                // panel for mag vs moment-rate graph
                innerPlotPanel.add( moPanel, new GridBagConstraints( 0, 1, 1, 1, 1.0, 1.0
                       , GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ) );

                  //panel for the legend
                  innerPlotPanel.add(legendScrollPane, new GridBagConstraints( 1,1, 1, 1, 1.0, 1.0
                        , GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ) );


            }
            else {
                if ( D )
                    System.out.println( S + "No Plot - So Showing Data" );


                if ( !titlePanel.isVisible() ) {
                    titlePanel.setVisible( true );
                    // newLoc = loc - titleSize;
                }

                // innerPlotPanel.setBorder(oval);
                innerPlotPanel.add( dataScrollPane, new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0
                        , GridBagConstraints.CENTER, GridBagConstraints.BOTH, plotInsets, 0, 0 ) );
            }

        }

        if ( D ) System.out.println( S + "Calling validate and repaint" );
        mainSplitPane.setDividerLocation( newLoc );
        validate();
        repaint();

        if ( D ) System.out.println( S + "Loc = " + loc + '\t' + "New Loc = " + newLoc );
        if ( D ) System.out.println( S + "Ending" );

    }


   /**
     *  Clears the plot screen of all traces, then sychs imr to model
     *
     * @param  e  Description of the Parameter
     */
    void clearButton_actionPerformed( ActionEvent e ) {
        clearButton();
    }

    void clearButton(){
        clearPlot( true );
    }

    /**
     * This function is called when show data button is clicked
     * @param e
     */
  void toggleButton_actionPerformed(ActionEvent e) {
      togglePlot();
  }

 /**
  * whenever selection is made in the combo box
  * @param e
  */
  void rangeComboBox_actionPerformed(ActionEvent e) {

    String str=(String)rangeComboBox.getSelectedItem();
    if(str.equalsIgnoreCase(INCR_AUTO_SCALE))  incrCustomAxis = false;
    else if(str.equalsIgnoreCase(CUM_AUTO_SCALE)) cumCustomAxis = false;
    else if(str.equalsIgnoreCase(MO_AUTO_SCALE)) moCustomAxis = false;
    else if(str.equalsIgnoreCase(AUTO_SCALE_ALL)) {
      incrCustomAxis = false;
      cumCustomAxis = false;
      moCustomAxis = false;
    }

   if(!str.equalsIgnoreCase(CUSTOM_SCALE)) addGraphPanel();

    if(str.equalsIgnoreCase(CUSTOM_SCALE) && incrXAxis!=null && incrYAxis!=null)  {
       Range rIncrX=incrXAxis.getRange();
       double xIncrMin=rIncrX.getLowerBound();
       double xIncrMax=rIncrX.getUpperBound();

       Range rIncrY=incrYAxis.getRange();
       double yIncrMin=rIncrY.getLowerBound();
       double yIncrMax=rIncrY.getUpperBound();

       Range rCumX=cumXAxis.getRange();
       double xCumMin=rCumX.getLowerBound();
       double xCumMax=rCumX.getUpperBound();

       Range rCumY=cumYAxis.getRange();
       double yCumMin=rCumY.getLowerBound();
       double yCumMax=rCumY.getUpperBound();

       Range rMoX=moXAxis.getRange();
       double xMoMin=rMoX.getLowerBound();
       double xMoMax=rMoX.getUpperBound();

       Range rMoY=moYAxis.getRange();
       double yMoMin=rMoY.getLowerBound();
       double yMoMax=rMoY.getUpperBound();

       MagFreqDistAxisScale axisScale=new MagFreqDistAxisScale(this,xIncrMin,xIncrMax,
                                      yIncrMin,yIncrMax,xCumMin, xCumMax,yCumMin,yCumMax,
                                      xMoMin,xMoMax,yMoMin,yMoMax);
       axisScale.setLocation(getX()+getWidth()/2,getY()+getHeight()/2);
       axisScale.pack();
       axisScale.setVisible(true);
    }
  }




  /**
   * sets the range for X-axis
   * @param xMin : minimum value for X-axis
   * @param xMax : maximum value for X-axis
   */
  public void setXRange(double xIncrMin,double xIncrMax,double xCumMin,double xCumMax,
                        double xMoMin, double xMoMax) {

     this.xIncrMin = xIncrMin;
     this.xIncrMax = xIncrMax;
     this.xCumMin  = xCumMin;
     this.xCumMax = xCumMax;
     this.xMoMin = xMoMin;
     this.xMoMax = xMoMax;
     this.incrCustomAxis = true;
     this.moCustomAxis = true;
     this.cumCustomAxis = true;
 }

  /**
   * sets the range for Y-axis
   * @param yMin : minimum value for Y-axis
   * @param yMax : maximum value for Y-axis
   */
  public void setYRange(double yIncrMin,double yIncrMax,double yCumMin,double yCumMax,
                        double yMoMin, double yMoMax) {

     this.yIncrMin = yIncrMin;
     this.yIncrMax = yIncrMax;
     this.yCumMin  = yCumMin;
     this.yCumMax = yCumMax;
     this.yMoMin = yMoMin;
     this.yMoMax = yMoMax;
     this.incrCustomAxis = true;
     this.moCustomAxis = true;
     this.cumCustomAxis = true;
     addGraphPanel();
  }

  /**
   * This function is called when Summed distribution box is clicked
   *
   * @param e
   */
  void jCheckSumDist_actionPerformed(ActionEvent e) {

    int k=0;
    if(jCheckSumDist.isSelected()) {

      legendColor[k]= Color.red;
      legendPaint[k++]=Color.red;
      // if user wants a summed distribution
      double min = magDistEditor.getMin();
      double max = magDistEditor.getMax();
      int num = magDistEditor.getNum();

      // make the new object of summed distribution
      summedMagFreqDist = new  SummedMagFreqDist(min,max,num);

      // add all the existing distributions to the summed distribution
      int size = incrFunctions.size();

      try {
      for(int i=0; i < size; ++i)
        summedMagFreqDist.addIncrementalMagFreqDist((IncrementalMagFreqDist)incrFunctions.get(i));
      }catch(Exception ex) {
         JOptionPane.showMessageDialog(this,
                                       "min, max, and num must be the same to sum the distributions"
                                       );
         jCheckSumDist.setSelected(false);
         return;
      }

      // now we will do work so that we can put summed distribuiton to top of functionlist
      insertSummedDistribution();

    }
    // if summed distribution needs to be removed
   else {
     // remove the summed distribution and related moment rate and cumulative rate
     incrFunctions.remove(0);
     toCumFunctions.remove(0);
     toMoFunctions.remove(0);
   }


    //making the legend color for the plot and the legend based on the selection of the Summed check box
     legendColor[k]= Color.blue;
     legendPaint[k++]= Color.blue;
     legendColor[k]= Color.green;
     legendPaint[k++]= Color.green;
     legendColor[k]= Color.orange;
     legendPaint[k++]= Color.orange;
     legendColor[k]= Color.magenta;
     legendPaint[k++]= Color.magenta;
     legendColor[k]= Color.cyan;
     legendPaint[k++]= Color.cyan;

     legendColor[k]= Color.pink;
     legendPaint[k++]= Color.pink;

     legendColor[k]= Color.yellow;
     legendPaint[k++]= Color.yellow;

     legendColor[k]= Color.darkGray;
     legendPaint[k++]= Color.darkGray;

   // Add points data to text area, people can see
    pointsTextArea.setText(INCR_RATE +" vs. "+ MAG + '\n' + "--------------------------" + '\n' + incrFunctions.toString());
    pointsTextArea.append('\n' + CUM_RATE +" vs. "+ MAG + '\n' + "-------------------------" + '\n' + toCumFunctions.toString());
    pointsTextArea.append('\n' + MO_RATE +" vs. "+ MAG + '\n' + "-----------------------" + '\n' + toMoFunctions.toString());

    addGraphPanel();

  }



  /**
   * private function to insert the summed distribtuion to function list
   * It first makes the clone of the original function list
   * Then clears the original function list and then adds summed distribtuion to
   * the top of the original function list and then adds other distributions
   *
   */
  private void insertSummedDistribution() {

    // clone the function lists
     DiscretizedFuncList cloneIncrFunctions = incrFunctions.deepClone();
     DiscretizedFuncList cloneCumFunctions = toCumFunctions.deepClone();
     DiscretizedFuncList cloneMoFunctions = toMoFunctions.deepClone();

     // now clear the function lists
     incrFunctions.clear();
     toCumFunctions.clear();
     toMoFunctions.clear();

     // add the summed distribution to the list
     incrFunctions.add(summedMagFreqDist);
     toCumFunctions.add(summedMagFreqDist.getCumRateDist());
     toMoFunctions.add(summedMagFreqDist.getMomentRateDist());

     int size = cloneIncrFunctions.size();

     //now add the other distributions
     for(int i=0; i<size; ++i) {
       incrFunctions.add(cloneIncrFunctions.get(i));
       toCumFunctions.add(cloneCumFunctions.get(i));
       toMoFunctions.add(cloneMoFunctions.get(i));
     }

  }

  void imgLabel_mouseClicked(MouseEvent e) {
    try{
    this.getAppletContext().showDocument(new URL(OPENSHA_WEBSITE),"new_mag_win");
    }catch(java.net.MalformedURLException ee){
      JOptionPane.showMessageDialog(this,new String("No Internet Connection Available"),
                                    "Error Connecting to Internet",JOptionPane.OK_OPTION);
    }
  }

}
