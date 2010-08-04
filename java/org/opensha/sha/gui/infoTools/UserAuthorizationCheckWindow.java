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
import java.awt.Color;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.ObjectInputStream;
import java.net.URL;
import java.net.URLConnection;

import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JPasswordField;
import javax.swing.JTextField;
import javax.swing.SwingConstants;

/**
 * <p>Title: UserAuthorizationCheckWindow</p>
 * <p>Description: This class provide controlled access to the users who want to generate
 * the datasets for the Hazard Maps using Condor at University of Southern California.</p>
 * @author : Nitin Gupta & Vipin Gupta
 * @version 1.0
 */

public class UserAuthorizationCheckWindow extends JFrame {

  private static final boolean D= false;

  private JPanel passwordPanel = new JPanel();
  private JButton continueButton = new JButton();
  private JPasswordField passwordText = new JPasswordField();
  private JLabel jLabel5 = new JLabel();
  private JButton cancelButton = new JButton();
  private JLabel jLabel2 = new JLabel();
  JTextField usernameText = new JTextField();
  JLabel jLabel1 = new JLabel();
  BorderLayout borderLayout1 = new BorderLayout();

  //checks if user did successful login
  private boolean loginSuccess = false;


  //Servlet address
  private final static String SERVLET_ADDRESS = "http://gravity.usc.edu/OpenSHA/servlet/CheckAuthorizationServlet";
  JButton newUserButton = new JButton();
  JButton forgetPassButton = new JButton();
  GridBagLayout gridBagLayout1 = new GridBagLayout();
  public UserAuthorizationCheckWindow(){
    init();
  }


  public void init() {
    try {
      jbInit();
    }
    catch(Exception e) {
      e.printStackTrace();
    }
  }

