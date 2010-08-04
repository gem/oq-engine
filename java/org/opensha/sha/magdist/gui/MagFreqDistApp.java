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
import java.awt.FlowLayout;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.IOException;
import java.util.ArrayList;

import javax.swing.ImageIcon;
import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JCheckBoxMenuItem;
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
import javax.swing.event.ChangeEvent;

import org.jfree.data.Range;
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ConstrainedStringParameterEditor;
import org.opensha.commons.param.editor.ParameterListEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.gui.controls.PlotColorAndLineTypeSelectorControlPanel;
import org.opensha.sha.gui.infoTools.ButtonControlPanel;
import org.opensha.sha.gui.infoTools.ButtonControlPanelAPI;
import org.opensha.sha.gui.infoTools.GraphPanel;
import org.opensha.sha.gui.infoTools.GraphPanelAPI;
import org.opensha.sha.gui.infoTools.GraphWindow;
import org.opensha.sha.gui.infoTools.GraphWindowAPI;
import org.opensha.sha.gui.infoTools.PlotCurveCharacterstics;
import org.opensha.sha.magdist.ArbIncrementalMagFreqDist;
import org.opensha.sha.magdist.GaussianMagFreqDist;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.magdist.SingleMagFreqDist;
import org.opensha.sha.magdist.SummedMagFreqDist;
import org.opensha.sha.magdist.YC_1985_CharMagFreqDist;
import org.opensha.sha.param.MagFreqDistParameter;
import org.opensha.sha.param.MagPDF_Parameter;
import org.opensha.sha.param.editor.MagDistParameterEditorAPI;
import org.opensha.sha.param.editor.MagFreqDistParameterEditor;
import org.opensha.sha.param.editor.MagPDF_ParameterEditor;
/**
 * <p>Title:MagFreqDistApp </p>
 *
 * <p>Description: Shows the MagFreqDist Editor and plot in a window.</p>
 *
 * <p>Copyright: Copyright (c) 2002</p>
 *
 * <p>Company: </p>
 *
 * @author not attributable
 * @version 1.0
 */
