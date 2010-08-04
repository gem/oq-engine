package junk.PEER_TestsGroupResults;

import java.awt.Color;
import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Iterator;

import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JComboBox;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPasswordField;
import javax.swing.JTextArea;
import javax.swing.SwingConstants;

/**
 * <p>Title: PEER_FileDeleteWindow</p>
 * <p>Description: This class deletes the PEER data file after checking if the
 * user has input the correct password</p>
 * @author : Nitin Gupta & Vipin Gupta
 * @version 1.0
 */

public class PEER_FileDeleteWindow extends JFrame {
  JComboBox testComboBox = new JComboBox();
  JLabel jLabel1 = new JLabel();
  JPasswordField filePassword = new JPasswordField();
  JLabel jLabel2 = new JLabel();
  JButton okButton = new JButton();
  JButton cancelButton = new JButton();

  // messages shown to the user
  private static String MSG_INCORRECT_PASSWORD = "Incorrect Password";
  private static String TITLE_INCORRECT_PASSWORD  = "Check Password";
  private static String TITLE_CONFIRMATION = "Confirmation Message";
  private static String MSG_DELETE = "Are you sure you want to delete ";

  //Instance of the PEER_TestResultsSubmissionApplet
  PEER_TestResultsSubmissionApplet peer=null;

  //ArrayList to store all the fileNames, gets is value from the PEER_TestResultsSubmissionApplet
  ArrayList dataFiles=null;
  private JLabel jLabel5 = new JLabel();
  private JLabel jLabel6 = new JLabel();
  private JTextArea deletionMessageText = new JTextArea();
  private JComboBox identifierComboBox = new JComboBox();
  private JLabel jLabel3 = new JLabel();
  private GridBagLayout gridBagLayout1 = new GridBagLayout();

  public PEER_FileDeleteWindow(PEER_TestResultsSubmissionApplet p,ArrayList fileNames) {
    try {
      jbInit();
    }
    catch(Exception e) {
      e.printStackTrace();
    }
    peer=p;
    dataFiles=fileNames;
    updateFileNames(dataFiles);
  }

  private void jbInit() throws Exception {
    this.getContentPane().setLayout(gridBagLayout1);
    testComboBox.setBackground(new Color(200, 200, 230));
    testComboBox.setForeground(new Color(80, 80, 133));
    jLabel1.setFont(new java.awt.Font("Dialog", 1, 12));
    jLabel1.setForeground(new Color(80, 80, 133));
    jLabel1.setText("Select Test Case:");
    filePassword.setBackground(new Color(200, 200, 230));
    filePassword.setFont(new java.awt.Font("Dialog", 1, 12));
    filePassword.setForeground(new Color(80, 80, 133));
    jLabel2.setFont(new java.awt.Font("Dialog", 1, 12));
    jLabel2.setForeground(new Color(80, 80, 133));
    jLabel2.setText("Enter Password:");
    okButton.setBackground(new Color(200, 200, 230));
    okButton.setFont(new java.awt.Font("Dialog", 1, 12));
    okButton.setForeground(new Color(80, 80, 133));
    okButton.setText("OK");
    okButton.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        okButton_actionPerformed(e);
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
    jLabel5.setText("PEER Data Deletion");
    jLabel6.setFont(new java.awt.Font("Dialog", 1, 12));
    jLabel6.setForeground(new Color(80, 80, 133));
    jLabel6.setText("Instructions:");
    deletionMessageText.setBackground(new Color(200, 200, 230));
    deletionMessageText.setFont(new java.awt.Font("Dialog", 1, 11));
    deletionMessageText.setForeground(new Color(80, 80, 133));
    deletionMessageText.setBorder(BorderFactory.createLineBorder(Color.black));
    deletionMessageText.setMinimumSize(new Dimension(142, 50));
    deletionMessageText.setPreferredSize(new Dimension(349, 100));
    deletionMessageText.setLineWrap(true);
    deletionMessageText.setWrapStyleWord(true);
    identifierComboBox.setBackground(new Color(200, 200, 230));
    identifierComboBox.setForeground(new Color(80, 80, 133));
    jLabel3.setFont(new java.awt.Font("Dialog", 1, 12));
    jLabel3.setForeground(new Color(80, 80, 133));
    jLabel3.setText("Select Identifier:");
    this.getContentPane().add(jLabel5,  new GridBagConstraints(0, 0, 3, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(9, 86, 0, 136), 104, 16));
    this.getContentPane().add(deletionMessageText,  new GridBagConstraints(0, 2, 3, 1, 1.0, 1.0
            ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(0, 36, 0, 59), 49, -53));
    this.getContentPane().add(jLabel6,  new GridBagConstraints(0, 1, 1, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(0, 36, 0, 7), 49, 4));
    this.getContentPane().add(jLabel3,  new GridBagConstraints(0, 4, 2, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(18, 36, 0, 98), 36, 10));
    this.getContentPane().add(identifierComboBox,  new GridBagConstraints(1, 4, 2, 1, 1.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL, new Insets(15, 15, 0, 108), 63, 10));
    this.getContentPane().add(jLabel2,  new GridBagConstraints(0, 5, 1, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(19, 36, 0, 0), 33, 10));
    this.getContentPane().add(filePassword,  new GridBagConstraints(1, 5, 2, 1, 1.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(13, 14, 0, 107), 191, 13));
    this.getContentPane().add(okButton,  new GridBagConstraints(1, 6, 1, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(20, 12, 28, 0), 46, 13));
    this.getContentPane().add(cancelButton,  new GridBagConstraints(2, 6, 1, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(20, 8, 28, 114), 20, 13));
    this.getContentPane().add(testComboBox,  new GridBagConstraints(1, 3, 2, 1, 1.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL, new Insets(20, 15, 0, 108), 63, 10));
    this.getContentPane().add(jLabel1,  new GridBagConstraints(0, 3, 1, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(22, 36, 0, 0), 24, 11));
    deletionMessageText.setText("Choose test case, the Identifier, " +
                                "enter the password, and hit OK to delete the file.\n");
    deletionMessageText.setEditable(false);
    this.setTitle("PEER Data File Deletion Window");
  }


