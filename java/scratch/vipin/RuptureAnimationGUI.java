package scratch.vipin;

import java.awt.BasicStroke;
import java.awt.Color;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.URLConnection;
import java.util.ArrayList;
import java.util.StringTokenizer;

import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JSlider;
import javax.swing.JSplitPane;
import javax.swing.UIManager;
import javax.swing.border.EtchedBorder;
import javax.swing.event.ChangeEvent;
import javax.swing.event.ChangeListener;

import org.jfree.chart.ChartPanel;
import org.jfree.chart.JFreeChart;
import org.jfree.chart.axis.NumberAxis;
import org.jfree.chart.plot.XYPlot;
import org.jfree.chart.renderer.xy.StandardXYItemRenderer;
import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.gui.plot.jfreechart.GriddedSurfaceXYDataSet;
import org.opensha.commons.param.IntegerParameter;
import org.opensha.commons.param.editor.IntegerParameterEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.faultSurface.GriddedSurface;

/**
 * <p>Title: Show all the ruptures as a animation using JFreechart</p>
 * <p>Description: Read the fault sections and ruptures from files and display
 * them using JFreechart. </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class RuptureAnimationGUI extends JFrame implements  ActionListener,
    ChangeListener, Runnable, ParameterChangeListener {
  private JPanel displayPanel = new JPanel();
  private JButton playButton = new JButton();
  private final static String FAULT_SECTION_FILE_NAME = PrepareTreeStructure.DEFAULT_FAULT_SECTIONS_OUT_FILENAME;
  private final static String X_AXIS_LABEL = "Longitude (deg.)";
  private final static String Y_AXIS_LABEL = "Latitude (deg.)";
  private final static String TITLE = "Fault Sections & Ruptures";
  // light blue color
  private final static Color lightBlue = new Color( 200, 200, 230 );
  private final static Color buttonColor = new Color( 80, 80, 133 );
  private NumberAxis yAxis = new NumberAxis( Y_AXIS_LABEL );
  private NumberAxis xAxis = new NumberAxis( X_AXIS_LABEL );
  private final static int TIME_DELAY = 200;
   // build the plot
  private  XYPlot plot = new XYPlot(null, xAxis, yAxis, new StandardXYItemRenderer());
  private  int faultSectionCounter=0;
  private ArrayList masterRupList; // list of all ruptures from the file
  private ArrayList displayRupList;
  private ChartPanel chartPanel;
  private JSplitPane controlSplitPane = new JSplitPane();
  private JSplitPane filterSplitPane = new JSplitPane();
  private JPanel filterParamsPanel = new JPanel();
  private JPanel buttonPanel = new JPanel();
  private JButton stopButton = new JButton();
  private JButton filterButton = new JButton("Filter");
  private JSlider ruptureSlider = new JSlider();
  private GridBagLayout gridBagLayout1 = new GridBagLayout();
  private GridBagLayout gridBagLayout2 = new GridBagLayout();
  private GridBagLayout gridBagLayout3 = new GridBagLayout();
  private GridBagLayout gridBagLayout4 = new GridBagLayout();
  private final static int WIDTH  = 900;
  private final static int HEIGHT  = 800;
  private int rupIndex=0;
  private final static String PLAY = "Play";
  private final static String PAUSE = "Pause";
  private boolean playStatus;
  private JLabel currentRupLabel= new JLabel("Rupture Index:");
  private JLabel rupValLabel = new JLabel();
  private RuptureFilterGuiBean rupFilterGuiBean;
  private final static String TIME_DELAY_PARAM_NAME = "Time Delay";
  private int timeDelayVal = TIME_DELAY;
  private IntegerParameter timeDelayParam = new IntegerParameter(TIME_DELAY_PARAM_NAME, "milliseconds",new Integer(timeDelayVal));


  //static initializer for setting look & feel
  static {
    String osName = System.getProperty("os.name");
    try {
        UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
    }
    catch(Exception e) {
    }
  }

  public RuptureAnimationGUI() {
    try {
      ArrayList sectionNames = loadFaultSections(); // load the fault sections
      rupFilterGuiBean = new RuptureFilterGuiBean(sectionNames);
      jbInit();
      addGraphPanel(); // show the fault sections using JFreechart
      RuptureFileReaderWriter rupFileReader = new RuptureFileReaderWriter(PrepareTreeStructure.DEFAULT_RUP_OUT_FILENAME);
      masterRupList = rupFileReader.loadRuptures();
      rupFileReader.close();
      timeDelayParam.addParameterChangeListener(this);
      this.displayRupList = masterRupList;
      setRuptureSlider();
      this.setSize(WIDTH, HEIGHT);
      setTitle(TITLE);
      controlSplitPane.setDividerLocation(660);
      filterSplitPane.setDividerLocation(700);
      //this.setLocationRelativeTo(null);
      this.setDefaultCloseOperation(EXIT_ON_CLOSE);
      this.setVisible(true);
    }
    catch(Exception e) {
      e.printStackTrace();
    }
  }

  public void parameterChange(ParameterChangeEvent event) {
    if(event.getParameterName().equalsIgnoreCase(this.TIME_DELAY_PARAM_NAME))
      this.timeDelayVal = ((Integer)this.timeDelayParam.getValue()).intValue();
  }

  /**
   * Set the limits of the rupture slider
   */
  private void setRuptureSlider() {
    if(ruptureSlider!=null) buttonPanel.remove(ruptureSlider);
    ruptureSlider = new JSlider();
    int numRups = this.displayRupList.size();
    // set the properties for rupture slider
    ruptureSlider.setMinimum(0);
    ruptureSlider.setMaximum(displayRupList.size()-1);
    ruptureSlider.setMajorTickSpacing(numRups/10);

    ruptureSlider.setPaintTicks(true);
    //ruptureSlider.setFocusable(false);
    ruptureSlider.setPaintLabels(true);
    ruptureSlider.setPaintTrack(true);
    // add action listeners
    ruptureSlider.addChangeListener(this);
    ruptureSlider.setValue(0);
    buttonPanel.add(ruptureSlider,  new GridBagConstraints(0, 0, 5, 1, 1.0, 0.0
        ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(7, 7, 0, 13), 334, 1));
  }


  /**
   * when user click on button to view the ruptures
   * @param event
   */
  public void actionPerformed(ActionEvent event) {
    Object source = event.getSource();
    if(source == this.playButton)  {
      // if play button is clicked
      if(playButton.getText().equalsIgnoreCase(PLAY)) {
        playButton.setText(PAUSE);
        playStatus = true;
        showRuptures();
      }
      // if pause button is clicked
      else if(playButton.getText().equalsIgnoreCase(PAUSE)) {
        playButton.setText(PLAY);
        playStatus = false;
      }
    }
    // stop the animation
    else if(source==this.stopButton) {
      playStatus = false;
      rupIndex=0;
      playButton.setText(PLAY);
      this.ruptureSlider.setValue(rupIndex);
    }
    // filter the ruptures
    else if(source==this.filterButton) {
      String selectedSectionName = this.rupFilterGuiBean.getSelectedSectionName();
      double minLength = rupFilterGuiBean.getMinRupLength();
      double maxLength = rupFilterGuiBean.getMaxRupLength();
      filter(selectedSectionName, minLength, maxLength, rupFilterGuiBean.areOnlyMultiSectionRuptures());
      rupIndex=0;
    }
  }

  /**
   *
   * @param selectedSectionName
   * @param minRupLen
   * @param maxRupLen
   */
  private void filter(String selectedSectionName, double minRupLen, double maxRupLen, boolean onlyMutliSectionRups) {
    this.displayRupList  = RuptureFilter.getRupturesForLengthAndSection(this.masterRupList, selectedSectionName, minRupLen, maxRupLen, onlyMutliSectionRups);
    this.setRuptureSlider();
  }



  /**
   * Whenuser clicks on JSlider, update the rupture index to display
   * @param event
   */
  public void stateChanged(ChangeEvent event) {
    this.rupIndex = this.ruptureSlider.getValue();
    rupValLabel.setText(rupIndex+" of "+(this.displayRupList.size()-1));
  }

  /**
   * Show the ruptures animation. It makes a new thread to do the animation
   */
  private void showRuptures() {
    Thread animationThread = new Thread(this);
    animationThread.start();
  }

  /**
   * Thread runs this to create a animation  for ruptures
   */
  public void run() {
    for( ; rupIndex<this.displayRupList.size() && playStatus; ++rupIndex) {
      // get the next rupture from the list
      MultiSectionRupture rupture = (MultiSectionRupture) displayRupList.get(rupIndex);
      // put all the locations of this rupture into location list
      ArrayList nodesList = rupture.getNodesList();
      LocationList locList = new LocationList();
      for (int i = 0; i < nodesList.size(); ++i)
        locList.add( ( (Node) nodesList.get(i)).getLoc());
        // add the location list to be plotted in JFreeChart
      addLocationListToPlot(locList, faultSectionCounter);
      addRendererForRupture(faultSectionCounter); // add renderer to ruptures
      ruptureSlider.setValue(rupIndex);
      this.addGraphPanel();
      try {
        Thread.sleep(timeDelayVal);
      }
      catch (InterruptedException ex) {
        ex.printStackTrace();
      }
    }
  }

  /**
   * Set the black rendered color to draw a rupture
   * @param index
   */
   private void addRendererForRupture(int index) {
    StandardXYItemRenderer xyItemRenderer = new StandardXYItemRenderer();
    xyItemRenderer.setPaint(Color.black);
    xyItemRenderer.setStroke(new BasicStroke((float)2.0));
    if(index==0) plot.setRenderer(xyItemRenderer);
    else plot.setRenderer(index-1, xyItemRenderer);
  }


   private void addGraphPanel() {
    JFreeChart chart = new JFreeChart(TITLE, JFreeChart.DEFAULT_TITLE_FONT, plot, false );
    chart.setBackgroundPaint( lightBlue );
    xAxis.setAutoRangeIncludesZero( false );
    yAxis.setAutoRangeIncludesZero( false );

    if(chartPanel!=null) // if chart panel already exists, just chnage jfreechart instance in it
      chartPanel.setChart(chart);
    else { // add chart panel for first time
      // Put into a panel
      chartPanel = new ChartPanel(chart, true, true, true, true, false);
      chartPanel.setBorder(BorderFactory.createEtchedBorder(EtchedBorder.
          LOWERED));
      chartPanel.setMouseZoomable(true);
      chartPanel.setDisplayToolTips(true);
      chartPanel.setHorizontalAxisTrace(false);
      chartPanel.setVerticalAxisTrace(false);
      displayPanel.add(chartPanel,  new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
            ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(2, 3, 0, 3), 0, 0));
    }

  }



  public static void main(String[] args) {
    RuptureAnimationGUI ruptureAnimationGUI = new RuptureAnimationGUI();
  }

  /**
   * Load the fault sections to be displayed in the window
   */
  private ArrayList  loadFaultSections() {
    ArrayList sectionNames = new ArrayList();
    try {
      LocationList locList=null;
      File file = new File(FAULT_SECTION_FILE_NAME);
      BufferedReader br;
      if(file.exists()) { // load file without jar file
        // read from fault sections file
        FileReader fr = new FileReader(FAULT_SECTION_FILE_NAME);
        br = new BufferedReader(fr);
      } else { // load file from jar file
        URLConnection uc = FileUtils.class.getResource("/"+FAULT_SECTION_FILE_NAME).openConnection();
        br =
            new BufferedReader(new InputStreamReader((InputStream) uc.getContent()));
      }
      String line = br.readLine().trim();
      double lat, lon;
      int col=0;
      faultSectionCounter=-1;
      while(line!=null) {
        line=line.trim();
        if(!line.equalsIgnoreCase("")) { // if line is not a blank line
          if(line.startsWith("#"))  { // this is new fault section name
            col=0;
            sectionNames.add(line.substring(1));
            if(faultSectionCounter>=0)  addLocationListToPlot(locList, faultSectionCounter);
            locList = new LocationList();
            faultSectionCounter++;

          } else { // location on a faulr section
            StringTokenizer tokenizer = new StringTokenizer(line,",");
            lat = Double.parseDouble(tokenizer.nextToken());
            lon = Double.parseDouble(tokenizer.nextToken());
            locList.add(new Location(lat,lon,0.0));
          }
        }
        line=br.readLine();
      }
      // add the last fault section to the plot
      addLocationListToPlot(locList, faultSectionCounter++);
      br.close();
    }catch(Exception e) {
      e.printStackTrace();
    }
    return sectionNames;
  }

  /**
   * Add fault section to plot
   *
   * @param locList
   * @param faultSectionCounter
   * @param row
   * @throws InvalidRangeException
   * @throws java.lang.ClassCastException
   * @throws java.lang.ArrayIndexOutOfBoundsException
   */
   private void addLocationListToPlot(LocationList locList,
                                     int index) throws
      InvalidRangeException, ClassCastException, ArrayIndexOutOfBoundsException {
    GriddedSurface griddedSurface = new GriddedSurface(1, locList.size());
    for (int i = 0; i < locList.size(); ++i)
      griddedSurface.setLocation(0, i, locList.get(i));
    GriddedSurfaceXYDataSet griddedDataSet = new GriddedSurfaceXYDataSet(griddedSurface);
    if(index==0) plot.setDataset(griddedDataSet);
    else plot.setDataset(index-1, griddedDataSet);
  }

  /**
   * intialize the GUI components
   * @throws java.lang.Exception
   */
  private void jbInit() throws Exception {
    this.getContentPane().setLayout(gridBagLayout3);
    displayPanel.setLayout(gridBagLayout4);
    playButton.setText(PLAY);
    controlSplitPane.setOrientation(JSplitPane.VERTICAL_SPLIT);
    controlSplitPane.setLastDividerLocation(375);
    filterParamsPanel.setLayout(gridBagLayout2);
    buttonPanel.setLayout(gridBagLayout1);
    stopButton.setText("Stop");
    // set the colors
    this.playButton.setForeground(buttonColor);
    this.stopButton.setForeground(buttonColor);
    this.ruptureSlider.setForeground(buttonColor);
    this.currentRupLabel.setForeground(buttonColor);
    this.rupValLabel.setForeground(buttonColor);

    this.getContentPane().add(controlSplitPane,  new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
            ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(5, 7, 3, 4), 0, 374));
    controlSplitPane.add(filterSplitPane, JSplitPane.TOP);
    filterSplitPane.add(displayPanel, JSplitPane.LEFT);
    filterSplitPane.add(this.filterParamsPanel, JSplitPane.RIGHT);
    controlSplitPane.add(buttonPanel, JSplitPane.BOTTOM);

    buttonPanel.add(playButton,  new GridBagConstraints(0, 1, 1, 1, 0.0, 0.0
        ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(0, 104, 10, 0), 12, 8));
    buttonPanel.add(stopButton,  new GridBagConstraints(1, 1, 1, 1, 0.0, 0.0
        ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(0, 0, 10, 0), 10, 8));

    buttonPanel.add(this.currentRupLabel,  new GridBagConstraints(2, 1, 1, 1, 0.0, 0.0
        ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(0, 15, 10, 0), 0, 8));
    buttonPanel.add(this.rupValLabel,  new GridBagConstraints(3, 1, 1, 1, 0.0, 0.0
        ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(0, 2, 10, 0), 10, 8));

    filterParamsPanel.add(this.rupFilterGuiBean,  new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
            ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(2, 3, 0, 3), 0, 0));
    filterParamsPanel.add(this.filterButton,  new GridBagConstraints(0, 1, 1, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(2, 3, 0, 3), 0, 0));
    IntegerParameterEditor timeDelayParamEditor = new IntegerParameterEditor(timeDelayParam);
    filterParamsPanel.add(timeDelayParamEditor,  new GridBagConstraints(0, 2, 1, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(2, 3, 0, 3), 0, 0));
    // add action listeners
    stopButton.addActionListener(this);
    this.playButton.addActionListener(this);
    filterButton.addActionListener(this);


  }
}