public class MagFreqDistApp
    extends JFrame implements GraphPanelAPI,ButtonControlPanelAPI,GraphWindowAPI,
    ParameterChangeListener{

  private JSplitPane mainSplitPane = new JSplitPane();
  private JSplitPane plotSplitPane = new JSplitPane();
  private JTabbedPane plotTabPane = new JTabbedPane();
  private JPanel editorPanel = new JPanel();
  private JPanel MagSelectionEditorPanel;
  private JPanel buttonPanel = new JPanel();

  /**
   * Defines the panel and layout for the GUI elements
   */
  private JPanel incrRatePlotPanel = new JPanel();
  private JPanel momentRatePlotPanel = new JPanel();
  private JPanel cumRatePlotPanel = new JPanel();
  private GridBagLayout gridBagLayout1 = new GridBagLayout();
  private FlowLayout flowLayout1 = new FlowLayout();
  private BorderLayout borderLayout1 = new BorderLayout();
  private JButton addButton = new JButton();

  protected final static int W = 870;
  protected final static int H = 750;

  private final boolean D = false;

  //instance for the ButtonControlPanel
  private ButtonControlPanel buttonControlPanel;

  //instance of the GraphPanel (window that shows all the plots)
  private GraphPanel incrRateGraphPanel,momentRateGraphPanel,cumRateGraphPanel;

  //instance of the GraphWindow to pop up when the user wants to "Peel-Off" curves;
  private GraphWindow graphWindow;

  private JSplitPane paramSplitPane = new JSplitPane();

  //X and Y Axis  when plotting the Curves Name
  private String incrRateXAxisName = "Magnitude", incrRateYAxisName = "Incremental-Rate";
  //X and Y Axis  when plotting the Curves Name
  private String cumRateXAxisName = "Magnitude" , cumRateYAxisName = "Cumulative-Rate";
  //X and Y Axis  when plotting the Curves Name
  private String momentRateXAxisName = "Magnitude", momentRateYAxisName =  "Moment-Rate";

  private boolean isIncrRatePlot,isMomentRatePlot,isCumRatePlot;

  //log flags declaration
  private boolean xLog;
  private boolean yLog;

  /**
   * these four values save the custom axis scale specified by user
   */
  private double incrRateMinXValue,incrRateMaxXValue,incrRateMinYValue,incrRateMaxYValue;
  private double cumRateMinXValue,cumRateMaxXValue,cumRateMinYValue,cumRateMaxYValue;
  private double momentRateMinXValue,momentRateMaxXValue,momentRateMinYValue,momentRateMaxYValue;

  private boolean incrCustomAxis,momentCustomAxis,cumCustomAxis;

  private JButton peelOffButton = new JButton();
  private JMenuBar menuBar = new JMenuBar();
  private JMenu fileMenu = new JMenu();


  private JMenuItem fileExitMenu = new JMenuItem();
  private JMenuItem fileSaveMenu = new JMenuItem();
  private JMenuItem filePrintMenu = new JCheckBoxMenuItem();
  private JToolBar jToolBar = new JToolBar();

  private JButton closeButton = new JButton();
  private ImageIcon closeFileImage = new ImageIcon(FileUtils.loadImage("icons/closeFile.png"));

  private JButton printButton = new JButton();
  private ImageIcon printFileImage = new ImageIcon(FileUtils.loadImage("icons/printFile.jpg"));

  private  JButton saveButton = new JButton();
  ImageIcon saveFileImage = new ImageIcon(FileUtils.loadImage("icons/saveFile.jpg"));

  private final static String POWERED_BY_IMAGE = "logos/PoweredByOpenSHA_Agua.jpg";

  private JLabel imgLabel = new JLabel(new ImageIcon(FileUtils.loadImage(this.POWERED_BY_IMAGE)));
  private JButton clearButton = new JButton();


  //instance of the MagDist Editor
  private MagDistParameterEditorAPI magDistEditor;
  private MagFreqDistParameterEditor magFreqDistEditor;
  private MagPDF_ParameterEditor magPDF_Editor ;

  private JCheckBox jCheckSumDist = new JCheckBox();


  //list for storing all types of Mag Freq. dist. (incremental, cumulative and momentRate).
  private ArrayList incrRateFunctionList = new ArrayList();
  private ArrayList cumRateFunctionList =  new ArrayList();
  private ArrayList momentRateFunctionList = new ArrayList();
  //summed distribution
  private final static String textString = "(Last Plotted Dist. gets used"+
      ", Summed Dist. gets used if selected)";
  private JLabel textLabel = new JLabel(textString);


  private String incrRatePlotTitle="",cumRatePlotTitle="",momentRatePlotTitle="";


  //checks to see if summed distribution has been added, then this number will be
  //one less then the number of plotted disctributions.
  private int numFunctionsWithoutSumDist;
  private static final String MAG_DIST_PARAM_SELECTOR_NAME = "Mag. Dist. Type";
  private static final String MAG_FREQ_DIST = "Mag. Freq. Dist";
  private static final String MAG_PDF_PARAM = "Mag. PDF";
  private StringParameter stParam;
  private SummedMagFreqDist summedMagFreqDist;


  public MagFreqDistApp() {
    try {
      jbInit();
    }
    catch (Exception exception) {
      exception.printStackTrace();
    }
  }

  private void jbInit() throws Exception {
    getContentPane().setLayout(borderLayout1);



    addButton.setText("Plot-Dist");
    addButton.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        addButton_actionPerformed(e);
      }
    });

    //object for the ButtonControl Panel
    buttonControlPanel = new ButtonControlPanel(this);

    peelOffButton.setText("Peel-Off");
    peelOffButton.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        peelOffButton_actionPerformed(e);
      }
    });

    clearButton.setText("Clear-Plot");
    clearButton.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        clearButton_actionPerformed(e);
      }
    });


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

    mainSplitPane.setOrientation(JSplitPane.VERTICAL_SPLIT);
    plotSplitPane.setOrientation(JSplitPane.HORIZONTAL_SPLIT);
    editorPanel.setLayout(gridBagLayout1);

    buttonPanel.setLayout(flowLayout1);
    plotSplitPane.add(plotTabPane, JSplitPane.LEFT);
    mainSplitPane.add(plotSplitPane, JSplitPane.TOP);
    plotSplitPane.add(paramSplitPane, JSplitPane.RIGHT);
    mainSplitPane.add(buttonPanel, JSplitPane.BOTTOM);
    paramSplitPane.setOrientation(JSplitPane.VERTICAL_SPLIT);
    paramSplitPane.setDividerLocation(200);
    this.getContentPane().add(mainSplitPane, java.awt.BorderLayout.CENTER);
    plotSplitPane.setDividerLocation(600);
    mainSplitPane.setDividerLocation(570);
    incrRatePlotPanel.setLayout(gridBagLayout1);
    momentRatePlotPanel.setLayout(gridBagLayout1);
    cumRatePlotPanel.setLayout(gridBagLayout1);
    plotTabPane.add("Incremental-Rate", incrRatePlotPanel);
    plotTabPane.add("Cumulative-Rate", cumRatePlotPanel);
    plotTabPane.add("Moment-Rate", momentRatePlotPanel);
    plotTabPane.addChangeListener(new javax.swing.event.ChangeListener() {
      public void stateChanged(ChangeEvent e) {
        plotTabPane_stateChanged(e);
      }
    });
    jCheckSumDist.setForeground(Color.black);
    jCheckSumDist.setText("Summed Dist");
    jCheckSumDist.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        jCheckSumDist_actionPerformed(e);
      }
    });
    jCheckSumDist.setVisible(false);
    buttonPanel.add(jCheckSumDist,0);
    buttonPanel.add(addButton, 1);
    buttonPanel.add(clearButton, 2);
    buttonPanel.add(peelOffButton, 3);
    buttonPanel.add(buttonControlPanel, 4);
    buttonPanel.add(imgLabel, 5);
    buttonPanel.add(textLabel, 6);


    incrRateGraphPanel = new GraphPanel(this);
    cumRateGraphPanel = new GraphPanel(this);
    momentRateGraphPanel = new GraphPanel(this);

    this.setSize( W, H );
    Dimension dm = Toolkit.getDefaultToolkit().getScreenSize();
    setLocation( ( dm.width - this.getSize().width ) / 2, ( dm.height - this.getSize().height ) / 2 );
    this.setTitle("Magnitude Frequency Distribution Application");
    this.setVisible( true );
  }

  /**
   * Initiates the Mag Param selection and adds that to the GUI.
   * User has the option of creating a MagFreqDist or MagPDF
   */
  private void initMagParamEditor() {
    ArrayList magParamTypes = new ArrayList();
    magParamTypes.add(this.MAG_FREQ_DIST);
    magParamTypes.add(this.MAG_PDF_PARAM);
    stParam = new StringParameter(this.
                                  MAG_DIST_PARAM_SELECTOR_NAME,
                                  magParamTypes,
                                  (String) magParamTypes.get(0));
    ConstrainedStringParameterEditor stParamEditor = new
        ConstrainedStringParameterEditor(stParam);
    stParam.addParameterChangeListener(this);
    MagSelectionEditorPanel = new JPanel();
    MagSelectionEditorPanel.setLayout(gridBagLayout1);
    MagSelectionEditorPanel.add(stParamEditor,
                    new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
                                           , GridBagConstraints.NORTH,
                                           GridBagConstraints.BOTH,
                                           new Insets(1, 1, 1, 1), 0, 0));
    MagSelectionEditorPanel.validate();
    MagSelectionEditorPanel.repaint();
    this.paramSplitPane.add(MagSelectionEditorPanel,paramSplitPane.TOP);
    this.setDefaultCloseOperation(3);


  }

  /**
   * Creates the MagDist Param.
   * It can be Mag_PDF_Param or MagFreqDistParam.
   * Adding the SummedDist MagDist to the MagFreqDistParam list of Distribution.
   * It has not been added the Mag_PDFParam because then user will have to provide
   * Relative Wts for the Dist. which has not decided yet.
   *
   */
  private void createMagParam(){

    String magTypeSelected = (String)stParam.getValue();
    if(magTypeSelected.equals(MAG_FREQ_DIST)){

      if(magFreqDistEditor == null){
        ArrayList distNames = new ArrayList();
        distNames.add(SingleMagFreqDist.NAME);
        distNames.add(GutenbergRichterMagFreqDist.NAME);
        distNames.add(GaussianMagFreqDist.NAME);
        distNames.add(YC_1985_CharMagFreqDist.NAME);
        distNames.add(SummedMagFreqDist.NAME);
        distNames.add(ArbIncrementalMagFreqDist.NAME);
        String MAG_DIST_PARAM_NAME = "Mag Dist Param";
        // make  the mag dist parameter
        MagFreqDistParameter magDist = new MagFreqDistParameter(
            MAG_DIST_PARAM_NAME, distNames);
        magFreqDistEditor = new MagFreqDistParameterEditor();
        magFreqDistEditor.setParameter(magDist);
        // make the magdist param button invisible instead display it as the panel in the window
        magFreqDistEditor.setMagFreqDistParamButtonVisible(false);
      }
      else
        editorPanel.remove(magDistEditor.getMagFreqDistParameterEditor());
      setMagDistEditor(magFreqDistEditor);
    }
    else{
      editorPanel.remove(magDistEditor.getMagFreqDistParameterEditor());
      //making the Summed Distn option not visible for Mag PDF.
      this.makeSumDistVisible(false);
      if(magPDF_Editor == null){
        String MAG_DIST_PARAM_NAME = "Mag Dist Param";
        // make  the mag dist parameter
        ArrayList distNames = new ArrayList();
        distNames.add(SingleMagFreqDist.NAME);
        distNames.add(GutenbergRichterMagFreqDist.NAME);
        distNames.add(GaussianMagFreqDist.NAME);
        distNames.add(YC_1985_CharMagFreqDist.NAME);
        distNames.add(ArbIncrementalMagFreqDist.NAME);
        MagPDF_Parameter magDist = new MagPDF_Parameter(
            MAG_DIST_PARAM_NAME, distNames);
        magPDF_Editor = new MagPDF_ParameterEditor();
        magPDF_Editor.setParameter(magDist);
        // make the magdist param button invisible instead display it as the panel in the window
        magPDF_Editor.setMagFreqDistParamButtonVisible(false);
      }
      setMagDistEditor(magPDF_Editor);
    }
    magDistEditor.refreshParamEditor();
  }

  /**
   *
   */
  public void setMagDistEditor(MagDistParameterEditorAPI magDistEditor) {

    this.magDistEditor = magDistEditor;
    ParameterListEditor listEditor = magDistEditor.createMagFreqDistParameterEditor();
    ParameterAPI distParam = listEditor.getParameterEditor(MagFreqDistParameter.DISTRIBUTION_NAME).getParameter();
    distParam.addParameterChangeListener(this);
    ArrayList allowedVals = ((StringConstraint)listEditor.getParameterEditor(MagFreqDistParameter.DISTRIBUTION_NAME).
    		getParameter().getConstraint()).getAllowedValues();
    //if Summed Distn. is within the allowed list of MagDistn then show it as the JCheckBox.
    //it will work the same for the Mag_PDF_Dist
    if(allowedVals.contains(SummedMagFreqDist.NAME)){
    		makeSumDistVisible(true);
    }
    editorPanel.add(listEditor,
                    new GridBagConstraints(0, 1, 1, 1, 1.0, 1.0
                                           , GridBagConstraints.NORTH,
                                           GridBagConstraints.BOTH,
                                           new Insets(2, 2, 2, 2), 0, 0));
    //if user is not being the shown the option of both PDF and MagFreqDist then
    //user just making the SplitPane not adjustable.
   if(MagSelectionEditorPanel == null){
     paramSplitPane.setDividerLocation(0);
     paramSplitPane.setOneTouchExpandable(false);
   }
   paramSplitPane.add(editorPanel,paramSplitPane.BOTTOM);
   editorPanel.validate();
   editorPanel.repaint();
  }


  /**
   * Makes the Summed Dist. option visible or invisible based on the passed in
   * argument to the function. By default Summed Distribution option is not visible.
   * Once this method is called it makes the Summed Dist. option available
   * to user.
   * @param toShow boolean
   */
  public void makeSumDistVisible(boolean toShow){
    this.jCheckSumDist.setVisible(toShow);
  }


  /**
   * This function is called when Summed distribution box is clicked
   *
   * @param e
   */
  void jCheckSumDist_actionPerformed(ActionEvent e) {

    if(jCheckSumDist.isSelected()) {
      magDistEditor.setSummedDistPlotted(true);
     // if user wants a summed distribution
      double min = magDistEditor.getMin();
      double max = magDistEditor.getMax();
      int num = magDistEditor.getNum();
      // make the new object of summed distribution
      summedMagFreqDist = new  SummedMagFreqDist(min,max,num);

      // add all the existing distributions to the summed distribution
      int size = incrRateFunctionList.size();

      try {
      for(int i=0; i < size; ++i)
        summedMagFreqDist.addIncrementalMagFreqDist((IncrementalMagFreqDist)incrRateFunctionList.get(i));
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
     magDistEditor.setSummedDistPlotted(false);
     if(incrRateFunctionList.size()>0){
       // remove the summed distribution and related moment rate and cumulative rate
       incrRateFunctionList.remove(incrRateFunctionList.size() - 1);
       cumRateFunctionList.remove(cumRateFunctionList.size() - 1);
       momentRateFunctionList.remove(momentRateFunctionList.size() - 1);
       //removing the plotting features from the plot prefs. for the summed distribution
       ArrayList incrPlotFeaturesList = incrRateGraphPanel.
           getCurvePlottingCharacterstic();
       ArrayList cumPlotFeaturesList = cumRateGraphPanel.
           getCurvePlottingCharacterstic();
       ArrayList momentPlotFeaturesList = momentRateGraphPanel.
           getCurvePlottingCharacterstic();
       incrPlotFeaturesList.remove(incrPlotFeaturesList.size() - 1);
       cumPlotFeaturesList.remove(cumPlotFeaturesList.size() - 1);
       momentPlotFeaturesList.remove(momentPlotFeaturesList.size() - 1);
     }
   }
    addGraphPanel();
  }


  /**
  *  Adds a feature to the GraphPanel attribute of the EqkForecastApplet object
  */
 private void addGraphPanel() {

     // Starting
     String S = ": addGraphPanel(): ";

     incrRateGraphPanel.drawGraphPanel(incrRateXAxisName,incrRateYAxisName,
                                       incrRateFunctionList,xLog,yLog,incrCustomAxis,
                                       incrRatePlotTitle,buttonControlPanel);
     cumRateGraphPanel.drawGraphPanel(cumRateXAxisName,cumRateYAxisName,
                                       cumRateFunctionList,xLog,yLog,cumCustomAxis,
                                       cumRatePlotTitle,buttonControlPanel);
     momentRateGraphPanel.drawGraphPanel(momentRateXAxisName,momentRateYAxisName,
                                       momentRateFunctionList,xLog,yLog,momentCustomAxis,
                                       momentRatePlotTitle,buttonControlPanel);
     togglePlot();
  }

  //checks if the user has plot the data window or plot window
  public void togglePlot(){
    incrRatePlotPanel.removeAll();
    cumRatePlotPanel.removeAll();
    momentRatePlotPanel.removeAll();
    incrRateGraphPanel.togglePlot(buttonControlPanel);
    cumRateGraphPanel.togglePlot(buttonControlPanel);
    momentRateGraphPanel.togglePlot(buttonControlPanel);

    incrRatePlotPanel.add(incrRateGraphPanel, new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0
           , GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ));
    incrRatePlotPanel.validate();
    incrRatePlotPanel.repaint();

    cumRatePlotPanel.add(cumRateGraphPanel, new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0
           , GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ));
    cumRatePlotPanel.validate();
    cumRatePlotPanel.repaint();

    momentRatePlotPanel.add(momentRateGraphPanel,
                            new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
                                                   , GridBagConstraints.CENTER,
                                                   GridBagConstraints.BOTH,
                                                   new Insets(0, 0, 0, 0), 0, 0));
    momentRatePlotPanel.validate();
    momentRatePlotPanel.repaint();
  }


  /**
   * private function to insert the summed distribtuion to function list
   * It first makes the clone of the original function list
   * Then clears the original function list and then adds summed distribtuion to
   * the top of the original function list and then adds other distributions
   *
   */
  private void insertSummedDistribution() {
      // add the summed distribution to the list
      incrRateFunctionList.add(summedMagFreqDist);
      cumRateFunctionList.add(summedMagFreqDist.getCumRateDist());
      momentRateFunctionList.add(summedMagFreqDist.getMomentRateDist());
      String metadata = "\n"+( (EvenlyDiscretizedFunc) incrRateFunctionList.get(incrRateFunctionList.size()-1)).getInfo()+"\n";
      for (int i = 0; i < incrRateFunctionList.size()-1; ++i)
        metadata += (i+1)+")"+( (EvenlyDiscretizedFunc) incrRateFunctionList.get(i)).getInfo()+ "\n";

      magDistEditor.setMagDistFromParams(summedMagFreqDist, metadata);

      addGraphPanel();
       //adding the plotting features to the sum distribution because this will
       //allow to create the default color scheme first then can change for the
       //sum distribution
      ArrayList incrPlotFeaturesList = incrRateGraphPanel.getCurvePlottingCharacterstic();
      ArrayList cumPlotFeaturesList = cumRateGraphPanel.getCurvePlottingCharacterstic();
      ArrayList momentPlotFeaturesList = momentRateGraphPanel.getCurvePlottingCharacterstic();
      incrPlotFeaturesList.set(incrPlotFeaturesList.size() -1,new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
          Color.BLACK,1.0,1));
      cumPlotFeaturesList.set(incrPlotFeaturesList.size() -1,new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
          Color.BLACK,1.0,1));
      momentPlotFeaturesList.set(incrPlotFeaturesList.size() -1,new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
          Color.BLACK,1.0,1));
      addGraphPanel();
  }

  /**
   *
   * @param e ChangeEvent
   */
  private void plotTabPane_stateChanged(ChangeEvent e){
    JTabbedPane pane = (JTabbedPane)e.getSource();
    int index = pane.getSelectedIndex();
    if(index == 0){
      isCumRatePlot = false;
      isIncrRatePlot = true;
      isMomentRatePlot = false;
    }
    else if(index ==1){
      isCumRatePlot = true;
      isIncrRatePlot = false;
      isMomentRatePlot = false;
    }
    else if(index ==2){
      isCumRatePlot = false;
      isIncrRatePlot = false;
      isMomentRatePlot = true;
    }
  }


  /**
   * this function is called when "Add Dist" button is clicked
   * @param e
   */
  void addButton_actionPerformed(ActionEvent e) {
     addButton();
  }


  /**
   * This causes the model data to be calculated and a plot trace added to
   * the current plot
   *
   * @param  e  The feature to be added to the Button_mouseClicked attribute
   */
  private void addButton() {

    if (D)
      System.out.println("Starting");

    try {
    	if(magDistEditor instanceof MagFreqDistParameterEditor)
    	   magDistEditor.setSummedDistPlotted(false);
      this.magDistEditor.setMagDistFromParams();

      String magDistMetadata = magDistEditor.getMagFreqDistParameterEditor().
          getVisibleParametersCloned().getParameterListMetadataString();

      IncrementalMagFreqDist function = (IncrementalMagFreqDist)this.
          magDistEditor.getParameter().getValue();
      function.setInfo(magDistMetadata);
      function.setName("Mag - Incremental Rate Dist.");
      if (D)
        System.out.println(" after getting mag dist from editor");
      EvenlyDiscretizedFunc cumRateFunction;
      EvenlyDiscretizedFunc moRateFunction;

      // get the cumulative rate and moment rate distributions for this function
      cumRateFunction = (EvenlyDiscretizedFunc) function.getCumRateDist();
      cumRateFunction.setInfo(magDistMetadata);
      cumRateFunction.setName("Mag - Cumulative Rate Dist.");
      moRateFunction = (EvenlyDiscretizedFunc) function.getMomentRateDist();
      moRateFunction.setInfo(magDistMetadata);
      moRateFunction.setName("Mag - Moment Rate Dist.");
      int size = incrRateFunctionList.size();
      //if the number of functions is 1 more then numFunctionsWithoutSumDist
      //then summed has been added ealier so needs to be removed
      if (size == numFunctionsWithoutSumDist + 1) {
        incrRateFunctionList.remove(incrRateFunctionList.size() - 1);
        cumRateFunctionList.remove(cumRateFunctionList.size() - 1);
        momentRateFunctionList.remove(momentRateFunctionList.size() - 1);

        //removing the plotting features from the plot prefs. for the summed distribution
        ArrayList incrPlotFeaturesList = incrRateGraphPanel.
            getCurvePlottingCharacterstic();
        ArrayList cumPlotFeaturesList = cumRateGraphPanel.
            getCurvePlottingCharacterstic();
        ArrayList momentPlotFeaturesList = momentRateGraphPanel.
            getCurvePlottingCharacterstic();
        incrPlotFeaturesList.remove(incrPlotFeaturesList.size() - 1);
        cumPlotFeaturesList.remove(cumPlotFeaturesList.size() - 1);
        momentPlotFeaturesList.remove(momentPlotFeaturesList.size() - 1);
      }

      // add the functions to the functionlist
      incrRateFunctionList.add( (EvenlyDiscretizedFunc) function);
      cumRateFunctionList.add(cumRateFunction);
      momentRateFunctionList.add(moRateFunction);
      numFunctionsWithoutSumDist = momentRateFunctionList.size();

      if (jCheckSumDist.isVisible() && jCheckSumDist.isSelected()) { // if summed distribution is selected, add to summed distribution
        try {
          magDistEditor.setSummedDistPlotted(true);
          double min = magDistEditor.getMin();
          double max = magDistEditor.getMax();
          int num = magDistEditor.getNum();

          if(summedMagFreqDist == null)
            summedMagFreqDist = new SummedMagFreqDist(min,max,num);
          // add this distribution to summed distribution
          summedMagFreqDist.addIncrementalMagFreqDist(function);

          // this function will insert summed distribution at top of function list
          insertSummedDistribution();

        }
        catch (Exception ex) {
          JOptionPane.showMessageDialog(this,
                                        "min, max, and num must be the same to sum the distributions." +
                                        "\n To add this distribution first deselect the Summed Dist option"
              );
          return;
        }
      }
      // draw the graph
      addGraphPanel();

      // catch the error and display messages in case of input error
    }
    catch (NumberFormatException e) {
      e.printStackTrace();
      JOptionPane.showMessageDialog(this,
                                    new String("Enter a Valid Numerical Value"),
                                    "Invalid Data Entered",
                                    JOptionPane.ERROR_MESSAGE);
    }
    catch (NullPointerException e) {
      e.printStackTrace();
      //JOptionPane.showMessageDialog(this,new String(e.getMessage()),"Data Not Entered",JOptionPane.ERROR_MESSAGE);
      e.printStackTrace();
    }
    catch (Exception e) {
      e.printStackTrace();
      JOptionPane.showMessageDialog(this, new String(e.getMessage()),
                                    "Invalid Data Entered",
                                    JOptionPane.ERROR_MESSAGE);
    }

    if (D)
      System.out.println("Ending");

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

    int loc = mainSplitPane.getDividerLocation();
    int newLoc = loc;

    if( clearFunctions){
      incrRateGraphPanel.removeChartAndMetadata();
      cumRateGraphPanel.removeChartAndMetadata();
      momentRateGraphPanel.removeChartAndMetadata();
      incrRatePlotPanel.removeAll();
      cumRatePlotPanel.removeAll();
      momentRatePlotPanel.removeAll();

      //panel.removeAll();
      incrRateFunctionList.clear();
      cumRateFunctionList.clear();
      momentRateFunctionList.clear();
      summedMagFreqDist = null;
    }
    if(isCumRatePlot)
      cumCustomAxis = false;
    else if(isMomentRatePlot)
      this.momentCustomAxis = false;
    else if(isIncrRatePlot)
      this.incrCustomAxis = false;

    mainSplitPane.setDividerLocation( newLoc );
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
    if(isIncrRatePlot)
      incrRateGraphPanel.save();
    else if(isCumRatePlot)
      cumRateGraphPanel.save();
    else if(isMomentRatePlot)
      momentRateGraphPanel.save();
  }

  /**
   * Creates a print job for the chart.
   */
  public void print() {
    if(isIncrRatePlot)
      incrRateGraphPanel.print(this);
    else if(isCumRatePlot)
      cumRateGraphPanel.print(this);
    else if(isMomentRatePlot)
      momentRateGraphPanel.print(this);
  }


  /**
   * Actual method implementation of the "Peel-Off"
   * This function peels off the window from the current plot and shows in a new
   * window. The current plot just shows empty window.
   */
  private void peelOffCurves(){
    graphWindow = new GraphWindow(this);
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
   *
   * @returns the Min X-Axis Range Value, if custom Axis is choosen
   */
  public double getMinX() {
    if(isIncrRatePlot)
      return incrRateMinXValue;
    else if(isCumRatePlot)
      return cumRateMinXValue;
    else
      return momentRateMinXValue;
  }

  /**
   *
   * @returns the Max X-Axis Range Value, if custom axis is choosen
   */
  public double getMaxX() {
    if(isIncrRatePlot)
      return incrRateMaxXValue;
    else if(isCumRatePlot)
      return cumRateMaxXValue;
    else
      return momentRateMaxXValue;
  }

  /**
   *
   * @returns the Min Y-Axis Range Value, if custom axis is choosen
   */
  public double getMinY() {
    if(isIncrRatePlot)
      return incrRateMinYValue;
    else if(isCumRatePlot)
      return cumRateMinYValue;
    else
      return momentRateMinYValue;
  }

  /**
   *
   * @returns the Max X-Axis Range Value, if custom axis is choosen
   */
  public double getMaxY() {
    if(isIncrRatePlot)
      return incrRateMaxYValue;
    else if(isCumRatePlot)
      return cumRateMaxYValue;
    else
      return momentRateMaxYValue;
  }


  /**
   * Main function to run this as an application
   * @param args String[]
   */
  public static void main(String[] args) {

    MagFreqDistApp magFreqDistApp = new MagFreqDistApp();
    magFreqDistApp.initMagParamEditor();
    magFreqDistApp.createMagParam();
    magFreqDistApp.makeSumDistVisible(true);
  }



  public void setAxisRange(double xMin, double xMax, double yMin, double yMax) {
    if(isIncrRatePlot){
      incrRateMinXValue = xMin;
      incrRateMaxXValue = xMax;
      incrRateMinYValue = yMin;
      incrRateMaxYValue = yMax;
      this.incrCustomAxis=true;
    }
    else if(isCumRatePlot){
      cumRateMinXValue = xMin;
      cumRateMaxXValue = xMax;
      cumRateMinYValue = yMin;
      cumRateMaxYValue = yMax;
      this.cumCustomAxis = true;
    }
    else{
      momentRateMinXValue = xMin;
      momentRateMaxXValue = xMax;
      momentRateMinYValue = yMin;
      momentRateMaxYValue = yMax;
      this.momentCustomAxis = true;
    }
    addGraphPanel();
  }

  public void setAutoRange() {
    if(isIncrRatePlot)
      incrCustomAxis=false;
    if(isCumRatePlot)
      cumCustomAxis=false;
    if(isMomentRatePlot)
      momentCustomAxis=false;
    addGraphPanel();
  }


  public void setX_Log(boolean xLog) {
    this.xLog = xLog;
    this.addGraphPanel();
  }

  public void setY_Log(boolean yLog) {
    this.yLog = yLog;
    this.addGraphPanel();
  }

  public Range getX_AxisRange() {
    if(isIncrRatePlot)
      return incrRateGraphPanel.getX_AxisRange();
    else if(isCumRatePlot)
      return cumRateGraphPanel.getX_AxisRange();
    else
      return momentRateGraphPanel.getX_AxisRange();
  }

  public Range getY_AxisRange() {
    if(isIncrRatePlot)
      return incrRateGraphPanel.getY_AxisRange();
    else if(isCumRatePlot)
      return cumRateGraphPanel.getY_AxisRange();
    else
      return momentRateGraphPanel.getY_AxisRange();
  }

  public ArrayList getPlottingFeatures() {
    if(isIncrRatePlot)
      return incrRateGraphPanel.getCurvePlottingCharacterstic();
    else if(isCumRatePlot)
      return cumRateGraphPanel.getCurvePlottingCharacterstic();
    else
      return momentRateGraphPanel.getCurvePlottingCharacterstic();
  }

  public void plotGraphUsingPlotPreferences() {
    ArrayList plotPrefs;
    if(isIncrRatePlot){
      plotPrefs = incrRateGraphPanel.getCurvePlottingCharacterstic();
      cumRateGraphPanel.setCurvePlottingCharacterstic(plotPrefs);
      momentRateGraphPanel.setCurvePlottingCharacterstic(plotPrefs);
    }
    else if(isCumRatePlot){
      plotPrefs = cumRateGraphPanel.getCurvePlottingCharacterstic();
      incrRateGraphPanel.setCurvePlottingCharacterstic(plotPrefs);
      momentRateGraphPanel.setCurvePlottingCharacterstic(plotPrefs);
    }
    else{
      plotPrefs = momentRateGraphPanel.getCurvePlottingCharacterstic();
      incrRateGraphPanel.setCurvePlottingCharacterstic(plotPrefs);
      cumRateGraphPanel.setCurvePlottingCharacterstic(plotPrefs);
    }
    addGraphPanel();
  }

  public String getXAxisLabel() {
    if(isIncrRatePlot)
      return incrRateXAxisName;
    else if(isCumRatePlot)
      return cumRateXAxisName;
    else
      return momentRateXAxisName;
  }

  public String getYAxisLabel() {
    if(isIncrRatePlot)
      return incrRateYAxisName;
    else if(isCumRatePlot)
      return cumRateYAxisName;
    else
      return momentRateYAxisName;
  }

  public String getPlotLabel() {
    if(isIncrRatePlot)
      return incrRatePlotTitle;
    else if(isCumRatePlot)
      return cumRatePlotTitle;
    else
      return momentRatePlotTitle;

  }


  public void setXAxisLabel(String xAxisLabel) {
    if(isIncrRatePlot)
      incrRateXAxisName = xAxisLabel;
    else if(isCumRatePlot)
      cumRateXAxisName = xAxisLabel;
    else
      momentRateXAxisName = xAxisLabel;
  }

  public void setYAxisLabel(String yAxisLabel) {
    if (isIncrRatePlot)
      incrRateYAxisName = yAxisLabel;
    else if (isCumRatePlot)
      cumRateYAxisName = yAxisLabel;
    else
      momentRateYAxisName = yAxisLabel;

  }

  public void setPlotLabel(String plotTitle) {
    if(isIncrRatePlot)
      incrRatePlotTitle = plotTitle;
    else if(isCumRatePlot)
      cumRatePlotTitle = plotTitle;
    else
      momentRatePlotTitle = plotTitle;
  }

  public ArrayList getCurveFunctionList() {
    if(isIncrRatePlot)
      return incrRateFunctionList;
    else if(isCumRatePlot)
      return cumRateFunctionList;
    else
      return momentRateFunctionList;

  }

  public boolean getXLog() {
    return xLog;
  }

  public boolean getYLog() {
    return yLog;
  }

  public boolean isCustomAxis() {
    if(isIncrRatePlot)
      return incrCustomAxis;
    else if(isCumRatePlot)
      return cumCustomAxis;
    else
      return momentCustomAxis;
  }

  public void parameterChange(ParameterChangeEvent event) {
    String paramName = event.getParameterName();
    if(paramName.equals(this.MAG_DIST_PARAM_SELECTOR_NAME)){
      createMagParam();
    }
  }
}
