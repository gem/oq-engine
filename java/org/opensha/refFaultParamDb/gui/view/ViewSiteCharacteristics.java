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

import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;

import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JSplitPane;

import org.opensha.commons.gui.LabeledBoxPanel;
import org.opensha.commons.gui.TitledBorderPanel;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ConstrainedStringParameterEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.refFaultParamDb.dao.db.DB_AccessAPI;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.PaleoSiteDB_DAO;
import org.opensha.refFaultParamDb.gui.addEdit.paleoSite.AddEditIndividualEvent;
import org.opensha.refFaultParamDb.gui.addEdit.paleoSite.AddEditSiteCharacteristics;
import org.opensha.refFaultParamDb.gui.addEdit.paleoSite.AddSiteInfo;
import org.opensha.refFaultParamDb.gui.event.DbAdditionListener;
import org.opensha.refFaultParamDb.gui.event.DbAdditionSuccessEvent;
import org.opensha.refFaultParamDb.gui.infotools.GUI_Utils;
import org.opensha.refFaultParamDb.gui.infotools.InfoLabel;
import org.opensha.refFaultParamDb.gui.infotools.SessionInfo;
import org.opensha.refFaultParamDb.vo.CombinedDisplacementInfo;
import org.opensha.refFaultParamDb.vo.CombinedEventsInfo;
import org.opensha.refFaultParamDb.vo.CombinedNumEventsInfo;
import org.opensha.refFaultParamDb.vo.CombinedSlipRateInfo;
import org.opensha.refFaultParamDb.vo.FaultSectionSummary;
import org.opensha.refFaultParamDb.vo.PaleoSite;
import org.opensha.refFaultParamDb.vo.PaleoSitePublication;
import org.opensha.refFaultParamDb.vo.PaleoSiteSummary;

