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

package org.opensha.sha.gui.infoTools;

import java.awt.BorderLayout;
import java.awt.Component;
import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.net.URL;
import java.net.URLConnection;

import javax.swing.JButton;
import javax.swing.JDialog;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextField;
import javax.swing.JTextPane;


/**
 * <p>Title: ExceptionWindow</p>
 * <p>Description: This application window gets popped up whenever the
 * any application crashes. When application aburptly crashes this window gets popped up
 * with exception that occured. When this window pops up user can also specify how
 * that exception (what was user trying to do) occured. An email will be send out
 * to the people maintaining the system. </p>
 * @author : Nitin Gupta and Vipin Gupta
 * @created
 * @version 1.0
 */

public class ExceptionWindow extends JDialog {
	private JPanel jPanel1 = new JPanel();
	private JLabel exceptionLabel = new JLabel();
	private JScrollPane exceptionScrollPane = new JScrollPane();
	private JTextPane exceptionTextPane = new JTextPane();
	private JScrollPane errorDescriptionPanel = new JScrollPane();
	private JTextPane errorTextPanel = new JTextPane();
	private JLabel jLabel1 = new JLabel();
	private JButton sendButton = new JButton();
	private JButton cancelButton = new JButton();
	private BorderLayout borderLayout1 = new BorderLayout();
	private JLabel emailLabel = new JLabel();
	private JTextField emailText = new JTextField();

	//servlet ( to send the mail)
	private static final String SERVLET_URL = "http://gravity.usc.edu/OpenSHA/servlet/EmailServlet";

	//TITLE of this window
	private static final String TITLE = "Application bug reporting window";
	private static final boolean D = false;
	private GridBagLayout gridBagLayout1 = new GridBagLayout();

	public ExceptionWindow(Component parent,Throwable t,String selectedParametersInfo) {

		try {
			//making the exception window be the most active window
			setModal(true);
			//user is forced to use the "button" operations.
			setDefaultCloseOperation(DO_NOTHING_ON_CLOSE);
			// show the window at center of the parent component
			if (parent != null) {
				this.setLocation(parent.getX()+parent.getWidth()/2,
						parent.getY()+parent.getHeight()/2);
			}
			jbInit();

			String expMessage = t.toString() + "\n";

			StackTraceElement[] exceptionText = t.getStackTrace();

			for(int i=0;i<exceptionText.length;++i)
				expMessage +=exceptionText[i]+"\n";

			String exceptionMessage = expMessage+"\n\n"+
			"Selected Parameters Info :\n"+
			"---------------------\n\n"+selectedParametersInfo;


			exceptionTextPane.setText(exceptionMessage);
		}
		catch(Exception e) {
			e.printStackTrace();
		}
	}

