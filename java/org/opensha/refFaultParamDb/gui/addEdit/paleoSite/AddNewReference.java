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

import javax.swing.JButton;
import javax.swing.JOptionPane;

import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.StringParameterEditor;
import org.opensha.refFaultParamDb.dao.db.DB_AccessAPI;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.ReferenceDB_DAO;
import org.opensha.refFaultParamDb.dao.exception.DBConnectException;
import org.opensha.refFaultParamDb.dao.exception.InsertException;
import org.opensha.refFaultParamDb.gui.CommentsParameterEditor;
import org.opensha.refFaultParamDb.gui.event.DbAdditionFrame;
import org.opensha.refFaultParamDb.gui.infotools.ConnectToEmailServlet;
import org.opensha.refFaultParamDb.gui.infotools.GUI_Utils;
import org.opensha.refFaultParamDb.gui.infotools.SessionInfo;
import org.opensha.refFaultParamDb.gui.view.ViewAllReferences;
import org.opensha.refFaultParamDb.vo.Reference;

/**
 * <p>Title: AddNewReference.java </p>
 * <p>Description: Add a new Reference </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class AddNewReference extends DbAdditionFrame implements ActionListener {
	private final static String AUTHOR_PARAM_NAME="Short Citation";
	private final static String AUTHOR_PARAM_DEFAULT="e.g. Knight & Dey";
	private final static String BIBLIO_PARAM_NAME="Full Bibliographic Ref";
	private final static String BIBLIO_PARAM_DEFAULT="Enter full citation here";
	private final static String YEAR_PARAM_NAME="Year";
	private final static String MSG_AUTHOR = "Author is missing";
	private final static String MSG_FULL_BIBLIO = "Full Bibliographic Reference is missing";
	private final static String MSG_YEAR = "Year is missing";
	private StringParameter authorParam;
	private StringParameter biblioParam;
	private StringParameter yearParam;
	private StringParameterEditor authorParameterEditor;
	private CommentsParameterEditor biblioParameterEditor;
	private StringParameterEditor yearParamEditor;
	private final static String NEW_SITE_TYPE_LABEL="Add Reference";
	private JButton okButton = new JButton("Submit");
	private JButton cancelButton = new JButton("Cancel");
	private JButton viewAllRefsButton = new JButton("View All References");
	private ReferenceDB_DAO referenceDAO;
	private final static String MSG_INSERT_SUCCESS = "Reference added sucessfully to the database";
	private final static String MSG_SINGLE_QUOTES_NOT_ALLOWED = "Single quotes are not allowed for author, year or full bibliographic reference";
	
	private DB_AccessAPI dbConnection;
	
	public AddNewReference(DB_AccessAPI dbConnection) {
		this.dbConnection = dbConnection;
		referenceDAO = new ReferenceDB_DAO(dbConnection);
		initParamsAndEditors();
		addEditorsToGUI();
		addActionListeners();
		this.setTitle(NEW_SITE_TYPE_LABEL);
		this.pack();
		setSize(400,400);
		this.setLocationRelativeTo(null);
		this.setVisible(true);
	}

	/**
	 * Add action listeners to the button
	 */
	private void addActionListeners() {
		okButton.addActionListener(this);
		this.cancelButton.addActionListener(this);
		viewAllRefsButton.addActionListener(this);
	}

	/**
	 * This function is called when ok or cancel button is clicked
	 * @param event
	 */
	public void actionPerformed(ActionEvent event) {
		Object source = event.getSource();
		if(source == okButton) {
			// add the reference to the database
			addReferenceToDatabase();
		}else if(source==cancelButton) this.dispose();
		else if(source == viewAllRefsButton) {
			new ViewAllReferences(dbConnection);
		}
	}

	/**
	 * Add the reference to the database
	 */
	private void addReferenceToDatabase() {
		String author = (String)this.authorParam.getValue();
		String fullBiblio = (String)this.biblioParam.getValue();
		String year = (String)this.yearParam.getValue();
		// check that usr has provided both short citation as well as full Biblio reference
		if (author == null || author.trim().equalsIgnoreCase("")) {
			JOptionPane.showMessageDialog(this, this.MSG_AUTHOR);
			return;
		}
		// check that  full bibliographic reference has been filled
		if (fullBiblio == null || fullBiblio.trim().equalsIgnoreCase("")) {
			JOptionPane.showMessageDialog(this, this.MSG_FULL_BIBLIO);
			return;
		}
		// check that year value has been filled
		if (year == null || year.trim().equalsIgnoreCase("")) {
			JOptionPane.showMessageDialog(this, this.MSG_YEAR);
			return;
		}
		// single quotes are not allowed
		if (author.indexOf("'") >= 0 || fullBiblio.indexOf("'") >= 0 ||
				year.indexOf("'") >= 0) {
			JOptionPane.showMessageDialog(this, this.MSG_SINGLE_QUOTES_NOT_ALLOWED);
			return;
		}

		try { // catch the insert exception
			Reference reference = new Reference(author, year, fullBiblio);
			ConnectToEmailServlet.sendEmail(SessionInfo.getUserName()+" trying to add new Reference to database\n"+reference.toString());
			referenceDAO.addReference(reference);
			this.sendEventToListeners(reference);
			JOptionPane.showMessageDialog(this, MSG_INSERT_SUCCESS);
			ConnectToEmailServlet.sendEmail("New Reference "+fullBiblio +" added sucessfully by "+SessionInfo.getUserName());
			this.dispose();
		}catch(InsertException insertException) { // if there is problem inserting the reference
			JOptionPane.showMessageDialog(this, insertException.getMessage());
		}catch(DBConnectException connectException) {
			JOptionPane.showMessageDialog(this, connectException.getMessage());
		}
	}

	/**
	 * Add editors to the GUI
	 */
	private void addEditorsToGUI() {
		Container contentPane = this.getContentPane();
		contentPane.setLayout(GUI_Utils.gridBagLayout);
		int yPos = 0;
		// author parameter
		contentPane.add(authorParameterEditor,  new GridBagConstraints(0, yPos++, 2, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(5, 5, 5, 5), 0, 0));
		// year parameter
		contentPane.add(this.yearParamEditor,  new GridBagConstraints(0, yPos++, 2, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(5, 5, 5, 5), 0, 0));
		// full bibliographic information
		contentPane.add(biblioParameterEditor,  new GridBagConstraints(0, yPos++, 2, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(5, 5, 5, 5), 0, 0));
		contentPane.add(this.viewAllRefsButton,  new GridBagConstraints(1, yPos++, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(5, 5, 5, 5), 0, 0));
		// ok/cancel button
		contentPane.add(okButton,  new GridBagConstraints(0, yPos, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(5, 5, 5, 5), 0, 0));
		contentPane.add(cancelButton,  new GridBagConstraints(1, yPos++, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(5, 5, 5, 5), 0, 0));
	}

	/**
	 * initialize parameters and editors
	 */
	private void initParamsAndEditors() {
		authorParam = new StringParameter(AUTHOR_PARAM_NAME, AUTHOR_PARAM_DEFAULT);
		biblioParam = new StringParameter(BIBLIO_PARAM_NAME, BIBLIO_PARAM_DEFAULT);
		this.yearParam = new StringParameter(this.YEAR_PARAM_NAME);
		authorParameterEditor = null;
		biblioParameterEditor = null;
		try {
			authorParameterEditor = new StringParameterEditor(authorParam);
			biblioParameterEditor = new CommentsParameterEditor(biblioParam);
			yearParamEditor = new StringParameterEditor(yearParam);
		}
		catch (Exception ex) {
			ex.printStackTrace();
		}
	}
}
