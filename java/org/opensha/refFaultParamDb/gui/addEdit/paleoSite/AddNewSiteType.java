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
import org.opensha.refFaultParamDb.dao.db.SiteTypeDB_DAO;
import org.opensha.refFaultParamDb.dao.exception.DBConnectException;
import org.opensha.refFaultParamDb.dao.exception.InsertException;
import org.opensha.refFaultParamDb.gui.CommentsParameterEditor;
import org.opensha.refFaultParamDb.gui.event.DbAdditionFrame;
import org.opensha.refFaultParamDb.gui.infotools.ConnectToEmailServlet;
import org.opensha.refFaultParamDb.gui.infotools.GUI_Utils;
import org.opensha.refFaultParamDb.gui.infotools.SessionInfo;
import org.opensha.refFaultParamDb.vo.SiteType;

/**
 * <p>Title: AddNewSiteType.java </p>
 * <p>Description: Add a new site type </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class AddNewSiteType extends DbAdditionFrame implements ActionListener {
	private final static String SITE_TYPE_NAME_PARAM_NAME="Site Type Name";
	private final static String SITE_TYPE_COMMENTS_PARAM_NAME="Site Type Comments";
	private final static String SITE_TYPE_NAME_PARAM_DEFAULT="Enter Name Here";
	private final static String MSG_SITE_TYPE_NAME_MISSING = "Site Type Name is Missing";
	private final static String MSG_SINGLE_QUOTES_NOT_ALLOWED = "Single quotes are not allowed in Site type name";
	private final static String MSG_SITE_TYPE_COMMENTS_MISSING = "Site Type comments are missing";
	private StringParameter siteTypeParam;
	private StringParameter siteTypeCommentsParam;

	private StringParameterEditor siteTypeNameParameterEditor = null;
	private CommentsParameterEditor siteTypeCommentsParamEditor = null;

	private final static String NEW_SITE_TYPE_LABEL="Add New Site Type";
	private JButton okButton = new JButton("Submit");
	private JButton cancelButton = new JButton("Cancel");
	private final static String MSG_INSERT_SUCCESS = "Site type added sucessfully to the database";

	private SiteTypeDB_DAO siteTypeDAO;

	public AddNewSiteType(DB_AccessAPI dbConnection) {
		siteTypeDAO = new SiteTypeDB_DAO(dbConnection);
		//intialize the parameters and editors
		initParamsAndEditors();
		// add the editors to GUI
		addEditorsToGUI();
		// add action listeners  to the buttons
		addActionListeners();
		this.setTitle(NEW_SITE_TYPE_LABEL);
		this.pack();
		this.setLocationRelativeTo(null);
		this.setVisible(true);
	}

	/**
	 * Add the action listeners to the buttons
	 */
	private void addActionListeners() {
		this.okButton.addActionListener(this);
		this.cancelButton.addActionListener(this);
	}

	/**
	 * This fucntion is called when user clicks on "Ok" or "Cancel" button
	 * @param event
	 */
	public void actionPerformed(ActionEvent event) {
		Object source = event.getSource();
		if(source==okButton) addNewSiteType();
		else if(source==cancelButton) this.dispose();
	}

	/**
	 * Add new site type to the database
	 */
	private void addNewSiteType() {
		String siteTypeName = (String)this.siteTypeParam.getValue();
		String siteTypeComments = (String)this.siteTypeCommentsParam.getValue();
		// check that user has entered site type name
		if(siteTypeName.trim().equalsIgnoreCase("")) {
			JOptionPane.showMessageDialog(this, MSG_SITE_TYPE_NAME_MISSING);
			return;
		}
		// single quotes not allowed in site type name
		if(siteTypeName.trim().indexOf("'")>=0) {
			JOptionPane.showMessageDialog(this, MSG_SINGLE_QUOTES_NOT_ALLOWED);
			return;
		}
		// check that user has entered site type comments
		if(siteTypeComments.trim().equalsIgnoreCase("")) {
			JOptionPane.showMessageDialog(this, MSG_SITE_TYPE_COMMENTS_MISSING);
			return;
		}
		SiteType siteType = new SiteType(siteTypeName, SessionInfo.getContributor(),
				siteTypeComments);
		try {
			ConnectToEmailServlet.sendEmail(SessionInfo.getUserName()+" trying to add New SiteType to database\n"+siteType.toString());
			siteTypeDAO.addSiteType(siteType);
			// show the success message to the user
			JOptionPane.showMessageDialog(this,MSG_INSERT_SUCCESS);
			ConnectToEmailServlet.sendEmail("New SiteType "+siteTypeName +" added sucessfully by "+SessionInfo.getUserName());
			this.sendEventToListeners(siteType);
			this.dispose();
		}  catch(InsertException insertException) { // if there is problem inserting the site type
			JOptionPane.showMessageDialog(this, insertException.getMessage());
		}catch(DBConnectException connectException) {
			JOptionPane.showMessageDialog(this, connectException.getMessage());
		}

	}

	/**
	 * Add editors to GUI
	 */
	private void addEditorsToGUI() {
		Container contentPane = this.getContentPane();
		contentPane.setLayout(GUI_Utils.gridBagLayout);
		// add string parameter editor so that user can type in site type name
		int yPos =0;
		contentPane.add(siteTypeNameParameterEditor,  new GridBagConstraints(0, yPos++, 2, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(5, 5, 5, 5), 0, 0));
		contentPane.add(siteTypeCommentsParamEditor,  new GridBagConstraints(0, yPos++, 2, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(5, 5, 5, 5), 0, 0));
		// ok/cancel button
		contentPane.add(okButton,  new GridBagConstraints(0, yPos, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(5, 5, 5, 5), 0, 0));
		contentPane.add(cancelButton,  new GridBagConstraints(1, yPos++, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(5, 5, 5, 5), 0, 0));
	}

	/**
	 * Initialize parameters and editors
	 */
	private void initParamsAndEditors() {
		siteTypeParam = new StringParameter(SITE_TYPE_NAME_PARAM_NAME, SITE_TYPE_NAME_PARAM_DEFAULT);
		siteTypeCommentsParam = new StringParameter(SITE_TYPE_COMMENTS_PARAM_NAME);
		try {
			siteTypeNameParameterEditor = new StringParameterEditor(siteTypeParam);
			siteTypeCommentsParamEditor = new CommentsParameterEditor(siteTypeCommentsParam);
		}
		catch (Exception ex) {
			ex.printStackTrace();
		}
	}
}