  /**
   * This method updates the test cases and the identifer names in the combo box
   * If PEER file is added or deleted, this method updates the combo box with
   * latest changes to the PEER data
   * @param dataFiles: ArrayList that contains all the peer file names
   */
  void updateFileNames(ArrayList dataFiles){
    testComboBox.removeAllItems();
    identifierComboBox.removeAllItems();
    // arraylist are needed below for sorting purposes
    ArrayList testList1= new ArrayList(); // for test cases 1-9
    ArrayList testList2= new ArrayList(); // for test cases 10 and 11
    ArrayList idList= new ArrayList(); // for identifier list
    int size=dataFiles.size();
    for(int i=0;i<size;++i){
        String testFileName=dataFiles.get(i).toString();
        int index=testFileName.indexOf("_");
        int indexofDot = testFileName.indexOf(".");
        String testCases = testFileName.substring(0,index);
        String identifier = testFileName.substring(index+1,indexofDot);

        boolean isTenOrEleven = false; //whether it is test case 10 or 11


        Iterator it;
        boolean flag = false;


        // check wther this is test case 10 or 11
        if((testCases.indexOf("10")>-1) || (testCases.indexOf("11")>-1))
          isTenOrEleven = true;

        // check in list 1
        if(!isTenOrEleven) { // if this is case from 1 through 9
          it = testList1.iterator();
          while(it.hasNext()) {
            // check whether this set has already been added to list
            if(((String)it.next()).equalsIgnoreCase(testCases)) {
              flag = true;
              break;
            }
          }
          if(!flag) testList1.add(testCases);
         } else  {// check in list 2 whether the case exists
           // if this is case 10 or 11
           it = testList2.iterator();
           while(it.hasNext()) {
             // check whether this set has already been added to list
             if(((String)it.next()).equalsIgnoreCase(testCases)) {
               flag = true;
               break;
             }
           }
           if(!flag) testList2.add(testCases);
         }

        // check whether identifier has already been added to the list
        it = idList.iterator();
        flag=false;
        while(it.hasNext()) {
          if(((String)it.next()).equals(identifier)) {
            flag = true;
            break;
          }
        }
        if(!flag) idList.add(identifier); // add identifier to list if it has not been added yet
    }


    // now sort the lists and add it to combo boxes
    Collections.sort(testList1);
    Collections.sort(testList2);
    Collections.sort(idList);

    // add cases 1-9 and then 10 and 11
    Iterator it = testList1.iterator();
    while(it.hasNext())  testComboBox.addItem(it.next()); // add test cases 1-9
    it = testList2.iterator();
    while(it.hasNext())  testComboBox.addItem(it.next()); // add test cases 10-11

    // add to identifier box
    it = idList.iterator();
    while(it.hasNext()) identifierComboBox.addItem(it.next());
  }

  /**
   * Makes the connection to the servlet if user enters the correct password &
   * confirms that he indeed wants to delete the file
   * @param e
   */
  void okButton_actionPerformed(ActionEvent e) {

    String password = new String(filePassword.getPassword());

    if(!peer.checkPassword(password))
      JOptionPane.showMessageDialog(this,this.MSG_INCORRECT_PASSWORD,
                                    this.TITLE_INCORRECT_PASSWORD,
                                    JOptionPane.OK_OPTION);

    else {
      String selectedTestCase = testComboBox.getSelectedItem().toString();
      String identifier = identifierComboBox.getSelectedItem().toString();
      String fileName = selectedTestCase+"_"+identifier+".dat";
      //delete the file selected.
      int flag=JOptionPane.showConfirmDialog(this,this.MSG_DELETE+fileName+"?",
          this.TITLE_CONFIRMATION,JOptionPane.OK_CANCEL_OPTION);
      int found=0;
      if(flag == JOptionPane.OK_OPTION) found=1;
      if(found==1) peer.openDeleteConnection(fileName);
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
