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

package org.opensha.refFaultParamDb.gui;
import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Font;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

import javax.swing.JButton;
import javax.swing.JComboBox;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JPasswordField;
import javax.swing.JTextField;
import javax.swing.SwingConstants;
import javax.swing.UIManager;

import org.opensha.commons.util.ClassUtils;
import org.opensha.refFaultParamDb.dao.db.DB_AccessAPI;
import org.opensha.refFaultParamDb.dao.exception.DBConnectException;
import org.opensha.refFaultParamDb.gui.infotools.SessionInfo;
import org.opensha.refFaultParamDb.gui.login.ChangePassword;
import org.opensha.refFaultParamDb.gui.login.GetAccountInfo;
import org.opensha.refFaultParamDb.gui.login.RequestUserAccount;

/**
 * <p>Title: LoginWindow</p>
 * <p>Description: This class provide controlled access to the users who want to access the
 * California Reference Geologic Fault Parameter (Paleo Site) GUI </p>
 * @author : Nitin Gupta & Vipin Gupta
 * @version 1.0
 */

public class LoginWindow extends JFrame implements ActionListener {

	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;
	
	private static final boolean D= false;
	private final static String TITLE = "Login";
	private JPanel passwordPanel = new JPanel();
	private JButton loginButton = new JButton();
	private JPasswordField passwordText = new JPasswordField();
	private JLabel headerLabel = new JLabel();
	private JLabel passwordLabel = new JLabel();
	private JTextField usernameText = new JTextField();
	private JLabel userNameLabel = new JLabel();
	private JComboBox loginTypeComboBox = new JComboBox();
	private JLabel loginTypeLabel = new JLabel();

	private JButton newUserButton = new JButton();
	private JButton forgetPassButton = new JButton();
	private JButton changePassButton = new JButton();
	private GridBagLayout gridBagLayout1 = new GridBagLayout();
	private BorderLayout borderLayout1 = new BorderLayout();
	public final static String MSG_INVALID_USERNAME_PWD = "Invalid username/password";
	private final static String READ_ONLY = "Read Only";
	private final static String READ_WRITE = "Read/Write";
	private String appClassName;
	
	private DB_AccessAPI dbConnection;

	public LoginWindow(DB_AccessAPI dbConnection, String className){
		this.dbConnection = dbConnection;
		this.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		init();
		showHideUserNamePwd();
		this.appClassName = className;
	}


	public void init() {
		try {
			jbInit();
			setTitle(TITLE);
			addActionListeners();
		}
		catch(Exception e) {
			e.printStackTrace();
		}
	}

	private void addActionListeners() {
		loginButton.addActionListener(this);
		newUserButton.addActionListener(this);
		forgetPassButton.addActionListener(this);
		changePassButton.addActionListener(this);
		loginTypeComboBox.addActionListener(this);
	}