	public ExceptionWindow(Component parent,StackTraceElement[] exceptionText,String selectedParametersInfo) {

		try {
			//making the exception window be the most active window
			setModal(true);
			//user is forced to use the "button" operations.
			setDefaultCloseOperation(DO_NOTHING_ON_CLOSE);
			// show the window at center of the parent component
//			this.setLocation(parent.getX()+parent.getWidth()/2,
//			parent.getY()+parent.getHeight()/2);
			this.setLocationRelativeTo(parent);
			jbInit();

			String expMessage = "";

			for(int i=0;i<exceptionText.length;++i)
				expMessage +=exceptionText[i]+"\n";

			String exceptionMessage = expMessage+"\n\n"+
			"Selected Parameters Info :\n"+
			"---------------------\n\n"+selectedParametersInfo;


			exceptionTextPane.setText(exceptionMessage);
		}
		catch(Exception e) {
			e.printStackTrace();
		}
	}
	/*public static void main(String[] args) {
    ExceptionWindow exceptionWindow = new ExceptionWindow("Hello");
    exceptionWindow.setVisible(true);
    exceptionWindow.pack();
  }*/
	private void jbInit() throws Exception {
		this.getContentPane().setLayout(borderLayout1);
		jPanel1.setLayout(gridBagLayout1);
		exceptionLabel.setFont(new java.awt.Font("Lucida Grande", 1, 17));
		exceptionLabel.setText("Exception Occured:");
		exceptionTextPane.setEditable(false);
		jLabel1.setFont(new java.awt.Font("Lucida Grande", 1, 17));
		jLabel1.setText("Brief desc. of how problem occured:");
		sendButton.setActionCommand("cancelButton");
		sendButton.setText("Send");
		sendButton.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				sendButton_actionPerformed(e);
			}
		});
		cancelButton.setActionCommand("cancelButton");
		cancelButton.setText("Cancel");
		cancelButton.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				cancelButton_actionPerformed(e);
			}
		});
		emailLabel.setText("Enter your email:");
		jPanel1.setMinimumSize(new Dimension(100, 100));
		jPanel1.setPreferredSize(new Dimension(470, 330));
		this.getContentPane().add(jPanel1, BorderLayout.CENTER);
		jPanel1.add(exceptionScrollPane,  new GridBagConstraints(0, 1, 3, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(0, 8, 0, 8), 418, 65));
		exceptionScrollPane.getViewport().add(exceptionTextPane, null);
		jPanel1.add(errorDescriptionPanel,  new GridBagConstraints(0, 3, 3, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(0, 8, 0, 8), 418, 61));
		errorDescriptionPanel.getViewport().add(errorTextPanel, null);
		jPanel1.add(jLabel1,  new GridBagConstraints(0, 2, 3, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(12, 14, 0, 43), 93, 8));
		jPanel1.add(exceptionLabel,  new GridBagConstraints(0, 0, 3, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(12, 15, 0, 123), 148, 12));
		jPanel1.add(emailLabel,  new GridBagConstraints(0, 4, 1, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(11, 14, 6, 0), 31, 13));
		jPanel1.add(sendButton,  new GridBagConstraints(1, 5, 1, 1, 0.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(23, 44, 17, 0), 1, 10));
		jPanel1.add(emailText,  new GridBagConstraints(1, 4, 2, 1, 1.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(11, 0, 0, 114), 170, 16));
		jPanel1.add(cancelButton,  new GridBagConstraints(2, 5, 1, 1, 0.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(23, 25, 17, 56), 0, 10));
		emailText.setText("");
		this.setSize(500,600);
	}

	void cancelButton_actionPerformed(ActionEvent e) {
		this.dispose();
		System.exit(0);
	}

	void sendButton_actionPerformed(ActionEvent e) {

		String email = emailText.getText();
		if(email.trim().equalsIgnoreCase("")) {
			JOptionPane.showMessageDialog(this, "Please Enter email Address");
			return;
		}
		if(email.indexOf("@") ==-1 || email.indexOf(".") ==-1) {
			JOptionPane.showMessageDialog(this, "Please Enter valid email Address");
			return;
		}
		else{
			String emailMessage = "Application Exception\n"+
			"----------------------\n"+
			exceptionTextPane.getText()+"\n\n\n"+
			"Exception Description (as provided by user)\n"+
			"----------------------\n"+
			errorTextPanel.getText();
			//establishing connection with servlet to email exception message to system maintainer
			sendParametersToServlet(email,emailMessage);
			dispose();
			System.exit(0);
		}
	}


	/**
	 * sets up the connection with the servlet on the server (gravity.usc.edu), to send the mail
	 */
	private void sendParametersToServlet(String email,String emailMessage) {

		try{
			if(D) System.out.println("starting to make connection with servlet");
			URL hazardMapServlet = new URL(SERVLET_URL);


			URLConnection servletConnection = hazardMapServlet.openConnection();
			if(D) System.out.println("connection established");

			// inform the connection that we will send output and accept input
			servletConnection.setDoInput(true);
			servletConnection.setDoOutput(true);

			// Don't use a cached version of URL connection.
			servletConnection.setUseCaches (false);
			servletConnection.setDefaultUseCaches (false);
			// Specify the content type that we will send binary data
			servletConnection.setRequestProperty ("Content-Type","application/octet-stream");

			ObjectOutputStream toServlet = new
			ObjectOutputStream(servletConnection.getOutputStream());


			//sending email address to the servlet
			toServlet.writeObject(email);

			//sending the email message to the servlet
			toServlet.writeObject(emailMessage);


			toServlet.flush();
			toServlet.close();

			// Receiving the "email sent" message from servlet
			ObjectInputStream fromServlet = new ObjectInputStream(servletConnection.getInputStream());
			String sentEmailText=(String)fromServlet.readObject();
			fromServlet.close();

		}catch (Exception e) {
			System.out.println("Exception in connection with servlet:" +e);
			e.printStackTrace();
		}
	}




}
