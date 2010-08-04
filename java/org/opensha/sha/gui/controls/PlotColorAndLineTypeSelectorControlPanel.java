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

package org.opensha.sha.gui.controls;

import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Component;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;

import javax.swing.JButton;
import javax.swing.JColorChooser;
import javax.swing.JComboBox;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.SwingConstants;

import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ConstrainedDoubleParameterEditor;
import org.opensha.commons.param.editor.ParameterListEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.sha.gui.infoTools.PlotCurveCharacterstics;

/**
 * <p>Title: PlotColorAndLineTypeSelectorControlPanel</p>
 * <p>Description: This class allows user to select different plotting
 * styles for curves. Here user can specify color, curve style and
 * it size. the default value for lines are 1.0f and and for shapes
 * it is 4.0f.
 * Currently supported Styles are:
 * SOLID_LINE
 * DOTTED_LINE
 * DASHED_LINE
 * DOT_DASH_LINE
 * X Symbols
 * CROSS_SYMBOLS
 * FILLED_CIRCLES
 * CIRCLES
 * FILLED_SQUARES
 * SQUARES
 * FILLED_TRIANGLES
 * TRIANGLES
 * FILLED_INV_TRIANGLES
 * INV_TRIANGLES
 * FILLED_DIAMONDS
 * DIAMONDS
 * LINE_AND_CIRCLES
 * LINE_AND_TRIANGLES
 * HISTOGRAMS
 * </p>
 * @author : Ned Field, Nitin Gupta and Vipin Gupta
 * @version 1.0
 */

