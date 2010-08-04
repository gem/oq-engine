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
import javax.swing.JTextField;
import javax.swing.SwingConstants;

import org.opensha.refFaultParamDb.gui.infotools.ConnectToEmailServlet;

/**
 * <p>Title: RequestUserAccount.java </p>
 * <p>Description: Request a new user account to use the database entry screens</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class RequestUserAccount extends JFrame implements ActionListener {
	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;
	
	
	private JPanel mainPanel = new JPanel();
	private JLabel emailLabel = new JLabel();
	private JLabel firstNameLabel = new JLabel();
	private JLabel lastNameLabel = new JLabel();
	private JLabel requestAccountLabel = new JLabel();
	private JTextField firstNameText = new JTextField();
	private JButton requestAccountButton = new JButton();
	private JTextField lastNameText = new JTextField();
	private JTextField emailText = new JTextField();
	private GridBagLayout gridBagLayout1 = new GridBagLayout();
	private BorderLayout borderLayout1 = new BorderLayout();
	private final static String EMAIL_MISSING = "Email is Missing";
	private final static String FIRST_NAME_MISSING = "First Name is Missing";
	private final static String LAST_NAME_MISSING = "Last Name is Missing";
	private final static String ACCOUNT_REQUEST_SUCCESS = "Your account request has been received.\n"+
	"Username and password will be emailed to you when after processing your request";

	public RequestUserAccount() {
		try {
			jbInit();
			requestAccountButton.addActionListener(this);
			pack();
			this.setLocationRelativeTo(null);
			this.setVisible(true);
		}
		catch(Exception e) {
			e.printStackTrace();
		}
	}
	public static void main(String[] args) {
		new RequestUserAccount();
	}
	private void jbInit() throws Exception {
		this.getContentPane().setLayout(borderLayout1);
		mainPanel.setLayout(gridBagLayout1);
		emailLabel.setFont(new java.awt.Font("Dialog", 1, 12));
		emailLabel.setForeground(new Color(80, 80, 133));
		emailLabel.setText("Email:");
		firstNameLabel.setFont(new java.awt.Font("Dialog", 1, 12));
		firstNameLabel.setForeground(new Color(80, 80, 133));
		firstNameLabel.setRequestFocusEnabled(true);
		firstNameLabel.setText("First Name:");
		lastNameLabel.setFont(new java.awt.Font("Dialog", 1, 12));
		lastNameLabel.setForeground(new Color(80, 80, 133));
		lastNameLabel.setText("Last Name:");
		requestAccountLabel.setFont(new java.awt.Font("Dialog", 1, 16));
		requestAccountLabel.setForeground(new Color(80, 80, 133));
		requestAccountLabel.setHorizontalAlignment(SwingConstants.CENTER);
		requestAccountLabel.setText("Request New Account");
		firstNameText.setForeground(new Color(80, 80, 133));
		firstNameText.setText("");
		requestAccountButton.setForeground(new Color(80, 80, 133));
		requestAccountButton.setText("Request Account");
		lastNameText.setText("");
		lastNameText.setForeground(new Color(80, 80, 133));
		emailText.setText("");
		emailText.setForeground(new Color(80, 80, 133));
		this.getContentPane().add(mainPanel, BorderLayout.CENTER);
		mainPanel.add(emailLabel,  new GridBagConstraints(0, 3, 1, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(19, 12, 0, 0), 73, 13));
		mainPanel.add(lastNameLabel,  new GridBagConstraints(0, 2, 1, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(18, 12, 0, 0), 39, 13));
		mainPanel.add(firstNameLabel,  new GridBagConstraints(0, 1, 1, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(26, 12, 0, 18), 25, 13));
		mainPanel.add(requestAccountLabel,  new GridBagConstraints(0, 0, 2, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(3, 33, 0, 14), 119, 13));
		mainPanel.add(firstNameText,  new GridBagConstraints(1, 1, 1, 1, 1.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(29, 11, 0, 28), 172, 3));
		mainPanel.add(lastNameText,  new GridBagConstraints(1, 2, 1, 1, 1.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(17, 11, 6, 28), 172, 3));
		mainPanel.add(emailText,  new GridBagConstraints(1, 3, 1, 1, 1.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(14, 11, 10, 28), 172, 3));
		mainPanel.add(requestAccountButton,  new GridBagConstraints(1, 4, 1, 1, 0.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(8, 60, 25, 27), 11, 7));
	}


	public void actionPerformed(ActionEvent e) {
		String email = this.emailText.getText().trim();
		String firstName = this.firstNameText.getText().trim();
		String lastName = this.lastNameText.getText().trim();
		// check that user has entered first name
		if(firstName.equalsIgnoreCase("")) {
			JOptionPane.showMessageDialog(this, FIRST_NAME_MISSING);
			return;
		}
		// check that usr has entered last name
		if(lastName.equalsIgnoreCase("")) {
			JOptionPane.showMessageDialog(this, LAST_NAME_MISSING);
			return;
		}
		//check that user has entered email
		if(email.equalsIgnoreCase("")) {
			JOptionPane.showMessageDialog(this, EMAIL_MISSING);
			return;
		}

		String message = "New account request by - "+"\n"+
		"First Name:"+firstName+"\n"+
		"Last Name:"+lastName+"\n"+
		"Email:"+email;
		ConnectToEmailServlet.sendEmail(message);
		JOptionPane.showMessageDialog(this, ACCOUNT_REQUEST_SUCCESS);
		this.dispose();
	}
}
