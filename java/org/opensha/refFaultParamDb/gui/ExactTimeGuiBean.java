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
import org.opensha.commons.param.IntegerConstraint;
import org.opensha.commons.param.IntegerParameter;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.editor.ParameterListEditor;
import org.opensha.refFaultParamDb.data.ExactTime;
/**
 * <p>Title: ExactTimeGuiBean.java </p>
 * <p>Description: This GUI allows the user to enter all the information
 * so that user can enter all the information related to the Gregorian Calendar.</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class ExactTimeGuiBean extends ParameterListEditor{
    // Start-Time Parameters
    public final static String YEAR_PARAM_NAME = "Year";
    private IntegerParameter yearParam;
    private IntegerConstraint yearConstraint = new IntegerConstraint(0,Integer.MAX_VALUE);
    private final static Integer YEAR_PARAM_DEFAULT = new Integer(2005);
    public final static String MONTH_PARAM_NAME = "Month";
    private IntegerParameter monthParam;
    private IntegerConstraint monthConstraint = new IntegerConstraint(1,12);
    private final static Integer MONTH_PARAM_DEFAULT = new Integer(1);
    public final static String DAY_PARAM_NAME = "Day";
    private IntegerParameter dayParam;
    private final static Integer DAY_PARAM_DEFAULT = new Integer(1);
    private IntegerConstraint dayConstraint = new IntegerConstraint(1,31);
    public final static String HOUR_PARAM_NAME = "Hour";
    private IntegerParameter hourParam;
    private final static Integer HOUR_PARAM_DEFAULT = new Integer(0);
    private IntegerConstraint hourConstraint = new IntegerConstraint(0,59);
    public final static String MINUTE_PARAM_NAME = "Minute";
    private IntegerParameter minuteParam;
    private final static Integer MINUTE_PARAM_DEFAULT = new Integer(0);
    private IntegerConstraint minuteConstraint = new IntegerConstraint(0,59);
    public final static String SECOND_PARAM_NAME = "Second";
    private IntegerParameter secondParam;
    private final static Integer SECOND_PARAM_DEFAULT = new Integer(0);
    private IntegerConstraint secondConstraint = new IntegerConstraint(0,59);

  public ExactTimeGuiBean(String title) {
    initParamsList();
    this.addParameters();
    this.setTitle(title);
  }


  /**
   * Set the parameters for exact time
   * @param exactTime
   */
  public void setTime(ExactTime exactTime) {
    int year = exactTime.getYear();
    int month=exactTime.getMonth();
    int day=exactTime.getDay();
    int hour=exactTime.getHour();
    int minute=exactTime.getMinute();
    int second = exactTime.getSecond();

    // set year
    yearParam.setValue(new Integer(exactTime.getYear()));
    getParameterEditor(yearParam.getName()).refreshParamEditor();
    //set month
    if(month!=0){
      monthParam.setValue(new Integer(month));
      getParameterEditor(monthParam.getName()).refreshParamEditor();
    }
    //set day
    if(day!=0){
      dayParam.setValue(new Integer(day));
      getParameterEditor(dayParam.getName()).refreshParamEditor();
    }
    //set hour
    if(hour!=0){
      hourParam.setValue(new Integer(hour));
      getParameterEditor(hourParam.getName()).refreshParamEditor();
    }
    //set minute
    if(minute!=0){
      minuteParam.setValue(new Integer(minute));
      getParameterEditor(minuteParam.getName()).refreshParamEditor();
    }
     //set second
    if(second!=0){
      secondParam.setValue(new Integer(second));
      getParameterEditor(secondParam.getName()).refreshParamEditor();
    }

  }

  /**
   * Initialize the parameters
   */
  private void initParamsList() {
    parameterList = new ParameterList();
    yearParam = new IntegerParameter(YEAR_PARAM_NAME, yearConstraint, YEAR_PARAM_DEFAULT);
    monthConstraint.setNullAllowed(true);
    dayConstraint.setNullAllowed(true);
    hourConstraint.setNullAllowed(true);
    minuteConstraint.setNullAllowed(true);
    secondConstraint.setNullAllowed(true);
    monthParam = new IntegerParameter(MONTH_PARAM_NAME, monthConstraint, MONTH_PARAM_DEFAULT);
    dayParam = new IntegerParameter(DAY_PARAM_NAME, dayConstraint, DAY_PARAM_DEFAULT);
    hourParam = new IntegerParameter(HOUR_PARAM_NAME, hourConstraint,HOUR_PARAM_DEFAULT);
    minuteParam = new IntegerParameter(MINUTE_PARAM_NAME, minuteConstraint, MINUTE_PARAM_DEFAULT);
    secondParam = new IntegerParameter(SECOND_PARAM_NAME, secondConstraint, SECOND_PARAM_DEFAULT);
    parameterList.addParameter(yearParam);
    parameterList.addParameter(monthParam);
    parameterList.addParameter(dayParam);
    parameterList.addParameter(hourParam);
    parameterList.addParameter(minuteParam);
    parameterList.addParameter(secondParam);
  }

  /**
   * Return the exact time
   * @return
   */
  public ExactTime getExactTime() {
    int year =((Integer)yearParam.getValue()).intValue();
    int month=0, day=0, hour=0, minute=0, second=0;
    // month parameter value
    Integer monthParamVal = (Integer)monthParam.getValue();
    if(monthParamVal!=null) month = monthParamVal.intValue();
    // day parameter value
    Integer dayParamVal = (Integer)dayParam.getValue();
    if(dayParamVal!=null) day = dayParamVal.intValue();
    // hour parameter value
    Integer hourParamVal = (Integer)hourParam.getValue();
    if(hourParamVal!=null) hour = hourParamVal.intValue();
    // minute parameter value
    Integer minuteParamVal = (Integer)minuteParam.getValue();
    if(minuteParamVal!=null) minute = minuteParamVal.intValue();
    // second parameter value
    Integer secondParamVal = (Integer)secondParam.getValue();
    if(secondParamVal!=null) second = secondParamVal.intValue();
    ExactTime exactTime = new ExactTime(year, month, day, hour, minute, second, false);
    return exactTime;
  }

}
