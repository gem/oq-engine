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

import java.awt.Container;
import java.awt.GridBagConstraints;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;

import javax.swing.JButton;
import javax.swing.JFrame;

import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ConstrainedStringParameterEditor;
import org.opensha.refFaultParamDb.dao.db.DB_AccessAPI;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.ReferenceDB_DAO;
import org.opensha.refFaultParamDb.dao.db.SiteRepresentationDB_DAO;
import org.opensha.refFaultParamDb.dao.db.SiteTypeDB_DAO;
import org.opensha.refFaultParamDb.gui.event.DbAdditionListener;
import org.opensha.refFaultParamDb.gui.event.DbAdditionSuccessEvent;
import org.opensha.refFaultParamDb.gui.infotools.GUI_Utils;
import org.opensha.refFaultParamDb.gui.view.ViewAllReferences;
import org.opensha.refFaultParamDb.vo.Reference;
import org.opensha.refFaultParamDb.vo.SiteRepresentation;
import org.opensha.refFaultParamDb.vo.SiteType;

/**
 * <p>Title: ChooseReference.java </p>
 * <p>Description: Choose a reference for this data </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class ChooseReference extends JFrame implements ActionListener,
DbAdditionListener {
	private final static String TIMESPAN_REFERENCES_PARAM_NAME="Choose Reference";
	private final static String addNewReferenceToolTipText = "Add Reference not currently in database";
	private JButton addNewReferenceButton = new JButton("Add Reference");
	private JButton viewAllRefButtons = new JButton("View All References");
	private AddNewReference addNewReference;
	private ConstrainedStringParameterEditor referencesParamEditor;
	private StringParameter referencesParam;
	private JButton okButton = new JButton("OK");
	private JButton closeButton = new JButton("Close");
	private AddSiteInfo addSiteInfo;
	private static ArrayList referenceSummaryList;
	private static ArrayList referenceList;
	private final static String SITE_TYPE_PARAM_NAME="Site Type";
	private final static String SITE_REPRESENTATION_PARAM_NAME="How Representative is this Site";
	private StringParameter siteTypeParam;
	private StringParameter siteRepresentationParam;
	private ConstrainedStringParameterEditor siteTypeParamEditor;
	private ConstrainedStringParameterEditor siteRepresentationParamEditor;
	// site type DAO
	private SiteTypeDB_DAO siteTypeDAO;
	// site representations DAO
	private SiteRepresentationDB_DAO siteRepresentationDAO;
	private final static String TITLE="Choose Reference";

	// references DAO
	private ReferenceDB_DAO referenceDAO;
	
	private DB_AccessAPI dbConnection;

	public ChooseReference(DB_AccessAPI dbConnection, AddSiteInfo addSiteInfo) {
		this.dbConnection = dbConnection;
		siteTypeDAO = new SiteTypeDB_DAO(dbConnection);
		siteRepresentationDAO = new SiteRepresentationDB_DAO(dbConnection);
		referenceDAO = new ReferenceDB_DAO(dbConnection);
		
		this.setLocationRelativeTo(null);
		this.setDefaultCloseOperation(DO_NOTHING_ON_CLOSE);
		this.addSiteInfo = addSiteInfo;
		addActionListeners();
		setTitle(TITLE);
		addNewReferenceButton.setToolTipText(addNewReferenceToolTipText);
		try {
			jbInit();
		}catch(Exception e) {
			e.printStackTrace();
		}
		pack();
	}


	/**
	 * Set the values to be shown here
	 *
	 * @param siteType
	 * @param representativeStrandIndex
	 * @param reference
	 */
	public void setParameters(String siteType, String representativeStrandIndex,
			Reference reference) {
		siteTypeParam.setValue(siteType);
		siteTypeParamEditor.refreshParamEditor();
		siteRepresentationParam.setValue(representativeStrandIndex);
		siteRepresentationParamEditor.refreshParamEditor();
		referencesParam.setValue(reference.getSummary());
		referencesParamEditor.refreshParamEditor();
	}

	/**
	 * Add action listeners to the buttons
	 */
	private void addActionListeners() {
		addNewReferenceButton.addActionListener(this);
		this.okButton.addActionListener(this);
		viewAllRefButtons.addActionListener(this);
		this.closeButton.addActionListener(this);
	}

	/**
	 * When user chooses to add a new reference
	 * @param event
	 */
	public void actionPerformed(ActionEvent event) {
		Object source = event.getSource();
		if(source == addNewReferenceButton)  {
			addNewReference = new AddNewReference(dbConnection);
			addNewReference.addDbAdditionSuccessListener(this);
		} else if(source == okButton) {
			int index = this.referenceSummaryList.indexOf((String)this.referencesParam.getValue());
			addSiteInfo.setReference((Reference)referenceList.get(index));
			addSiteInfo.setSiteType((String)this.siteTypeParam.getValue());
			addSiteInfo.setSiteRepresentativeStrandIndex((String)this.siteRepresentationParam.getValue());
			//this.dispose();
			okButton.setEnabled(false);
		} else if (source==closeButton) {
			//addSiteInfo.dispose();
			this.dispose();
		} else if(source == this.viewAllRefButtons) {
			ViewAllReferences viewAllRefs = new ViewAllReferences(dbConnection);
		}
	}

	private void jbInit() throws Exception {
		Container contentPane = this.getContentPane();
		contentPane.setLayout(GUI_Utils.gridBagLayout);
		makeReferencesParamAndEditor();
		makeSiteTypeParamAndEditor();
		makeSiteRepresentationParamAndEditor();
		int yPos=3;

		contentPane.add(viewAllRefButtons,  new GridBagConstraints(0, yPos, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(2, 2, 2, 2), 0, 0));
		contentPane.add(addNewReferenceButton,  new GridBagConstraints(1, yPos++, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(2, 2, 2, 2), 0, 0));
		contentPane.add(okButton,  new GridBagConstraints(0, yPos, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(2, 2, 2, 2), 0, 0));
		contentPane.add(closeButton,  new GridBagConstraints(1, yPos++, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(2, 2, 2, 2), 0, 0));
	}


	/**
	 * make param and editor for references
	 *
	 * @throws ConstraintException
	 */
	private void makeReferencesParamAndEditor() throws ConstraintException {
		if(referencesParamEditor!=null)
			this.remove(referencesParamEditor);
		// references
		ArrayList availableReferences = getAvailableReferences();
		this.referencesParam = new StringParameter(this.
				TIMESPAN_REFERENCES_PARAM_NAME, availableReferences,
				(String)availableReferences.get(0));
		referencesParamEditor = new ConstrainedStringParameterEditor(referencesParam);
		this.getContentPane().add(referencesParamEditor,
				new GridBagConstraints(0, 0, 2, 1, 1.0, 1.0
						, GridBagConstraints.CENTER,
						GridBagConstraints.BOTH,
						new Insets(0, 0, 0, 0), 0, 0));
	}

	/**
	 * Get a list of available references.
	 * @return
	 */
	private ArrayList getAvailableReferences() {
		this.referenceList  = referenceDAO.getAllReferencesSummary();
		this.referenceSummaryList = new ArrayList();
		for(int i=0; referenceList!=null && i<referenceList.size(); ++i)
			referenceSummaryList.add(((Reference)referenceList.get(i)).getSummary());
		return referenceSummaryList;
	}

	// make site type param and editor
	private void makeSiteTypeParamAndEditor() {

		ArrayList siteTypes = getSiteTypes();
		// available study types
		siteTypeParam = new StringParameter(SITE_TYPE_PARAM_NAME, siteTypes,
				(String)siteTypes.get(0));
		siteTypeParamEditor = new ConstrainedStringParameterEditor(siteTypeParam);
		// site types
		this.getContentPane().add(siteTypeParamEditor,  new GridBagConstraints(0, 1, 2, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(5, 5, 5, 5), 0, 0));
	}

	/**
	 * Get the study types.
	 * It gets all the SITE TYPES from the database
	 *
	 * @return
	 */
	private ArrayList getSiteTypes() {
		ArrayList siteTypeVOs = siteTypeDAO.getAllSiteTypes();
		ArrayList siteTypesList = new ArrayList();
		for(int i=0; i<siteTypeVOs.size(); ++i)
			siteTypesList.add(((SiteType)siteTypeVOs.get(i)).getSiteType());
		return siteTypesList;
	}

	// representative strand index param and editor
	private void makeSiteRepresentationParamAndEditor() {
		ArrayList siteRepresentations = getSiteRepresentations();
		// how representative is this site?
		siteRepresentationParam = new StringParameter(SITE_REPRESENTATION_PARAM_NAME, siteRepresentations,
				(String)siteRepresentations.get(0));
		siteRepresentationParamEditor = new ConstrainedStringParameterEditor(siteRepresentationParam);
		this.getContentPane().add(siteRepresentationParamEditor,  new GridBagConstraints(0, 2, 2, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(5, 5, 5, 5), 0, 0));

	}



	/**
	 * Get the site representations.
	 * It gets the SITE REPRSENTATIONS from the database
	 *
	 * @return
	 */
	private ArrayList getSiteRepresentations() {
		ArrayList siteRepresentationVOs = siteRepresentationDAO.getAllSiteRepresentations();
		ArrayList siteRepresentations = new ArrayList();
		for(int i=0; i<siteRepresentationVOs.size(); ++i) {
			siteRepresentations.add(((SiteRepresentation)siteRepresentationVOs.get(i)).getSiteRepresentationName());
		}
		return siteRepresentations;
	}





	/**
	 * This function is called whenever a new site type/ new Reference is added
	 * to the database
	 *
	 * @param event
	 */
	public void dbAdditionSuccessful(DbAdditionSuccessEvent event) {
		Object source  = event.getSource();
		if(source == this.addNewReference) makeReferencesParamAndEditor();
		this.validate();
		this.repaint();
	}
}