	private void jbInit() throws Exception {
		usernameText.setForeground(new Color(80, 80, 133));
		usernameText.setBackground(Color.white);
		passwordText.setBackground(Color.white);
		loginTypeComboBox.setForeground(new Color(80, 80, 133));
		loginTypeComboBox.addItem(READ_ONLY);
		loginTypeComboBox.addItem(READ_WRITE);
		this.getContentPane().setLayout(borderLayout1);
		newUserButton.setFont(new java.awt.Font("Dialog", Font.BOLD, 12));
		newUserButton.setForeground(new Color(80, 80, 133));
		newUserButton.setText("New User");
		forgetPassButton.setFont(new java.awt.Font("Dialog", Font.BOLD, 12));
		forgetPassButton.setForeground(new Color(80, 80, 133));
		forgetPassButton.setToolTipText("Forgot Password");
		forgetPassButton.setText("Forgot Passwd");
		changePassButton.setText("Change Passwd");
		changePassButton.setToolTipText("Change Password");
		changePassButton.setActionCommand("Forgot Passwd");
		changePassButton.setForeground(new Color(80, 80, 133));
		changePassButton.setFont(new java.awt.Font("Dialog", Font.BOLD, 12));
		this.getContentPane().add(passwordPanel, BorderLayout.CENTER);
		passwordPanel.setLayout(gridBagLayout1);
		loginButton.setFont(new java.awt.Font("Dialog", 1, 12));
		loginButton.setForeground(new Color(80, 80, 133));
		loginButton.setText("Login");
		passwordText.setBackground(Color.white);
		passwordText.setFont(new java.awt.Font("Dialog", 1, 12));
		passwordText.setForeground(new Color(80, 80, 133));
		headerLabel.setFont(new java.awt.Font("Dialog", 1, 16));
		headerLabel.setForeground(new Color(80, 80, 133));
		headerLabel.setHorizontalAlignment(SwingConstants.CENTER);
		headerLabel.setHorizontalTextPosition(SwingConstants.CENTER);
		headerLabel.setText("Authorizing User");
		passwordLabel.setFont(new java.awt.Font("Dialog", 1, 12));
		passwordLabel.setForeground(new Color(80, 80, 133));
		passwordLabel.setText("Enter Password:");
		userNameLabel.setFont(new java.awt.Font("Dialog", Font.BOLD, 12));
		userNameLabel.setForeground(new Color(80, 80, 133));
		userNameLabel.setText("Enter Username:");
		loginTypeLabel.setFont(new java.awt.Font("Dialog", Font.BOLD, 12));
		loginTypeLabel.setForeground(new Color(80, 80, 133));
		loginTypeLabel.setText("Login Type:");

		passwordPanel.add(headerLabel, new GridBagConstraints(0, 0, 5, 1, 0.0, 0.0
				, GridBagConstraints.WEST, GridBagConstraints.NONE,
				new Insets(6, 2, 0, 4), 271, 13));
		passwordPanel.add(passwordText,  new GridBagConstraints(1, 3, 2, 1, 1.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(9, 7, 7, 23), 134, 3));
		passwordPanel.add(passwordLabel,  new GridBagConstraints(0, 3, 1, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(10, 9, 0, 0), 20, 13));
		passwordPanel.add(userNameLabel,  new GridBagConstraints(0, 2, 1, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(21, 9, 0, 0), 20, 13));
		passwordPanel.add(usernameText,  new GridBagConstraints(1, 2, 2, 1, 1.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(21, 7, 6, 23), 132, 2));
		passwordPanel.add(this.loginTypeLabel,  new GridBagConstraints(0, 1, 1, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(21, 9, 0, 0), 20, 13));
		passwordPanel.add(this.loginTypeComboBox,  new GridBagConstraints(1, 1, 2, 1, 1.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(21, 7, 6, 23), 132, 2));
		passwordPanel.add(headerLabel,  new GridBagConstraints(0, 0, 3, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(13, 41, 0, 36), 86, 0));
		passwordPanel.add(forgetPassButton,  new GridBagConstraints(0, 4, 2, 1, 0.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(7, 9, 0, 0), 5, 0));
		passwordPanel.add(loginButton,  new GridBagConstraints(2, 4, 1, 1, 0.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(0, 58, 0, 23), 5, 0));
		passwordPanel.add(changePassButton,  new GridBagConstraints(0, 5, 2, 1, 0.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(8, 9, 26, 0), 6, 0));
		passwordPanel.add(newUserButton,  new GridBagConstraints(2, 5, 1, 1, 0.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(6, 39, 26, 23), 0, 0));
		/*passwordPanel.add(cancelButton, new GridBagConstraints(1, 3, 2, 1, 0.0, 0.0
        , GridBagConstraints.CENTER, GridBagConstraints.NONE,
        new Insets(24, 0, 24, 0), 9, 0));

    passwordPanel.add(newUserButton,
                      new GridBagConstraints(3, 3, 1, 1, 0.0, 0.0
                                             , GridBagConstraints.CENTER,
                                             GridBagConstraints.NONE,
                                             new Insets(24, 0, 24, 0), 0, 0));
    passwordPanel.add(forgetPassButton,
                      new GridBagConstraints(4, 3, 1, 1, 0.0, 0.0
                                             , GridBagConstraints.CENTER,v
                                             GridBagConstraints.NONE,
                                             new Insets(24, 0, 24, 45), -29, 0));*/
		pack();
		this.setLocationRelativeTo(null);
		this.setVisible(true);
	}

	/**
	 * This function is called when any button is clicked on this window
	 * @param event
	 */
	public void actionPerformed(ActionEvent event) {
		Object source = event.getSource();
		if(source==loginButton) { // if login button is clicked, save the username/passwd

			// check username/password for read /write access
			if(this.loginTypeComboBox.getSelectedItem().equals(READ_WRITE)) {
				SessionInfo.setPassword(new String(passwordText.getPassword()).trim());
				SessionInfo.setUserName(this.usernameText.getText());
				try {
					SessionInfo.setContributorInfo();
					if(SessionInfo.getContributor()==null)  {
						JOptionPane.showMessageDialog(this, MSG_INVALID_USERNAME_PWD);
						return;
					}
				}catch(DBConnectException connectException) {
					//connectException.printStackTrace();
					JOptionPane.showMessageDialog(this,MSG_INVALID_USERNAME_PWD);
					return;
				}
			}
			//    show the next application
			ClassUtils.createNoArgConstructorClassInstance(appClassName);

			//PaleoSiteApp2 paleoSiteApp = new PaleoSiteApp2();
			this.dispose();
		} else if(source == newUserButton) {
			new RequestUserAccount();
		} else if(source == forgetPassButton) {
			new GetAccountInfo(dbConnection);
		} else if(source == changePassButton) {
			new ChangePassword(dbConnection);
		} else if(source == this.loginTypeComboBox) {
			showHideUserNamePwd();
		}
	}

	private void showHideUserNamePwd() {
		String selected = (String)loginTypeComboBox.getSelectedItem();
		if(selected.equalsIgnoreCase(READ_ONLY)) {
			this.userNameLabel.setVisible(false);
			this.usernameText.setVisible(false);
			this.passwordLabel.setVisible(false);
			this.passwordText.setVisible(false);
			newUserButton.setVisible(false);
			forgetPassButton.setVisible(false);
			changePassButton.setVisible(false);
		} else {
			this.userNameLabel.setVisible(true);
			this.usernameText.setVisible(true);
			this.passwordLabel.setVisible(true);
			this.passwordText.setVisible(true);
			newUserButton.setVisible(true);
			forgetPassButton.setVisible(true);
			changePassButton.setVisible(true);
		}
	}

	//static initializer for setting look & feel
	static {
//		String osName = System.getProperty("os.name");
		try {
			UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
		}
		catch(Exception e) {
		}
	}

}
