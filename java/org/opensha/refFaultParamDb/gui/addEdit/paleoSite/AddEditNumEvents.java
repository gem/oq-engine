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

package org.opensha.refFaultParamDb.gui.addEdit.paleoSite;

import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.Insets;

import javax.swing.JOptionPane;

import org.opensha.commons.data.estimate.IntegerEstimate;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFunc;
import org.opensha.commons.gui.LabeledBoxPanel;
import org.opensha.commons.param.ArbitrarilyDiscretizedFuncParameter;
import org.opensha.commons.param.IntegerParameter;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ArbitrarilyDiscretizedFuncParameterEditor;
import org.opensha.commons.param.editor.IntegerParameterEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.refFaultParamDb.gui.CommentsParameterEditor;
import org.opensha.refFaultParamDb.gui.infotools.GUI_Utils;
import org.opensha.refFaultParamDb.vo.CombinedNumEventsInfo;
import org.opensha.refFaultParamDb.vo.EstimateInstances;

/**
 * <p>Title: AddEditNumEvents.java </p>
 * <p>Description: </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class AddEditNumEvents extends LabeledBoxPanel implements ParameterChangeListener {
  // Number of events parameter
  private final static String NUM_EVENTS_PARAM_NAME="Number of Events";
  private final static String MIN_EVENTS_PARAM_NAME="Min # of Events";
  private final static String MAX_EVENTS_PARAM_NAME="Max # of Events";
  private final static String NUM_EVENTS_COMMENTS_PARAM_NAME="Comments";
  private final static String NUM_EVENTS_LIST_HEADER="# of Events";
  private final static String PROB_HEADER="Prob. this is correct # events";
  private final static String EVENT_PROB_PARAM_NAME= "Events Prob";
  private final static int NUM_EVENTS_MIN=0;
  private final static int NUM_EVENTS_MAX=Integer.MAX_VALUE;
  public final static String NUM_EVENTS_UNITS=" ";


  // various parameters
  private IntegerParameter minEventsParam;
  private IntegerParameter maxEventsParam;
  private StringParameter numEventsCommentsParam;
  private ArbitrarilyDiscretizedFuncParameter eventsProbParameter;

  // parameter editors
  private IntegerParameterEditor minEventsParamEditor;
  private IntegerParameterEditor maxEventsParamEditor;
  private CommentsParameterEditor numEventsCommentsParamEditor;
  private ArbitrarilyDiscretizedFuncParameterEditor eventsProbParameterEditor;

  private ArbitrarilyDiscretizedFunc eventProbs = new ArbitrarilyDiscretizedFunc();
  private final static String NUM_EVENTS_PARAMS_TITLE = "Num Events Params";

  public AddEditNumEvents() {
    try {
       this.setLayout(GUI_Utils.gridBagLayout);
       addNumEventsParameters();
       this.setMinimumSize(new Dimension(0, 0));
    }catch(Exception e) {
      e.printStackTrace();
    }
  }

  /**
   * set the values in the editor
   * @param combinedNumEventsInfo
   */
  public AddEditNumEvents(CombinedNumEventsInfo combinedNumEventsInfo) {
    this();
    if(combinedNumEventsInfo!=null) {
      minEventsParam.removeParameterChangeListener(this);
      setParameterValues(combinedNumEventsInfo);
      minEventsParam.addParameterChangeListener(this);
    }
  }


  private void setParameterValues(CombinedNumEventsInfo combinedNumEventsInfo) {
    // num events comments
    numEventsCommentsParam.setValue(combinedNumEventsInfo.getNumEventsComments());
    numEventsCommentsParamEditor.refreshParamEditor();
    // num events estimate
    IntegerEstimate estimate  = (IntegerEstimate)combinedNumEventsInfo.getNumEventsEstimate().getEstimate();
    DiscretizedFunc func = estimate.getValues();
    // min events param
    minEventsParam.setValue(new Integer((int)func.getMinX()));
    minEventsParamEditor.refreshParamEditor();
    // max events param
    maxEventsParam.setValue(new Integer((int)func.getMaxX()));
    maxEventsParamEditor.refreshParamEditor();
    // events probabilities
    eventsProbParameter.setValue((ArbitrarilyDiscretizedFunc)func);
    eventsProbParameterEditor.refreshParamEditor();

  }




  /**
  * Add the input parameters if user provides the events
  */
 private void addNumEventsParameters() throws Exception {

   // min number of events
   minEventsParam = new IntegerParameter(this.MIN_EVENTS_PARAM_NAME, NUM_EVENTS_MIN, NUM_EVENTS_MAX);
   minEventsParam.addParameterChangeListener(this);
   minEventsParamEditor = new IntegerParameterEditor(minEventsParam);
   // max number of events
   maxEventsParam = new IntegerParameter(this.MAX_EVENTS_PARAM_NAME, NUM_EVENTS_MIN, NUM_EVENTS_MAX);
   maxEventsParam.addParameterChangeListener(this);
   maxEventsParamEditor = new IntegerParameterEditor(maxEventsParam);

   // parameter to show events list
   eventProbs.setXAxisName(this.NUM_EVENTS_LIST_HEADER);
   eventProbs.setYAxisName(this.PROB_HEADER);
   eventsProbParameter = new ArbitrarilyDiscretizedFuncParameter(EVENT_PROB_PARAM_NAME,eventProbs);
   eventsProbParameterEditor = new ArbitrarilyDiscretizedFuncParameterEditor(eventsProbParameter);
   eventsProbParameterEditor.setXEnabled(false); // user cannot type in the X values

   // comments
   numEventsCommentsParam = new StringParameter(this.NUM_EVENTS_COMMENTS_PARAM_NAME);
   numEventsCommentsParamEditor = new CommentsParameterEditor(numEventsCommentsParam);

   // Add the editors to the panel
   int yPos=0;
   add(minEventsParamEditor, new GridBagConstraints( 0, yPos++, 1, 1, 1.0, 1.0
       ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ));
   add(maxEventsParamEditor, new GridBagConstraints( 0, yPos++, 1, 1, 1.0, 1.0
       ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ));
   add(eventsProbParameterEditor, new GridBagConstraints( 0, yPos++, 1, 1, 1.0, 1.0
       ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ));
   add(numEventsCommentsParamEditor, new GridBagConstraints( 0, yPos++, 1, 1, 1.0, 1.0
       ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ));

   setTitle(this.NUM_EVENTS_PARAMS_TITLE);
 }


 /**
  *  This method is called whenever a min or max is changed so that num events list
  * is updated
  * @param event
  */
 public void parameterChange(ParameterChangeEvent event) {
   updateNumEventsList();
 }

 /**
  * Update the  num events list
  */
 private void updateNumEventsList() {
   Integer minVal = (Integer)minEventsParam.getValue();
   if(minVal==null) {
     JOptionPane.showMessageDialog(this, minEventsParam.getName() + " is missing");
     return;
   }
   int min = minVal.intValue();
   Integer maxVal = (Integer)maxEventsParam.getValue();
   if(maxVal==null) {
    JOptionPane.showMessageDialog(this, maxEventsParam.getName() + " is missing");
    return;
  }
   int max = maxVal.intValue();
   String text="";
   eventProbs.clear();
   for(int i=min; i<=max; ++i) {
     eventProbs.set((double)i,0.0);
   }
   eventsProbParameter.setValue(eventProbs);
   eventsProbParameterEditor.refreshParamEditor();
  }


  public CombinedNumEventsInfo getCombinedNumEventsInfo(){
    CombinedNumEventsInfo combinedNumEventsInfo = new CombinedNumEventsInfo();
    combinedNumEventsInfo.setNumEventsComments(getNumEventsComments());
    combinedNumEventsInfo.setNumEventsEstimate(getNumEventsEstimate());
    return combinedNumEventsInfo;
  }
  /**
   * Get the comments for num events estimate
   *
   * @return
   */
  private String getNumEventsComments() {
    return (String)this.numEventsCommentsParam.getValue();
  }

  /**
   * Get the num events estimate
   *
   * @return
   */
  private EstimateInstances getNumEventsEstimate() {
     ArbitrarilyDiscretizedFunc eventProb = (ArbitrarilyDiscretizedFunc)this.eventsProbParameter.getValue();
     IntegerEstimate numEventsEstimate = new IntegerEstimate(eventProb,true);
     return new EstimateInstances(numEventsEstimate, this.NUM_EVENTS_UNITS);
   }

}