/**
 * <p>Title: ViewPaleoSites.java </p>
 * <p>Description: This GUI allows user to choose sites and view information about
 * them. </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class ViewSiteCharacteristics extends JPanel implements ActionListener,
ParameterChangeListener, DbAdditionListener {
	// various input parameter names
	private final static String SITE_NAME_PARAM_NAME="Site Name";
	private final static String SITE_LOCATION_PARAM_NAME="Site Location";
	private final static String SITE_ELEVATION_PARAM_NAME="Site Elevation";
	private final static String ASSOCIATED_WITH_FAULT_PARAM_NAME="Associated With Fault Section";
	private final static String SITE_TYPE_PARAM_NAME="Site Type";
	private final static String SITE_REPRESENTATION_PARAM_NAME="How Representative is this Site";
	private final static String SITE_REFERENCES_PARAM_NAME="References";
	// various types of information that can be provided by the user
	private final static String AVAILABLE_INFO_PARAM_NAME="I have Publication data for";
	private final static String SLIP_RATE_INFO = "Slip Rate";
	private final static String CUMULATIVE_DISPLACEMENT_INFO = "Cumulative Displacement";
	private final static String NUM_EVENTS_INFO = "Number of Events";
	private final static String INDIVIDUAL_EVENTS_INFO = "Individual Events";
	private final static String SEQUENCE_INFO = "Sequence Info";
	private final static String NO_SITE_NAME="No Site Name-";
	private final static String CONTRIBUTOR_PARAM_NAME = "Last Updated by";
	private final static String ENTRY_DATE_PARAM_NAME = "Last Updated on";
	private final static String MSG_ADD_DATA_ALREADY_OPEN = "Add Data window is already open";
	private final static String MSG_EVENT_ALREADY_OPEN = "Add Events Data window is already open";
	private final static String TOOLTIP_EDIT_COMBINED_INFO = "Edit Data for this reference for selected timespan";
	private final static String MSG_NO_DATA_TO_EDIT = "Cannot edit data as timespan has not been selected";
	private final static String MSG_NEED_DISPLACEMENT = "Displacement data does not exist for this timespan.\n"+
	"Do you want to add that?";
	private final static String MSG_NEED_SLIP_RATE = "Slip Rate data does not exist for this timespan.\n"+
	"Do you want to add that?";
	private final static String MSG_NEED_NUM_EVENTS = "Num Events data does not exist for this timespan.\n"+
	"Do you want to add that?";
	private final static String EDIT_INFO = "Edit Data";

	// various types of information that can be provided by the user
	private JCheckBox slipRateCheckBox, cumDispCheckBox, numEventsCheckBox,
	individualEventsCheckBox, sequenceCheckBox;


	// input parameters declaration
	private StringParameter siteNameParam;
	private StringParameter referencesForSiteParam;
	public final static String TEST_SITE = "A Sample Site";
	private final static String MSG_TEST_SITE_NOT_EDITABLE = "Sample site is non-editable";


	// input parameter editors
	private ConstrainedStringParameterEditor siteNameParamEditor;
	private ConstrainedStringParameterEditor referencesForSiteParamEditor;
	private InfoLabel siteLocationLabel = new InfoLabel();
	private InfoLabel siteElevationLabel = new InfoLabel();
	private InfoLabel assocWithFaultLabel = new InfoLabel();
	private InfoLabel siteTypeLabel= new InfoLabel();
	private InfoLabel siteRepresentationLabel= new InfoLabel();
	private InfoLabel lastEntryDateLabel = new InfoLabel();
	private InfoLabel sendEmailLabel = new InfoLabel("To change the above info, send email to perry@gps.caltech.edu");
	private InfoLabel contributorNameLabel = new InfoLabel();
	private LabeledBoxPanel iHaveInfoOnPanel;

	// various buttons in thos window
	private String ADD_SITE = "Add New Site";
	private JButton editSiteButton = new JButton("Edit");
	private JButton editCombinedInfoButton = new JButton("Edit Data");
	private JButton qFaultsEntriesButton = new JButton("Show QFault entries");
	private JButton addInfoButton = new JButton("Add Data");
	private JSplitPane splitPane = new JSplitPane();

	private JPanel addEditSitePanel = new TitledBorderPanel("Site Characteristics");

	private ArrayList paleoSiteSummaryList;
	private ArrayList siteNamesList;
	private PaleoSite paleoSite; //currently selected paleo site

	// class listening to site change events
	private SiteSelectionAPI siteSelectionListener;
	private AddEditSiteCharacteristics addEditSiteChars;
	private AddSiteInfo addSiteInfo;
	private AddEditIndividualEvent addEditIndividualEvent;

	//dao
	private PaleoSiteDB_DAO paleoSiteDAO;

	private DB_AccessAPI dbConnection;

	public ViewSiteCharacteristics(DB_AccessAPI dbConnection, SiteSelectionAPI siteSelectionListener) {
		this.dbConnection = dbConnection;
		paleoSiteDAO = new PaleoSiteDB_DAO(dbConnection);
		try {
			this.siteSelectionListener = siteSelectionListener;
			addEditSitePanel.setLayout(GUI_Utils.gridBagLayout);
			qFaultsEntriesButton.setEnabled(false);
			// initialize parameters and editors
			initSiteNamesParameterAndEditor();
			// add user provided info choices
			addUserProvidedInfoChoices();
			// add the editors to this window
			jbInit();
			// ad action listeners to catch the event on button click
			addActionListeners();
			//		 do not allow edit for non authenticated users
			if(SessionInfo.getContributor()==null) {
				addInfoButton.setEnabled(false);
				this.editCombinedInfoButton.setEnabled(false);
				this.editSiteButton.setEnabled(false);
			}

		}catch(Exception e)  {
			e.printStackTrace();
		}
	}

	/**
	 * Add the panel which lists the information which can be provided by the user
	 */
	private void addUserProvidedInfoChoices() {
		iHaveInfoOnPanel = new LabeledBoxPanel(GUI_Utils.gridBagLayout);
		iHaveInfoOnPanel.setTitle(AVAILABLE_INFO_PARAM_NAME);
		slipRateCheckBox = new JCheckBox(SLIP_RATE_INFO);
		cumDispCheckBox = new JCheckBox(CUMULATIVE_DISPLACEMENT_INFO);
		numEventsCheckBox = new JCheckBox(NUM_EVENTS_INFO);
		individualEventsCheckBox = new JCheckBox(INDIVIDUAL_EVENTS_INFO);
		sequenceCheckBox = new JCheckBox(SEQUENCE_INFO);
		slipRateCheckBox.addActionListener(this);
		cumDispCheckBox.addActionListener(this);
		int yPos=0;
		iHaveInfoOnPanel.add(slipRateCheckBox, new GridBagConstraints(0, yPos++, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER,
				GridBagConstraints.BOTH,
				new Insets(2, 2, 2, 2), 0, 0));
		iHaveInfoOnPanel.add(cumDispCheckBox, new GridBagConstraints(0, yPos++, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER,
				GridBagConstraints.BOTH,
				new Insets(2, 2, 2, 2), 0, 0));
		iHaveInfoOnPanel.add(numEventsCheckBox, new GridBagConstraints(0, yPos++, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER,
				GridBagConstraints.BOTH,
				new Insets(2, 2, 2, 2), 0, 0));
		iHaveInfoOnPanel.add(individualEventsCheckBox,
				new GridBagConstraints(0, yPos++, 1, 1, 1.0, 1.0
						, GridBagConstraints.CENTER,
						GridBagConstraints.BOTH,
						new Insets(2, 2, 2, 2), 0, 0));
		iHaveInfoOnPanel.add(sequenceCheckBox,
				new GridBagConstraints(0, yPos++, 1, 1, 1.0, 1.0
						, GridBagConstraints.CENTER,
						GridBagConstraints.BOTH,
						new Insets(2, 2, 2, 2), 0, 0));
		iHaveInfoOnPanel.add(addInfoButton,
				new GridBagConstraints(0, yPos++, 1, 1, 1.0, 1.0
						, GridBagConstraints.CENTER,
						GridBagConstraints.NONE,
						new Insets(2, 2, 2, 2), 0, 0));
	}

	/**
	 * Add the editors to the window
	 */
	private void jbInit() {
		setLayout(GUI_Utils.gridBagLayout);
		splitPane.setOrientation(JSplitPane.VERTICAL_SPLIT);
		// site name editor
		this.setMinimumSize(new Dimension(0, 0));
		add(splitPane, new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER,
				GridBagConstraints.BOTH, new Insets(2, 2, 2, 2),
				0, 0));
		splitPane.add(addEditSitePanel, JSplitPane.TOP);
		addEditSiteCharacteristicsPanel();

		//adding the options so that user can provide the info
		splitPane.add(this.iHaveInfoOnPanel, JSplitPane.BOTTOM);
		splitPane.setDividerLocation(375);
	}

	private void addEditSiteCharacteristicsPanel() {
		int siteYPos = 1;

		// edit site button
		/*addEditSitePanel.add(editSiteButton, new GridBagConstraints(0, siteYPos++, 1, 1, 1.0, 1.0
                                               , GridBagConstraints.EAST,
                                               GridBagConstraints.NONE,
                                               new Insets(2, 2, 2, 2), 0, 0));*/

		//++siteYPos; // increment because site names editor exists at this place
		// site location
		addEditSitePanel.add(siteLocationLabel,
				new GridBagConstraints(0, siteYPos++, 1, 1, 1.0, 1.0
						, GridBagConstraints.CENTER,
						GridBagConstraints.BOTH,
						new Insets(2, 2, 2, 2), 0, 0));
		// site elevation
		addEditSitePanel.add(this.siteElevationLabel,
				new GridBagConstraints(0, siteYPos++, 1, 1, 1.0, 1.0
						, GridBagConstraints.CENTER,
						GridBagConstraints.BOTH,
						new Insets(2, 2, 2, 2), 0, 0));

		// associated with fault
		addEditSitePanel.add(assocWithFaultLabel, new GridBagConstraints(0, siteYPos++, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER,
				GridBagConstraints.BOTH,
				new Insets(2, 2 , 2, 2), 0, 0));
		// send email to edit site location/association with fault
		addEditSitePanel.add(sendEmailLabel,
				new GridBagConstraints(0, siteYPos++, 1, 1, 1.0, 1.0
						, GridBagConstraints.CENTER,
						GridBagConstraints.BOTH,
						new Insets(2, 2, 2, 2), 0, 0));

		++siteYPos; // increment  because references param editor exists at this place

		// site types
		addEditSitePanel.add(siteTypeLabel, new GridBagConstraints(0, siteYPos++, 1, 1, 1.0, 1.0
				, GridBagConstraints.CENTER,
				GridBagConstraints.BOTH,
				new Insets(2, 2 , 2, 2), 0, 0));
		// how representative is this site
		addEditSitePanel.add(siteRepresentationLabel,
				new GridBagConstraints(0, siteYPos++, 1, 1, 1.0, 1.0
						, GridBagConstraints.CENTER,
						GridBagConstraints.BOTH, new Insets(2, 2, 2, 2),
						0, 0));

		// entry date
		addEditSitePanel.add(this.lastEntryDateLabel,
				new GridBagConstraints(0, siteYPos++, 1, 1, 1.0, 1.0
						, GridBagConstraints.CENTER,
						GridBagConstraints.BOTH, new Insets(2, 2, 2, 2),
						0, 0));


		// contributor
		addEditSitePanel.add(this.contributorNameLabel,
				new GridBagConstraints(0, siteYPos++, 1, 1, 1.0, 1.0
						, GridBagConstraints.CENTER,
						GridBagConstraints.BOTH, new Insets(2, 2, 2, 2),
						0, 0));

		// Edit Combined Info Button
		addEditSitePanel.add(this.editCombinedInfoButton,
				new GridBagConstraints(0, siteYPos++, 1, 1, 1.0, 1.0
						, GridBagConstraints.CENTER,
						GridBagConstraints.NONE, new Insets(2, 2, 2, 2),
						0, 0));

		editCombinedInfoButton.setToolTipText(TOOLTIP_EDIT_COMBINED_INFO);
		// QFault entries for this site
		addEditSitePanel.add(qFaultsEntriesButton,
				new GridBagConstraints(0, siteYPos++, 1, 1, 1.0, 1.0
						, GridBagConstraints.CENTER,
						GridBagConstraints.NONE, new Insets(2, 2, 2, 2),
						0, 0));

	}

	/**
	 * Add the action listeners to the button.
	 */
	private void addActionListeners() {
		editSiteButton.addActionListener(this);
		addInfoButton.addActionListener(this);
		editCombinedInfoButton.addActionListener(this);
	}

	/**
	 * Whenever user presses a button on this window, this function is called
	 * @param event
	 */
	public void actionPerformed(ActionEvent event) {
		// if it is "Add New Site" request, pop up another window to fill the new site type
		Object source = event.getSource();
		try {
			if (paleoSite == null) { //  if it is test site
				JOptionPane.showMessageDialog(this, MSG_TEST_SITE_NOT_EDITABLE);
				return;
			}

			// EDIT THE SITE CHARACTERISTICS
			if (source == this.editSiteButton) { // edit the paleo site
				//addEditSiteChars = new AddEditSiteCharacteristics(true, this.paleoSite);
				addEditSiteChars.addDbAdditionSuccessListener(this);
			}

			// ADD NEW COMBINED INFO FOR SITE
			else if (source == this.addInfoButton) { // add new combined events info
				addNewCombinedInfo();// if it is a valid site, NOT a test site
			}

			// EDIT COMBINED INFO FOR SITE
			else if (source == this.editCombinedInfoButton) {
				editCombinedInfo();
			}

		} catch(Exception e) {
			//e.printStackTrace();
			JOptionPane.showMessageDialog(this, e.getMessage());
		}

	}

	/**
	 * Edit the combined info
	 */
	private void editCombinedInfo() {
		CombinedEventsInfo combinedInfo  = this.siteSelectionListener.getSelectedCombinedInfo();
		if(combinedInfo==null)  { // if there is no data displayed in window to edit
			JOptionPane.showMessageDialog(this, MSG_NO_DATA_TO_EDIT);
			return;
		}

		// do not show window if already open
		if(addSiteInfo!=null && addSiteInfo.isVisible()) {
			JOptionPane.showMessageDialog(this, MSG_ADD_DATA_ALREADY_OPEN);
			return;
		}

		boolean isDispVisible=false, isSlipRateVisible=false, isNumEventsVisible=false;

		// check whether combined displacement panel needs to be shown
		CombinedDisplacementInfo combinedDisplacementInfo = combinedInfo.getCombinedDisplacementInfo();
		if(combinedDisplacementInfo!=null) isDispVisible = true;
		else {
			int option = JOptionPane.showConfirmDialog(this, MSG_NEED_DISPLACEMENT, EDIT_INFO, JOptionPane.YES_NO_OPTION);
			if(option==JOptionPane.YES_OPTION) isDispVisible = true;
		}

		// check whether slip rate panel needs to be shown
		CombinedSlipRateInfo combinedSlipRateInfo = combinedInfo.getCombinedSlipRateInfo();
		if(combinedSlipRateInfo!=null) isSlipRateVisible = true;
		else {
			int option = JOptionPane.showConfirmDialog(this, MSG_NEED_SLIP_RATE, EDIT_INFO, JOptionPane.YES_NO_OPTION);
			if(option==JOptionPane.YES_OPTION) isSlipRateVisible = true;
		}


		// check whether num events panel needs to be shown
		CombinedNumEventsInfo combinedNumEventsInfo = combinedInfo.getCombinedNumEventsInfo();
		if(combinedNumEventsInfo!=null) isNumEventsVisible = true;
		else {
			int option = JOptionPane.showConfirmDialog(this, MSG_NEED_NUM_EVENTS, EDIT_INFO, JOptionPane.YES_NO_OPTION);
			if(option==JOptionPane.YES_OPTION) isNumEventsVisible = true;
		}
		combinedInfo.setPaleoSitePublication(getPaleoSitePublication((String)this.referencesForSiteParam.getValue()));
		// show window to enter data
		addSiteInfo = new AddSiteInfo(dbConnection, this.paleoSite.getSiteId(),
				this.paleoSite.getEntryDate(),
				isSlipRateVisible,
				isDispVisible,
				isNumEventsVisible,
				false, combinedInfo);
		addSiteInfo.addDbAdditionSuccessListener(this);
	}

	/**
	 * Add new combined info for a site
	 */
	private void addNewCombinedInfo() {
		// make sure one of slip rate/cim dip/num evennts and sequence are selected
		if(slipRateCheckBox.isSelected() ||
				this.cumDispCheckBox.isSelected() ||
				numEventsCheckBox.isSelected()||
				this.sequenceCheckBox.isSelected()) {
			// do not show window if already open
			if(addSiteInfo!=null && addSiteInfo.isVisible()) {
				JOptionPane.showMessageDialog(this, MSG_ADD_DATA_ALREADY_OPEN);
				return;
			}
			// show window to enter data
			addSiteInfo = new AddSiteInfo(dbConnection, this.paleoSite.getSiteId(),
					this.paleoSite.getEntryDate(),
					this.slipRateCheckBox.isSelected(),
					this.cumDispCheckBox.isSelected(),
					this.numEventsCheckBox.isSelected(),
					this.sequenceCheckBox.isSelected());

			addSiteInfo.addDbAdditionSuccessListener(this);
		}
		// whether to show individual event window
		if(this.individualEventsCheckBox.isSelected()) {
			if(addEditIndividualEvent!=null && addEditIndividualEvent.isVisible()) {
				JOptionPane.showMessageDialog(this, MSG_EVENT_ALREADY_OPEN);
				return;
			}
			showIndividualEventWindow();
		}
	}

	/**
	 * Initialize all the parameters and the editors
	 */
	private void initSiteNamesParameterAndEditor() throws Exception {
		if(siteNameParamEditor!=null) addEditSitePanel.remove(siteNameParamEditor);
		// available site names in the database
		ArrayList availableSites = getSiteNames();
		siteNameParam = new StringParameter(SITE_NAME_PARAM_NAME, availableSites, (String)availableSites.get(0));
		siteNameParamEditor = new ConstrainedStringParameterEditor(siteNameParam);
		siteNameParam.addParameterChangeListener(this);

		addEditSitePanel.add(siteNameParamEditor,
				new GridBagConstraints(0, 0, 1, 1, 1.0,
						1.0
						, GridBagConstraints.CENTER,
						GridBagConstraints.BOTH,
						new Insets(2, 2, 2, 2), 0, 0));

		setSiteInfo((String)availableSites.get(0));
	}


	/**
	 * When a site is selected by the user choose the references for that site
	 *
	 */
	private void initReferencesForSiteParameterAndEditor()  {
		if(this.referencesForSiteParamEditor!=null) addEditSitePanel.remove(referencesForSiteParamEditor);
		ArrayList pubNames = new ArrayList();
		if(paleoSite!=null) { // if it is not a test site
			ArrayList paleoSitePubList = paleoSite.getPaleoSitePubList();
			for (int i = 0; i < paleoSitePubList.size(); ++i) {
				pubNames.add( ( (PaleoSitePublication) paleoSitePubList.get(i)).
						getReference().getSummary());
			}
		} else { // add fake references for a test site
			pubNames.add("Ref 1");
			pubNames.add("Ref 2");
		}
		referencesForSiteParam = new StringParameter(SITE_REFERENCES_PARAM_NAME, pubNames,
				(String)pubNames.get(0));
		referencesForSiteParam.addParameterChangeListener(this);
		referencesForSiteParamEditor = new ConstrainedStringParameterEditor(referencesForSiteParam);
		// site references
		addEditSitePanel.add(this.referencesForSiteParamEditor,
				new GridBagConstraints(0, 5, 1, 1, 1.0, 1.0
						, GridBagConstraints.CENTER,
						GridBagConstraints.BOTH,
						new Insets(2, 2, 2, 2),
						0, 0));
		setValuesBasedOnReference((String)pubNames.get(0));
	}

	/**
	 * Set the site types, representative strand index whenever a reference is selected
	 * by the user
	 * @param refName
	 */
	private void setValuesBasedOnReference(String refName) {
		String siteType=null, siteRepresentation=null;
		String lastEntryDate=null, lastUpdatedBy=null;
		int refId = -1;
		if(paleoSite==null) { // if it is a test site
			siteType = "Trench";
			siteRepresentation = "Most Significant Strand";
			lastEntryDate = "Not Available";
			lastUpdatedBy="Test";
		}
		else { // if it is a real site
			PaleoSitePublication paleoSitePub = getPaleoSitePublication(refName);
			refId = paleoSitePub.getReference().getReferenceId();
			ArrayList studyTypes = paleoSitePub.getSiteTypeNames();
			siteType = "";
			for (int j = 0; j < studyTypes.size(); ++j)
				siteType += studyTypes.get(j) + ",";
			siteRepresentation = paleoSitePub.getRepresentativeStrandName();
			lastEntryDate = paleoSitePub.getEntryDate();
			lastUpdatedBy = paleoSitePub.getContributorName();
		}
		// site type for this site
		siteTypeLabel.setTextAsHTML(SITE_TYPE_PARAM_NAME,siteType);
		// Site representation
		siteRepresentationLabel.setTextAsHTML(SITE_REPRESENTATION_PARAM_NAME,siteRepresentation);
		// last entry date
		this.lastEntryDateLabel.setTextAsHTML(ENTRY_DATE_PARAM_NAME, lastEntryDate);
		// last entry by
		this.contributorNameLabel.setTextAsHTML(CONTRIBUTOR_PARAM_NAME, lastUpdatedBy);
		// call the listener
		siteSelectionListener.siteSelected(this.paleoSite, refId); // call the listening class

	}

	/**
	 * Get paleo site publication based on ref name
	 * @param refName
	 * @return
	 */
	private PaleoSitePublication getPaleoSitePublication(String refName) {
		ArrayList paleoSitePubList = paleoSite.getPaleoSitePubList();
		for (int i = 0; i < paleoSitePubList.size(); ++i) {
			PaleoSitePublication paleoSitePub = (PaleoSitePublication)
			paleoSitePubList.get(i);
			String summary = paleoSitePub.getReference().getSummary();
			if (summary.equalsIgnoreCase(refName)) {
				return paleoSitePub;
			}
		}
		return null;
	}


	/**
	 * Set the paleo site info based on selected Paleo Site
	 * @param paleoSite
	 */
	private void setSiteInfo(String siteName)  {
		String  faultSectionName;
		float latitude, longitude, elevation;
		if(siteName.equalsIgnoreCase(TEST_SITE)) { // test site
			faultSectionName = "FaultSection1";
			latitude = 34.0f;
			longitude=-116.0f;
			elevation=0.0f;
			paleoSite=null;
		}
		else { // paleo site information from the database
			int index = this.siteNamesList.indexOf(siteName)-1; // -1 IS NEEDED BECAUSE OF TEST SITE
			PaleoSiteSummary paleoSiteSummary = (PaleoSiteSummary)this.paleoSiteSummaryList.get(index);
			paleoSite = this.paleoSiteDAO.getPaleoSite(paleoSiteSummary.getSiteId());
			FaultSectionSummary fs = paleoSite.getFaultSectionSummary();
			if (fs == null)
				faultSectionName = "(null)";
			else
				faultSectionName = fs.getSectionName();
			latitude = paleoSite.getSiteLat1();
			longitude = paleoSite.getSiteLon1();
			elevation = paleoSite.getSiteElevation1();
		}

		siteLocationLabel.setTextAsHTML(SITE_LOCATION_PARAM_NAME,
				GUI_Utils.latFormat.format(latitude)+","+ GUI_Utils.lonFormat.format(longitude));
		String elevationStr = null;
		if(!Float.isNaN(elevation)) elevationStr = GUI_Utils.decimalFormat.format(elevation);
		this.siteElevationLabel.setTextAsHTML(SITE_ELEVATION_PARAM_NAME,
				elevationStr);
		//  fault with which this site is associated
		assocWithFaultLabel.setTextAsHTML(ASSOCIATED_WITH_FAULT_PARAM_NAME,faultSectionName);
		// set the references for this site
		this.initReferencesForSiteParameterAndEditor();
	}


	public void parameterChange(ParameterChangeEvent event) {
		String paramName = event.getParameterName();
		// if a  new site names is selected by the user
		if(paramName.equalsIgnoreCase(SITE_NAME_PARAM_NAME)) {
			String siteName = (String) this.siteNameParam.getValue();
			// if add site is selected, show window to add a site
			if(siteName.equalsIgnoreCase(this.ADD_SITE)) {
				addEditSiteChars = new AddEditSiteCharacteristics(dbConnection);
				addEditSiteChars.addDbAdditionSuccessListener(this);
			}
			else setSiteInfo(siteName);
		}
		// if user chooses a new reference
		else if(paramName.equalsIgnoreCase(SITE_REFERENCES_PARAM_NAME)) {
			String refName = (String)this.referencesForSiteParam.getValue();
			setValuesBasedOnReference(refName);
		}
	}

	/**
	 * It gets all the site names from the database
	 * @return
	 */
	private ArrayList getSiteNames() {
		paleoSiteSummaryList = paleoSiteDAO.getAllPaleoSiteNames();
		siteNamesList = new ArrayList();
		siteNamesList.add(TEST_SITE);
		int numSites = paleoSiteSummaryList.size();
		String siteName;
		PaleoSiteSummary paleoSiteSummary;
		for(int i=0; i<numSites; ++i) {
			paleoSiteSummary = (PaleoSiteSummary)paleoSiteSummaryList.get(i);
			siteName = paleoSiteSummary.getSiteName().trim();
			if(siteName==null || siteName.equalsIgnoreCase("")) siteName=NO_SITE_NAME+i;
			siteNamesList.add(siteName);
		}
		siteNamesList.add(ADD_SITE);
		return siteNamesList;
	}

	/**
	 * This function is called whenever new info is added for a site into the database.
	 * @param event
	 */
	public void dbAdditionSuccessful(DbAdditionSuccessEvent event) {
		Object source = event.getSource();
		if(source == addEditIndividualEvent) {
			addEditIndividualEvent.dispose();
			showIndividualEventWindow();
		}
		String siteName = (String) this.siteNameParam.getValue();
		if(siteName.equalsIgnoreCase(this.ADD_SITE)) {
			try {
				this.initSiteNamesParameterAndEditor();
				this.updateUI();
			}catch(Exception e) {
				e.printStackTrace();
			}
		}
		else {

			this.setSiteInfo(siteName);
		}
	}

	private void showIndividualEventWindow() {
		addEditIndividualEvent = new AddEditIndividualEvent(dbConnection, paleoSite.getSiteId(),
				paleoSite.getEntryDate());
		addEditIndividualEvent.addDbAdditionSuccessListener(this);
	}

}