public class PlotColorAndLineTypeSelectorControlPanel extends JFrame implements
    ActionListener,ParameterChangeListener{
  private JPanel jPanel1 = new JPanel();
  private JLabel jLabel1 = new JLabel();
  private JScrollPane colorAndLineTypeSelectorPanel = new JScrollPane();

  //X-Axis Label param name
  private StringParameter xAxisLabelParam;
  public final static String xAxisLabelParamName = "X-Axis Label";

  //Y-Axis Label param name
  private StringParameter yAxisLabelParam;
  public final static String yAxisLabelParamName = "Y-Axis Label";


  //Plot Label param name
  private StringParameter plotLabelParam;
  public final static String plotLabelParamName = "Plot Label";


  //Axis and plot labels variables
  private String xAxisLabel;
  private String yAxisLabel;
  private String plotLabel;


  //static String definitions
  private final static String colorChooserString = "Choose Color";
  private final static String lineTypeString = "Choose Line Type";
  //name of the attenuationrelationship weights parameter
  public static final String lineWidthParamName = "Size -";



  //static line types that allows user to select in combobox.
  public final static String SOLID_LINE = "Solid Line";
  public final static String DOTTED_LINE = "Dotted Line";
  public final static String DASHED_LINE = "Dash Line";
  public final static String DOT_DASH_LINE = "Dot and Dash Line";
  public final static String X = "X Symbols";
  public final static String CROSS_SYMBOLS = "+ Symbols";
  public final static String FILLED_CIRCLES = "Filled Circles";
  public final static String CIRCLES = "Circles";
  public final static String FILLED_SQUARES = "Filled Squares";
  public final static String SQUARES = "Squares";
  public final static String FILLED_TRIANGLES = "Filled Triangles";
  public final static String TRIANGLES = "Triangles";
  public final static String FILLED_INV_TRIANGLES = "Filled Inv. Triangles";
  public final static String INV_TRIANGLES = "Inv. Triangles";
  public final static String FILLED_DIAMONDS = "Filled Diamond";
  public final static String DIAMONDS = "Diamond";
  public final static String LINE_AND_CIRCLES = "Line and Circles";
  public final static String LINE_AND_TRIANGLES = "Line and Triangles";
  public final static String HISTOGRAM = "Histograms";
  public final static String STACKED_BAR = "Stacked Bar";
  
  //parameter for tick label font size
  private  StringParameter tickFontSizeParam;
  public static final String tickFontSizeParamName = "Set tick label size";
  //private ConstrainedStringParameterEditor tickFontSizeParamEditor;

  //parameter for axis label font size
  private StringParameter axisLabelsFontSizeParam;
  public static final String axislabelsFontSizeParamName = "Set axis label ";
  
  //parameter for plot label font size
  private StringParameter plotLabelsFontSizeParam;
  public static final String plotlabelsFontSizeParamName = "Set Plot label ";
  
  //private ConstrainedStringParameterEditor axisLabelsFontSizeParamEditor;

  //parameterList and editor for axis and plot label parameters
  private ParameterList plotParamList;
  private ParameterListEditor plotParamEditor;

  //Dynamic Gui elements array to show the dataset color coding and line plot scheme
  private JLabel[] datasetSelector;
  private JButton[] colorChooserButton;
  private JComboBox[] lineTypeSelector;
  //AttenuationRelationship parameters and list declaration
  private DoubleParameter[] lineWidthParameter;
  private ConstrainedDoubleParameterEditor[] lineWidthParameterEditor;

  private JButton applyButton = new JButton();
  private JButton cancelButton = new JButton();
  private BorderLayout borderLayout1 = new BorderLayout();

  //Curve characterstic array
  private ArrayList plottingFeatures;
  //default curve characterstics with values , when this control panel was called
  private ArrayList defaultPlottingFeatures;
  private JButton RevertButton = new JButton();
  //instance of application using this control panel
  private PlotColorAndLineTypeSelectorControlPanelAPI application;
  private JPanel curveFeaturePanel = new JPanel();
  private GridBagLayout gridBagLayout2 = new GridBagLayout();
  private JButton doneButton = new JButton();
  private GridBagLayout gridBagLayout1 = new GridBagLayout();

  //last updated width vals for Labels
  private int tickLabelWidth ;
  private int axisLabelWidth;
  private int plotLabelWidth;

  public PlotColorAndLineTypeSelectorControlPanel(PlotColorAndLineTypeSelectorControlPanelAPI api,
      ArrayList curveCharacterstics) {
    application = api;
    try {
      jbInit();
    }
    catch(Exception e) {
      e.printStackTrace();
    }

    Component parent = (Component)api;

    xAxisLabel = api.getXAxisLabel();
    yAxisLabel = api.getYAxisLabel();
    plotLabel = api.getPlotLabel();


    // show the window at center of the parent component
     this.setLocation(parent.getX()+parent.getWidth()/3,
                      parent.getY()+parent.getHeight()/2);

     //creating the parameters to change the size of Labels
     //creating list of supported font sizes
     ArrayList supportedFontSizes = new ArrayList();

     supportedFontSizes.add("8");
     supportedFontSizes.add("10");
     supportedFontSizes.add("12");
     supportedFontSizes.add("14");
     supportedFontSizes.add("16");
     supportedFontSizes.add("18");
     supportedFontSizes.add("20");
     supportedFontSizes.add("22");
     supportedFontSizes.add("24");


     //creating the font size parameters
     tickFontSizeParam = new StringParameter(tickFontSizeParamName,supportedFontSizes,(String)supportedFontSizes.get(1));
     axisLabelsFontSizeParam = new StringParameter(axislabelsFontSizeParamName,supportedFontSizes,(String)supportedFontSizes.get(2));
     plotLabelsFontSizeParam = new StringParameter(plotlabelsFontSizeParamName,supportedFontSizes,(String)supportedFontSizes.get(2));
     tickFontSizeParam.addParameterChangeListener(this);
     axisLabelsFontSizeParam.addParameterChangeListener(this);
     plotLabelsFontSizeParam.addParameterChangeListener(this);
     tickLabelWidth = Integer.parseInt((String)tickFontSizeParam.getValue());
     axisLabelWidth = Integer.parseInt((String)axisLabelsFontSizeParam.getValue());
     plotLabelWidth = Integer.parseInt((String)this.plotLabelsFontSizeParam.getValue());
     //creating the axis and plot label params
     xAxisLabelParam = new StringParameter(xAxisLabelParamName,xAxisLabel);
     yAxisLabelParam = new StringParameter(yAxisLabelParamName,yAxisLabel);
     plotLabelParam = new StringParameter(plotLabelParamName,plotLabel);

     xAxisLabelParam.addParameterChangeListener(this);
     yAxisLabelParam.addParameterChangeListener(this);
     plotLabelParam.addParameterChangeListener(this);

     //creating parameterlist and its corresponding parameter to hold the Axis and plot label parameter together.
     plotParamList = new ParameterList();
     plotParamList.addParameter(tickFontSizeParam);
     plotParamList.addParameter(axisLabelsFontSizeParam);
     plotParamList.addParameter(xAxisLabelParam);
     plotParamList.addParameter(yAxisLabelParam);
     plotParamList.addParameter(plotLabelParam);
     plotParamList.addParameter(plotLabelsFontSizeParam);

     plotParamEditor = new ParameterListEditor(plotParamList);
     plotParamEditor.setTitle("Plot Label Prefs Setting");

     //creating editors for these font size parameters
     setPlotColorAndLineType(curveCharacterstics);
  }

  private void jbInit() throws Exception {
    this.getContentPane().setLayout(borderLayout1);
    jPanel1.setLayout(gridBagLayout1);
    jLabel1.setFont(new java.awt.Font("Arial", 0, 18));
    jLabel1.setHorizontalAlignment(SwingConstants.CENTER);
    jLabel1.setHorizontalTextPosition(SwingConstants.CENTER);
    jLabel1.setText("Plot Settings");
    applyButton.setText("Apply");
    applyButton.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        applyButton_actionPerformed(e);
      }
    });
    cancelButton.setText("Cancel");
    cancelButton.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        cancelButton_actionPerformed(e);
      }
    });
    RevertButton.setText("Revert");
    RevertButton.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        RevertButton_actionPerformed(e);
      }
    });
    curveFeaturePanel.setLayout(gridBagLayout2);
    doneButton.setText("Done");
    doneButton.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        doneButton_actionPerformed(e);
      }
    });
    this.getContentPane().add(jPanel1, BorderLayout.CENTER);
    jPanel1.add(jLabel1,  new GridBagConstraints(0, 0, 4, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(5, 6, 0, 11), 0, 0));
    jPanel1.add(colorAndLineTypeSelectorPanel,  new GridBagConstraints(0, 1, 4, 1, 1.0, 1.0
            ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(0, 6, 0, 11), 0, 0));
    colorAndLineTypeSelectorPanel.getViewport().add(curveFeaturePanel, null);
    jPanel1.add(cancelButton,  new GridBagConstraints(3, 2, 1, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(0, 22, 2, 108), 0, 0));
    jPanel1.add(RevertButton,  new GridBagConstraints(2, 2, 1, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(0, 21, 2, 0), 0, 0));
    jPanel1.add(doneButton,  new GridBagConstraints(1, 2, 1, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(0, 22, 2, 0), 0, 0));
    jPanel1.add(applyButton,  new GridBagConstraints(0, 2, 1, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(0, 99, 2, 0), 0, 0));
    jPanel1.setSize(600,500);
    //colorAndLineTypeSelectorPanel.setSize(500,250);
    setSize(600,500);
  }


  /**
   * creates the control panel with plotting characterstics for each curve in list.
   * This function shows plotting characterstics (curve style, color, and its width)
   * for each curve in list ,so creates these gui components dynamically based on
   * number of functions in list.
   */
  public void setPlotColorAndLineType(ArrayList curveCharacterstics){
    int numCurves = curveCharacterstics.size();
    plottingFeatures = curveCharacterstics;
    defaultPlottingFeatures = new ArrayList();

    //creating the defaultPlotting features with original color scheme.
    for(int i=0;i<numCurves;++i){
      PlotCurveCharacterstics curvePlotPref = (PlotCurveCharacterstics)plottingFeatures.get(i);
      defaultPlottingFeatures.add(new PlotCurveCharacterstics(curvePlotPref.getCurveType(),
          curvePlotPref.getCurveColor(),curvePlotPref.getCurveWidth()));
    }


    datasetSelector = new JLabel[numCurves];
    colorChooserButton = new  JButton[numCurves];
    lineTypeSelector = new JComboBox[numCurves];
    lineWidthParameter = new DoubleParameter[numCurves];
    lineWidthParameterEditor = new ConstrainedDoubleParameterEditor[numCurves];
    DoubleConstraint sizeConstraint = new DoubleConstraint(0,20);
    for(int i=0;i<numCurves;++i){
      PlotCurveCharacterstics curvePlotPref = (PlotCurveCharacterstics)plottingFeatures.get(i);
      //creating the dataset Labl with the color in which they are shown in plots.
      datasetSelector[i] = new JLabel(curvePlotPref.getCurveName());
      datasetSelector[i].setForeground(curvePlotPref.getCurveColor());
      colorChooserButton[i] = new JButton(colorChooserString);
      colorChooserButton[i].addActionListener(this);
      lineTypeSelector[i] = new JComboBox();
      //adding choices to line type selector
      lineTypeSelector[i].addItem(SOLID_LINE);
      lineTypeSelector[i].addItem(DOTTED_LINE);
      lineTypeSelector[i].addItem(DASHED_LINE);
      lineTypeSelector[i].addItem(DOT_DASH_LINE);
      lineTypeSelector[i].addItem(X);
      lineTypeSelector[i].addItem(CROSS_SYMBOLS);
      lineTypeSelector[i].addItem(FILLED_CIRCLES);
      lineTypeSelector[i].addItem(CIRCLES);
      lineTypeSelector[i].addItem(FILLED_SQUARES);
      lineTypeSelector[i].addItem(SQUARES);
      lineTypeSelector[i].addItem(FILLED_TRIANGLES);
      lineTypeSelector[i].addItem(TRIANGLES);
      lineTypeSelector[i].addItem(FILLED_INV_TRIANGLES);
      lineTypeSelector[i].addItem(INV_TRIANGLES);
      lineTypeSelector[i].addItem(FILLED_DIAMONDS);
      lineTypeSelector[i].addItem(DIAMONDS);
      lineTypeSelector[i].addItem(LINE_AND_CIRCLES);
      lineTypeSelector[i].addItem(LINE_AND_TRIANGLES);
      lineTypeSelector[i].addItem(HISTOGRAM);
      //setting the selected plot type to be one currently selected.
      lineTypeSelector[i].setSelectedItem(curvePlotPref.getCurveType());
      lineTypeSelector[i].addActionListener(this);

      try{
        //creating double parameter for size of each curve.
        lineWidthParameter[i] = new DoubleParameter(lineWidthParamName+(i+1),sizeConstraint,
            new Double(curvePlotPref.getCurveWidth()));

        lineWidthParameterEditor[i] = new ConstrainedDoubleParameterEditor(lineWidthParameter[i]);
      }catch(Exception e){
        e.printStackTrace();
      }
    }

    curveFeaturePanel.removeAll();
    //adding color chooser button,plot style and size to GUI.
    for(int i=0;i<numCurves;++i){
      curveFeaturePanel.add(datasetSelector[i],new GridBagConstraints(0, i+1, 1, 1, 1.0, 1.0
      ,GridBagConstraints.WEST, GridBagConstraints.WEST, new Insets(4, 3, 5, 5), 0, 0));
      curveFeaturePanel.add(colorChooserButton[i],new GridBagConstraints(1, i+1, 1, 1, 1.0, 1.0
          ,GridBagConstraints.CENTER, GridBagConstraints.WEST, new Insets(4, 3, 5, 5), 0, 0));
      curveFeaturePanel.add(lineTypeSelector[i],new GridBagConstraints(2, i+1, 1, 1, 1.0, 1.0
          ,GridBagConstraints.CENTER, GridBagConstraints.WEST, new Insets(4, 3, 5, 5), 0, 0));
      curveFeaturePanel.add(lineWidthParameterEditor[i],new GridBagConstraints(3, i+1, 1, 1, 1.0, 1.0
          ,GridBagConstraints.CENTER, GridBagConstraints.WEST, new Insets(4, 3, 5, 5), 0, 0));
    }
    curveFeaturePanel.add(plotParamEditor,new GridBagConstraints(1, numCurves+1, 2, 1, 0.75, 1.0
      ,GridBagConstraints.WEST, GridBagConstraints.BOTH, new Insets(4, 3, 5, 5), 0, 0));
  }

  /**
   * If parameter is changed then Parameter change event is called on this class
   * @param event
   */
  public void parameterChange(ParameterChangeEvent event){
    //updating the size of the labels
    String paramName = event.getParameterName();
    if(paramName.equals(this.tickFontSizeParamName)){
      tickLabelWidth = Integer.parseInt((String)tickFontSizeParam.getValue());
      //tickFontSizeParam.setValue(""+tickLabelWidth);

    }
    else if(paramName.equals(this.axislabelsFontSizeParamName)){
    	axisLabelWidth = Integer.parseInt((String)axisLabelsFontSizeParam.getValue());
      //axisLabelsFontSizeParam.setValue(""+axisLabelWidth);
    } else if(paramName.equals(this.plotlabelsFontSizeParamName)) {
    	plotLabelWidth = Integer.parseInt((String)this.plotLabelsFontSizeParam.getValue());
    }
    else if(paramName.equals(this.xAxisLabelParamName))
      xAxisLabel = (String)this.xAxisLabelParam.getValue();
    else if(paramName.equals(this.yAxisLabelParamName))
      yAxisLabel = (String)this.yAxisLabelParam.getValue();
    else if(paramName.equals(this.plotLabelParamName))
      plotLabel = (String)this.plotLabelParam.getValue();

    plotParamEditor.refreshParamEditor();

  }

  /**
   * This is a common function if any action is performed on the color chooser button
   * and plot line type selector
   * It checks what is the source of the action and depending on the source how will it
   * response to it.
   * @param e
   */
  public void actionPerformed(ActionEvent e){
    int numCurves = plottingFeatures.size();
    //checking if the source of the action was the button
    if(e.getSource() instanceof JButton){
      Object button = e.getSource();
      //if the source of the event was color button
      for(int i=0;i<numCurves;++i){
        PlotCurveCharacterstics curvePlotPref = (PlotCurveCharacterstics)plottingFeatures.get(i);
        if(button.equals(colorChooserButton[i])){
          Color color = JColorChooser.showDialog(this,"Select Color",curvePlotPref.getCurveColor());
          //chnage the default color only if user has selected a new color , else leave it the way it is
          if(color !=null){
            curvePlotPref.setCurveColor(color);
            datasetSelector[i].setForeground(color);
          }
        }
      }
    }
    else if(e.getSource() instanceof JComboBox){
      Object comboBox = e.getSource();
      //if the source of the event was color button
      int itemIndex=0;
      for(int i=0;i<numCurves;++i){
        PlotCurveCharacterstics curvePlotPref = (PlotCurveCharacterstics)plottingFeatures.get(i);
        if(comboBox.equals(lineTypeSelector[i])){
          curvePlotPref.setCurveType((String)lineTypeSelector[i].getSelectedItem());
          itemIndex= i;
          break;
        }
      }
      //method to set the default value for line and shapes
      setStyleSizeBasedOnSelectedShape(itemIndex,(String)lineTypeSelector[itemIndex].getSelectedItem());
    }
  }


  /**
   * Set the default size value based on the selected Style. For line it is 1.0f
   * and for shapes it is 4.0f.
   * @param index : Curve index
   * @param selectedStyle
   */
  private void setStyleSizeBasedOnSelectedShape(int index,String selectedStyle){

    if(selectedStyle.equals(this.SOLID_LINE) || selectedStyle.equals(this.DASHED_LINE) ||
       selectedStyle.equals(this.DOTTED_LINE) || selectedStyle.equals(this.DOT_DASH_LINE)||
       selectedStyle.equals(HISTOGRAM))
      lineWidthParameterEditor[index].setValue(new Double(1.0));
    else if(selectedStyle.equals(this.LINE_AND_CIRCLES) || selectedStyle.equals(this.LINE_AND_TRIANGLES))
      lineWidthParameterEditor[index].setValue(new Double(1.0));
    else
     lineWidthParameterEditor[index].setValue(new Double(4.0));
    lineWidthParameterEditor[index].refreshParamEditor();
  }


  /**
   * Apply changes to the Plot and keeps the control panel for user to view the results
   * @param e
   */
  void applyButton_actionPerformed(ActionEvent e) {
    applyChangesToPlot();
  }

  private void applyChangesToPlot(){
    int numCurves = plottingFeatures.size();
    //getting the line width parameter
    for(int i=0;i<numCurves;++i)
      ((PlotCurveCharacterstics)plottingFeatures.get(i)).setCurveWidth(((Double)lineWidthParameterEditor[i].getParameter().getValue()).doubleValue());
    application.setXAxisLabel(xAxisLabel);
    application.setYAxisLabel(yAxisLabel);
    application.setPlotLabel(plotLabel);
    application.plotGraphUsingPlotPreferences();
  }

  /**
   * reverts the plots to original values and close the window
   * @param e
   */
  void cancelButton_actionPerformed(ActionEvent e) {
    revertPlotToOriginal();
    this.dispose();
  }

  /**
   * Restoring the original values for plotting features
   * @param e
   */
  void RevertButton_actionPerformed(ActionEvent e) {
    int flag =JOptionPane.showConfirmDialog(this,"Restore Original Values","Reverting changes",JOptionPane.OK_CANCEL_OPTION);
    if(flag == JOptionPane.OK_OPTION){
      revertPlotToOriginal();
    }
  }

  private void revertPlotToOriginal(){
    int numCurves = defaultPlottingFeatures.size();
    for(int i=0;i<numCurves;++i){
      PlotCurveCharacterstics curveCharacterstics = (PlotCurveCharacterstics)defaultPlottingFeatures.get(i);
      datasetSelector[i].setForeground(curveCharacterstics.getCurveColor());
      ((PlotCurveCharacterstics)plottingFeatures.get(i)).setCurveColor(curveCharacterstics.getCurveColor());
      //setting the selected plot type to be one currently selected.
      lineTypeSelector[i].setSelectedItem(curveCharacterstics.getCurveType());
      ((PlotCurveCharacterstics)plottingFeatures.get(i)).setCurveType(curveCharacterstics.getCurveType());
      lineWidthParameterEditor[i].setValue(new Double(curveCharacterstics.getCurveWidth()));
      lineWidthParameterEditor[i].refreshParamEditor();
      ((PlotCurveCharacterstics)plottingFeatures.get(i)).setCurveWidth(curveCharacterstics.getCurveWidth());
      curveFeaturePanel.repaint();
      curveFeaturePanel.validate();
      application.plotGraphUsingPlotPreferences();
    }
  }

  /**
   *
   * @returns axis label font size
   */
  public int getAxisLabelFontSize(){
    return  Integer.parseInt((String)axisLabelsFontSizeParam.getValue());
  }
  
  /**
  *Set axis label font size
  * @returns 
  */
 public void setAxisLabelFontSize(int fontSize){
     axisLabelsFontSizeParam.setValue(""+fontSize);
 }
  
  /**
  *
  * @returns axis label font size
  */
  public int getPlotLabelFontSize(){
	  return  Integer.parseInt((String)plotLabelsFontSizeParam.getValue());
  }
  
  /**
   * Set plot label font size
   * 
   * @param fontSize
   */
  public void setPlotLabelFontSize(int fontSize) {
	  plotLabelsFontSizeParam.setValue(""+fontSize);
  }

  /**
   *
   * @returns the tick label font size
   */
  public int getTickLabelFontSize(){
    return  Integer.parseInt((String)tickFontSizeParam.getValue());
  }
  
  /**
   * Set the tick label font size
   * 
   * @param fontSize
   */
  public void setTickLabelFontSize(int fontSize) {
	  this.tickFontSizeParam.setValue(""+fontSize);
  }

  /**
   * Apply all changes to Plot and closes the control window
   * @param e
   */
  void doneButton_actionPerformed(ActionEvent e) {
    applyChangesToPlot();
    this.dispose();
  }

  /**
   *
   * @returns the X Axis Label
   */
  public String getXAxisLabel(){
    if(xAxisLabel !=null)
      return xAxisLabel;
    return "";
  }

  /**
   *
   * @returns Y Axis Label
   */
  public String getYAxisLabel(){
    if(yAxisLabel !=null)
      return yAxisLabel;
    return "";
  }

  /**
   *
   * @returns plot Title
   */
   public String getPlotLabel(){
     if(plotLabel !=null)
      return plotLabel;
    return "";
   }

}