  private void jbInit() throws Exception {
    //this.setDefaultCloseOperation(this.EXIT_ON_CLOSE);
    usernameText.setForeground(new Color(80, 80, 133));
    usernameText.setBackground(Color.white);
    passwordText.setBackground(Color.white);
    this.getContentPane().setLayout(borderLayout1);
    newUserButton.setFont(new java.awt.Font("Dialog", Font.BOLD, 12));
    newUserButton.setForeground(new Color(80, 80, 133));
    newUserButton.setText("New User");
    newUserButton.addActionListener(new ActionListener() {
      public void actionPerformed(ActionEvent actionEvent) {
        newUserButton_actionPerformed(actionEvent);
      }
    });
    forgetPassButton.setFont(new java.awt.Font("Dialog", Font.BOLD, 12));
    forgetPassButton.setForeground(new Color(80, 80, 133));
    forgetPassButton.setToolTipText("Forgot Password");
    forgetPassButton.setText("Forgot Passwd");
    forgetPassButton.addActionListener(new ActionListener() {
      public void actionPerformed(ActionEvent actionEvent) {
        forgetPassButton_actionPerformed(actionEvent);
      }
    });
    this.getContentPane().add(passwordPanel, java.awt.BorderLayout.CENTER);
    passwordPanel.setLayout(gridBagLayout1);
    continueButton.setFont(new java.awt.Font("Dialog", 1, 12));
    continueButton.setForeground(new Color(80, 80, 133));
    continueButton.setText("Continue");
    continueButton.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        continueButton_actionPerformed(e);
      }
    });
    passwordText.setBackground(Color.white);
    passwordText.setFont(new java.awt.Font("Dialog", 1, 12));
    passwordText.setForeground(new Color(80, 80, 133));
    jLabel5.setFont(new java.awt.Font("Dialog", 1, 16));
    jLabel5.setForeground(new Color(80, 80, 133));
    jLabel5.setHorizontalAlignment(SwingConstants.CENTER);
    jLabel5.setHorizontalTextPosition(SwingConstants.CENTER);
    jLabel5.setText("Authorizing User");
    cancelButton.setFont(new java.awt.Font("Dialog", 1, 12));
    cancelButton.setForeground(new Color(80, 80, 133));
    cancelButton.setText("Cancel");
    cancelButton.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        cancelButton_actionPerformed(e);
      }
    });
    jLabel2.setFont(new java.awt.Font("Dialog", 1, 12));
    jLabel2.setForeground(new Color(80, 80, 133));
    jLabel2.setText("Enter Password:");
    jLabel1.setFont(new java.awt.Font("Dialog", Font.BOLD, 12));
    jLabel1.setForeground(new Color(80, 80, 133));
    jLabel1.setText("Enter Username:");
    passwordPanel.add(jLabel5, null);
    passwordPanel.add(jLabel5, new GridBagConstraints(0, 0, 5, 1, 0.0, 0.0
        , GridBagConstraints.WEST, GridBagConstraints.NONE,
        new Insets(6, 2, 0, 4), 271, 13));
    passwordPanel.add(usernameText, new GridBagConstraints(2, 1, 3, 1, 1.0, 0.0
        , GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL,
        new Insets(24, 0, 0, 83), 186, 7));
    passwordPanel.add(passwordText, new GridBagConstraints(2, 2, 3, 1, 1.0, 0.0
        , GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL,
        new Insets(8, 0, 0, 83), 186, 9));
    passwordPanel.add(jLabel1, new GridBagConstraints(0, 1, 2, 1, 0.0, 0.0
        , GridBagConstraints.WEST, GridBagConstraints.NONE,
        new Insets(25, 8, 0, 0), 20, 13));
    passwordPanel.add(jLabel2, new GridBagConstraints(0, 2, 2, 1, 0.0, 0.0
        , GridBagConstraints.WEST, GridBagConstraints.NONE,
        new Insets(10, 8, 0, 0), 20, 13));
    passwordPanel.add(cancelButton, new GridBagConstraints(1, 3, 2, 1, 0.0, 0.0
        , GridBagConstraints.CENTER, GridBagConstraints.NONE,
        new Insets(24, 0, 24, 0), 9, 0));
    passwordPanel.add(continueButton,
                      new GridBagConstraints(0, 3, 1, 1, 0.0, 0.0
                                             , GridBagConstraints.CENTER,
                                             GridBagConstraints.NONE,
                                             new Insets(24, 25, 24, 0), 5, 0));
    passwordPanel.add(newUserButton,
                      new GridBagConstraints(3, 3, 1, 1, 0.0, 0.0
                                             , GridBagConstraints.CENTER,
                                             GridBagConstraints.NONE,
                                             new Insets(24, 0, 24, 0), 0, 0));
    passwordPanel.add(forgetPassButton,
                      new GridBagConstraints(4, 3, 1, 1, 0.0, 0.0
                                             , GridBagConstraints.CENTER,
                                             GridBagConstraints.NONE,
                                             new Insets(24, 0, 24, 45), -29, 0));
    pack();
    //this.setSize(370,200);
    Dimension d = Toolkit.getDefaultToolkit().getScreenSize();
    this.setLocation( (d.width - this.getSize().width) / 2,
                     (d.height - this.getSize().height) / 2);
  }



  /**
   * Makes the connection to the servlet if user enters the correct password &
   * confirms that he indeed wants to delete the file
   * @param e
   */
  void continueButton_actionPerformed(ActionEvent e) {


    String username = new String(usernameText.getText());
    String password = new String(passwordText.getPassword());
    if(username == null || username.trim().equals("") || password == null || username.trim().equals("")){

      String message = "<html><body><b>Must Enter User Name and Password.</b>"+
                                               "<p>Not registered, "+
                                               "<a href =\"http://gravity.usc.edu:8080/usermanagement\">"+
                                               "Click Here </a>.</body></html>";

      MessageDialog messageWindow = new MessageDialog(message,"Check Login", this);
      messageWindow.setVisible(true);
      return;
    }
    if(!isUserAuthorized(username,password)){
      String message = "<html><body><b>Incorrect Username or Password.</b>"+
                                               "<p>Not registered or forgot password, "+
                                               "<a href =\"http://gravity.usc.edu:8080/usermanagement\">"+
                                               "Click Here </a>.</body></html>";
      MessageDialog messageWindow = new MessageDialog(message,"Incorrect login information", this);
      messageWindow.setVisible(true);
      passwordText.setText("");
      return;
    }
    else
      loginSuccess = true;

  }





  /**
   * Check if user was able to successfully login.
   * @return boolean to hazard dataset calculation application to see if the login
   * was successful.
   */
  public boolean isLoginSuccess(){
    return loginSuccess;
  }

  /**
   *
   * @param e =this event occurs to destroy the popup window if the user has selected cancel option
   */
  void cancelButton_actionPerformed(ActionEvent e) {
    System.exit(0);
  }



  /**
   * Returns true if the user is authorized to use the applications
   * @param username
   * @param password
   * @return
   */
  private static boolean isUserAuthorized(String username, String password) {
    try {

      System.setProperty("java.protocol.handler.pkgs",
                         "com.sun.net.ssl.internal.www.protocol"); //add https protocol handler
      java.security.Security.addProvider(new com.sun.net.ssl.internal.ssl.
                                         Provider()); //dynamic registration of SunJSSE provider

//Create a trust manager that does not validate certificate chains:
      com.sun.net.ssl.TrustManager[] trustAllCerts = new com.sun.net.ssl.
          TrustManager[] {
          new com.sun.net.ssl.X509TrustManager() {
        public java.security.cert.X509Certificate[] getAcceptedIssuers() {
          return null;
        }

        public boolean isServerTrusted(java.security.cert.X509Certificate[]
                                       certs) {
          return true;
        }

        public boolean isClientTrusted(java.security.cert.X509Certificate[]
                                       certs) {
          return true;
        }

        public void checkServerTrusted(java.security.cert.X509Certificate[]
                                       certs, String authType) throws javax.
            security.cert.CertificateException {
          return;
        }

        public void checkClientTrusted(java.security.cert.X509Certificate[]
                                       certs, String authType) throws javax.
            security.cert.CertificateException {
          return;
        }
      } //X509TrustManager
      } ; //TrustManager[]

      //Install the all-trusting trust manager:
      com.sun.net.ssl.SSLContext sc = com.sun.net.ssl.SSLContext.getInstance(
          "SSL");
      sc.init(null, trustAllCerts, new java.security.SecureRandom());
      com.sun.net.ssl.HttpsURLConnection.setDefaultSSLSocketFactory(sc.
          getSocketFactory());

      // servlet URL
      //URL servletURL = new URL(SERVLET_ADDRESS+"?"+CheckAuthorizationServlet.USERNAME+"="+username+
      //                         "&"+CheckAuthorizationServlet.PASSWORD+"="+password);
      URL servletURL = new URL(SERVLET_ADDRESS + "?" + "username" + "=" +
                               username +
                               "&" + "password" + "=" + password);
      URLConnection servletConnection = servletURL.openConnection();

      // Receive the "object" from the servlet after it has received all the data
      ObjectInputStream fromServlet = new
          ObjectInputStream(servletConnection.getInputStream());
      Boolean auth = (Boolean) fromServlet.readObject();
      fromServlet.close();
      return auth.booleanValue();
      //OpenSHA_UsersDBDAO dao = new OpenSHA_UsersDBDAO();
      //OpenSHA_UsersVO userInfo  = dao.getUserInfo(username, password);
      //return (userInfo!=null);
    }
    catch (Exception e) {
      e.printStackTrace();
    }
    return false;
  }

  /**
   * Button for user to register as a new user.
   * @param actionEvent ActionEvent
   */
  public void newUserButton_actionPerformed(ActionEvent actionEvent) {
    try {
    	edu.stanford.ejalbert.BrowserLauncher.openURL(
          "http://gravity.usc.edu:8080/usermanagement/AccountRequest.do");
    }
    catch (Exception ex) {
      ex.printStackTrace();
    }
          //displayPage(e.getURL());   // Follow the link; display new page
  }

  /**
   *
   * @param actionEvent ActionEvent
   */
  public void forgetPassButton_actionPerformed(ActionEvent actionEvent) {
    try{
    	edu.stanford.ejalbert.BrowserLauncher.openURL("http://gravity.usc.edu:8080/usermanagement/PasswdRequest.do");
    }catch(Exception ex) { ex.printStackTrace(); }
  }

}
