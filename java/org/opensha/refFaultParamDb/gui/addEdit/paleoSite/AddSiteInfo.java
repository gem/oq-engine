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

import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;

import javax.swing.JButton;
import javax.swing.JOptionPane;
import javax.swing.JSplitPane;
import javax.swing.JTabbedPane;

import org.opensha.refFaultParamDb.dao.db.CombinedEventsInfoDB_DAO;
import org.opensha.refFaultParamDb.dao.db.DB_AccessAPI;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.data.TimeAPI;
import org.opensha.refFaultParamDb.gui.event.DbAdditionFrame;
import org.opensha.refFaultParamDb.gui.infotools.ConnectToEmailServlet;
import org.opensha.refFaultParamDb.gui.infotools.SessionInfo;
import org.opensha.refFaultParamDb.vo.CombinedDisplacementInfo;
import org.opensha.refFaultParamDb.vo.CombinedEventsInfo;
import org.opensha.refFaultParamDb.vo.CombinedNumEventsInfo;
import org.opensha.refFaultParamDb.vo.CombinedSlipRateInfo;
import org.opensha.refFaultParamDb.vo.PaleoSitePublication;
import org.opensha.refFaultParamDb.vo.Reference;

/**
 * <p>Title: AddSiteInfo.java </p>
 * <p>Description: This GUI allows the user to enter a timespan and related info
 * (slip rate or displacement, number of events) about a new site. </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class AddSiteInfo extends DbAdditionFrame implements ActionListener{
	private JSplitPane mainSplitPane = new JSplitPane();
	private JButton okButton = new JButton("Submit");
	private JButton cancelButton = new JButton("Cancel");
	private GridBagLayout gridBagLayout1 = new GridBagLayout();
	private boolean isSlipVisible, isDisplacementVisible, isNumEventsVisible, isSequenceVisible;
	private ArrayList referenceList;
	private AddEditNumEvents addEditNumEvents;
	private AddEditSlipRate addEditSlipRate;
	private AddEditCumDisplacement addEditCumDisp;
	private AddEditSequence addEditSequence;
	private AddEditTimeSpan addEditTimeSpan;
	private JTabbedPane tabbedPane = new JTabbedPane();
	private final static String NUM_EVENTS_TITLE = "Num Events Est";
	private final static String SLIP_RATE_TITLE = "Slip Rate Est";
	private final static String DISPLACEMENT_TITLE = "Displacement Est";
	private final static String SEQUENCE_TITLE = "Sequence";
	private final static String ATLEAT_ONE_MSG = "Atleast one of Slip, Cumulative Displacement, Num events or Sequence should be specified";
	private final static int W = 900;
	private final static int H = 650;
	private final static String TITLE = "Add Data for Slip Rate, Displacement, or Number of Events";
	private final static String MSG_DB_OPERATION_SUCCESS = "Site Info successfully inserted into the database";
	private final static String MSG_NO_REFERENCE_CHOSEN = "Cannot add info to database as reference has not been chosen";
	private int siteId;
	private String siteEntryDate;
	private String siteRepresentativeIndex;
	private ArrayList siteTypes;
	private CombinedEventsInfoDB_DAO combinedEventsInfoDAO;


	/**
	 * This constructor can be used for adding new site info
	 * @param siteId
	 * @param siteEntryDate
	 * @param isSlipVisible
	 * @param isDisplacementVisible
	 * @param isNumEventsVisible
	 * @param isSequenceVisible
	 */
	public AddSiteInfo(DB_AccessAPI dbConnection, int siteId, String siteEntryDate,
			boolean isSlipVisible, boolean isDisplacementVisible,
			boolean isNumEventsVisible, boolean isSequenceVisible)  {
		this(dbConnection, siteId, siteEntryDate, isSlipVisible, isDisplacementVisible,
				isNumEventsVisible, isSequenceVisible, null);
	}

	/**
	 * This constructor is useful when editing existing data
	 *
	 * @param siteId
	 * @param siteEntryDate
	 * @param isSlipVisible
	 * @param isDisplacementVisible
	 * @param isNumEventsVisible
	 * @param isSequenceVisible
	 * @param combinedInfo
	 */
	public AddSiteInfo(DB_AccessAPI dbConnection, int siteId, String siteEntryDate,
			boolean isSlipVisible, boolean isDisplacementVisible,
			boolean isNumEventsVisible, boolean isSequenceVisible,
			CombinedEventsInfo combinedInfo) {
		combinedEventsInfoDAO = new CombinedEventsInfoDB_DAO(dbConnection);
		this.siteId = siteId;
		// user should provide info about at least one of slip, cum disp or num events
		if(!isSlipVisible && !isDisplacementVisible && !isNumEventsVisible && !isSequenceVisible)
			throw new RuntimeException(ATLEAT_ONE_MSG);
		this.isSlipVisible = isSlipVisible;
		this.isDisplacementVisible = isDisplacementVisible;
		this.isNumEventsVisible = isNumEventsVisible;
		this.isSequenceVisible = isSequenceVisible;

		this.siteEntryDate = siteEntryDate;
		try {
			if (this.isSequenceVisible)
				this.addEditSequence = new AddEditSequence(dbConnection, siteId, siteEntryDate);
		}catch(RuntimeException e) {
			JOptionPane.showMessageDialog(this, e.getMessage());
			this.isSequenceVisible = false;
			// show the window if any one of slip, displacement or num events needs to be visible
			if(!(isSlipVisible || isDisplacementVisible || isNumEventsVisible)) {
				this.dispose();
				return;
			}
		}

		// if slip is visible
		if(isSlipVisible) {
			CombinedSlipRateInfo combinedSlipRateInfo = null;
			if(combinedInfo!=null) combinedSlipRateInfo = combinedInfo.getCombinedSlipRateInfo();
			this.addEditSlipRate = new AddEditSlipRate(combinedSlipRateInfo);
		}

		// if displacement is visible
		if(isDisplacementVisible) {
			CombinedDisplacementInfo combinedDispInfo = null;
			if(combinedInfo!=null) combinedDispInfo = combinedInfo.getCombinedDisplacementInfo();
			this.addEditCumDisp = new AddEditCumDisplacement(combinedDispInfo);
		}

		// if num events are visible
		if(isNumEventsVisible) {
			CombinedNumEventsInfo combinedEventsInfo = null;
			if(combinedInfo!=null) combinedEventsInfo = combinedInfo.getCombinedNumEventsInfo();
			this.addEditNumEvents = new AddEditNumEvents(combinedEventsInfo);
		}

		// make timespan
		if(combinedInfo!=null) {
			addEditTimeSpan = new AddEditTimeSpan(combinedInfo.getStartTime(), combinedInfo.getEndTime(), combinedInfo.getDatedFeatureComments());
		} else  addEditTimeSpan = new AddEditTimeSpan();


		jbInit();
		addActionListeners();
		this.setSize(W,H);
		setTitle(TITLE);
		this.setLocationRelativeTo(null);
		this.setVisible(true);

		// show window to get the reference
		ChooseReference referencesDialog = new ChooseReference(dbConnection, this);
		referencesDialog.setFocusableWindowState(true);
		referencesDialog.setVisible(true);
		if(combinedInfo!=null) {
			// set paleo site publication
			PaleoSitePublication paleoSitePub = combinedInfo.getPaleoSitePublication();
			referencesDialog.setParameters((String)paleoSitePub.getSiteTypeNames().get(0),
					paleoSitePub.getRepresentativeStrandName(),
					paleoSitePub.getReference());
			setSiteType((String)paleoSitePub.getSiteTypeNames().get(0));
			setSiteRepresentativeStrandIndex(paleoSitePub.getRepresentativeStrandName());
			setReference(paleoSitePub.getReference());
		}
	}



	// site type as given in the publication
	public void setSiteType(String siteType) {
		siteTypes = new ArrayList();
		siteTypes.add(siteType);
	}

	// representative strand index as given in the publication
	public void setSiteRepresentativeStrandIndex(String representativeStrandIndex) {
		this.siteRepresentativeIndex = representativeStrandIndex;
	}

	public void setReference(Reference reference) {
		referenceList = new ArrayList();
		referenceList.add(reference);
		try {
			/* sometimes year of publication is not a integer. So, it handles that condition */
			int pubYear = Integer.parseInt(reference.getRefYear());
			this.addEditTimeSpan.setNowYearVal(pubYear);
		}catch( NumberFormatException e) {

		}
		//this.setEnabled(true);
	}

	/**
	 * Add the action listeners on the buttons
	 */
	private void addActionListeners() {
		this.okButton.addActionListener(this);
		this.cancelButton.addActionListener(this);
	}

	public void actionPerformed(ActionEvent event) {
		Object source = event.getSource();
		if(source==this.cancelButton) this.dispose(); // cancel button is clicked
		else if(source==this.okButton) { // ok button is clicked
			try {
				if(this.isSlipVisible || this.isDisplacementVisible ||
						this.isNumEventsVisible || this.isSequenceVisible)
					if(referenceList==null || referenceList.size()==0)
						throw new RuntimeException(MSG_NO_REFERENCE_CHOSEN);
				putSiteInfoInDatabase(); // put site info in database
				JOptionPane.showMessageDialog(this, MSG_DB_OPERATION_SUCCESS);
				ConnectToEmailServlet.sendEmail("New Site Info added successfully for site Id="+this.siteId +" by "+SessionInfo.getUserName());
				this.dispose();
			}catch(Exception e){
				JOptionPane.showMessageDialog(this, e.getMessage());
			}
		}
	}

	/**
	 * Put the site info in the database
	 */
	private void putSiteInfoInDatabase() {
		CombinedEventsInfo combinedEventsInfo = new CombinedEventsInfo();
		// it is not expert opinion. this is publication info
		combinedEventsInfo.setIsExpertOpinion(false);
		// if there is error in user input for start time
		try {
			// set the time span info
			TimeAPI startTime = addEditTimeSpan.getStartTime();
			startTime.setReferencesList(this.referenceList);
			combinedEventsInfo.setStartTime(startTime);
		}catch(Exception e) {
			throw new RuntimeException("Check Start Time\n"+e.getMessage());
		}
		// if there is error in user input for end time
		try {
			TimeAPI endTime = addEditTimeSpan.getEndTime();
			endTime.setReferencesList(this.referenceList);
			combinedEventsInfo.setEndTime(endTime);
		}catch(Exception e) {
			throw new RuntimeException("Check End Time\n"+e.getMessage());
		}
		combinedEventsInfo.setReferenceList(referenceList);
		combinedEventsInfo.setDatedFeatureComments(addEditTimeSpan.getTimeSpanComments());
		// set the site
		combinedEventsInfo.setSiteEntryDate(this.siteEntryDate);
		combinedEventsInfo.setSiteId(this.siteId);
		// paleo site publication info
		PaleoSitePublication paleoSitePub = new PaleoSitePublication();
		paleoSitePub.setReference((Reference)this.referenceList.get(0));
		paleoSitePub.setRepresentativeStrandName(this.siteRepresentativeIndex);
		paleoSitePub.setSiteTypeNames(this.siteTypes);
		paleoSitePub.setSiteId(this.siteId);
		paleoSitePub.setSiteEntryDate(siteEntryDate);
		combinedEventsInfo.setPaleoSitePublication(paleoSitePub);

		try {// set the slip rate info
			if (isSlipVisible) {
				CombinedSlipRateInfo combinedSlipRateInfo = addEditSlipRate.
				getCombinedSlipRateInfo();
				combinedEventsInfo.setCombinedSlipRateInfo(combinedSlipRateInfo);
			}
		}catch(Exception e) {
			throw new RuntimeException("Check  "+this.SLIP_RATE_TITLE+"\n"+e.getMessage());
		}

		try{ // set the diplacement info
			if(this.isDisplacementVisible) {
				CombinedDisplacementInfo combinedDisplacementInfo = addEditCumDisp.getCombinedDisplacementInfo();
				combinedEventsInfo.setCombinedDisplacementInfo(combinedDisplacementInfo);
			}
		}catch(Exception e) {
			throw new RuntimeException("Check "+this.DISPLACEMENT_TITLE+"\n"+e.getMessage());
		}

		try {//set the num events info
			if(this.isNumEventsVisible) {
				CombinedNumEventsInfo combinedNumEventsInfo = addEditNumEvents.getCombinedNumEventsInfo();
				combinedEventsInfo.setCombinedNumEventsInfo(combinedNumEventsInfo);
			}
		}catch(Exception e) {
			throw new RuntimeException("Check "+this.NUM_EVENTS_TITLE+"\n"+e.getMessage());
		}


		try {// set the sequence info
			if(this.isSequenceVisible) {
				combinedEventsInfo.setEventSequenceList(addEditSequence.getAllSequences());
			}
		}catch(Exception e) {
			throw new RuntimeException("Check "+this.SEQUENCE_TITLE+ "\n"+e.getMessage());
		}

		ConnectToEmailServlet.sendEmail(SessionInfo.getUserName()+" trying to add new combined events info to database\n"+ combinedEventsInfo.toString());
		combinedEventsInfoDAO.addCombinedEventsInfo(combinedEventsInfo);
		this.sendEventToListeners(combinedEventsInfo);
	}



	/**
	 * intialize the GUI components
	 *
	 * @throws java.lang.Exception
	 */
	private void jbInit(){
		this.getContentPane().setLayout(gridBagLayout1);
		mainSplitPane.setOrientation(JSplitPane.HORIZONTAL_SPLIT);
		this.getContentPane().add(mainSplitPane,
				new GridBagConstraints(0, 0, 2, 1, 1.0, 1.0
						, GridBagConstraints.CENTER, GridBagConstraints.BOTH,
						new Insets(1, 3, 0, 0), 237, 411));
		this.getContentPane().add(okButton,
				new GridBagConstraints(0, 1, 1, 1, 0.0, 0.0
						, GridBagConstraints.CENTER, GridBagConstraints.NONE,
						new Insets(0, 155, 11, 0), 39, -1));
		this.getContentPane().add(cancelButton,
				new GridBagConstraints(1, 1, 1, 1, 0.0, 0.0
						, GridBagConstraints.CENTER, GridBagConstraints.NONE,
						new Insets(0, 22, 11, 175), 8, 0));
		String constraints = "";

		mainSplitPane.add(addEditTimeSpan, JSplitPane.LEFT);
		mainSplitPane.add(this.tabbedPane, JSplitPane.RIGHT);
		if (this.isSlipVisible) // if slip rate estimate is visible
			tabbedPane.add(this.SLIP_RATE_TITLE, this.addEditSlipRate);
		if (this.isDisplacementVisible) // if displacement is visible
			tabbedPane.add(this.DISPLACEMENT_TITLE, this.addEditCumDisp);
		if (isNumEventsVisible) // if num events estimate is visible
			tabbedPane.add(this.NUM_EVENTS_TITLE, addEditNumEvents);
		if(this.isSequenceVisible) // if sequence is visible
			tabbedPane.add(SEQUENCE_TITLE, this.addEditSequence);
		mainSplitPane.setDividerLocation(2*W/3);
	}
}
