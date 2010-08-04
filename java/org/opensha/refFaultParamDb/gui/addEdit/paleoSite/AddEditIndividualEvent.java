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

import java.awt.BorderLayout;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;

import javax.swing.JButton;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JSplitPane;
import javax.swing.UIManager;

import org.opensha.commons.data.estimate.Estimate;
import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.gui.LabeledBoxPanel;
import org.opensha.commons.param.BooleanParameter;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.StringListParameter;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ConstrainedStringParameterEditor;
import org.opensha.commons.param.editor.ParameterListEditor;
import org.opensha.commons.param.editor.StringParameterEditor;
import org.opensha.commons.param.editor.estimate.ConstrainedEstimateParameterEditor;
import org.opensha.commons.param.estimate.EstimateConstraint;
import org.opensha.commons.param.estimate.EstimateParameter;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.refFaultParamDb.dao.db.DB_AccessAPI;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.PaleoEventDB_DAO;
import org.opensha.refFaultParamDb.dao.db.ReferenceDB_DAO;
import org.opensha.refFaultParamDb.dao.exception.InsertException;
import org.opensha.refFaultParamDb.data.TimeAPI;
import org.opensha.refFaultParamDb.gui.CommentsParameterEditor;
import org.opensha.refFaultParamDb.gui.TimeGuiBean;
import org.opensha.refFaultParamDb.gui.event.DbAdditionFrame;
import org.opensha.refFaultParamDb.gui.event.DbAdditionListener;
import org.opensha.refFaultParamDb.gui.event.DbAdditionSuccessEvent;
import org.opensha.refFaultParamDb.gui.infotools.ConnectToEmailServlet;
import org.opensha.refFaultParamDb.gui.infotools.SessionInfo;
import org.opensha.refFaultParamDb.gui.view.ViewAllReferences;
import org.opensha.refFaultParamDb.vo.EstimateInstances;
import org.opensha.refFaultParamDb.vo.PaleoEvent;
import org.opensha.refFaultParamDb.vo.Reference;

