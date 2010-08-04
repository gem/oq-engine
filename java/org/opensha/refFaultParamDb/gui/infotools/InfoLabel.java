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

package org.opensha.refFaultParamDb.gui.infotools;
import java.awt.Color;
import java.util.ArrayList;

import javax.swing.JLabel;

import org.opensha.commons.data.estimate.DiscretizedFuncEstimate;
import org.opensha.commons.data.estimate.Estimate;
import org.opensha.commons.data.estimate.FractileListEstimate;
import org.opensha.commons.data.estimate.LogNormalEstimate;
import org.opensha.commons.data.estimate.MinMaxPrefEstimate;
import org.opensha.commons.data.estimate.NormalEstimate;
import org.opensha.commons.data.function.DiscretizedFunc;
import org.opensha.refFaultParamDb.data.ExactTime;
import org.opensha.refFaultParamDb.data.TimeAPI;
import org.opensha.refFaultParamDb.data.TimeEstimate;

/**
 * <p>Title: InfoLabel.java </p>
 * <p>Description: This class constructs the JLabel to view the information about
 * a parameter or an estimate</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class InfoLabel extends JLabel {
  // color for JLabels
  private Color labelColor = new Color( 80, 80, 133 );
  private final static String ESTIMATE_TYPE = "Estimate Type";
  private final static String TIME = "Time";
  public final static String NOT_AVAILABLE = "NA";
  private final static String TIME_VAL = "Time Val";
  private final static String PROB = "Prob this is correct value";

  /**
   * default constructor
   */
  public InfoLabel() {
     this.setForeground(labelColor);
  }

  /**
   * Make  a JLabel for a param name-value pair
   * @param paramName
   * @param paramValue
   */
  public InfoLabel(String paramName, String paramValue) {
    this();
    setTextAsHTML(paramName, paramValue);
  }

  /**
  *  JLabel text for a param name-value pair
  * @param paramName
  * @param paramValue
  */

  public void setTextAsHTML(String paramName, String paramValue) {
    if(paramValue==null) paramValue = NOT_AVAILABLE;
    String label  = "<html><b>"+paramName+":&nbsp;</b>"+paramValue+"</html>";
    setText(label);
  }

  /**
   * Make  a JLabel for a String
   *
   * @param paramName
   * @param paramValue
   */
  public InfoLabel(String value) {
    this();
    setTextAsHTML(value);
  }

  /**
   *  JLabel text for a String
   *
   * @param paramName
   * @param paramValue
   */

  public void setTextAsHTML(String value) {
    if(value==null) value = NOT_AVAILABLE;
    String label  = "<html>"+value+"</html>";
    setText(label);
  }


  /**
   * Make  a JLabel for a Arraylist of Strings
   *
   * @param paramName
   * @param paramValue
   */
  public InfoLabel(ArrayList values) {
    this();
    setTextAsHTML(values);
  }

  /**
   * JLabel text for a Arraylist of Strings
   *
   * @param paramName
   * @param paramValue
   */
  public void setTextAsHTML(ArrayList values) {
    String label  = "<html>";
    if(values==null || values.size()==0) label += NOT_AVAILABLE;
    else {
      for (int i = 0; i < values.size(); ++i)
        label += values.get(i).toString() + "<br>";
    }
    label = label+"</html>";
    setText(label);
  }



  /**
   * Make a JLabel to provide info about a estimate
   *
   * @param estimate
   */
  public InfoLabel(Estimate estimate, String xAxisName, String yAxisName) {
    this();
    setTextAsHTML(estimate,  xAxisName, yAxisName);
  }

  /**
   * JLabel text to provide info about a estimate
   *
   * @param estimate
   */

  public void setTextAsHTML(Estimate estimate, String xAxisName, String yAxisName) {
    String text;
    if(estimate==null) text = "<html>"+NOT_AVAILABLE+"</html>";
    else  text="<html>"+getTextForEstimate(estimate, xAxisName, yAxisName)+"</html>";
    setText(text);
  }

  /**
   * Get Text For estimate
   *
   * @param estimate
   * @return
   */
  private String getTextForEstimate(Estimate estimate, String xAxisName, String yAxisName) {
    String text = "";
    if(estimate instanceof NormalEstimate)
      text = getTextForNormalEstimate((NormalEstimate)estimate);
    else if(estimate instanceof LogNormalEstimate)
      text = getTextForLogNormalEstimate((LogNormalEstimate)estimate);
    else if(estimate instanceof DiscretizedFuncEstimate) {
      DiscretizedFuncEstimate discretizedFunEstimate = (DiscretizedFuncEstimate)estimate;
      discretizedFunEstimate.getValues().setXAxisName(xAxisName);
      discretizedFunEstimate.getValues().setYAxisName(yAxisName);
      text = getTextForDiscretizedFuncEstimate( discretizedFunEstimate );
    }
    else if(estimate instanceof FractileListEstimate) {
      FractileListEstimate fractileListEstimate  = (FractileListEstimate) estimate;
      fractileListEstimate.getValues().setXAxisName(xAxisName);
      fractileListEstimate.getValues().setYAxisName(yAxisName);
      text = getTextForFractileListEstimate( fractileListEstimate );
    } else if(estimate instanceof MinMaxPrefEstimate) {
      MinMaxPrefEstimate minMaxPrefEstimate = (MinMaxPrefEstimate) estimate;
      text = getTextForMinMaxPrefEstimate(minMaxPrefEstimate, xAxisName, yAxisName);
    }
    return text;
  }

  /**
   * Make a JLabel to provide info about Time (Time can be exact time or
   * time estimate)
   *
   * @param estimate
   */
  public InfoLabel(TimeAPI time) {
    this.setForeground(labelColor);
    setTextAsHTML(time);
  }

  /**
   *
   * @param time
   */
  public void setTextAsHTML(TimeAPI time) {
    String text="";
    if(time == null ) // if time is not available
      text = "<html>"+NOT_AVAILABLE+"</html>";
    else if(time instanceof TimeEstimate)
      text = getTextForTimeEstimate((TimeEstimate)time);
    else if(time instanceof ExactTime)
      text = getTextForExactTime((ExactTime)time);
    setText(text);
  }

  /**
   * Get the Information to be displayed in case of exact estimate
   *
   * @param exactTime
   * @return
   */
  private String getTextForExactTime(ExactTime exactTime) {
    if(!exactTime.getIsNow()) { // it i not "NOW"
      return "<html><b>" + TIME + ":&nbsp;</b>Exact Time" + "<br>" +
          "<b>Year:&nbsp;</b>" + exactTime.getYear() + " "+exactTime.getEra() +
          "<br>" +
          "<b>Month:&nbsp;</b>" + exactTime.getMonth() + "<br>" +
          "<b>Date:&nbsp;</b>" + exactTime.getDay() + "<br>" +
          "<b>Hour:&nbsp;</b>" + exactTime.getHour() + "<br>" +
          "<b>Second:&nbsp;</b>" + exactTime.getSecond() + "<br></html>";
    } else { // represent "NOW"
      return "<html><b>" + TIME + ":&nbsp;</b>Now" /*+ "<br>" +
           "<b>Publication Year:&nbsp;</b>" + exactTime.getYear() + exactTime.getEra() +
           "<br></html>"*/;
    }
  }

  /**
   * get the information to be displayed in case of time estimate
   *
   * @param timeEstimate
   * @return
   */
  private String getTextForTimeEstimate(TimeEstimate timeEstimate) {
    // whether user provided ka values estimate/ calendar year estimates
    boolean isKaSelected = timeEstimate.isKaSelected();
    String text="";
    if(isKaSelected) { // if KA is selected
      text = "<html><b>"+TIME+":&nbsp;</b>Time Estimate"+"<br>"+
          "<html><b>Units:&nbsp;</b>ka"+"<br>"+
          "<b>Zero Year:&nbsp;</b>"+timeEstimate.getZeroYear()+" AD<br>"+
          getTextForEstimate(timeEstimate.getEstimate(), TIME_VAL, PROB)+"</html>";
    } else { // if calendar year is selected for estimate
      text = "<html><b>"+TIME+":&nbsp;</b>Time Estimate"+"<br>"+
       "<html><b>Units:&nbsp;</b>Calendar Years"+"<br>"+
       getTextForEstimate(timeEstimate.getEstimate(), TIME_VAL, PROB)+"</html>";
    }
    return text;
  }


  /**
   * Information for normal estimate
   *
   * @param estimate
   * @return
   */
  private String getTextForNormalEstimate(NormalEstimate estimate) {
    String text = "<b>" + ESTIMATE_TYPE + ":&nbsp;</b>" + estimate.getName() +
        "<br>" +
        "<b>Mean =&nbsp;</b>" + GUI_Utils.decimalFormat.format(estimate.getMean()) +
        "<br>" +
        "<b>StdDev =&nbsp;</b>" +
        GUI_Utils.decimalFormat.format(estimate.getStdDev()) + "<br>";
    if (!Double.isInfinite(estimate.getMin()))
      text += "<b>Lower Truncation(absolute):&nbsp;</b>" +
          GUI_Utils.decimalFormat.format(estimate.getMin()) + "<br>" +
          "<b>Lower Truncation(# of sigmas):&nbsp;</b>" +
          GUI_Utils.decimalFormat.format(estimate.getMinSigma()) + "<br>";
    if (!Double.isInfinite(estimate.getMax()))
      text += "<b>Upper Truncation(absolute):&nbsp;</b>" +
          GUI_Utils.decimalFormat.format(estimate.getMax()) + "<br>" +
          "<b>Upper Truncation(# of sigmas):&nbsp;</b>" +
          GUI_Utils.decimalFormat.format(estimate.getMaxSigma());
    if(Double.isInfinite(estimate.getMin()) && Double.isInfinite(estimate.getMax()))
      text += "<b>No Truncation";
    return text;
  }

  /**
   * Information for lognormal estimate
   *
   * @param estimate
   * @return
   */
  private String getTextForLogNormalEstimate(LogNormalEstimate estimate) {
    return "<b>"+ESTIMATE_TYPE+":&nbsp;</b>"+estimate.getName()+"<br>"+
        "<b>Linear Median:&nbsp;</b>"+ GUI_Utils.decimalFormat.format(estimate.getLinearMedian())+"<br>"+
        "<b>StdDev:&nbsp;</b>"+ GUI_Utils.decimalFormat.format(estimate.getStdDev())+"<br>"+
        "<b>Lower Truncation(absolute):&nbsp;</b>"+ GUI_Utils.decimalFormat.format(estimate.getMin())+"<br>"+
        "<b>Upper Truncation(absolute):&nbsp;</b>"+ GUI_Utils.decimalFormat.format(estimate.getMax())+"<br>"+
        "<b>Lower Truncation(# of sigmas):&nbsp;</b>"+ GUI_Utils.decimalFormat.format(estimate.getMinSigma())+"<br>"+
        "<b>Upper Truncation(# of sigmas):&nbsp;</b>"+ GUI_Utils.decimalFormat.format(estimate.getMaxSigma());

  }

  /**
   * Information for Discretized func estimate
   *
   * @param estimate
   * @return
   */
  private String getTextForDiscretizedFuncEstimate(DiscretizedFuncEstimate estimate) {
    DiscretizedFunc func = estimate.getValues();
    String text =  "<b>"+ESTIMATE_TYPE+":&nbsp;</b>"+estimate.getName()+"<br>"+
        "<b>Value&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Probability</b> <br>";
    for(int i=0; i<func.getNum(); ++i)
        text+=   GUI_Utils.decimalFormat.format(func.getX(i))+
            "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"+
             GUI_Utils.decimalFormat.format(func.getY(i))+"<br>";
    return text;
  }

  /**
  * Information for Fractile List estimate
  *
  * @param estimate
  * @return
  */
 private String getTextForFractileListEstimate(FractileListEstimate estimate) {
   DiscretizedFunc func = estimate.getValues();
   String text =  "<b>"+ESTIMATE_TYPE+":&nbsp;</b>"+estimate.getName()+"<br>"+
       "<b>"+func.getXAxisName()+"&nbsp;&nbsp;"+func.getYAxisName()+"</b> <br>";
   for(int i=0; i<func.getNum(); ++i)
       text+=   GUI_Utils.decimalFormat.format(func.getX(i))+
           "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"+
            GUI_Utils.decimalFormat.format(func.getY(i))+"<br>";
   return text;
 }

 /**
  * Information for min/max/pref estimate
  *
  * @param estimate
  * @return
  */
 private String getTextForMinMaxPrefEstimate(MinMaxPrefEstimate estimate,
                                             String xAxisName, String yAxisName) {
   String text =  "<b>"+ESTIMATE_TYPE+":&nbsp;</b>"+estimate.getName()+"<br>";
   double minX = estimate.getMinimum();
   double maxX = estimate.getMaximum();
   double prefX = estimate.getPreferred();
   double minProb = estimate.getMinimumProb();
   double maxProb = estimate.getMaximumProb();
   double prefProb = estimate.getPreferredProb();

   String minXStr="", maxXStr="", prefXStr="", minProbStr="", maxProbStr="", prefProbStr="";
   // min X
   if(!Double.isNaN(minX)) minXStr= GUI_Utils.decimalFormat.format(minX);
   else minXStr = ""+NOT_AVAILABLE;
     // max X
   if(!Double.isNaN(maxX)) maxXStr= GUI_Utils.decimalFormat.format(maxX);
   else maxXStr = ""+NOT_AVAILABLE;
     // pref X
   if(!Double.isNaN(prefX)) prefXStr= GUI_Utils.decimalFormat.format(prefX);
   else prefXStr = ""+NOT_AVAILABLE;
     // min Prob
   if(!Double.isNaN(minProb)) minProbStr= GUI_Utils.decimalFormat.format(minProb);
   else minProbStr = ""+NOT_AVAILABLE;
     // max Prob
   if(!Double.isNaN(maxProb)) maxProbStr= GUI_Utils.decimalFormat.format(maxProb);
   else maxProbStr = ""+NOT_AVAILABLE;
     // pref Prob
   if(!Double.isNaN(prefProb)) prefProbStr= GUI_Utils.decimalFormat.format(prefProb);
   else prefProbStr = ""+NOT_AVAILABLE;

   text+=  "Min =&nbsp;&nbsp;"+minXStr+"  ["+minProbStr+"]<br>";
   text+=  "Pref =&nbsp;&nbsp;"+prefXStr+"  ["+prefProbStr+"]<br>";
   text+=  "Max =&nbsp;&nbsp;"+maxXStr+"  ["+maxProbStr+"]<br>";
   text+=  "<br> Numbers in brackets are probabilities that "+xAxisName+" is � each value.<br>";

   return text;
 }


}
