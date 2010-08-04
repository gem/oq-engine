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

package org.opensha.refFaultParamDb.gui.view;

import java.awt.GridBagConstraints;
import java.awt.Insets;
import java.util.ArrayList;

import org.opensha.commons.gui.LabeledBoxPanel;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ConstrainedStringParameterEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.refFaultParamDb.gui.addEdit.paleoSite.AddEditSequence;
import org.opensha.refFaultParamDb.gui.infotools.GUI_Utils;
import org.opensha.refFaultParamDb.gui.infotools.InfoLabel;
import org.opensha.refFaultParamDb.vo.EventSequence;
import org.opensha.refFaultParamDb.vo.PaleoEvent;

/**
 * <p>Title: ViewSequences.java </p>
 * <p>Description: This allows the user to view the event sequences for a selected
 * paleo site </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class ViewSequences extends LabeledBoxPanel implements ParameterChangeListener {

  // various parameter names
  private final static String SEQUENCE_NAME_PARAM_NAME = "Sequence Name";
  private final static String SEQUENCE_PROB_PARAM_NAME = "Prob this is correct sequence";
  private final static String COMMENTS_PARAM_NAME = "Comments";
  private final static String MISSED_EVENTS_PROB_PARAM_NAME = "Probability of missed events";
  private final static String EVENTS_PARAM_NAME = "Events in Sequence";
  private final static String TITLE = "Sequences";

  // labels to show the information
  private InfoLabel sequenceProbLabel = new InfoLabel();
  private InfoLabel eventsLabel = new InfoLabel();
  private InfoLabel missedProbLabel = new InfoLabel();
  private InfoLabel commentsLabel = new InfoLabel();

  // StringParameter and editor to show list of all sequences
  private StringParameter sequenceNameParam;
  private ConstrainedStringParameterEditor sequenceNamesEditor;

  // site for which seequences will be displayed
  private ArrayList sequenceNamesList;
  private ArrayList sequencesList;

  public ViewSequences() {
    try {
     this.setLayout(GUI_Utils.gridBagLayout);
     // add Parameters and editors
     createSequencesListParameterEditor();
     // add the parameter editors to the GUI componenets
     addEditorstoGUI();
     // set the title
     this.setTitle(TITLE);
   }
   catch(Exception e) {
     e.printStackTrace();
   }
  }

  /**
   * Intialize the parameters and editors and add to the GUI
   */
  private void createSequencesListParameterEditor()  {

    // event name parameter
     if(this.sequenceNamesEditor!=null) this.remove(sequenceNamesEditor);

    ArrayList sequenceNamesList = getSequenceNamesList();
    sequenceNameParam = new StringParameter(this.SEQUENCE_NAME_PARAM_NAME, sequenceNamesList,
                                         (String)sequenceNamesList.get(0));
    sequenceNameParam.addParameterChangeListener(this);
    sequenceNamesEditor = new ConstrainedStringParameterEditor(sequenceNameParam);
    add(sequenceNamesEditor ,  new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
        ,GridBagConstraints.NORTH, GridBagConstraints.HORIZONTAL, new Insets(2, 2, 2, 2), 0, 0));
    sequenceNamesEditor.refreshParamEditor();
    this.updateUI();

    // set event info according to selected event
    this.setSequenceInfo((String)sequenceNameParam.getValue());
  }

  /**
   *
   * @return
   */
  private ArrayList getSequenceNamesList() {
    this.sequenceNamesList = new ArrayList();

    if(sequencesList==null || sequencesList.size()==0) // if no event exists for this site
      sequenceNamesList.add(InfoLabel.NOT_AVAILABLE);
    else {
      // make a list of event names
      for(int i=0; i<sequencesList.size(); ++i)
        sequenceNamesList.add(((EventSequence)sequencesList.get(i)).getSequenceName());
    }
    return sequenceNamesList;
  }

  /**
  * Add all the event information to theGUI
  */
 private void addEditorstoGUI() {
   int yPos=1;
   add(GUI_Utils.getPanel(this.sequenceProbLabel,this.SEQUENCE_PROB_PARAM_NAME) ,  new GridBagConstraints(0, yPos++, 1, 1, 1.0, 1.0
       ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(2, 2, 2, 2), 0, 0));
   add(GUI_Utils.getPanel(this.eventsLabel,this.EVENTS_PARAM_NAME) ,  new GridBagConstraints(0, yPos++, 1, 1, 1.0, 1.0
       ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(2, 2, 2, 2), 0, 0));
   add(GUI_Utils.getPanel(missedProbLabel,this.MISSED_EVENTS_PROB_PARAM_NAME) ,  new GridBagConstraints(0, yPos++, 1, 1, 1.0, 1.0
       ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(2, 2, 2, 2), 0, 0));
   add(GUI_Utils.getPanel(commentsLabel,COMMENTS_PARAM_NAME) ,  new GridBagConstraints(0, yPos++, 1, 1, 1.0, 1.0
       ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(2, 2, 2, 2), 0, 0));
 }


  /**
   * This function is called whenever a parameter is changed and we have
   * registered as listeners to that parameters
   *
   * @param event
   */
  public void parameterChange(ParameterChangeEvent event) {
    this.setSequenceInfo((String)sequenceNameParam.getValue());
  }


  /**
   * Sitename for which sequences will be displayed
   *
   * @param siteName
   */
  public void setSequenceList(ArrayList sequenceList) {
    this.sequencesList = sequenceList;
    createSequencesListParameterEditor();
  }

  /**
  * Show the info according to event selected by the user
  *
  * @param eventName
  */
 private void setSequenceInfo(String sequenceName) {
   if(this.sequencesList!=null && this.sequencesList.size()!=0) {
      int index  = this.sequenceNamesList.indexOf(sequenceName);
      EventSequence eventSequence = (EventSequence)this.sequencesList.get(index);
      // make a list of event names from event list
      ArrayList paleoEventsList = eventSequence.getEventsParam();
      ArrayList eventNames = new ArrayList();
      for(int i=0; i<paleoEventsList.size(); ++i) {
        PaleoEvent paleoEvent = (PaleoEvent)paleoEventsList.get(i);
        eventNames.add(paleoEvent.getEventName());
      }
      updateLabels(eventSequence.getSequenceProb(), eventNames,
                   eventSequence.getMissedEventsProbs(), eventSequence.getComments());
   }
   else {
     updateLabels(Double.NaN, null, null, null);
   }
 }

 /**
  * Update the labels to view the information about the sequences
  * @param sequenceProb
  * @param eventsInthisSequence
  * @param missedEventProbs
  * @param comments
  * @param references
  */
 private void updateLabels(double sequenceProb, ArrayList eventsInthisSequence,
                           double[] missedEventProbs, String comments) {

   if(Double.isNaN(sequenceProb)) {
     sequenceProbLabel.setTextAsHTML((String)null);
   }
   else sequenceProbLabel.setTextAsHTML( GUI_Utils.decimalFormat.format(sequenceProb));
   ArrayList missedProbInfoList = null;
   if(eventsInthisSequence!=null ) {
     missedProbInfoList = new ArrayList();
     ArrayList names = AddEditSequence.getNamesForMissedEventProbs(
         eventsInthisSequence);
     for (int i = 0; i < names.size(); ++i)
       missedProbInfoList.add(names.get(i) + ": " +  GUI_Utils.decimalFormat.format(missedEventProbs[i]));
   }
   missedProbLabel.setTextAsHTML(missedProbInfoList);
   commentsLabel.setTextAsHTML(comments);
   eventsLabel.setTextAsHTML(eventsInthisSequence);
 }

}
