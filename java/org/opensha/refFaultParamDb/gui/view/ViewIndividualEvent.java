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

import javax.swing.JPanel;

import org.opensha.commons.data.estimate.Estimate;
import org.opensha.commons.data.estimate.LogNormalEstimate;
import org.opensha.commons.data.estimate.NormalEstimate;
import org.opensha.commons.gui.LabeledBoxPanel;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ConstrainedStringParameterEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.refFaultParamDb.dao.db.DB_AccessAPI;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.PaleoEventDB_DAO;
import org.opensha.refFaultParamDb.data.TimeAPI;
import org.opensha.refFaultParamDb.data.TimeEstimate;
import org.opensha.refFaultParamDb.gui.infotools.GUI_Utils;
import org.opensha.refFaultParamDb.gui.infotools.InfoLabel;
import org.opensha.refFaultParamDb.vo.EstimateInstances;
import org.opensha.refFaultParamDb.vo.PaleoEvent;
import org.opensha.refFaultParamDb.vo.PaleoSite;
import org.opensha.refFaultParamDb.vo.Reference;

/**
 * <p>Title: AddEditIndividualEvent.java </p>
 * <p>Description: This GUI allows to view an event information: Event name,
 * event date estimate, slip estimate, whether diplacement shared with other events, references, comments </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class ViewIndividualEvent extends LabeledBoxPanel implements ParameterChangeListener {

	// various parameter names
	private final static String EVENT_NAME_PARAM_NAME = "Event Name";
	private final static String COMMENTS_PARAM_NAME = "Comments";
	private final static String REFERENCES_PARAM_NAME = "References";
	private final static String TIME_ESTIMATE_PARAM_NAME = "Event Time Estimate";
	private final static String SLIP_ESTIMATE_PARAM_NAME = "Event Slip Estimate";
	private final static String DISPLACEMENT_SHARED_PARAM_NAME = "Slip Shared With Other Events";
	private final static String SHARED_EVENT_PARAM_NAME = "Names of Events Sharing Slip";
	private final static String TITLE = "Individual Events";
	private final static String TEST_EVENT1 = "Test Event 1";
	private final static String TEST_EVENT2 = "Test Event 2";
	private final static String SHARED = "Shared";
	private final static String NOT_SHARED = "Not Shared";
	private final static String SLIP = "Slip";
	private final static String PROB = "Prob this is correct value";
	private final static String SENSE_OF_MOTION_TITLE="Sense of Motion";
	private final static String MEASURED_COMP_SLIP_TITLE = "Measured Component of Slip";
	private final static String DISPLACEMENT = "Displacement";
	private final static String RAKE = "Rake";
	private final static String QUALITATIVE = "Qualitative";

	// information displayed for selected event
	private StringParameter eventNameParam;
	private InfoLabel commentsLabel = new InfoLabel();
	private InfoLabel timeEstLabel = new InfoLabel();
	private InfoLabel slipEstLabel = new InfoLabel();
	private InfoLabel displacementSharedLabel = new InfoLabel();
	private InfoLabel sharedEventLabel = new InfoLabel();
	private InfoLabel referencesLabel = new InfoLabel();
	private InfoLabel senseOfMotionRakeLabel = new InfoLabel();
	private InfoLabel senseOfMotionQualLabel = new InfoLabel();
	private InfoLabel measuredCompQualLabel = new InfoLabel();

	// various parameter editors
	private ConstrainedStringParameterEditor eventNameParamEditor;
	// site name
	private PaleoSite paleoSite=null;
	private PaleoEventDB_DAO paleoEventDAO;
	private ArrayList paleoEventsList;
	private ArrayList eventNamesList;

	public ViewIndividualEvent(DB_AccessAPI dbConnection) {
		paleoEventDAO = new PaleoEventDB_DAO(dbConnection);
		try {
			this.setLayout(GUI_Utils.gridBagLayout);
			// add Parameters and editors
			createEventListParameterEditor();
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
	private void createEventListParameterEditor()  {

		// event name parameter
		if(this.eventNameParamEditor!=null) this.remove(eventNameParamEditor);

		ArrayList eventNamesList = getEventNamesList();
		eventNameParam = new StringParameter(this.EVENT_NAME_PARAM_NAME, eventNamesList,
				(String)eventNamesList.get(0));
		eventNameParam.addParameterChangeListener(this);
		eventNameParamEditor = new ConstrainedStringParameterEditor(eventNameParam);
		add(eventNameParamEditor ,  new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
				,GridBagConstraints.NORTH, GridBagConstraints.HORIZONTAL, new Insets(2, 2, 2, 2), 0, 0));
		eventNameParamEditor.refreshParamEditor();
		this.updateUI();

		// set event info according to selected event
		this.setEventInfo((String)eventNameParam.getValue());
	}





	/**
	 * Get a list of all the event names
	 * @return
	 */
	private ArrayList getEventNamesList() {
		paleoEventsList = null;
		eventNamesList = new ArrayList();
		if(isTestSite()) {
			eventNamesList.add(TEST_EVENT1);
			eventNamesList.add(TEST_EVENT2);
		} else {
			paleoEventsList=paleoEventDAO.getAllEvents(paleoSite.getSiteId());
			if(paleoEventsList==null || paleoEventsList.size()==0) // if no event exists for this site
				eventNamesList.add(InfoLabel.NOT_AVAILABLE);
			else {
				// make a list of event names
				for(int i=0; i<paleoEventsList.size(); ++i)
					eventNamesList.add(((PaleoEvent)paleoEventsList.get(i)).getEventName());
			}
		}
		return eventNamesList;
	}

	/**
	 * If selected site is a test site
	 *
	 * @return
	 */
	private boolean isTestSite() {
		return paleoSite==null || paleoSite.getSiteName().equalsIgnoreCase(ViewSiteCharacteristics.TEST_SITE);
	}

	/**
	 * Add all the event information to theGUI
	 */
	private void addEditorstoGUI() {
		int yPos=1;
		JPanel senseOfMotionPanel = GUI_Utils.getPanel(this.SENSE_OF_MOTION_TITLE);
		JPanel measuredSlipCompPanel = GUI_Utils.getPanel(this.MEASURED_COMP_SLIP_TITLE);

		// sense of motion panel
		senseOfMotionPanel.add(this.senseOfMotionRakeLabel, new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.BOTH,
				new Insets(0, 0, 0, 0), 0, 0));
		senseOfMotionPanel.add(this.senseOfMotionQualLabel, new GridBagConstraints(0, 1, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.BOTH,
				new Insets(0, 0, 0, 0), 0, 0));
		// measured component of slip panel
		measuredSlipCompPanel.add(this.measuredCompQualLabel, new GridBagConstraints(0, 1, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER, GridBagConstraints.BOTH,
				new Insets(0, 0, 0, 0), 0, 0));

		add(GUI_Utils.getPanel(timeEstLabel,TIME_ESTIMATE_PARAM_NAME) ,  new GridBagConstraints(0, yPos++, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(2, 2, 2, 2), 0, 0));
		add(GUI_Utils.getPanel(slipEstLabel,SLIP_ESTIMATE_PARAM_NAME) ,  new GridBagConstraints(0, yPos++, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(2, 2, 2, 2), 0, 0));
		add(GUI_Utils.getPanel(displacementSharedLabel,DISPLACEMENT_SHARED_PARAM_NAME) ,  new GridBagConstraints(0, yPos++, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(2, 2, 2, 2), 0, 0));
		add(GUI_Utils.getPanel(sharedEventLabel,SHARED_EVENT_PARAM_NAME) ,  new GridBagConstraints(0, yPos++, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(2, 2, 2, 2), 0, 0));
		add(GUI_Utils.getPanel(commentsLabel,COMMENTS_PARAM_NAME) ,  new GridBagConstraints(0, yPos++, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(2, 2, 2, 2), 0, 0));
		add(GUI_Utils.getPanel(referencesLabel,REFERENCES_PARAM_NAME) ,  new GridBagConstraints(0, yPos++, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(2, 2, 2, 2), 0, 0));
		add(measuredSlipCompPanel ,  new GridBagConstraints(0, yPos++, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(2, 2, 2, 2), 0, 0));
		add(senseOfMotionPanel ,  new GridBagConstraints(0, yPos++, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(2, 2, 2, 2), 0, 0));


	}


	/**
	 * This function is called whenever a paramter is changed and we have
	 * registered as listeners to that parameters
	 *
	 * @param event
	 */
	public void parameterChange(ParameterChangeEvent event) {
		this.setEventInfo((String)eventNameParam.getValue());
	}

	/**
	 * Set the site chosen by the user. Only show the events for the selected site.
	 * @param siteName
	 */
	public void setSite(PaleoSite paleoSite) {
		this.paleoSite = paleoSite;
		createEventListParameterEditor();
	}

	/**
	 * Show the info according to event selected by the user
	 *
	 * @param eventName
	 */
	private void setEventInfo(String eventName) {
		// just set some fake implementation right now
		// event time estimate
		if(this.isTestSite() && (eventName.equalsIgnoreCase(this.TEST_EVENT1) ||
				eventName.equalsIgnoreCase(this.TEST_EVENT2))) {
			TimeEstimate startTime = new TimeEstimate();
			startTime.setForKaUnits(new NormalEstimate(1000, 50), 1950);
			// comments
			String comments = "Comments about this event";
			// references
			ArrayList references = new ArrayList();
			references.add("Ref 4");
			references.add("Ref 1");
			// Slip Rate Estimate
			LogNormalEstimate slipRateEstimate = new LogNormalEstimate(1.5, 0.25);
			// displacement is shared or not
			String displacement = "Shared";
			// events with which displacement is shared
			ArrayList eventsList = new ArrayList();
			eventsList.add("Event 10");
			eventsList.add("Event 11");
			updateLabels(startTime, slipRateEstimate, comments, references,
					displacement,
					eventsList, null, null, null);
		}else if(this.paleoEventsList!=null && this.paleoEventsList.size()!=0) {
			int index  = this.eventNamesList.indexOf(eventName);
			PaleoEvent paleoEvent = (PaleoEvent)paleoEventsList.get(index);
			ArrayList sharingEventNames = this.paleoEventDAO.getEventNamesForDisplacement(paleoEvent.getDisplacementEstId());
			String displacement = this.NOT_SHARED;
			if(sharingEventNames!=null && sharingEventNames.size()>0)
				displacement = SHARED;
			else   sharingEventNames = null;
			ArrayList refList =  paleoEvent.getReferenceList();
			ArrayList summaryList = new ArrayList();
			for(int i=0 ; i<refList.size(); ++i)
				summaryList.add(((Reference)refList.get(i)).getSummary());
			updateLabels(paleoEvent.getEventTime(), paleoEvent.getDisplacementEst().getEstimate(),
					paleoEvent.getComments(), summaryList,
					displacement,sharingEventNames, paleoEvent.getSenseOfMotionRake(),
					paleoEvent.getSenseOfMotionQual(),
					paleoEvent.getMeasuredComponentQual());

		} else {
			updateLabels(null, null, null, null,
					null,
					null, null, null,  null);
		}
	}

	/**
	 * Update the labels to view information about the events
	 * @param eventTime
	 * @param slipEstimate
	 * @param comments
	 * @param references
	 * @param displacement
	 * @param sharingEvents
	 */
	private void updateLabels(TimeAPI eventTime, Estimate slipEstimate, String comments,
			ArrayList references, String displacement, ArrayList sharingEvents,
			EstimateInstances rakeForSenseOfMotion, String senseOfMotionQual,
			String measuredSlipQual) {
		commentsLabel.setTextAsHTML(comments);
		timeEstLabel.setTextAsHTML(eventTime);
		slipEstLabel.setTextAsHTML(slipEstimate, SLIP, PROB);
		displacementSharedLabel.setTextAsHTML(displacement);
		sharedEventLabel.setTextAsHTML(sharingEvents);
		referencesLabel.setTextAsHTML(references);
		this.measuredCompQualLabel.setTextAsHTML(this.QUALITATIVE, measuredSlipQual);
		Estimate rakeEst = null;
		if(rakeForSenseOfMotion!=null) rakeEst = rakeForSenseOfMotion.getEstimate();
		this.senseOfMotionRakeLabel.setTextAsHTML(rakeEst, RAKE, PROB);

		this.senseOfMotionQualLabel.setTextAsHTML(this.QUALITATIVE, senseOfMotionQual);


	}

}
