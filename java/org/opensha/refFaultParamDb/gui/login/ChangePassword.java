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

package org.opensha.refFaultParamDb.gui.login;

import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JPasswordField;
import javax.swing.JTextField;
import javax.swing.SwingConstants;

import org.opensha.refFaultParamDb.dao.db.ContributorDB_DAO;
import org.opensha.refFaultParamDb.dao.db.DB_AccessAPI;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.exception.DBConnectException;
import org.opensha.refFaultParamDb.gui.LoginWindow;
import org.opensha.refFaultParamDb.gui.infotools.SessionInfo;

/**
 * <p>Title: ChangePassword.java </p>
 * <p>Description: Change the password for the user</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class ChangePassword extends JFrame implements ActionListener {
	private JPanel mainPanel = new JPanel();
	private JLabel changePasswordLabel = new JLabel();
	private JLabel userNameLabel = new JLabel();
	private JTextField userNameText = new JTextField();
	private JLabel oldPwdLabel = new JLabel();
	private JLabel newPwdLabel = new JLabel();
	private JLabel confirmNewPwdLabel = new JLabel();
	private JPasswordField oldPwdText = new JPasswordField();
	private JPasswordField newPwdText = new JPasswordField();
	private JPasswordField confirmNewPwdText = new JPasswordField();
	private JButton changePasswordButton = new JButton();
	private GridBagLayout gridBagLayout1 = new GridBagLayout();
	private BorderLayout borderLayout1 = new BorderLayout();
	private final static String MSG_USERNAME_MISSING = "Username is missing";
	private final static String MSG_CURRENT_PWD_MISSING = "Current Password is missing";
	private final static String MSG_NEW_PWD_MISSING = "New Password is missing";
	private final static String MSG_NEW_PWDS_DIFFERENT = "New Passwords are different";
	private final static String MSG_PWD_CHANGE_SUCCESS = "Password changed successful";
	private final static String MSG_PWD_CHANGE_FAILED = "Password change failed\n"+
	"Check username and current password";

	private ContributorDB_DAO contributorDAO;

	public ChangePassword(DB_AccessAPI dbConnection) {
		contributorDAO = new ContributorDB_DAO(dbConnection);
		try {
			jbInit();
			changePasswordButton.addActionListener(this);
			this.pack();
			this.setLocationRelativeTo(null);
			this.setVisible(true);
		}
		catch(Exception e) {
			e.printStackTrace();
		}
	}
	private void jbInit() throws Exception {
		this.getContentPane().setLayout(borderLayout1);
		mainPanel.setLayout(gridBagLayout1);
		changePasswordLabel.setFont(new java.awt.Font("Dialog", 1, 16));
		changePasswordLabel.setForeground(new Color(80, 80, 133));
		changePasswordLabel.setHorizontalAlignment(SwingConstants.CENTER);
		changePasswordLabel.setText("Change Password");
		userNameLabel.setFont(new java.awt.Font("Dialog", 1, 12));
		userNameLabel.setForeground(new Color(80, 80, 133));
		userNameLabel.setRequestFocusEnabled(true);
		userNameLabel.setText("Username:");
		userNameText.setForeground(new Color(80, 80, 133));
		userNameText.setText("");
		oldPwdLabel.setFont(new java.awt.Font("Dialog", 1, 12));
		oldPwdLabel.setForeground(new Color(80, 80, 133));
		oldPwdLabel.setText("Old Password:");
		newPwdLabel.setFont(new java.awt.Font("Dialog", 1, 12));
		newPwdLabel.setForeground(new Color(80, 80, 133));
		newPwdLabel.setText("New Password:");
		confirmNewPwdLabel.setFont(new java.awt.Font("Dialog", 1, 12));
		confirmNewPwdLabel.setForeground(new Color(80, 80, 133));
		confirmNewPwdLabel.setRequestFocusEnabled(true);
		confirmNewPwdLabel.setText("Confirm New Password:");
		oldPwdText.setFont(new java.awt.Font("Dialog", 1, 12));
		oldPwdText.setForeground(new Color(80, 80, 133));
		oldPwdText.setText("");
		newPwdText.setText("");
		newPwdText.setFont(new java.awt.Font("Dialog", 1, 12));
		newPwdText.setForeground(new Color(80, 80, 133));
		confirmNewPwdText.setText("");
		confirmNewPwdText.setFont(new java.awt.Font("Dialog", 1, 12));
		confirmNewPwdText.setForeground(new Color(80, 80, 133));
		changePasswordButton.setForeground(new Color(80, 80, 133));
		changePasswordButton.setText("Change Password");
		this.getContentPane().add(mainPanel, BorderLayout.CENTER);
		mainPanel.add(userNameLabel,  new GridBagConstraints(0, 1, 1, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(26, 18, 0, 65), 27, 13));
		mainPanel.add(oldPwdLabel,  new GridBagConstraints(0, 2, 1, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(18, 18, 0, 53), 20, 13));
		mainPanel.add(newPwdLabel,  new GridBagConstraints(0, 3, 1, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(19, 18, 0, 49), 18, 13));
		mainPanel.add(confirmNewPwdLabel,  new GridBagConstraints(0, 4, 1, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(18, 18, 0, 0), 20, 13));
		mainPanel.add(userNameText,  new GridBagConstraints(1, 1, 1, 1, 1.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(28, 16, 0, 23), 163, 3));
		mainPanel.add(oldPwdText,  new GridBagConstraints(1, 2, 1, 1, 1.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(20, 16, 0, 23), 164, 4));
		mainPanel.add(confirmNewPwdText,  new GridBagConstraints(1, 4, 1, 1, 1.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(20, 16, 0, 23), 164, 4));
		mainPanel.add(newPwdText,  new GridBagConstraints(1, 3, 1, 1, 1.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(21, 16, 0, 23), 164, 4));
		mainPanel.add(changePasswordButton,  new GridBagConstraints(1, 5, 1, 1, 0.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(11, 37, 20, 23), 21, 4));
		mainPanel.add(changePasswordLabel,  new GridBagConstraints(0, 0, 2, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(2, 39, 0, 55), 148, 13));
	}

	public void actionPerformed(ActionEvent event) {
		String userName = this.userNameText.getText().trim();
		String oldPwd = (new String(oldPwdText.getPassword())).trim();
		String newPwd = (new String(this.newPwdText.getPassword())).trim();
		String confirmNewPwdText = (new String(this.confirmNewPwdText.getPassword())).trim();
		// check that username has been entered
		if(userName.equalsIgnoreCase("")) {
			JOptionPane.showMessageDialog(this, MSG_USERNAME_MISSING);
			return;
		}
		// check that old password has been entered
		if(oldPwd.equalsIgnoreCase("")) {
			JOptionPane.showMessageDialog(this, MSG_CURRENT_PWD_MISSING);
			return;
		}
		// check that new passwords have been entered
		if(newPwd.equalsIgnoreCase("") || confirmNewPwdText.equalsIgnoreCase("")) {
			JOptionPane.showMessageDialog(this, MSG_NEW_PWD_MISSING);
			return;
		}
		// check that new passwords in both fields are same
		if(!newPwd.equalsIgnoreCase(confirmNewPwdText)) {
			JOptionPane.showMessageDialog(this, MSG_NEW_PWDS_DIFFERENT);
			return;
		}
		// check that user has entered the correct current username/password
		SessionInfo.setUserName(userName);
		SessionInfo.setPassword(oldPwd);
		SessionInfo.setContributorInfo();
		try {
			SessionInfo.setContributorInfo();
			if(SessionInfo.getContributor()==null)  {
				JOptionPane.showMessageDialog(this, LoginWindow.MSG_INVALID_USERNAME_PWD);
				return;
			}
		}catch(DBConnectException connectException) {
			//connectException.printStackTrace();
			JOptionPane.showMessageDialog(this,LoginWindow.MSG_INVALID_USERNAME_PWD);
			return;
		}
		boolean success =  contributorDAO.updatePassword(userName, oldPwd, newPwd);
		if(success) {
			JOptionPane.showMessageDialog(this, MSG_PWD_CHANGE_SUCCESS);
			this.dispose();
		} else {
			JOptionPane.showMessageDialog(this, MSG_PWD_CHANGE_FAILED);
		}
	}
}
