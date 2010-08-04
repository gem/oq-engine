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

import java.awt.Color;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.net.URL;
import java.net.URLConnection;

import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JTextField;
import javax.swing.SwingConstants;

import org.opensha.refFaultParamDb.dao.db.ContributorDB_DAO;
import org.opensha.refFaultParamDb.dao.db.DB_AccessAPI;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.servlets.UserAccountInfoServlet;
import org.opensha.refFaultParamDb.vo.Contributor;

/**
 * <p>Title: GetAccountInfo.java </p>
 * <p>Description: Retrieve the account info and mail it to user if user forgets
 * username/password </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class GetAccountInfo extends JFrame implements ActionListener {
	private JPanel jPanel1 = new JPanel();
	private JTextField emailText = new JTextField();
	private JLabel emailLabel = new JLabel();
	private JButton emailAccountInfoButton = new JButton();
	private JLabel forgotLabel = new JLabel();
	private GridBagLayout gridBagLayout1 = new GridBagLayout();
	private GridBagLayout gridBagLayout2 = new GridBagLayout();
	private final static String MSG_EMAIL_MISSING = "Email address is missing";
	private final static String MSG_INVALID_EMAIL = "Invalid email address";
	private final static String MSG_SUCCESS = "Account Info emailed successfully";
	private ContributorDB_DAO contributorDAO;

	public GetAccountInfo(DB_AccessAPI dbConnection) {
		contributorDAO = new ContributorDB_DAO(dbConnection);
		try {
			jbInit();
			emailAccountInfoButton.addActionListener(this);
			pack();
			this.setLocationRelativeTo(null);
			this.setVisible(true);
		}
		catch(Exception e) {
			e.printStackTrace();
		}
	}
	private void jbInit() throws Exception {
		this.getContentPane().setLayout(gridBagLayout2);
		jPanel1.setLayout(gridBagLayout1);
		emailText.setText("");
		emailText.setForeground(new Color(80, 80, 133));
		emailLabel.setFont(new java.awt.Font("Dialog", 1, 12));
		emailLabel.setForeground(new Color(80, 80, 133));
		emailLabel.setText("Email:");
		emailAccountInfoButton.setForeground(new Color(80, 80, 133));
		emailAccountInfoButton.setText("Email Account Info");
		forgotLabel.setFont(new java.awt.Font("Dialog", 1, 16));
		forgotLabel.setForeground(new Color(80, 80, 133));
		forgotLabel.setHorizontalAlignment(SwingConstants.CENTER);
		forgotLabel.setText("Forgot username/password");
		this.getContentPane().add(jPanel1,  new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(2, 5, 13, 24), -4, 4));
		jPanel1.add(forgotLabel,  new GridBagConstraints(0, 0, 2, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(0, 0, 0, 7), 78, 13));
		jPanel1.add(emailAccountInfoButton,  new GridBagConstraints(1, 2, 1, 1, 0.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(0, 0, 22, 33), 20, 7));
		jPanel1.add(emailLabel,  new GridBagConstraints(0, 1, 1, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(14, 17, 0, 0), 73, 13));
		jPanel1.add(emailText,  new GridBagConstraints(0, 1, 2, 1, 1.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(15, 75, 0, 31), 184, 3));
	}

	public void actionPerformed(ActionEvent event) {
		String email = this.emailText.getText().trim();
		// check that email is not missing
		if(email.equalsIgnoreCase("")) {
			JOptionPane.showMessageDialog(this, MSG_EMAIL_MISSING);
			return;
		}
		Contributor contributor = this.contributorDAO.getContributorByEmail(email);
		// check that this email address existed in the database
		if(contributor==null) {
			JOptionPane.showMessageDialog(this, MSG_INVALID_EMAIL);
			return;
		}
		// reset the password
		String password = contributorDAO.resetPasswordByEmail(email);
		// email account info to the user
		String message = "Account info - "+"\n"+
		"user name:"+contributor.getName()+"\n"+
		"Password:"+password+"\n";
		sendEmail(message, email);
		JOptionPane.showMessageDialog(this, MSG_SUCCESS);
		this.dispose();

	}


	/**
	 * Send email to database curator whenever a data is addded/removed/updated
	 * from the database.
	 *
	 * @param message
	 */
	private void sendEmail(String message, String emailTo) {
		try {
			URL emailServlet = new URL(UserAccountInfoServlet.SERVLET_ADDRESS);

			URLConnection servletConnection = emailServlet.openConnection();

			// inform the connection that we will send output and accept input
			servletConnection.setDoInput(true);
			servletConnection.setDoOutput(true);
			// Don't use a cached version of URL connection.
			servletConnection.setUseCaches(false);
			servletConnection.setDefaultUseCaches(false);
			// Specify the content type that we will send binary data
			servletConnection.setRequestProperty("Content-Type",
			"application/octet-stream");
			ObjectOutputStream toServlet = new
			ObjectOutputStream(servletConnection.getOutputStream());
			//sending the email message
			toServlet.writeObject(emailTo);
			toServlet.writeObject(message);
			toServlet.flush();
			toServlet.close();

			// Receive the "actual webaddress of all the gmt related files"
			// from the servlet after it has received all the data
			ObjectInputStream fromServlet = new
			ObjectInputStream(servletConnection.getInputStream());

			String outputFromServlet = (String) fromServlet.readObject();
			fromServlet.close();
		}catch(Exception e) {
			e.printStackTrace();
		}
	}

}