/**
 * <p>Title: AddEditIndividualEvent.java </p>
 * <p>Description: This GUI allows to add an event information: Event name,
 * event date estimate, slip estimate, whether diplacement shared with other events, references, comments </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class AddEditIndividualEvent extends DbAdditionFrame implements ParameterChangeListener,
ActionListener, DbAdditionListener {
	private JPanel topPanel = new JPanel();
	private JSplitPane estimatesSplitPane = new JSplitPane();
	private JSplitPane mainSplitPane = new JSplitPane();
	private JSplitPane detailedEventInfoSplitPane = new JSplitPane();
	private JButton okButton = new JButton("Submit and Add Another Event");
	private JButton doneButton = new JButton("Done");
	private JButton cancelButton = new JButton("Cancel");
	private JPanel eventSummaryPanel = new JPanel();
	private GridBagLayout gridBagLayout1 = new GridBagLayout();
	private GridBagLayout gridBagLayout2 = new GridBagLayout();
	private BorderLayout borderLayout1 = new BorderLayout();

	// various parameter names
	private final static String EVENT_NAME_PARAM_NAME = "Event Name";
	private final static String EVENT_NAME_PARAM_DEFAULT = "Enter Event Name";
	private final static String COMMENTS_PARAM_NAME = "Comments";
	private final static String REFERENCES_PARAM_NAME = "Choose References";
	private final static String DATE_ESTIMATE_PARAM_NAME = "Event Time Estimate";
	private final static String SLIP_ESTIMATE_PARAM_NAME = "Event Slip Estimate";
	private final static String SLIP_TITLE = "Event Slip";
	private final static String SLIP = "Slip";
	private final static String DISPLACEMENT_SHARED_PARAM_NAME = "Slip Shared With Other Events";
	private final static String SHARED_EVENT_PARAM_NAME = "Names of Events Sharing Slip";
	private final static String COMMENTS_REFERENCES_TITLE="Comments & References";

	//date estimate related constants
	private final static double TIME_ESTIMATE_MIN=0;
	private final static double TIME_ESTIMATE_MAX=Double.POSITIVE_INFINITY;
	private final static String TIME_ESTIMATE_UNITS="years";

	// add new reference button
	private JButton addNewReferenceButton = new JButton("Add Reference");
	private JButton viewAllRefsButton = new JButton("View All References");
	private final static String addNewReferenceToolTipText = "Add Reference not currently in database";
	private final static String MSG_EVENT_NAME_MISSING = "Please enter event name";
	private final static String MSG_REFERENCE_MISSING = "Choose atleast 1 reference";
	private final static String MSG_SHARED_EVENTS_MISSING = "Choose atleast 1 event to share the displacement";
	private final static String MSG_EVENTS_DO_NOT_SHARE_DISPLACEMENT=
		"The selected event set for shared displacement is invalid.\nThese events do not share same displacement";
	private final static String MSG_PALEO_EVENT_ADD_SUCCESS = "Paleo Event added successfully to the database";
	private final static String MSG_NEED_TO_SAVE_CURR_EVENT = "Do you want to save current event to database?";
	private final static String MSG_CURR_EVENT_NOT_SAVED = "Current Event will not be saved in database";
	private final static String MSG_CONTACT_TO_DELETE = "events were added to database in this session. Contact perry@gps.caltech.edu to remove them";

	//slip rate constants
	private final static String SLIP_UNITS = "meters";
	private final static double SLIP_MIN = 0;
	private final static double SLIP_MAX = Double.POSITIVE_INFINITY;

	// diplacement parameter list editor title
	private final static String DISPLACEMENT_TITLE = "Shared Slip";
	private final static String TITLE = "Add Data, Individual Event(s)";

	// various parameter types
	private StringParameter eventNameParam;
	private StringParameter commentsParam;
	private TimeGuiBean eventTimeEst = new TimeGuiBean(DATE_ESTIMATE_PARAM_NAME, false);
	private EstimateParameter slipEstParam;
	private BooleanParameter displacementSharedParam;
	private StringListParameter sharedEventParam;
	private StringParameter referencesParam;

	// various parameter editors
	private StringParameterEditor eventNameParamEditor;
	private CommentsParameterEditor commentsParamEditor;
	private ConstrainedEstimateParameterEditor slipEstParamEditor;
	private ParameterListEditor displacementParamListEditor;
	private ConstrainedStringParameterEditor referencesParamEditor;


	private final static int WIDTH = 700;
	private final static int HEIGHT = 700;

	// references DAO
	private ReferenceDB_DAO referenceDAO;
	// paleo event DAO
	private PaleoEventDB_DAO paleoEventDAO;
	private ArrayList paleoEvents; // saves a list of all paleo events for this site
	private int siteId; // site id for which this paleo event will be added
	private String siteEntryDate; // site entry dat for which paleo event is to be added
	private AddNewReference addNewReference;
	private LabeledBoxPanel commentsReferencesPanel;
	private  ArrayList referenceSummaryList;
	private  ArrayList referenceList;
	private SenseOfMotionPanel senseOfMotionPanel;
	private MeasuredCompPanel measuredCompPanel;
	private static int eventToDatabaseCounter=0;
	
	private DB_AccessAPI dbConnection;

	public AddEditIndividualEvent(DB_AccessAPI dbConnection, int siteId, String siteEntryDate) {
		this.dbConnection = dbConnection;
		referenceDAO = new ReferenceDB_DAO(dbConnection);
		paleoEventDAO = new PaleoEventDB_DAO(dbConnection);
		try {
			senseOfMotionPanel = new SenseOfMotionPanel();
			measuredCompPanel = new MeasuredCompPanel();
			this.siteId = siteId;
			this.siteEntryDate = siteEntryDate;
			// initialize the GUI
			jbInit();
			// add Parameters and editors
			initParamsAndEditors();
			// add the action listeners to the button
			addActionListeners();
			// set the title
			this.setTitle(TITLE);
			// Show/Hide the editor to enter the name of event with which dispalcement is shared
			setSharedEventVisible(((Boolean)this.displacementSharedParam.getValue()).booleanValue());
			setSize(WIDTH, HEIGHT);
			this.setLocationRelativeTo(null);
			this.setVisible(true);
		}
		catch(Exception e) {
			e.printStackTrace();
		}
	}

	/**
	 * Intialize the parameters and editors and add to the GUI
	 */
	private void initParamsAndEditors() throws Exception {

		// event name parameter
		eventNameParam = new StringParameter(this.EVENT_NAME_PARAM_NAME, EVENT_NAME_PARAM_DEFAULT);
		eventNameParamEditor = new StringParameterEditor(eventNameParam);

		// comments param
		commentsParam = new StringParameter(this.COMMENTS_PARAM_NAME);
		commentsParamEditor = new CommentsParameterEditor(commentsParam);

		// date param
		ArrayList dateAllowedEstList = EstimateConstraint.createConstraintForDateEstimates();

		// slip rate param
		ArrayList allowedEstimates = EstimateConstraint.createConstraintForPositiveDoubleValues();
		this.slipEstParam = new EstimateParameter(this.SLIP_ESTIMATE_PARAM_NAME,
				SLIP_UNITS, SLIP_MIN, SLIP_MAX, allowedEstimates);
		slipEstParamEditor = new ConstrainedEstimateParameterEditor(slipEstParam, true);

		// whether displacement is shared with other events
		this.displacementSharedParam = new BooleanParameter(this.DISPLACEMENT_SHARED_PARAM_NAME, new Boolean(false));
		displacementSharedParam.addParameterChangeListener(this);
		ParameterList paramList  = new ParameterList();
		paramList.addParameter(displacementSharedParam);

		// event name parameter with which dispalcement is shared(only if displacement is shared)
		ArrayList eventNamesList = getEventNamesList();
		if(eventNamesList!=null && eventNamesList.size()>0) {
			this.sharedEventParam = new StringListParameter(SHARED_EVENT_PARAM_NAME,
					eventNamesList);
			paramList.addParameter(sharedEventParam);
		}
		displacementParamListEditor = new ParameterListEditor(paramList);
		displacementParamListEditor.setTitle(DISPLACEMENT_TITLE);

		// add the parameter editors to the GUI componenets
		addEditorstoGUI();

		makeReferencesParamAndEditor();
	}

	private void makeReferencesParamAndEditor() throws ConstraintException {
		if(referencesParamEditor!=null) commentsReferencesPanel.remove(referencesParamEditor);
		// references param
		ArrayList referenceList = this.getAvailableReferences();
		referencesParam = new StringParameter(this.REFERENCES_PARAM_NAME, referenceList,
				(String)referenceList.get(0));
		referencesParamEditor = new ConstrainedStringParameterEditor(referencesParam);
		commentsReferencesPanel.add(this.referencesParamEditor,  new GridBagConstraints(0, 1, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(2, 2, 2, 2), 0, 0));
	}


	/**
	 * Get a list of available references.
	 * @return
	 */
	private ArrayList getAvailableReferences() {
		//if(referenceSummaryList==null) {
		this.referenceList = referenceDAO.getAllReferencesSummary();
		this.referenceSummaryList = new ArrayList();
		for (int i = 0; referenceList != null && i < referenceList.size(); ++i)
			referenceSummaryList.add( ( (Reference) referenceList.get(i)).
					getSummary());
		//}

		return referenceSummaryList;
	}


	/**
	 * Get a list of all the event names
	 * @return
	 */
	private ArrayList getEventNamesList() {
		paleoEvents = paleoEventDAO.getAllEvents(siteId);
		ArrayList eventNames = new ArrayList();
		for(int i=0; i<paleoEvents.size(); ++i) {
			eventNames.add(((PaleoEvent)paleoEvents.get(i)).getEventName());
		}
		return eventNames;
	}

	/**
	 * Add the parameter editors to the GUI
	 */
	private void addEditorstoGUI() {

		// event time estimate
		this.estimatesSplitPane.add(eventTimeEst, JSplitPane.LEFT);

		// event slip and whether slip is shared
		LabeledBoxPanel slipPanel = new LabeledBoxPanel(gridBagLayout1);
		slipPanel.setTitle(SLIP_TITLE);
		slipPanel.add(displacementParamListEditor,  new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(2, 2, 2, 2), 0, 0));
		slipPanel.add(this.measuredCompPanel,
				new GridBagConstraints(0, 1, 1, 1, 1.0, 1.0
						, GridBagConstraints.CENTER,
						GridBagConstraints.BOTH,
						new Insets(0, 0, 0, 0), 0, 0));
		slipPanel.add(slipEstParamEditor,  new GridBagConstraints(0, 2, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(2, 2, 2, 2), 0, 0));
		slipPanel.add(senseOfMotionPanel,
				new GridBagConstraints(0, 3, 1, 1, 1.0, 1.0
						, GridBagConstraints.CENTER,
						GridBagConstraints.BOTH,
						new Insets(0, 0, 0, 0), 0, 0));
		estimatesSplitPane.add(slipPanel, JSplitPane.RIGHT);
		// comments and references
		commentsReferencesPanel = new LabeledBoxPanel(gridBagLayout1);
		commentsReferencesPanel.setTitle(COMMENTS_REFERENCES_TITLE);
		this.detailedEventInfoSplitPane.add(commentsReferencesPanel, JSplitPane.RIGHT);
		commentsReferencesPanel.add(this.commentsParamEditor,  new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(2, 2, 2, 2), 0, 0));
		commentsReferencesPanel.add(this.addNewReferenceButton,  new GridBagConstraints(0, 2, 1, 1, 1.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(2, 2, 2, 2), 0, 0));
		commentsReferencesPanel.add(this.viewAllRefsButton,  new GridBagConstraints(0, 3, 1, 1, 1.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(2, 2, 2, 2), 0, 0));
		// event name
		eventSummaryPanel.add(eventNameParamEditor,  new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(2, 2, 2, 2), 0, 0));
	}


	/**
	 * This function is called whenever a paramter is changed and we have
	 * registered as listeners to that parameters
	 *
	 * @param event
	 */
	public void parameterChange(ParameterChangeEvent event) {
		if(event.getParameterName().equalsIgnoreCase(this.DISPLACEMENT_SHARED_PARAM_NAME))
			setSharedEventVisible(((Boolean)event.getNewValue()).booleanValue());
	}

	/**
	 * Show/Hide the editor to enter the name of event with which dispalcement is shared
	 *
	 * @param isVisible
	 */
	private void setSharedEventVisible(boolean isVisible) {
		if(this.paleoEvents!=null && paleoEvents.size()>0) {
			this.displacementParamListEditor.setParameterVisible(this.
					SHARED_EVENT_PARAM_NAME, isVisible);
			this.slipEstParamEditor.setVisible(!isVisible);
			senseOfMotionPanel.setVisible(!isVisible);
			this.measuredCompPanel.setVisible(!isVisible);
		}
		else {
			this.displacementParamListEditor.setVisible(false);
			this.slipEstParamEditor.setVisible(true);
			this.senseOfMotionPanel.setVisible(true);
			this.measuredCompPanel.setVisible(true);
		}
	}

	/**
	 * This function is called when a button is clicked on this screen
	 *
	 * @param event
	 */
	public void actionPerformed(ActionEvent event) {
		Object source = event.getSource() ;
		if(source == addNewReferenceButton)  {
			addNewReference  = new AddNewReference(dbConnection);
			addNewReference.addDbAdditionSuccessListener(this);
		}
		else if(source == okButton) {
			try {
				addEventToDatabase();
				++eventToDatabaseCounter;
			}catch(InsertException e) {
				JOptionPane.showMessageDialog(this, e.getMessage());
			}
		}
		else if(source == doneButton) { // close the window
			int option = JOptionPane.showConfirmDialog(this,MSG_NEED_TO_SAVE_CURR_EVENT);
			if(option==JOptionPane.OK_OPTION) {// ask user whether current event need to be saved to DB
				try {
					addEventToDatabase();
					eventToDatabaseCounter=0;
					this.dispose();
				}
				catch (InsertException e) {
					JOptionPane.showMessageDialog(this, e.getMessage());
				}
			}else if(option == JOptionPane.NO_OPTION) {
				this.dispose();
			}
		} else if(source==cancelButton) {
			// if cancel button is pressed, inform the user that current event will not be
			// saved in database. If there were previously added events, give them contact
			// details to delete the events.
			String msg = MSG_CURR_EVENT_NOT_SAVED;
			if(this.eventToDatabaseCounter>0) {
				msg = msg+"\n"+eventToDatabaseCounter+" "+this.MSG_CONTACT_TO_DELETE;
			}
			JOptionPane.showMessageDialog(this, msg);
			eventToDatabaseCounter=0;
			this.dispose();
		}
		else if(source == viewAllRefsButton) new ViewAllReferences(dbConnection);
	}

	/**
	 * Add event to the database
	 */
	private void addEventToDatabase() {
		PaleoEvent paleoEvent = new PaleoEvent();
		// make sure that user entered event name
		String eventName = (String)this.eventNameParam.getValue();
		if(eventName.trim().equalsIgnoreCase("") ||
				eventName.trim().equalsIgnoreCase(this.EVENT_NAME_PARAM_DEFAULT)) {
			throw new InsertException(MSG_EVENT_NAME_MISSING);
		}
		paleoEvent.setEventName(eventName);
		// make sure that user choose a reference
		String reference = (String)this.referencesParam.getValue();
		if(reference==null) {
			throw new InsertException(MSG_REFERENCE_MISSING);
		}
		int index = this.referenceSummaryList.indexOf(reference);
		ArrayList referenceList = new ArrayList();
		referenceList.add(this.referenceList.get(index));
		paleoEvent.setReferenceList(referenceList);

		// if displacement is shared, make sure that user selects atleast 1 event
		boolean isDispShared = ((Boolean)this.displacementSharedParam.getValue()).booleanValue();
		ArrayList sharedEventNames=null;
		paleoEvent.setDisplacementShared(isDispShared);
		if(isDispShared) {
			sharedEventNames = (ArrayList)this.sharedEventParam.getValue();
			if(sharedEventNames==null || sharedEventNames.size()==0) {
				throw new InsertException(MSG_SHARED_EVENTS_MISSING);
			} // now check that user has selected valid events to share displacement
			else{
				int dispEstId = paleoEventDAO.checkSameDisplacement(sharedEventNames);
				if(dispEstId<=0) {
					throw new InsertException(MSG_EVENTS_DO_NOT_SHARE_DISPLACEMENT);
				} else paleoEvent.setDisplacementEstId(dispEstId);
			}
		} else { // if displacement is not shared, set displacement estimate in the paleo-event
			try {
				this.slipEstParamEditor.setEstimateInParameter();
			}catch(RuntimeException e) {
				throw new InsertException(e.getMessage());
			}
			paleoEvent.setDisplacementEst(
					new EstimateInstances((Estimate)this.slipEstParam.getValue(), this.SLIP_UNITS));
		}
		// set other properties of the paleo event
		paleoEvent.setComments((String)this.commentsParam.getValue());
		paleoEvent.setSiteId(this.siteId);
		paleoEvent.setSiteEntryDate(this.siteEntryDate);
		TimeAPI eventTime=null;
		try {
			eventTime = this.eventTimeEst.getSelectedTime();
		}catch(RuntimeException e) {
			throw new InsertException( e.getMessage());
		}
		eventTime.setDatingComments(paleoEvent.getComments());
		eventTime.setReferencesList(paleoEvent.getReferenceList());
		paleoEvent.setEventTime(eventTime);
		paleoEvent.setMeasuredComponentQual(this.measuredCompPanel.getMeasuredComp());
		paleoEvent.setSenseOfMotionQual(senseOfMotionPanel.getSenseOfMotionQual());
		paleoEvent.setSenseOfMotionRake(senseOfMotionPanel.getSenseOfMotionRake());
		ConnectToEmailServlet.sendEmail(SessionInfo.getUserName()+" trying to add new event to database\n"+ paleoEvent.toString());
		this.paleoEventDAO.addPaleoevent(paleoEvent);
		JOptionPane.showMessageDialog(this, MSG_PALEO_EVENT_ADD_SUCCESS);
		ConnectToEmailServlet.sendEmail("New Event "+ eventName+" added successfully for siteId="+this.siteId+" by "+SessionInfo.getUserName());
		this.sendEventToListeners(paleoEvent);
	}

	/**
	 * add the action listeners to the buttons
	 */
	private void addActionListeners() {
		okButton.addActionListener(this);
		doneButton.addActionListener(this);
		cancelButton.addActionListener(this);
		this.addNewReferenceButton.setToolTipText(this.addNewReferenceToolTipText);
		addNewReferenceButton.addActionListener(this);
		viewAllRefsButton.addActionListener(this);
	}

	//static initializer for setting look & feel
	static {
		String osName = System.getProperty("os.name");
		try {
			UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
		}
		catch(Exception e) {
		}
	}


	/**
	 * initialize the GUI
	 * @throws java.lang.Exception
	 */
	private void jbInit() throws Exception {
		mainSplitPane.setOrientation(JSplitPane.VERTICAL_SPLIT);
		topPanel.setLayout(gridBagLayout2);
		this.getContentPane().setLayout(borderLayout1);
		eventSummaryPanel.setLayout(gridBagLayout1);
		cancelButton.setText("Cancel");
		this.getContentPane().add(topPanel, BorderLayout.CENTER);
		topPanel.add(mainSplitPane,    new GridBagConstraints(0, 0, 4, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(5, 3, 0, 2), 305, 423));
		topPanel.add(okButton,         new GridBagConstraints(0, 1, 1, 1, 0.0, 0.0
				,GridBagConstraints.SOUTHWEST, GridBagConstraints.NONE, new Insets(7, 19, 19, 0), 42, 1));
		topPanel.add(doneButton,     new GridBagConstraints(1, 1, 1, 1, 0.0, 0.0
				,GridBagConstraints.SOUTHWEST, GridBagConstraints.NONE, new Insets(7, 7, 22, 0), 21, 1));
		topPanel.add(cancelButton,   new GridBagConstraints(2, 1, 1, 1, 0.0, 0.0
				,GridBagConstraints.NORTHEAST, GridBagConstraints.NONE, new Insets(7, 7, 0, 0), 0, 0));
		mainSplitPane.add(detailedEventInfoSplitPane, JSplitPane.BOTTOM);
		detailedEventInfoSplitPane.add(estimatesSplitPane, JSplitPane.LEFT);
		mainSplitPane.add(eventSummaryPanel, JSplitPane.TOP);
		estimatesSplitPane.setDividerLocation(233);
		mainSplitPane.setDividerLocation(50);
		detailedEventInfoSplitPane.setDividerLocation(466);
	}

	public void dbAdditionSuccessful(DbAdditionSuccessEvent event) {
		Object source = event.getSource();
		if(source == this.addNewReference) {
			makeReferencesParamAndEditor();
			this.commentsReferencesPanel.updateUI();
		}
	}
}
