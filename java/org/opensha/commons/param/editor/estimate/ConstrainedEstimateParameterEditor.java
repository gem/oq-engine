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

package org.opensha.commons.param.editor.estimate;

import java.awt.BorderLayout;
import java.awt.Container;
import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.text.DecimalFormat;
import java.util.ArrayList;

import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.UIManager;

import org.opensha.commons.data.estimate.DiscreteValueEstimate;
import org.opensha.commons.data.estimate.Estimate;
import org.opensha.commons.data.estimate.FractileListEstimate;
import org.opensha.commons.data.estimate.IntegerEstimate;
import org.opensha.commons.data.estimate.InvalidParamValException;
import org.opensha.commons.data.estimate.LogNormalEstimate;
import org.opensha.commons.data.estimate.MinMaxPrefEstimate;
import org.opensha.commons.data.estimate.NormalEstimate;
import org.opensha.commons.data.estimate.PDF_Estimate;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFunc;
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;
import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.param.ArbitrarilyDiscretizedFuncParameter;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.EvenlyDiscretizedFuncParameter;
import org.opensha.commons.param.Parameter;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ParameterEditor;
import org.opensha.commons.param.editor.ParameterListEditor;
import org.opensha.commons.param.estimate.EstimateConstraint;
import org.opensha.commons.param.estimate.EstimateParameter;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeFailEvent;
import org.opensha.commons.param.event.ParameterChangeFailListener;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.refFaultParamDb.gui.infotools.GUI_Utils;
import org.opensha.refFaultParamDb.gui.infotools.InfoLabel;
import org.opensha.sha.gui.infoTools.EstimateViewer;

/**
 * <p>Title: EstimateParameterEditor.java </p>
 * <p>Description: This is the Estimate Parameter Editor. All estimates listed
 * in the constraint of the EstimateParameter are listed as choices, and below
 * are shown the associated independent parameters than need to be filled in to
 * make the desired estimates.
 </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author Vipin Gupta, Nitin Gupta
 * @date July 19, 2005
 * @version 1.0
 */

