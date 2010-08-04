package junk.PEER_TestsGroupResults;

import java.awt.Color;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;

import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPasswordField;
import javax.swing.SwingConstants;

/**
 * <p>Title: PEER_FileOverwriteWindow</p>
 * <p>Description: This class deletes the PEER data file after checking if the
 * user has input the correct password</p>
 * @author : Nitin Gupta & Vipin Gupta
 * @version 1.0
 */

public class PEER_FileOverwriteWindow extends JFrame {
  JPasswordField filePassword = new JPasswordField();
  JLabel jLabel2 = new JLabel();
  JButton continueButton = new JButton();
  JButton cancelButton = new JButton();

  // messages shown to the user
  private static String MSG_INCORRECT_PASSWORD = "Incorrect Password";
  private static String TITLE_INCORRECT_PASSWORD  = "Check Password";
  private static String TITLE_CONFIRMATION = "Confirmation Message";
  private static String MSG_ADD = "Are you sure you want to add ";
  private static String MSG_OVERWRITE = "Are you sure you want to overwrite ";


  //Instance of the PEER_TestResultsSubmissionApplet
  PEER_TestResultsSubmissionApplet peer=null;

  //checks whether one wants to overwrite or add the existing file
  boolean overWriteFile=false;

  //Contains the name of the file to be overwritten
  String fileName;
  private JLabel jLabel5 = new JLabel();
  private GridBagLayout gridBagLayout1 = new GridBagLayout();

  /**
   *
   * @param p: instance of the applet
   * @param file: name of the file to added or overwritten
   * @param overWrite: determines whether the file is to be overwritten or
   * new file is be added
   * false means new file is added and true means file is to be overwritten
   */

  public PEER_FileOverwriteWindow(PEER_TestResultsSubmissionApplet p,String file,
                                  boolean overWrite) {
    try {
      jbInit();
    }
    catch(Exception e) {
      e.printStackTrace();
    }
    peer=p;
    this.fileName =file ;
    overWriteFile=overWrite;
  }

  private void jbInit() throws Exception {
    this.getContentPane().setLayout(gridBagLayout1);
    filePassword.setBackground(new Color(200, 200, 230));
    filePassword.setFont(new java.awt.Font("Dialog", 1, 12));
    filePassword.setForeground(new Color(80, 80, 133));
    jLabel2.setFont(new java.awt.Font("Dialog", 1, 12));
    jLabel2.setForeground(new Color(80, 80, 133));
    jLabel2.setText("Enter Password:");
    continueButton.setBackground(new Color(200, 200, 230));
    continueButton.setFont(new java.awt.Font("Dialog", 1, 12));
    continueButton.setForeground(new Color(80, 80, 133));
    continueButton.setText("Continue");
    continueButton.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        continueButton_actionPerformed(e);
      }
    });
    cancelButton.setBackground(new Color(200, 200, 230));
    cancelButton.setFont(new java.awt.Font("Dialog", 1, 12));
    cancelButton.setForeground(new Color(80, 80, 133));
    cancelButton.setText("Cancel");
    cancelButton.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        cancelButton_actionPerformed(e);
      }
    });
    this.setDefaultCloseOperation(DISPOSE_ON_CLOSE);
    jLabel5.setFont(new java.awt.Font("Dialog", 1, 16));
    jLabel5.setForeground(new Color(80, 80, 133));
    jLabel5.setHorizontalAlignment(SwingConstants.CENTER);
    jLabel5.setHorizontalTextPosition(SwingConstants.CENTER);
    jLabel5.setText("Data Submission Password");
    this.getContentPane().add(filePassword,  new GridBagConstraints(1, 1, 2, 1, 1.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(63, 10, 0, 62), 143, 13));
    this.getContentPane().add(continueButton,  new GridBagConstraints(1, 2, 1, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(20, 0, 23, 0), 4, 13));
    this.getContentPane().add(cancelButton,  new GridBagConstraints(2, 2, 1, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(20, 23, 23, 17), 16, 13));
    this.getContentPane().add(jLabel2,  new GridBagConstraints(0, 1, 1, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(66, 24, 0, 0), 33, 10));
    this.getContentPane().add(jLabel5,  new GridBagConstraints(0, 0, 3, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(2, 33, 0, 44), 114, 16));
    this.setTitle("PEER Data Submission Password Check");
  }



  /**
   * Makes the connection to the servlet if user enters the correct password &
   * confirms that he indeed wants to add or overwrite the file
   * @param e
   */
  void continueButton_actionPerformed(ActionEvent e) {

    String password = new String(filePassword.getPassword());

    if(!peer.checkPassword(password))
      JOptionPane.showMessageDialog(this,
                                    this.MSG_INCORRECT_PASSWORD,
                                    this.TITLE_INCORRECT_PASSWORD,
                                    JOptionPane.OK_OPTION);

    else {
      //add or overwrite the file selected.
      int flag;
      if(overWriteFile) // for overwriting, show overwrite message
        flag=JOptionPane.showConfirmDialog(this,this.MSG_OVERWRITE+fileName+"?",
               this.TITLE_CONFIRMATION,JOptionPane.OK_CANCEL_OPTION);
      else
        flag=JOptionPane.showConfirmDialog(this,this.MSG_ADD+fileName+"?",
               this.TITLE_CONFIRMATION,JOptionPane.OK_CANCEL_OPTION);
      int found=0;
      if(flag == JOptionPane.OK_OPTION)  found=1;
      if(found==1 && overWriteFile) peer.openOverwriteConnection(fileName);
      else if(found==1 && !overWriteFile)  peer.openConnection();
      this.dispose();
    }
    filePassword.setText("");
  }

  /**
   *
   * @param e =this event occurs to destroy the popup window if the user has selected cancel option
   */
  void cancelButton_actionPerformed(ActionEvent e) {
    this.dispose();
  }
}
