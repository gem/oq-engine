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

package org.opensha.refFaultParamDb.gui;
import java.awt.GridBagConstraints;
import java.awt.Insets;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.GregorianCalendar;

import org.opensha.commons.data.estimate.Estimate;
import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.gui.LabeledBoxPanel;
import org.opensha.commons.param.IntegerParameter;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ConstrainedStringParameterEditor;
import org.opensha.commons.param.editor.IntegerParameterEditor;
import org.opensha.commons.param.editor.estimate.ConstrainedEstimateParameterEditor;
import org.opensha.commons.param.estimate.EstimateConstraint;
import org.opensha.commons.param.estimate.EstimateParameter;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.refFaultParamDb.data.ExactTime;
import org.opensha.refFaultParamDb.data.TimeAPI;
import org.opensha.refFaultParamDb.data.TimeEstimate;
import org.opensha.refFaultParamDb.gui.infotools.GUI_Utils;



/**
 * <p>Title: TimeGuiBean.java </p>
 *
 * <p>Description: This GUI bean displays the GUI to the user so that
 * usr can enter the time estimate/exact time for a event. This GUI bean
 * can also be used to specify a start/end time for a timespan </p>
 *
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class TimeGuiBean extends LabeledBoxPanel implements ParameterChangeListener {
  // parameters for Date Estimate
  private StringParameter yearUnitsParam;
  private IntegerParameter zeroYearParam;
  private StringParameter eraParam;
  private IntegerParameter publicationYearParam;
  // various parameters
  private EstimateParameter estimateParameter;
  private StringParameter timeOptionsParam;


  private final static String YEAR_UNITS_PARAM_NAME="Year Units";
  private final static String CALENDAR_YEAR = "Calendar Year";
  private final static String ZERO_YEAR_PARAM_NAME = "Zero Year";

  private final static String CALENDAR_ERA_PARAM_NAME="Era";
  private final static String AD = "AD";
  private final static String BC = "BC";
  private final static String KA = "ka";
  private final static Integer YEAR1950 = new Integer(1950);

  private final static String YEARS = "Years";
  private final static String PUBLICATION_YEAR_PARAM_NAME = "Publication Year";
  private final static int DEFAULT_PUB_YEAR_VAL = 0;

  // editors
  private ConstrainedStringParameterEditor yearUnitsParamEditor;
  private IntegerParameterEditor zeroYearParamEditor;
  private ConstrainedStringParameterEditor eraParamEditor;
  private IntegerParameterEditor publicationYearParamEditor; // needed to represent "NOW"

  private final static String TIME_OPTIONS_PARAM_NAME = "Type of Time";
  private final static String ESTIMATE = "Estimate";
  private final static String EXACT="Exact";
  private final static String NOW = "Now";


  // GUI bean to provide the exact time
  private ExactTimeGuiBean exactTimeGuiBean;

  // parameter editors
  private ConstrainedEstimateParameterEditor estimateParamEditor;
  private ConstrainedStringParameterEditor timeOptionsParamEditor;
  private boolean isNowAllowed; // whether "Now" is allowed

  public TimeGuiBean(String title, boolean isNowAllowed) {
    try {
      this.isNowAllowed = isNowAllowed;
      this.title = title;
      // intialize the parameters and editors
      initParamListAndEditors();
      // add the editors this panel
      addEditorsToPanel();
      setParametersVisible();
      setTitle(title);
      setDateParamsVisibleBasedOnUnits();
    }catch(Exception e) {
      e.printStackTrace();
    }
  }

  /**
   * Set the time values in editor
   *
   * @param time
   */
  public void setTime(TimeAPI time) {
    if(time instanceof ExactTime) { // if it is exact time
      ExactTime exactTime = (ExactTime)time;
      // now
      if(exactTime.getIsNow()) { // NOW
        setParametersForNow(exactTime);
      }
      else   { // exact time
        timeOptionsParam.setValue(EXACT);
        exactTimeGuiBean.setTime(exactTime);
      }
    } else { // if it is time estimate
      setParametersForTimeEstimate(time);
    }
    timeOptionsParamEditor.refreshParamEditor();

  }

  /**
   * Set parameters for now
   * @param exactTime
   * @throws ParameterException
   * @throws ConstraintException
   */
  private void setParametersForNow(ExactTime exactTime) throws
      ParameterException, ConstraintException {
    timeOptionsParam.setValue(NOW);
    int year = exactTime.getYear();
    if(year!=DEFAULT_PUB_YEAR_VAL){
      this.publicationYearParam.setValue(new Integer(year));
      publicationYearParamEditor.refreshParamEditor();
    }
  }

  /**
   * Set parameters for time estimate
   * @param time
   * @throws ParameterException
   * @throws ConstraintException
   */
  private void setParametersForTimeEstimate(TimeAPI time) throws
      ParameterException, ConstraintException {
    timeOptionsParam.setValue(ESTIMATE);
    TimeEstimate timeEstimate = (TimeEstimate)time;
    timeEstimate.getEstimate().setUnits(null);
    estimateParameter.setValue(timeEstimate.getEstimate());
    estimateParamEditor.refreshParamEditor();

    eraParam.setValue(timeEstimate.getEra());
    eraParamEditor.refreshParamEditor();
    if(timeEstimate.isKaSelected()) {
      this.yearUnitsParam.setValue(KA);
      zeroYearParam.setValue(new Integer(timeEstimate.getZeroYear()));
      zeroYearParamEditor.refreshParamEditor();
    } else yearUnitsParam.setValue(this.CALENDAR_YEAR);
     yearUnitsParamEditor.refreshParamEditor();
  }

  /**
   * Set the publication year for "Now"
   * @param year
   */
  public void setNowYearVal(int year) {
    this.publicationYearParam.setValue(new Integer(year));
    this.publicationYearParamEditor.refreshParamEditor();
  }


  // intialize the various parameters and editors
  private void initParamListAndEditors() throws Exception {
    // user can choose to provide exact time or a time estimate
    ArrayList availableTimeOptions = getAvailableTimeOptions();
    timeOptionsParam = new StringParameter(TIME_OPTIONS_PARAM_NAME, availableTimeOptions,
                                           (String)availableTimeOptions.get(0));
    timeOptionsParam.addParameterChangeListener(this);
    timeOptionsParamEditor = new ConstrainedStringParameterEditor(timeOptionsParam);
    // GUI bean so that user can provide exact time
    exactTimeGuiBean = new ExactTimeGuiBean(" ");
    // param and editor to allow user to fill the time estimate values
    ArrayList allowedDateEstimates  = EstimateConstraint.createConstraintForDateEstimates();
    estimateParameter = new EstimateParameter("Years", 0,
                                              Double.POSITIVE_INFINITY, allowedDateEstimates);
    estimateParamEditor = new ConstrainedEstimateParameterEditor(estimateParameter,true);
    /**
    * Parameters for Date Estimate [ isCorrected, units(ka/calendar year),
    *  era, 0th year (in case it is ka)]
    */

   // whether user wants to enter ka or calendar year
   ArrayList yearUnitsList = new ArrayList();
   yearUnitsList.add(CALENDAR_YEAR);
   yearUnitsList.add(KA);
   yearUnitsParam = new StringParameter(YEAR_UNITS_PARAM_NAME,
       yearUnitsList, (String)yearUnitsList.get(0));
   yearUnitsParam.addParameterChangeListener(this);
   yearUnitsParamEditor = new ConstrainedStringParameterEditor(yearUnitsParam);

   // Add ERAs
   ArrayList eras = new ArrayList();
   eras.add(AD);
   eras.add(BC);
   this.eraParam = new StringParameter(this.CALENDAR_ERA_PARAM_NAME, eras, (String)eras.get(0));
   eraParamEditor = new ConstrainedStringParameterEditor(eraParam);

   // ZERO year param
   this.zeroYearParam = new IntegerParameter(this.ZERO_YEAR_PARAM_NAME, 0, (new GregorianCalendar()).get(Calendar.YEAR), AD, YEAR1950);
   zeroYearParamEditor = new IntegerParameterEditor(zeroYearParam);

   // publication year param needed for representing "NOW"
   this.publicationYearParam = new IntegerParameter(this.PUBLICATION_YEAR_PARAM_NAME, 0, (new GregorianCalendar()).get(Calendar.YEAR), AD);
   publicationYearParamEditor = new IntegerParameterEditor(publicationYearParam);
   publicationYearParamEditor.setEnabled(false);
  }


  /**
   * Add the editors the panel
   */
  private void addEditorsToPanel() {
    setLayout(GUI_Utils.gridBagLayout);
    int yPos=0;
    add(this.timeOptionsParamEditor,new GridBagConstraints( 0, yPos++, 1, 1, 1.0, 1.0
        ,GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL, new Insets( 0, 0, 0, 0 ), 0, 0 ) );
    add(this.yearUnitsParamEditor,new GridBagConstraints( 0, yPos++, 1, 1, 1.0, 1.0
        ,GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL, new Insets( 0, 0, 0, 0 ), 0, 0 ) );
    add(this.eraParamEditor,new GridBagConstraints( 0, yPos++, 1, 1, 1.0, 1.0
        ,GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL, new Insets( 0, 0, 0, 0 ), 0, 0 ) );
    add(this.zeroYearParamEditor,new GridBagConstraints( 0, yPos++, 1, 1, 1.0, 1.0
        ,GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL, new Insets( 0, 0, 0, 0 ), 0, 0 ) );
    add(this.publicationYearParamEditor,new GridBagConstraints( 0, yPos++, 1, 1, 1.0, 1.0
        ,GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL, new Insets( 0, 0, 0, 0 ), 0, 0 ) );
    add(this.exactTimeGuiBean, new GridBagConstraints( 0, yPos++, 1, 1, 1.0, 1.0
        ,GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL, new Insets( 0, 0, 0, 0 ), 0, 0 ) );
    add(this.estimateParamEditor, new GridBagConstraints( 0, yPos++, 1, 1, 1.0, 1.0
        ,GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL, new Insets( 0, 0, 0, 0 ), 0, 0 ) );
  }

  /**
   * What time options are available to the user. USer can provide an estimate
   * as well as an exact time
   * @return
   */
  private ArrayList getAvailableTimeOptions() {
    ArrayList availableTimes = new ArrayList();
    availableTimes.add(ESTIMATE);
    availableTimes.add(EXACT);
    if(isNowAllowed) availableTimes.add(NOW);
    return availableTimes;
  }

  /**
   * This function is called whenever a parameter changes and this class
   * has registered to listen to that event.
   * @param event
   */
  public void parameterChange(ParameterChangeEvent event) {
    String paramName = event.getParameterName();
    if(paramName.equalsIgnoreCase(this.TIME_OPTIONS_PARAM_NAME)) {
      setParametersVisible();
    }else if(event.getParameterName().equalsIgnoreCase(this.YEAR_UNITS_PARAM_NAME)) {
       // change date params based on whether user wants to enter calendar date or ka
       setDateParamsVisibleBasedOnUnits();
    }
  }

  // change date params based on whether user wants to enter calendar date or ka
  private void setDateParamsVisibleBasedOnUnits() {
    String yearUnitsVal = (String)this.yearUnitsParam.getValue();
     if(yearUnitsVal.equalsIgnoreCase(this.CALENDAR_YEAR)) { //if user wants to enter calendar date
       this.zeroYearParamEditor.setVisible(false);
       this.eraParamEditor.setVisible( true);
     }else if(yearUnitsVal.equalsIgnoreCase(KA)) { // if user wants to enter ka years
      this.zeroYearParamEditor.setVisible(true);
       this.eraParamEditor.setVisible(false);
     }
  }


  /**
   * Set the exact/estimate
   * @param isVisible
   */
  private void setParametersVisible() {
    String timeOptionChosen = (String)timeOptionsParam.getValue();
    if(timeOptionChosen.equalsIgnoreCase(this.EXACT)) {
      setParametersVisibleForEstimateTime(false);
      setParametersVisibleForExactTime(true);
      this.publicationYearParamEditor.setVisible(false);
    } else if(timeOptionChosen.equalsIgnoreCase(this.ESTIMATE)) {
       setParametersVisibleForExactTime(false);
       setParametersVisibleForEstimateTime(true);
       this.publicationYearParamEditor.setVisible(false);
       setDateParamsVisibleBasedOnUnits();
    } else if(timeOptionChosen.equalsIgnoreCase(this.NOW)) {
      setParametersVisibleForExactTime(false);
      setParametersVisibleForEstimateTime(false);
      this.publicationYearParamEditor.setVisible(true);
    }
  }

  /**
   * Set the parameters for exact time visible/invisible based on user selection
   * @param isVisible
   */
  private void setParametersVisibleForExactTime(boolean isVisible) {
    this.exactTimeGuiBean.setVisible(isVisible);
    eraParamEditor.setVisible( isVisible);
  }

  /**
   * Set the parameters for exact time visible/invisible based on user selection
   * @param isVisible
   */
  private void setParametersVisibleForEstimateTime(boolean isVisible) {
    this.estimateParamEditor.setVisible(isVisible);
    this.yearUnitsParamEditor.setVisible(isVisible);
    eraParamEditor.setVisible( isVisible);
    zeroYearParamEditor.setVisible(isVisible);
  }

  /**
   * Get the the time selected by the user. User can choose exact time or
   * a time estimate.
   */
  public TimeAPI getSelectedTime() {
    String timeOptionChosen = (String)timeOptionsParam.getValue();
    TimeAPI timeAPI;
    if(timeOptionChosen.equalsIgnoreCase(this.EXACT)) {
      timeAPI = getExactTime();
    } else if(timeOptionChosen.equalsIgnoreCase(this.ESTIMATE)){
      timeAPI = getTimeEstimate();
    } else { // "Now" is selected
      Integer pubYearVal = (Integer)this.publicationYearParam.getValue();
      // if publication year not available, set the current year as NOW
      if(pubYearVal==null) //pubYearVal = new Integer(new GregorianCalendar().get(Calendar.YEAR));
        pubYearVal = new Integer(DEFAULT_PUB_YEAR_VAL);
      timeAPI = new ExactTime(pubYearVal.intValue(), 0, 0, 0, 0, 0, AD, true);
    }
    return timeAPI;
  }

  /**
   * Get  exact time as specified by the user
   * @return
   */
  private TimeAPI getExactTime() {
   ExactTime exactTime = this.exactTimeGuiBean.getExactTime();
   exactTime.setEra((String)this.eraParam.getValue());
   return exactTime;
  }

  /**
   * Get the time estimate as specified by the user
   * @return
   */
  private TimeEstimate getTimeEstimate() {
    estimateParamEditor.setEstimateInParameter();
    TimeEstimate timeEstimate = new TimeEstimate();
    String yearUnitsVal = (String)this.yearUnitsParam.getValue();
    if(yearUnitsVal.equalsIgnoreCase(this.KA)) // if user is entering the Ka values
      timeEstimate.setForKaUnits((Estimate)estimateParameter.getValue(),
                                 ((Integer)this.zeroYearParam.getValue()).intValue());
    else // if user chooses to enter time estimate in terms of calendar years
      timeEstimate.setForCalendarYear((Estimate)estimateParameter.getValue(),
                                      (String)this.eraParam.getValue());
    return timeEstimate;
  }
}