public class ConstrainedEstimateParameterEditor  extends ParameterEditor
    implements ParameterChangeListener,
    ParameterChangeFailListener, ActionListener{

   private EstimateParameter estimateParam;

   /**
    * Paramter List for holding all parameters
    */
   private ParameterList parameterList;

   /**
    * ParameterListEditor for holding parameters
    */
   private ParameterListEditor editor;

    // title of Parameter List Editor
   public static final String ESTIMATE_TITLE = new String("Estimates");

   private StringParameter chooseEstimateParam;
   private final static String CHOOSE_ESTIMATE_PARAM_NAME = "Estimate Type";

   /**
    * Mean parameter for Normal distribution
    */
   private DoubleParameter meanParam;
   private final static String MEAN_PARAM_NAME_PREFIX="Mean ";
   private String meanParamName;
   /**
    * Std Dev parameter for normal/lognormal distribution
    */
   private DoubleParameter stdDevParam;
   private final static String STD_DEV_PARAM_NAME_PREFIX="Std Dev ";
   private String stdDevParamName;

   /**
    * Linear Median parameter for lognormal distribution
    */
   private DoubleParameter linearMedianParam;
   private final static String LINEAR_MEDIAN_PARAM_NAME_PREFIX="Linear Median ";
   private String linearMedianParamName;

   /**
    * Min/Max  values that can be set into Normal/LogNormal estimate
    * These are used for testing purposes. These  parameters may be removed
    * when we deploy this.
    */
   private DoubleParameter sigmaLowerTruncationParam;
   private final static String LOWER_SIGMA_PARAM_NAME="Lower Truncation (# of sigmas)";
   private DoubleParameter sigmaUpperTruncationParam ;
   private final static String UPPER_SIGMA_PARAM_NAME="Upper Truncation (# of sigmas)";
   private DoubleParameter absoluteLowerTruncationParam;
   private final static String ABOLUTE_LOWER_PARAM_NAME = "Absolute Lower Truncation";
   private DoubleParameter absoluteUpperTruncationParam;
   private final static String ABOLUTE_UPPER_PARAM_NAME = "Absolute Upper Truncation";

   /**
    * Truncation type parameter
    */
   private final static String TRUNCATION_TYPE_PARAM_NAME = "Truncation Type";
   private final static String TRUNCATION_NONE = "None";
   private final static String TRUNCATED_ABSOLUTE = "Truncated (absolute limits)";
   private final static String TRUNCATED_NUM_SIGMAS = "Truncated (number of sigmas)";
   private StringParameter truncationTypeParam;

   /**
    * Log Base param for log normal distribution
    */
   private StringParameter logBaseParam;
   private final static String LOG_BASE_PARAM_NAME="Log Base";
   private final static String LOG_BASE_10_NAME="10";
   private final static String NATURAL_LOG_NAME="E";

   // for X and Y vlaues for Discrete Value estimate and Min/Max/Preferred Estimate
   private ArbitrarilyDiscretizedFuncParameter arbitrarilyDiscFuncParam;
   private final static String XY_PARAM_NAME_SUFFIX = " Values/Probabilities";
   private String xyParamName;

   private EvenlyDiscretizedFuncParameter evenlyDiscFuncParam;
   private final static String PDF_PARAM_NAME_SUFFIX = "Evenly Discretized Values";
   private String pdfParamName;

   //private JButton setEstimateButton ;
   private JButton viewEstimateButton;

   /**
    * Min, Max, Preferred
    */
   private DoubleParameter minX_Param;
   private final static String MIN_X_PARAM_NAME_PREFIX="Min ";
   private String minXParamName;
   private DoubleParameter maxX_Param ;
   private final static String MAX_X_PARAM_NAME_PREFIX="Max ";
   private String maxXParamName;
   private DoubleParameter prefferedX_Param ;
   private final static String PREF_X_PARAM_NAME_PREFIX="Preferred ";
   private String preferredXParamName;
   private DoubleParameter minProbParam;
   private String minProbParamName;
   private DoubleParameter maxProbParam ;
   private String maxProbParamName;
   private DoubleParameter prefferedProbParam ;
   private String prefferedProbParamName;
   private ParameterListEditor xValsParamListEditor;
   private ParameterListEditor probValsParamListEditor;




   // title of Parameter List Editor
   public static final String X_TITLE_SUFFIX = new String(" Values");
   // title of Parameter List Editor
   public static final String PROB_TITLE = new String("Probability this value is correct");


   // size of the editor
   protected final static Dimension WIGET_PANEL_DIM = new Dimension( 140, 300 );

   /* this editor will be shown only as a button. On button click, a new window
    appears showing all the parameters */
   private JButton button;

   private JFrame frame;

   /* Whether to show this editor as a button.
      1. If this is set as true, a pop-up window appears on button click
      2. If this is set as false, button is not shown for pop-up window.
    */
   private boolean showEditorAsPanel = false;

   private EstimateConstraint estimateConstraint;
   private final static DecimalFormat decimalFormat = new DecimalFormat("0.###");



   private final static String MSG_VALUE_MISSING_SUFFIX = " value is missing ";

   public ConstrainedEstimateParameterEditor() {
   }

    public ConstrainedEstimateParameterEditor(ParameterAPI model) {
      this(model, false);
    }

   //constructor taking the Parameter as the input argument
   public ConstrainedEstimateParameterEditor(ParameterAPI model,
                                             boolean showEditorAsPanel){
     this.model = model;
     this.showEditorAsPanel = showEditorAsPanel;
     try {
       this.jbInit();
       setParameter(model);
     }catch(Exception e) {
       e.printStackTrace();
     }
   }

  public void setParameter(ParameterAPI param)  {
	 this.model = param; 
    String S = C + ": Constructor(): ";
    if ( D ) System.out.println( S + "Starting:" );
      // remove the previous editor
    //removeAll();
    estimateParam = (EstimateParameter) param;
    // make the params editor
    initParamListAndEditor();

    this.setLayout(GBL);

    Container container;
    if (!this.showEditorAsPanel) { // show editor as a button. In this case
                                   // parameters are shown in a pop up window on button click
      frame = new JFrame();
      frame.setTitle(this.estimateParam.getName());
      button = new JButton(this.estimateParam.getName());
      button.addActionListener(this);
      this.add(this.button,new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0
        , GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ) );
      container = frame.getContentPane();
      container.setLayout(GBL);
    } else { // add all the parameters in the current panel
      container = this;
    }

    /*container.add(addParamatersToPanel(), new GridBagConstraints( 0, 0, 1, 1, 1.0, 0.0
                                                 , GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ) );
     */
    container.add(this.editor,new GridBagConstraints( 0, 0, 2, 1, 1.0, 1.0
        ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ) );
    container.add(xValsParamListEditor,new GridBagConstraints( 0, 1, 1, 1, 1.0, 1.0
        , GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 5, 5, 5, 5 ), 0, 0 ) );
    container.add(probValsParamListEditor,new GridBagConstraints( 1, 1, 1, 1, 1.0, 1.0
        , GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 5, 5, 5, 5 ), 0, 0 ) );
    container.add(viewEstimateButton,new GridBagConstraints( 0, 2, 1, 1, 1.0, 0.0
        , GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets( 5, 5, 5, 5 ), 0, 0 ) );
    //container.add(this.estimateInfo,new GridBagConstraints( 0, 3, 2, 1, 1.0, 0.0
    //    , GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 5, 5, 5, 5 ), 0, 0 ) );
    setEstimateParams((String)chooseEstimateParam.getValue());
   
    
    if(model!=null) {
      Estimate estimate = (Estimate) model.getValue();
      if (estimate != null)
        setEstimateValue(estimate);
    }
    editor.refreshParamEditor();
    this.updateUI();
    // All done
    if ( D ) System.out.println( S + "Ending:" );
  }

  private void setEstimateValue(Estimate estimate) {
    if(estimate instanceof NormalEstimate)
      setNormalEstimateVals((NormalEstimate)estimate);
    else if (estimate instanceof LogNormalEstimate)
      setLogNormalEstimateVals((LogNormalEstimate)estimate);
    else if (estimate instanceof FractileListEstimate)
       setFractileListVals((FractileListEstimate)estimate);
    else if(estimate instanceof MinMaxPrefEstimate)
      setMinMaxPrefVals((MinMaxPrefEstimate)estimate);
    else if (estimate instanceof PDF_Estimate)
      setPDF_EstimateVals((PDF_Estimate)estimate);
    else if (estimate instanceof DiscreteValueEstimate)
      setDiscreteEstimateVals((DiscreteValueEstimate)estimate);
    else if (estimate instanceof IntegerEstimate)
      setIntegerEstimateVals((IntegerEstimate)estimate);

  }

  // set the value in normal estimate
  private void setNormalEstimateVals(NormalEstimate normalEstimate) {
    this.chooseEstimateParam.setValue(NormalEstimate.NAME);
    this.meanParam.setValue(normalEstimate.getMean());
    this.stdDevParam.setValue(normalEstimate.getStdDev());
    this.absoluteLowerTruncationParam.setValue(normalEstimate.getMin());
    this.absoluteUpperTruncationParam.setValue(normalEstimate.getMax());
    Double estimateConstraintMin = this.estimateConstraint.getMin();
    Double estimateConstraintMax = this.estimateConstraint.getMax();
    // set truncation type parameter
    if(estimateConstraintMin!=null && estimateConstraintMax!=null &&
       (normalEstimate.getMin()!=estimateConstraintMin.doubleValue() ||
        normalEstimate.getMax()!=estimateConstraintMax.doubleValue())) {
      this.truncationTypeParam.setValue(TRUNCATED_ABSOLUTE);
    }

    this.sigmaLowerTruncationParam.setValue(normalEstimate.getMinSigma());
    this.sigmaUpperTruncationParam.setValue(normalEstimate.getMaxSigma());
  }


  // set the parameter value in log normal estimate
  private void setLogNormalEstimateVals(LogNormalEstimate logNormalEstimate) {
    this.chooseEstimateParam.setValue(LogNormalEstimate.NAME);
    this.linearMedianParam.setValue(logNormalEstimate.getLinearMedian());
    this.stdDevParam.setValue(logNormalEstimate.getStdDev());
    this.absoluteLowerTruncationParam.setValue(logNormalEstimate.getMin());
    this.absoluteUpperTruncationParam.setValue(logNormalEstimate.getMax());
    Double estimateConstraintMin = this.estimateConstraint.getMin();
    Double estimateConstraintMax = this.estimateConstraint.getMax();
    // set truncation type parameter
    if(estimateConstraintMin!=null && estimateConstraintMax!=null &&
       (logNormalEstimate.getMin()!=estimateConstraintMin.doubleValue() ||
        logNormalEstimate.getMax()!=estimateConstraintMax.doubleValue())) {
      this.truncationTypeParam.setValue(TRUNCATED_ABSOLUTE);
    }

    this.sigmaLowerTruncationParam.setValue(logNormalEstimate.getMinSigma());
    this.sigmaUpperTruncationParam.setValue(logNormalEstimate.getMaxSigma());
    if(logNormalEstimate.getIsBase10())
      this.logBaseParam.setValue(LOG_BASE_10_NAME);
    else logBaseParam.setValue(NATURAL_LOG_NAME);
  }

  // set the estimate in fractile list estimate
  private void setFractileListVals(FractileListEstimate fractileListEstimate) {
    this.chooseEstimateParam.setValue(FractileListEstimate.NAME);
    DiscretizedFunc func = fractileListEstimate.getValues();
    this.minX_Param.setValue(func.getX(0));
    this.prefferedX_Param.setValue(func.getX(1));
    this.maxX_Param.setValue(func.getX(2));
    this.minProbParam.setValue(func.getY(0));
    this.prefferedProbParam.setValue(func.getY(1));
    this.maxProbParam.setValue(func.getY(2));
    xValsParamListEditor.refreshParamEditor();
    probValsParamListEditor.refreshParamEditor();

  }

  // set the estimate in min/max/pref estimate
  private void setMinMaxPrefVals(MinMaxPrefEstimate minMaxPrefEstimate) {
    this.chooseEstimateParam.setValue(MinMaxPrefEstimate.NAME);
    // min X
    double minX = minMaxPrefEstimate.getMinimum();
    if(!Double.isNaN(minX))  this.minX_Param.setValue(new Double(decimalFormat.format(minX)));
    // pref X
    double prefX = minMaxPrefEstimate.getPreferred();
    if(!Double.isNaN(prefX)) prefferedX_Param.setValue(new Double(decimalFormat.format(prefX)));
    //max X
    double maxX = minMaxPrefEstimate.getMaximum();
    if(!Double.isNaN(maxX)) maxX_Param.setValue(new Double(decimalFormat.format(maxX)));
    //min Prob
    double minProb = minMaxPrefEstimate.getMinimumProb();
    if(!Double.isNaN(minProb)) minProbParam.setValue(new Double(decimalFormat.format(minProb)));
    // pref prob
    double prefProb = minMaxPrefEstimate.getPreferredProb();
    if(!Double.isNaN(prefProb)) this.prefferedProbParam.setValue(new Double(decimalFormat.format(prefProb)));
    // max prob
    double maxProb = minMaxPrefEstimate.getMaximumProb();
    if(!Double.isNaN(maxProb)) this.maxProbParam.setValue(new Double(decimalFormat.format(maxProb)));

    xValsParamListEditor.refreshParamEditor();
    probValsParamListEditor.refreshParamEditor();

  }

  // set the values in discrete value estimate
  private void setDiscreteEstimateVals(DiscreteValueEstimate discreteValEst) {
	this.chooseEstimateParam.setValue(DiscreteValueEstimate.NAME);
    this.arbitrarilyDiscFuncParam.setValue(new ArbitrarilyDiscretizedFunc(discreteValEst.getValues()));
  }

  // set the values in integer estimate
  private void setIntegerEstimateVals(IntegerEstimate integerEst) {
	this.chooseEstimateParam.setValue(IntegerEstimate.NAME);
    this.arbitrarilyDiscFuncParam.setValue(new ArbitrarilyDiscretizedFunc(integerEst.getValues()));
  }

  // set the values in pdf estimate
  private void setPDF_EstimateVals(PDF_Estimate pdfEst) {
    this.evenlyDiscFuncParam.setValue((EvenlyDiscretizedFunc) pdfEst.getValues());
  }

  protected void jbInit() {
    this.setMinimumSize(new Dimension(0, 0));
    this.setLayout(GBL);
  }

  /**
   * Called when the parameter has changed independently from
   * the editor, such as with the ParameterWarningListener.
   * This function needs to be called to to update
   * the GUI component ( text field, picklist, etc. ) with
   * the new parameter value.
   */
  public void refreshParamEditor() {
    if(model!=null) {
      Estimate estimate = (Estimate)this.model.getValue();
      if (estimate != null)
        setEstimateValue(estimate);
    }
    editor.refreshParamEditor();
    this.updateUI();
    if(frame!=null)
      frame.repaint();
  }

  /**
   * Initialize the parameters and editors
   */
  protected void initParamListAndEditor()  {

    // Starting
    String S = C + ": initControlsParamListAndEditor(): ";
    if ( D ) System.out.println( S + "Starting:" );
    this.meanParamName = MEAN_PARAM_NAME_PREFIX;
    meanParam = new DoubleParameter(meanParamName);
    this.linearMedianParamName = LINEAR_MEDIAN_PARAM_NAME_PREFIX;
    linearMedianParam = new DoubleParameter(linearMedianParamName);
    this.stdDevParamName = STD_DEV_PARAM_NAME_PREFIX;
    stdDevParam = new DoubleParameter(stdDevParamName);

    ArbitrarilyDiscretizedFunc arbitraryDiscretizedFunc = new ArbitrarilyDiscretizedFunc();
    arbitraryDiscretizedFunc.setXAxisName("Values");
    arbitraryDiscretizedFunc.setYAxisName("Probabilities");
    this.xyParamName = XY_PARAM_NAME_SUFFIX;
    arbitrarilyDiscFuncParam = new ArbitrarilyDiscretizedFuncParameter(xyParamName, arbitraryDiscretizedFunc);

    EvenlyDiscretizedFunc evenlyDiscretizedFunc = new EvenlyDiscretizedFunc(1.0,4.0,7);
    evenlyDiscretizedFunc.setXAxisName("Value");
    evenlyDiscretizedFunc.setYAxisName("Probability");
    this.pdfParamName = PDF_PARAM_NAME_SUFFIX;
    evenlyDiscFuncParam = new EvenlyDiscretizedFuncParameter(pdfParamName, evenlyDiscretizedFunc);
    // list of available estimates
    estimateConstraint = (EstimateConstraint)estimateParam.getConstraint();
    ArrayList allowedEstimatesList = estimateConstraint.getAllowedEstimateList();
    chooseEstimateParam = new StringParameter(CHOOSE_ESTIMATE_PARAM_NAME,
                                              allowedEstimatesList,
                                              (String) allowedEstimatesList.get(0));

    chooseEstimateParam.addParameterChangeListener(this);

    // log choices for log normal distribution
    ArrayList logBases = new ArrayList();
    logBases.add(NATURAL_LOG_NAME);
    logBases.add(LOG_BASE_10_NAME);
    logBaseParam = new StringParameter(LOG_BASE_PARAM_NAME,logBases,(String)logBases.get(0));

    // put all the parameters in the parameter list
    parameterList = new ParameterList();
    parameterList.addParameter(chooseEstimateParam);
    parameterList.addParameter(this.meanParam);
    parameterList.addParameter(this.stdDevParam);
    parameterList.addParameter(this.linearMedianParam);
    parameterList.addParameter(this.logBaseParam);
    parameterList.addParameter(this.arbitrarilyDiscFuncParam);
    parameterList.addParameter(evenlyDiscFuncParam);

   // whether to show min/max truncation params
   addMinMaxTruncationParams(estimateConstraint);

    this.editor = new ParameterListEditor(parameterList);

   // show the units and estimate param name as the editor title
   String units = estimateParam.getUnits();
   String title;
   if(units!=null && !units.equalsIgnoreCase("")) title = estimateParam.getName()+" ("+units+")";
   else title = estimateParam.getName();
   editor.setTitle(title);

   // parameters for min/max/preferred user choice
  this.minXParamName = MIN_X_PARAM_NAME_PREFIX;
  minX_Param = new DoubleParameter(minXParamName);
  this.maxXParamName = MAX_X_PARAM_NAME_PREFIX;
  maxX_Param = new DoubleParameter(maxXParamName);
  this.preferredXParamName = PREF_X_PARAM_NAME_PREFIX;
  prefferedX_Param = new DoubleParameter(preferredXParamName);

  ParameterList xValsParamList = new ParameterList();
  xValsParamList.addParameter(minX_Param);
  xValsParamList.addParameter(prefferedX_Param);
  xValsParamList.addParameter(maxX_Param);
  xValsParamListEditor = new ParameterListEditor(xValsParamList);
  xValsParamListEditor.setTitle(X_TITLE_SUFFIX);

  this.minProbParamName = "Prob (� Min)";
  minProbParam = new DoubleParameter(minProbParamName,0,1);
  this.maxProbParamName = "Prob (� Max)";
  maxProbParam = new DoubleParameter(maxProbParamName,0,1);
  this.prefferedProbParamName = "Prob (� Preferred)";
  prefferedProbParam = new DoubleParameter(prefferedProbParamName,0,1);
  ParameterList probParamList = new ParameterList();
  probParamList.addParameter(minProbParam);
  probParamList.addParameter(prefferedProbParam);
  probParamList.addParameter(maxProbParam);
  probValsParamListEditor = new ParameterListEditor(probParamList);
  probValsParamListEditor.setTitle("Probability � Values");

   //setEstimateButton = new JButton("Set Estimate");
   viewEstimateButton = new JButton("Plot & Set Estimate");
   //setEstimateButton.addActionListener(this);
   viewEstimateButton.addActionListener(this);

   //double constraintMin = estimateConstraint.getMin().doubleValue();
   //double constraintMax = estimateConstraint.getMax().doubleValue();
   //String constraintMinText = this.MIN_CONSTRAINT_LABEL+constraintMin;
   //String constraintMaxText = this.MAX_CONSTRAINT_LABEL+constraintMax;
   //minConstraintLabel= new JLabel(this.MIN_CONSTRAINT_LABEL+constraintMin);
   //maxConstraintLabel= new JLabel(this.MAX_CONSTRAINT_LABEL+constraintMax);
   //editor.setToolTipText(minConstraintLabel.getText()+","+maxConstraintLabel.getText());
   //editor.setToolTipText(this.estimateParam.getInfo()+"::"+constraintMinText+","+constraintMaxText);
 }

 /**
  * Add the parameters  so that user can enter min/max truncation values
  * @param estimateConstraint
  * @throws ParameterException
  * @throws ConstraintException
  */
  private void addMinMaxTruncationParams(EstimateConstraint estimateConstraint) throws
      ParameterException, ConstraintException {
    /**
     * Min/Max  values that can be set into Normal/LogNormal estimate
     * These are used for testing purposes. These  parameters may be removed
     * when we deploy this.
     */
    ArrayList truncationTypeList = new ArrayList();
    truncationTypeList.add(TRUNCATION_NONE);
    truncationTypeList.add(TRUNCATED_ABSOLUTE);
    truncationTypeList.add(TRUNCATED_NUM_SIGMAS);

    this.truncationTypeParam= new StringParameter(TRUNCATION_TYPE_PARAM_NAME,
        truncationTypeList, (String)truncationTypeList.get(0));
    truncationTypeParam.addParameterChangeListener(this);

    // left and right sigma levels
    this.sigmaLowerTruncationParam = new DoubleParameter(LOWER_SIGMA_PARAM_NAME);
    this.sigmaUpperTruncationParam = new DoubleParameter(UPPER_SIGMA_PARAM_NAME);

    // left and right absolute truncation point
    this.absoluteLowerTruncationParam = new DoubleParameter(ABOLUTE_LOWER_PARAM_NAME,
        estimateConstraint.getMin());
    this.absoluteUpperTruncationParam = new DoubleParameter(ABOLUTE_UPPER_PARAM_NAME,
                                           estimateConstraint.getMax());

    parameterList.addParameter(truncationTypeParam);
    parameterList.addParameter(sigmaLowerTruncationParam);
    parameterList.addParameter(sigmaUpperTruncationParam);
    parameterList.addParameter(absoluteLowerTruncationParam);
    parameterList.addParameter(absoluteUpperTruncationParam);
  }


  public void parameterChangeFailed(ParameterChangeFailEvent event) {
    throw new RuntimeException("Unsupported method");
  }


  /**
   * Make the parameters visible/invisible based on selected estimate
   * @param event
   */
  public void parameterChange(ParameterChangeEvent event) {
    String paramName = event.getParameterName();
    // based on user selection of estimates, make the parameters visible/invisible
    if(paramName.equalsIgnoreCase(CHOOSE_ESTIMATE_PARAM_NAME)) {
      setEstimateParams( (String) chooseEstimateParam.getValue());
      editor.refreshParamEditor();
      this.updateUI();
    } else if(paramName.equalsIgnoreCase(TRUNCATION_TYPE_PARAM_NAME)) {
      this.setTruncationParamsVisibility();
    }
  }



  // make the params visible/invisible based on selected estimate type
  private void setEstimateParams(String estimateName) {

    // For NORMAL estimate
    if(estimateName.equalsIgnoreCase(NormalEstimate.NAME)) {
      setParamsForNormalEstimate();
    }
    // for LOGNORMAL Estimate
    else if(estimateName.equalsIgnoreCase(LogNormalEstimate.NAME)) {
      setParamsForLogNormalEstimate();
    }
    // for Integer Estimate and DiscretValueEstimate
    else if(estimateName.equalsIgnoreCase(IntegerEstimate.NAME) ||
            estimateName.equalsIgnoreCase(DiscreteValueEstimate.NAME))
      setParamsForXY_Estimate();
    // for Fractile List Estimate
    else if(estimateName.equalsIgnoreCase(FractileListEstimate.NAME))
      setParamsForFractileListEstimate();
    else if(estimateName.equalsIgnoreCase(MinMaxPrefEstimate.NAME))
      setParamsForMinMaxPrefEstimate();
    // For PDF Estimate
    else if(estimateName.equalsIgnoreCase(PDF_Estimate.NAME))
      setParamsForPDF_Estimate();

  }

  /**
   * make the parameters vfisible/invisible for Min/Max/Pref estimate
   */
  private void setParamsForMinMaxPrefEstimate() {
	  editor.setParameterVisible(CHOOSE_ESTIMATE_PARAM_NAME, true);
	  editor.setParameterVisible(meanParamName, false);
	  editor.setParameterVisible(stdDevParamName, false);
	  editor.setParameterVisible(TRUNCATION_TYPE_PARAM_NAME, false);
	  editor.setParameterVisible(linearMedianParamName, false);
	  editor.setParameterVisible(LOG_BASE_PARAM_NAME, false);
	  editor.setParameterVisible(this.pdfParamName, false);
	  editor.setParameterVisible(this.xyParamName, false);
	  setTruncationParamsVisibility();
	  xValsParamListEditor.setVisible(true);
	  probValsParamListEditor.setVisible(true);
	  viewEstimateButton.setVisible(false);
  }

  /**
   * make the parameters visible/invisible for FractileListEstimate estimate
   */
  private void setParamsForFractileListEstimate() {
	  setParamsForXY_Estimate();
  }

  /**
   * Set the params visible/invisible for normal estimate
   */
  private void setParamsForNormalEstimate() {
   editor.setParameterVisible(CHOOSE_ESTIMATE_PARAM_NAME, true);
   editor.setParameterVisible(meanParamName, true);
   editor.setParameterVisible(stdDevParamName, true);
   editor.setParameterVisible(TRUNCATION_TYPE_PARAM_NAME, true);
   editor.setParameterVisible(linearMedianParamName, false);
   editor.setParameterVisible(LOG_BASE_PARAM_NAME, false);
   editor.setParameterVisible(pdfParamName, false);
   editor.setParameterVisible(xyParamName, false);
   setTruncationParamsVisibility();
   xValsParamListEditor.setVisible(false);
   probValsParamListEditor.setVisible(false);
   viewEstimateButton.setVisible(true);
  }

  /**
   * Visible/Invisible the params for normal estimate
   */
  private void setTruncationParamsVisibility() {
    String truncationType = (String)this.truncationTypeParam.getValue();
    String chosenEstimateName = (String)chooseEstimateParam.getValue();
    editor.setParameterVisible(this.sigmaLowerTruncationParam.getName(), false);
    editor.setParameterVisible(this.sigmaUpperTruncationParam.getName(), false);
    editor.setParameterVisible(this.absoluteLowerTruncationParam.getName(), false);
    editor.setParameterVisible(this.absoluteUpperTruncationParam.getName(), false);
    // see if selectec estimate is normal/lognormal
    if(chosenEstimateName.equalsIgnoreCase(NormalEstimate.NAME) ||
       chosenEstimateName.equalsIgnoreCase(LogNormalEstimate.NAME)) {
      // if absolue truncation parameters need to be visible
      if(truncationType.equalsIgnoreCase(TRUNCATED_ABSOLUTE)) {
         editor.setParameterVisible(this.absoluteLowerTruncationParam.getName(), true);
         editor.setParameterVisible(this.absoluteUpperTruncationParam.getName(), true);
      } else if(truncationType.equalsIgnoreCase(TRUNCATED_NUM_SIGMAS)) {
        editor.setParameterVisible(this.sigmaLowerTruncationParam.getName(), true);
        editor.setParameterVisible(this.sigmaUpperTruncationParam.getName(), true);
      }
    }


  }


  /**
   * Set the params visible for lognormal estimate
   */
  private void setParamsForLogNormalEstimate() {
    editor.setParameterVisible(CHOOSE_ESTIMATE_PARAM_NAME, true);
    editor.setParameterVisible(meanParamName, false);
    editor.setParameterVisible(stdDevParamName, true);
    editor.setParameterVisible(linearMedianParamName, true);
    editor.setParameterVisible(LOG_BASE_PARAM_NAME, true);
    editor.setParameterVisible(TRUNCATION_TYPE_PARAM_NAME, true);
    editor.setParameterVisible(pdfParamName, false);
    editor.setParameterVisible(xyParamName, false);
    setTruncationParamsVisibility();
    xValsParamListEditor.setVisible(false);
    probValsParamListEditor.setVisible(false);
    viewEstimateButton.setVisible(true);
  }

  /**
  * Set the params visible for PDF  estimate
  */
 private void setParamsForPDF_Estimate() {
   editor.setParameterVisible(CHOOSE_ESTIMATE_PARAM_NAME, true);
   editor.setParameterVisible(meanParamName, false);
   editor.setParameterVisible(stdDevParamName, false);
   editor.setParameterVisible(linearMedianParamName, false);
   editor.setParameterVisible(TRUNCATION_TYPE_PARAM_NAME, false);
   editor.setParameterVisible(LOG_BASE_PARAM_NAME, false);
   editor.setParameterVisible(pdfParamName, true);
   editor.setParameterVisible(xyParamName, false);
   setTruncationParamsVisibility();
   xValsParamListEditor.setVisible(false);
   probValsParamListEditor.setVisible(false);
   viewEstimateButton.setVisible(true);
 }

 /**
  * It enables/disables the editor according to whether user is allowed to
  * fill in the values.
  */
 public void setEnabled(boolean isEnabled) {
   this.editor.setEnabled(isEnabled);
   this.xValsParamListEditor.setEnabled(isEnabled);
   this.probValsParamListEditor.setEnabled(isEnabled);

 }


 /**
  * Set the params visible for DiscreteValue and Integer  estimate
  */
 private void setParamsForXY_Estimate() {
   editor.setParameterVisible(CHOOSE_ESTIMATE_PARAM_NAME, true);
   editor.setParameterVisible(meanParamName, false);
   editor.setParameterVisible(stdDevParamName, false);
   editor.setParameterVisible(TRUNCATION_TYPE_PARAM_NAME, false);
   editor.setParameterVisible(linearMedianParamName, false);
   editor.setParameterVisible(LOG_BASE_PARAM_NAME, false);
   editor.setParameterVisible(pdfParamName, false);
   editor.setParameterVisible(xyParamName, true);
   setTruncationParamsVisibility();
   xValsParamListEditor.setVisible(false);
   probValsParamListEditor.setVisible(false);
   viewEstimateButton.setVisible(true);
 }

 public void actionPerformed(ActionEvent e) {
   if  (e.getSource()==viewEstimateButton) {
     try {
       setEstimateInParameter();
       viewEstimate();
     }catch(Exception ex) {
       JOptionPane.showMessageDialog(this, estimateParam+getName()+"\n"+ex.getMessage());
     }
   } else if (e.getSource()==this.button) {
     frame.pack();
     this.frame.setVisible(true);
   }
 }

 /**
  * Open a Jfreechart window to view the estimate
  */
 private void viewEstimate() {
   Estimate estimate = (Estimate)this.estimateParam.getValue();
   if(estimate!=null) {
     EstimateViewer estimateViewer = new EstimateViewer(estimate);
   }
 }


 /**
  * Set the estimate value inside the estimateParameter
  */
 public void setEstimateInParameter() {
   Estimate estimate = null;
   String estimateName=(String)this.chooseEstimateParam.getValue();
   try {
	   if (estimateName.equalsIgnoreCase(NormalEstimate.NAME))
		   estimate = setNormalEstimate();
	   else if (estimateName.equalsIgnoreCase(LogNormalEstimate.NAME))
		   estimate = setLogNormalEstimate();
	   else if (estimateName.equalsIgnoreCase(MinMaxPrefEstimate.NAME))
		   estimate = setMinMaxPrefEstimate();
	   else if (estimateName.equalsIgnoreCase(FractileListEstimate.NAME))
		   estimate = setFractileListEstimate();
	   else if (estimateName.equalsIgnoreCase(IntegerEstimate.NAME))
		   estimate = setIntegerEstimate();
	   else if (estimateName.equalsIgnoreCase(DiscreteValueEstimate.NAME))
		   estimate = setDiscreteValueEstimate();
	   else if (estimateName.equalsIgnoreCase(PDF_Estimate.NAME))
		   estimate = setPDF_Estimate();

	   estimate.setUnits(estimateParam.getUnits());
	   this.estimateParam.setValue(estimate);
   }catch(Exception e) {
	   throw new RuntimeException(this.estimateParam.getName()+"\n"+e.getMessage());
   }
 }

 /**
  * Set the estimate paramter value to be normal estimate
  */
 private Estimate setNormalEstimate() {
   // first check that user typed in the mean value
   Double meanParamVal = (Double)meanParam.getValue();
   if(meanParamVal==null)
     throw new RuntimeException(meanParam.getName()+MSG_VALUE_MISSING_SUFFIX);
   double mean = meanParamVal.doubleValue();
   // check that usr entered the standard deviation value
   Double stdDevVal = (Double)stdDevParam.getValue();
   if(stdDevVal==null)
      throw new RuntimeException(stdDevParam.getName()+MSG_VALUE_MISSING_SUFFIX);
   double stdDev = stdDevVal.doubleValue();
   // create Normal(Gaussian) estimate
   NormalEstimate estimate = new NormalEstimate(mean, stdDev);
   String truncationType = (String)this.truncationTypeParam.getValue();
   if(truncationType.equalsIgnoreCase(TRUNCATED_NUM_SIGMAS)) {
     Double lowerSigma =  (Double)this.sigmaLowerTruncationParam.getValue();
     // check that lower sigma value is present
     if(lowerSigma==null)
       throw new RuntimeException(sigmaLowerTruncationParam.getName()+MSG_VALUE_MISSING_SUFFIX);
     // check that upper sigma value is present
     Double upperSigma = (Double)this.sigmaUpperTruncationParam.getValue();
     if(upperSigma==null)
       throw new RuntimeException(this.sigmaUpperTruncationParam.getValue()+MSG_VALUE_MISSING_SUFFIX);
     estimate.setMinMaxSigmas(lowerSigma.doubleValue(), upperSigma.doubleValue());
   } else if(truncationType.equalsIgnoreCase(TRUNCATED_ABSOLUTE)) {
     Double absoluteMin =  (Double)this.absoluteLowerTruncationParam.getValue();
     // check that lower truncation value is present
     if(absoluteMin==null)
       throw new RuntimeException(absoluteLowerTruncationParam.getName()+MSG_VALUE_MISSING_SUFFIX);
     // check that upper truncation value is present
     Double absoluteMax = (Double)this.absoluteUpperTruncationParam.getValue();
     if(absoluteMax==null)
       throw new RuntimeException(this.absoluteUpperTruncationParam.getValue()+MSG_VALUE_MISSING_SUFFIX);
     estimate.setMinMax(absoluteMin.doubleValue(), absoluteMax.doubleValue());
   }
   return estimate;
 }




 /**
  * Set the estimate paramter value to be lognormal estimate
  */
 private Estimate setLogNormalEstimate() {
   // check that user entered linear median value
   Double linearMedianVal = (Double)linearMedianParam.getValue();
   if(linearMedianVal==null)
     throw new RuntimeException(linearMedianParam.getName()+MSG_VALUE_MISSING_SUFFIX);
   double linearMedian = linearMedianVal.doubleValue();
   // check that user entered std dev value
   Double stdDevVal = (Double)stdDevParam.getValue();
   if(stdDevVal==null)
     throw new RuntimeException(stdDevParam.getName()+MSG_VALUE_MISSING_SUFFIX);
   double stdDev =stdDevVal.doubleValue();
   // create instance of log normal estimate
   LogNormalEstimate estimate = new LogNormalEstimate(linearMedian, stdDev);
   if(this.logBaseParam.getValue().equals(LOG_BASE_10_NAME))
     estimate.setIsBase10(true);
   else   estimate.setIsBase10(false);

     // set truncation
   String truncationType = (String)this.truncationTypeParam.getValue();
   if(truncationType.equalsIgnoreCase(TRUNCATED_NUM_SIGMAS)) {
     Double lowerSigma =  (Double)this.sigmaLowerTruncationParam.getValue();
     // check that lower sigma value is present
     if(lowerSigma==null)
       throw new RuntimeException(sigmaLowerTruncationParam.getName()+MSG_VALUE_MISSING_SUFFIX);
     // check that upper sigma value is present
     Double upperSigma = (Double)this.sigmaUpperTruncationParam.getValue();
     if(upperSigma==null)
       throw new RuntimeException(this.sigmaUpperTruncationParam.getValue()+MSG_VALUE_MISSING_SUFFIX);
     estimate.setMinMaxSigmas(lowerSigma.doubleValue(), upperSigma.doubleValue());
   } else {
     Double absoluteMin =  (Double)this.absoluteLowerTruncationParam.getValue();
     // check that lower truncation value is present
     if(absoluteMin==null)
       throw new RuntimeException(absoluteLowerTruncationParam.getName()+MSG_VALUE_MISSING_SUFFIX);
     // check that upper truncation value is present
     Double absoluteMax = (Double)this.absoluteUpperTruncationParam.getValue();
     if(absoluteMax==null)
       throw new RuntimeException(this.absoluteUpperTruncationParam.getValue()+MSG_VALUE_MISSING_SUFFIX);
     estimate.setMinMax(absoluteMin.doubleValue(), absoluteMax.doubleValue());
   }


   return estimate;
 }




 /**
  * Set the estimate paramter value to be discrete vlaue estimate
  */
 private Estimate setDiscreteValueEstimate() {
   ArbitrarilyDiscretizedFunc val = (ArbitrarilyDiscretizedFunc)this.arbitrarilyDiscFuncParam.getValue();
   if(val.getNum()==0) throw new RuntimeException(arbitrarilyDiscFuncParam.getName()+
         MSG_VALUE_MISSING_SUFFIX);
   try {
     DiscreteValueEstimate estimate = new DiscreteValueEstimate(val, true);
     return estimate;
   }catch(InvalidParamValException e) {
     throw new RuntimeException(this.model.getName()+":"+e.getMessage());
   }
 }




 /**
  * Set the estimate paramter value to be integer estimate
  */
 private Estimate setIntegerEstimate() {
   ArbitrarilyDiscretizedFunc val = (ArbitrarilyDiscretizedFunc)this.arbitrarilyDiscFuncParam.getValue();
   if(val.getNum()==0)
      throw new RuntimeException(arbitrarilyDiscFuncParam.getName()+MSG_VALUE_MISSING_SUFFIX);
   try {
     IntegerEstimate estimate = new IntegerEstimate(val, true);
     return estimate;
   }catch(InvalidParamValException e) {
     throw new RuntimeException(this.model.getName()+":"+e.getMessage());
   }

 }

 /**
  * Set the estimate paramter value to be Pdf estimate
  */
 private Estimate setPDF_Estimate() {
   try {
     PDF_Estimate estimate = new PDF_Estimate( (EvenlyDiscretizedFunc)this.
                                              evenlyDiscFuncParam.getValue(), true);
     return estimate;
   }catch(InvalidParamValException e) {
     throw new RuntimeException(this.model.getName()+":"+e.getMessage());
   }

 }


 private Estimate setMinMaxPrefEstimate() {
   double minX, maxX, prefX, minProb, maxProb, prefProb;
   minX = getValueForParameter(minX_Param);
   maxX = getValueForParameter(maxX_Param);
   prefX = getValueForParameter(prefferedX_Param);
   // check that user typed in atleast one of minX, maxX or prefX
   if(Double.isNaN(minX) && Double.isNaN(maxX) && Double.isNaN(prefX)) {
     throw new RuntimeException("Enter atleast one of "+minX_Param.getName()+","+
                                maxX_Param.getName()+" or "+prefferedX_Param.getName());
   }
   minProb = getValueForParameter(minProbParam);
   maxProb = getValueForParameter(maxProbParam);
   prefProb = getValueForParameter(prefferedProbParam);
   if(!Double.isNaN(minProb) || !Double.isNaN(maxProb) || !Double.isNaN(prefProb)) {
     // check that if user entered minX, then minProb was also entered
     checkValidVals(minX, minProb, minX_Param.getName(), minProbParam.getName());
     // check that if user entered maxX, then maxProb was also entered
     checkValidVals(maxX, maxProb, maxX_Param.getName(), maxProbParam.getName());
     // check that if user entered prefX, then prefProb was also entered
     checkValidVals(prefX, prefProb, prefferedX_Param.getName(), prefferedProbParam.getName());
   }
   try {
     MinMaxPrefEstimate estimate = new MinMaxPrefEstimate(minX, maxX, prefX,
         minProb, maxProb, prefProb);
      return estimate;
   }catch(InvalidParamValException e) {
     throw new RuntimeException(this.model.getName()+":"+e.getMessage());
   }

 }
 /**
   * Set the estimate paramter value to be min/max/preferred estimate
   */
 private Estimate setFractileListEstimate() {
	 ArbitrarilyDiscretizedFunc val = (ArbitrarilyDiscretizedFunc)this.arbitrarilyDiscFuncParam.getValue();
	   if(val.getNum()==0) throw new RuntimeException(arbitrarilyDiscFuncParam.getName()+
	         MSG_VALUE_MISSING_SUFFIX);
	   try {
	     DiscreteValueEstimate estimate = new DiscreteValueEstimate(val, true);
	     return estimate;
	   }catch(InvalidParamValException e) {
	     throw new RuntimeException(this.model.getName()+":"+e.getMessage());
	   }
 }

 /**
  * Check that if usr entered X value, then prob value is also entered.
  * Similarly, a check is also made that if prob is entered, x val must be entered as well.
  * If any check fails RuntimException is thrown
  * @param xVal
  * @param probVal
  * @param xParamName
  * @param probParamName
  */
 private void checkValidVals(double xVal, double probVal, String xParamName,
                             String probParamName) {
   if(Double.isNaN(xVal) && !Double.isNaN(probVal))
     throw new RuntimeException("If " + xParamName +" is empty, "+probParamName+" is not allowed");
   if(!Double.isNaN(xVal) && Double.isNaN(probVal))
     throw new RuntimeException(probParamName+MSG_VALUE_MISSING_SUFFIX);
 }

 private double getValueForParameter(Parameter param) {
   Object val = param.getValue();
   if(val==null) return Double.NaN;
   else return ((Double)val).doubleValue();
 }



  private void copyFunction(DiscretizedFunc funcFrom, DiscretizedFunc funcTo) {
    int numVals = funcFrom.getNum();
    for(int i=0; i < numVals; ++i) funcTo.set(funcFrom.getX(i), funcFrom.getY(i));
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
  * test the parameter editor
  * @param args
  */
  public static void main(String args[]) {
    JFrame frame = new JFrame();
    JButton htmlSummaryButton = new JButton("View Estimate Summary(HTML)");
    JButton textSummaryButton = new JButton("Estimate toString()");

    frame.getContentPane().setLayout(new GridBagLayout());
    EstimateParameter estimateParam = new EstimateParameter("Slip Rate", Double.NEGATIVE_INFINITY, Double.POSITIVE_INFINITY, EstimateConstraint.createConstraintForAllEstimates());
    ConstrainedEstimateParameterEditor estimateParameterEditor = new ConstrainedEstimateParameterEditor(estimateParam,true);
    htmlSummaryButton.addActionListener(new HtmlEstimateSummaryListener(estimateParameterEditor, "Slip Rate"));
    textSummaryButton.addActionListener(new TextEstimateSummaryListener(estimateParameterEditor, "Slip Rate"));
    frame.getContentPane().add(estimateParameterEditor, new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0
        , GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ) );
    frame.getContentPane().add(htmlSummaryButton, new GridBagConstraints( 0, 1, 1, 1, 1.0, 0.0
            , GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets( 0, 0, 0, 0 ), 0, 0 ) );
    frame.getContentPane().add(textSummaryButton, new GridBagConstraints( 0, 2, 1, 1, 1.0, 0.0
            , GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets( 0, 0, 0, 0 ), 0, 0 ) );

    frame.pack();
    frame.setVisible(true);
  }

}

 /**
  * This class is used to view Estimate Summary in HTML form
  *
  * @author vipingupta
  *
  */
 class HtmlEstimateSummaryListener implements ActionListener {
	 private ConstrainedEstimateParameterEditor estimateParameterEditor;
	 private String title;

	 public HtmlEstimateSummaryListener(ConstrainedEstimateParameterEditor estimateParameterEditor, String title) {
		  this.estimateParameterEditor=estimateParameterEditor;
		  this.title = title;
	 }

	 public void actionPerformed(ActionEvent event) {
		 try {
			 estimateParameterEditor.setEstimateInParameter();
			 Estimate estimate = (Estimate)estimateParameterEditor.getParameter().getValue();
			 JFrame frame = new JFrame();
			 JPanel panel = GUI_Utils.getPanel(new InfoLabel(estimate, title, "Probability"), title);
			 frame.getContentPane().add(panel, BorderLayout.CENTER);
			 frame.setLocationRelativeTo(estimateParameterEditor);
			 frame.pack();
			 frame.show();
		 }catch(Exception e) {
			 JOptionPane.showMessageDialog(estimateParameterEditor,  e.getMessage());
		 }
	 }
 }
	
	 /**
	  * This class is used to view Estimate Summary in HTML form
	  *
	  * @author vipingupta
	  *
	  */
	 class TextEstimateSummaryListener implements ActionListener {
		 private ConstrainedEstimateParameterEditor estimateParameterEditor;
		 private String title;

		 public TextEstimateSummaryListener(ConstrainedEstimateParameterEditor estimateParameterEditor, String title) {
			  this.estimateParameterEditor=estimateParameterEditor;
			  this.title = title;
		 }

		 public void actionPerformed(ActionEvent event) {
			 try {
				 estimateParameterEditor.setEstimateInParameter();
				 Estimate estimate = (Estimate)estimateParameterEditor.getParameter().getValue();
				 JFrame frame = new JFrame();
				 JTextArea textArea = new JTextArea(estimate.toString());
				 frame.getContentPane().add(new JScrollPane(textArea), BorderLayout.CENTER);
				 frame.setLocationRelativeTo(estimateParameterEditor);
				 frame.pack();
				 frame.show();
			 }catch(Exception e) {
				 JOptionPane.showMessageDialog(estimateParameterEditor, e.getMessage());
			 }
		 }


 }
