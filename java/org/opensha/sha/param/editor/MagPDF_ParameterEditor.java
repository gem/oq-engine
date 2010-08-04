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

package org.opensha.sha.param.editor;

import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ListIterator;

import javax.swing.JButton;
import javax.swing.JOptionPane;

import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterConstraintAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.editor.ParameterEditor;
import org.opensha.commons.param.editor.ParameterListEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeFailEvent;
import org.opensha.commons.param.event.ParameterChangeFailListener;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.sha.magdist.ArbIncrementalMagFreqDist;
import org.opensha.sha.magdist.GaussianMagFreqDist;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.SingleMagFreqDist;
import org.opensha.sha.magdist.SummedMagFreqDist;
import org.opensha.sha.magdist.YC_1985_CharMagFreqDist;
import org.opensha.sha.magdist.gui.MagFreqDistApp;
import org.opensha.sha.param.MagFreqDistParameter;
import org.opensha.sha.param.MagPDF_Parameter;

/**
 *  <b>Title:</b> MagPDF_ParameterEditor<p>
 *
 *  b>Description:</b> This is a MagFreqDistParameter editor. All parameters listed
 * in the constraint of the MagFreqDistParameter are listed as choices, and below
 * are shown the associated independent parameters than need to be filled in to
 * make the desired distribution.<p>
 *
 * @author     Nitin & Vipin Gupta, and Ned Field
 * @created    Oct 18, 2002
 * @version    1.0
 */

