package junk.PEER_TestsGroupResults;

import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.net.URL;
import java.net.URLConnection;

import javax.swing.JApplet;
import javax.swing.JButton;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JPasswordField;
import javax.swing.SwingConstants;
import javax.swing.border.Border;
import javax.swing.border.EtchedBorder;

/**
 * <p>Title: PEER_PasswordCheck</p>
 * <p>Description: This class provides the password protection for the PEER Applets
 * viewing by user</p>
 * @author : Nitin Gupta & Vipin Gupta
 * @version 1.0
 */

public class PEER_PasswordCheck extends JApplet {

  private static final boolean D= false;
  private static final String C="PEER_PasswordCheck";

  private JPanel passwordPanel = new JPanel();
  private Border border1;
  private JButton continueButton = new JButton();
  private JPasswordField filePassword = new JPasswordField();
  private JLabel jLabel5 = new JLabel();
  private JButton cancelButton = new JButton();
  private JLabel jLabel2 = new JLabel();
  private BorderLayout borderLayout1 = new BorderLayout();
  private GridBagLayout gridBagLayout1 = new GridBagLayout();


  //Construct the applet
  public PEER_PasswordCheck() {
  }
  public void init() {
    try {
      jbInit();
      /*filePassword.setVisible(true);
      filePassword.requestFocus(true);
      filePassword.setText("");*/
    }
    catch(Exception e) {
      e.printStackTrace();
    }
  }

  private void jbInit() throws Exception {
    border1 = new EtchedBorder(EtchedBorder.RAISED,new Color(248, 254, 255),new Color(121, 124, 136));
    this.getContentPane().setLayout(borderLayout1);
    passwordPanel.setBorder(border1);
    passwordPanel.setLayout(gridBagLayout1);
    continueButton.setBackground(new Color(200, 200, 230));
    continueButton.setFont(new java.awt.Font("Dialog", 1, 12));
    continueButton.setForeground(new Color(80, 80, 133));
    continueButton.setText("Continue");
    continueButton.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        continueButton_actionPerformed(e);
      }
    });
    filePassword.setBackground(new Color(200, 200, 230));
    filePassword.setFont(new java.awt.Font("Dialog", 1, 12));
    filePassword.setForeground(new Color(80, 80, 133));
    jLabel5.setFont(new java.awt.Font("Dialog", 1, 16));
    jLabel5.setForeground(new Color(80, 80, 133));
    jLabel5.setHorizontalAlignment(SwingConstants.CENTER);
    jLabel5.setHorizontalTextPosition(SwingConstants.CENTER);
    jLabel5.setText("Password Checking");
    cancelButton.setBackground(new Color(200, 200, 230));
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
    this.getContentPane().add(passwordPanel, BorderLayout.CENTER);
    passwordPanel.add(jLabel5,  new GridBagConstraints(0, 0, 3, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(39, 61, 0, 41), 107, 16));
    passwordPanel.add(filePassword,  new GridBagConstraints(1, 1, 2, 1, 1.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(23, 10, 0, 25), 170, 13));
    passwordPanel.add(jLabel2,  new GridBagConstraints(0, 1, 1, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(29, 27, 0, 0), 33, 10));
    passwordPanel.add(continueButton,  new GridBagConstraints(1, 2, 1, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(20, 0, 48, 0), 4, 13));
    passwordPanel.add(cancelButton,  new GridBagConstraints(2, 2, 1, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(20, 9, 48, 25), 16, 13));

    String val=getParameter("PEER_Tests");

    if(D)System.out.println("Val:"+val);

  }



  /**
   * Makes the connection to the servlet if user enters the correct password &
   * confirms that he indeed wants to delete the file
   * @param e
   */
  void continueButton_actionPerformed(ActionEvent e) {

    String password = new String(filePassword.getPassword());

    if(!checkPassword(password))
      JOptionPane.showMessageDialog(this,new String("Incorrect Password"),"Check Password",
                                    JOptionPane.OK_OPTION);

    else {
      //make the connection to the PEER HTML requested by the user
      String val=getParameter("PEER_Tests");
      if(D)System.out.println("Val:"+val);
      try{
        this.getAppletContext().showDocument(new URL(val));
        this.destroy();
      }catch(java.net.MalformedURLException ee){
        JOptionPane.showMessageDialog(this,new String("Not able to connect to Server"),
                                      "Server Error",JOptionPane.OK_OPTION);
      }
    }
    filePassword.setText("");
  }

  /**
   *
   * @param e =this event occurs to destroy the popup window if the user has selected cancel option
   */
  void cancelButton_actionPerformed(ActionEvent e) {
    filePassword.setText("");
    this.setVisible(false);
  }


  /**
   * Opens the connection with the servlet to check password
   * @param password= to see if the user has entered the correct password
   * for deletion of file
   */
  private boolean checkPassword(String password) {

    try{
      if(D)
        System.out.println("starting to make connection with servlet");
      URL PEER_TestServlet = new
                             URL("http://scec.usc.edu:9999/examples/servlet/PEER_InputFilesServlet");


      URLConnection servletConnection = PEER_TestServlet.openConnection();
      if(D)
        System.out.println("connection established");

      // inform the connection that we will send output and accept input
      servletConnection.setDoInput(true);
      servletConnection.setDoOutput(true);

      // Don't use a cached version of URL connection.
      servletConnection.setUseCaches (false);
      servletConnection.setDefaultUseCaches (false);
      // Specify the content type that we will send binary data
      servletConnection.setRequestProperty ("Content-Type","application/octet-stream");

      ObjectOutputStream outputToServlet = new
          ObjectOutputStream(servletConnection.getOutputStream());

      if(D)
        System.out.println("Password::"+password);

      //sending the "Password" string to servlet to tell it to check the password
      outputToServlet.writeObject(new String("Password"));

      // sending the password entered by the user to the servlet to check for its
      // authentication.
      outputToServlet.writeObject(password);

      outputToServlet.flush();
      outputToServlet.close();

      // Receive the "destroy" from the servlet after it has received all the data
      ObjectInputStream inputToServlet = new
          ObjectInputStream(servletConnection.getInputStream());

      String temp=inputToServlet.readObject().toString();

      if(D)
        System.out.println("Receiving the Input from the Servlet:"+temp);
      inputToServlet.close();
      if(temp.equalsIgnoreCase("success"))return true;
      else return false;
    }catch (Exception e) {
      System.out.println("Exception in connection with servlet:" +e);
      e.printStackTrace();
    }
    return false;
  }

  //Start the applet
  public void start() {

  }
  //Stop the applet
  public void stop() {
  }
  //Destroy the applet
  public void destroy() {
  }
  //Get Applet information
  public String getAppletInfo() {
    return C;
  }
  //Get parameter info
  public String[][] getParameterInfo() {
    return null;
  }

}