public class MagPDF_ParameterEditor
    extends ParameterEditor implements ParameterChangeListener,
    ParameterChangeFailListener,
    ActionListener,MagDistParameterEditorAPI {

  /** Class name for debugging. */
  protected final static String C = "MagPDF_ParameterEditor";
  /** If true print out debug statements. */
  protected final static boolean D = false;

  private MagPDF_Parameter magPDF_Param;

  //Checks if the magDist Params have been changed
  private boolean magPDF_ParamsChange = true;
  // name of the is mag Freq dist
  private String name;
  /**
   * Paramter List for holding all parameters
   */
  private ParameterList parameterList;

  /**
   * ParameterListEditor for holding parameters
   */
  private ParameterListEditor editor;

  // title of Parameter List Editor
  public static final String MAG_DIST_TITLE = new String("Mag PDF Params");

  //shows the parameters in a window
  private MagFreqDistApp magDistPanel;

  /**
   * Constructor
   */
  public MagPDF_ParameterEditor() {

  }

  public MagPDF_ParameterEditor(ParameterAPI model) {
    super(model);
    setParameter(model);
  }


  /** Returns the parameter that is stored internally that this GUI widget is editing */
  public void setParameter( ParameterAPI param ){

    String S = C + ": Constructor(): ";
    if (D) System.out.println(S + "Starting:");
    setParameterInEditor(param);
    valueEditor = new JButton("Set " + param.getName());
    ( (JButton) valueEditor).addActionListener(this);
    add(valueEditor, new GridBagConstraints(0, 0, 1, 1, 1.0, 0.0
                                            , GridBagConstraints.CENTER,
                                            GridBagConstraints.HORIZONTAL,
                                            new Insets(0, 0, 0, 0), 0, 0));
    // remove the previous editor
    //removeAll();
    magPDF_Param = (MagPDF_Parameter) param;

    createMagFreqDistParameterEditor();


    // All done
    if (D) System.out.println(S + "Ending:");
  }

  /**
   * This function is called when the user click for the ParameterListParameterEditor Button
   *
   * @param ae
   */
  public void actionPerformed(ActionEvent ae) {

    magDistPanel = new MagFreqDistApp();
    magDistPanel.setMagDistEditor(this);
    //magDistPanel.pack();
    magDistPanel.setVisible(true);
  }

  /**
   * Checks whether you want to show the Mag Freq Dist Param Editor as button or a panel
   * This function mostly come in handy if instead of displaying this parameter
   * as the button user wants to show it as the Parameterlist in the panel.
   * @param visible : If it it true, button is visible else not visible
   * By default it is visible
   */
  public void setMagFreqDistParamButtonVisible(boolean visible) {
    valueEditor.setVisible(visible);
  }

  /**
   * Clones the Mag ParamList and the makes the parameters visible based on the
   * selected Distribution.
   * @return
   */
  public ParameterListEditor createMagFreqDistParameterEditor() {
	  // make the params editor
	  initParamList();
	  editor = new ParameterListEditor(parameterList);
	  editor.setTitle(MAG_DIST_TITLE);


      // Update which parameters should be invisible
      synchRequiredVisibleParameters();
      return editor;
  }


  /**
   * Function that returns the magFreDist Param as a parameterListeditor
   * so that user can display it as the panel in window rather then
   * button.
   * @return
   */
  public ParameterListEditor getMagFreqDistParameterEditor(){
	  return editor;
  }

  /**
   * Main GUI Initialization point. This block of code is updated by JBuilder
   * when using it's GUI Editor.
   */
  protected void jbInit() throws Exception {
    //super.jbInit();
    // Main component
    this.setLayout(new GridBagLayout());
  }

  /**
   * Called when the parameter has changed independently from
   * the editor, such as with the ParameterWarningListener.
   * This function needs to be called to to update
   * the GUI component ( text field, picklist, etc. ) with
   * the new parameter value.
   */
  public void refreshParamEditor() {
    editor.refreshParamEditor();
  }

  /**
   *
   */
  protected void initParamList() {

    // Starting
    String S = C + ": initControlsParamListAndEditor(): ";
    if (D) System.out.println(S + "Starting:");

    /**
     * get adjustable params from MagFreqDistParam and add listeners to them
     */
    parameterList = (ParameterList)magPDF_Param.getAdjustableParams().clone();
    //do it if not done already ( allows the person to just do it once)

    ListIterator it = parameterList.getParametersIterator();
    while (it.hasNext()) {
      ParameterAPI param = (ParameterAPI) it.next();
      param.addParameterChangeFailListener(this);
      param.addParameterChangeListener(this);
    }
  }

  /**
   *  Description of the Method
   *
   * @exception  ParameterException  Description of the Exception
   */
  protected void synchRequiredVisibleParameters() throws ParameterException {

    String S = C + ":synchRequiredVisibleParameters:";

    String distributionName = parameterList.getParameter(MagFreqDistParameter.
        DISTRIBUTION_NAME).getValue().toString();

    // Turn off all parameters - start fresh, then make visible as required below
    ListIterator it = parameterList.getParametersIterator();
    while (it.hasNext())
      editor.setParameterVisible( ( (ParameterAPI) it.next()).getName(), false);

    // make the min, max, num and select dist to be visible
    editor.setParameterVisible(MagFreqDistParameter.MIN, true);
    editor.setParameterVisible(MagFreqDistParameter.MAX, true);
    editor.setParameterVisible(MagFreqDistParameter.NUM, true);
    editor.setParameterVisible(MagFreqDistParameter.DISTRIBUTION_NAME, true);

    /**
     * if Single Mag Freq dist is selected
     * depending on the parameter chosen from the SINGLE_PARAMS_TO_SET, it redraws
     * all the independent parameters again and draws the text boxes to fill
     * in the values.
     */
    if (distributionName.equalsIgnoreCase(SingleMagFreqDist.NAME)) {
      editor.getParameterEditor(MagFreqDistParameter.ARB_INCR_PARAM_NAME).setVisible(false);
      setSingleDistParamsVisible();
    }

    /**
     *  If Gutenberg Richter Freq dist is selected
     */
    if (distributionName.equalsIgnoreCase(GutenbergRichterMagFreqDist.NAME)) {
      editor.getParameterEditor(MagFreqDistParameter.ARB_INCR_PARAM_NAME).setVisible(false);
      setGR_DistParamsVisible();
    }

    /**
     * If Gaussian Freq dist is selected
     */
    if (distributionName.equalsIgnoreCase(GaussianMagFreqDist.NAME)) {
      editor.getParameterEditor(MagFreqDistParameter.ARB_INCR_PARAM_NAME).setVisible(false);
      this.setGaussianDistParamsVisible();
    }

    /**
     * If YC Freq dist is selected
     */
    if (distributionName.equalsIgnoreCase(YC_1985_CharMagFreqDist.NAME)) {
      editor.getParameterEditor(MagFreqDistParameter.ARB_INCR_PARAM_NAME).setVisible(false);
      this.setYC_DistParamsVisible();

    }
    else if (distributionName.equalsIgnoreCase(ArbIncrementalMagFreqDist.NAME))
      this.setArbIncrDistParamsVisible();


    editor.validate();
    editor.repaint();

    // All done
    if (D)
      System.out.println(S + "Ending: ");
  }

  /**
   * make the parameters related to SINGLE Mag dist visible
   */
  private void setSingleDistParamsVisible() {
    editor.setParameterVisible(MagFreqDistParameter.MAG, true);
  }

  /**
   * make the parameters related to GAUSSIAN Mag dist visible
   */
  private void setGaussianDistParamsVisible() {
    // set all the parameters visible
    editor.setParameterVisible(MagFreqDistParameter.MEAN, true);
    editor.setParameterVisible(MagFreqDistParameter.STD_DEV, true);
    editor.setParameterVisible(MagFreqDistParameter.TRUNCATION_REQ, true);

    String truncReq = parameterList.getParameter(MagFreqDistParameter.
                                                 TRUNCATION_REQ).getValue().
        toString();
    // make the truncation level visible only if truncation req is NOT NONE
    if (truncReq.equalsIgnoreCase(MagFreqDistParameter.NONE))
      editor.setParameterVisible(MagFreqDistParameter.TRUNCATE_NUM_OF_STD_DEV, false);
    else
      editor.setParameterVisible(MagFreqDistParameter.TRUNCATE_NUM_OF_STD_DEV, true);
  }

  /**
   * make the parameters related to Gutenberg Richter Mag dist visible
   */
  private void setGR_DistParamsVisible() {

    editor.setParameterVisible(MagFreqDistParameter.GR_MAG_LOWER, true);
    editor.setParameterVisible(MagFreqDistParameter.GR_BVALUE, true);
    editor.setParameterVisible(MagFreqDistParameter.GR_MAG_UPPER, true);
  }

  /**
   * make the parameters related to Youngs and Coppersmith Mag dist visible
   */
  private void setYC_DistParamsVisible() {
    editor.setParameterVisible(MagFreqDistParameter.GR_MAG_LOWER, true);
    editor.setParameterVisible(MagFreqDistParameter.GR_MAG_UPPER, true);
    editor.setParameterVisible(MagFreqDistParameter.YC_DELTA_MAG_CHAR, true);
    editor.setParameterVisible(MagFreqDistParameter.YC_MAG_PRIME, true);
    editor.setParameterVisible(MagFreqDistParameter.YC_DELTA_MAG_PRIME, true);
    editor.setParameterVisible(MagFreqDistParameter.GR_BVALUE, true);
  }

  /**
   *  Gets the name attribute of the MagDistGuiBean object
   *
   * @return    The name value
   */
  public String getName() {
    return name;
  }

  /**
   *  This is the main function of this interface. Any time a control
   *  paramater or independent paramater is changed by the user in a GUI this
   *  function is called, and a paramater change event is passed in. This
   *  function then determines what to do with the information ie. show some
   *  paramaters, set some as invisible, basically control the paramater
   *  lists.
   *
   * @param  event
   */
  public void parameterChange(ParameterChangeEvent event) {

    String S = C + ": parameterChange(): ";
    if (D)
      System.out.println("\n" + S + "starting: ");

    String name1 = event.getParameterName();

    if (name1.equalsIgnoreCase(MagFreqDistParameter.DISTRIBUTION_NAME)) {
      try { // if selectde distribution changes
        synchRequiredVisibleParameters();
      }
      catch (Exception e) {
        System.out.println(this.C + " " + e.toString());
        e.printStackTrace();
      }
    }
    magPDF_ParamsChange = true;

  }

  /**
   * make the parameters for the Arb Incremental MagFreqDist Visible
   */
  private void setArbIncrDistParamsVisible(){
    editor.getParameterEditor(MagFreqDistParameter.MIN).setVisible(false);
    editor.getParameterEditor(MagFreqDistParameter.MAX).setVisible(false);
    editor.getParameterEditor(MagFreqDistParameter.NUM).setVisible(false);
    editor.getParameterEditor(MagFreqDistParameter.ARB_INCR_PARAM_NAME).setVisible(true);
  }

  /**
   *  Controller function. Dispacter function. Based on which Mag Dist was
   *  choosen, and which parameters are set. determines which dependent
   *  variable discretized function to return.
   *
   * @return                          The choosenFunction value
   * @exception  ConstraintException  Description of the Exception
   */
  public void setMagDistFromParams() throws ConstraintException {

    // Starting
    String S = C + ": setMagDistFromParams():";
    if (D) System.out.println(S + "Starting");
    if (magPDF_ParamsChange) {
      magPDF_Param.setMagDist(this.parameterList);
      magPDF_ParamsChange = false;
    }
  }


  /**
   *  Sets the MagDistParam to be SummedMagFreqDist
   *
   * @return                          The choosenFunction value
   * @exception  ConstraintException  Description of the Exception
   */
  public void setMagDistFromParams(SummedMagFreqDist summedDist,
                                   String metadata) throws UnsupportedOperationException {
   throw new UnsupportedOperationException("setMagDistFromParams  not implemented "+
                                            "for MagPDF_Parameter");
  }

  /**
   * Sets the Summed Dist plotted to be false or true based on
   * @param sumDistPlotted boolean
   */
  public void setSummedDistPlotted(boolean sumDistPlotted) throws UnsupportedOperationException{
    throw new UnsupportedOperationException("setMagDistFromParams  not implemented "+
                                         "for MagPDF_Parameter");
  }


  /**
   *  Shown when a Constraint error is thrown on a ParameterEditor
   *
   * @param  e  Description of the Parameter
   */
  public void parameterChangeFailed(ParameterChangeFailEvent e) {

    String S = C + " : parameterChangeWarning(): ";
    if (D) System.out.println(S + "Starting");

    StringBuffer b = new StringBuffer();

    ParameterAPI param = (ParameterAPI) e.getSource();
    ParameterConstraintAPI constraint = param.getConstraint();
    String oldValueStr = e.getOldValue().toString();
    String badValueStr = e.getBadValue().toString();
    String name = param.getName();

    b.append("The value ");
    b.append(badValueStr);
    b.append(" is not permitted for '");
    b.append(name);
    b.append("'.\n");

    b.append("Resetting to ");
    b.append(oldValueStr);
    b.append(". The constraints are: \n");
    b.append(constraint.toString());
    b.append("\n");

    JOptionPane.showMessageDialog(
        this, b.toString(),
        "Cannot Change Value", JOptionPane.INFORMATION_MESSAGE
        );

    if (D) System.out.println(S + "Ending");

  }

  /**
   * returns the MagDistName
   * @return
   */
  public String getMagDistName() {
    return parameterList.getParameter(MagFreqDistParameter.DISTRIBUTION_NAME).
        getValue().toString();
  }

  /**
   * returns the Min of the magnitude for the distribution
   * @return
   */
  public double getMin() {
    return ( (Double) parameterList.getParameter(MagFreqDistParameter.MIN).
            getValue()).doubleValue();
  }

  /**
   * returns the Max of the magnitude for thr distribution
   * @return
   */
  public double getMax() {
    return ( (Double) parameterList.getParameter(MagFreqDistParameter.MAX).
            getValue()).doubleValue();
  }

  /**
   * returns the Number of magnitudes for the Distribution
   * @return
   */
  public int getNum() {
    return ( (Integer) parameterList.getParameter(MagFreqDistParameter.NUM).
            getValue()).intValue();
  }

  /**
   * returns the ParamterList for the MagfreqDistParameter
   * @return
   */
  public ParameterList getParamterList() {
    return parameterList;
  }

  /** Returns each parameter for the MagFreqDist */
  public ParameterAPI getParameter(String name) throws ParameterException {
    return parameterList.getParameter(name);
  }

  /** returns the parameterlist */
  public ParameterList getParameterList() {
    return this.parameterList;
  }

}

