package junk.PEER_TestsGroupResults;

import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.Rectangle;
import java.awt.SystemColor;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.MouseEvent;
import java.io.DataInputStream;
import java.io.InputStream;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.net.URL;
import java.net.URLConnection;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Iterator;
import java.util.ListIterator;
import java.util.StringTokenizer;

import javax.swing.BorderFactory;
import javax.swing.ImageIcon;
import javax.swing.JApplet;
import javax.swing.JButton;
import javax.swing.JComboBox;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.JTextField;
import javax.swing.SwingConstants;
import javax.swing.UIManager;
import javax.swing.border.Border;
import javax.swing.border.EtchedBorder;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.util.FileUtils;






/**
 * <p>Title: PEER_TestResultsSubmissionApplet </p>
 * <p>Description: This Applet allows the different user to submit their dataFiles
 * for the PEER Tests and these datafiles are then stored  as the Jar files on the
 * server scec.usc.edu .
 * After Submission of their datafiles, the users can see the result of their files
 * as the PEER test plots in the Applet PEER_TestResultsPlotterApplet</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * @author: Nitin Gupta & Vipin Gupta
 * @date : Dec 17,2002
 * @version 1.0
 */

public class PEER_TestResultsSubmissionApplet extends JApplet {

  //ClassName and Debug property
  private static final String C = "PEER_TestResultsSubmissionApplet";
  private static final boolean D = true;

  // Strings for various messages to be shown
  private static String MSG_INSTRUCTIONS = "1) Select the test case you would like to submit data for.\n\n"+
                        "2) Enter your identifier (this is used to label your "+
                        "result in the comparison plot).  NOTE: your identifier"+
                        " cannot have any spaces, dots (.) or an underscore (_) in it.\n\n"+
                        "3) Paste your y-axis data in the right-hand box to the right "+
                        "according to the x-values shown in the left-hand box.\n\n"+
                        "4) Hit the submit button.";
  private static String MSG_ALREADY_EXISTS = "Identifier already exists, Want to overwrite? ";
  private static String TITLE_INFORMATION = "Information Message ";
  private static String MSG_ENTER_Y_VALUES = "Must Enter Y Values";
  private static String TITLE_INPUT_ERROR = "Input Error";
  private static String MSG_INCORRECT_Y_VALUES = "Incorrect Number of Y Values";
  private static String MSG_MISSING_IDENTIFIER = "Must Enter Identifier Name";
  private static String MSG_SPACES_IDENTIFIER = "Indentifier name cannot have spaces";
  private static String MSG_UNDERSCORE_IDENTIFIER = "Indentifier name cannot have an underscore ('_')";
  private static String MSG_DOT_IDENTIFIER = "Indentifier name cannot have dot ('.')";
  private static String MSG_ADDING_FILE = "  Adding new file; please be patient ...";
  private static String MSG_FILE_ADDED = "File was added successfully\n\n " +
      "NOTE: To see this change in the  web-based plotter you'll "+
      "need to quit and restart your browser (or download a new "+
      "stand-alone version)";
  private static String TITLE_ADD_CONFIRMATION = "Add Confirmation";
  private static String MSG_DELETING_FILE ="  Deletion being performed; please be patient ...";
  private static String MSG_FILE_DELETED =new String("File deleted successfully");
  private static String TITLE_DELETE_CONFIRMATION ="Delete Confirmation";
  private static String MSG_FILE_OVERWRITE ="  Overwriting file; please be patient ...";
  private static String MSG_FILE_OVERWRITTEN = "File was overwritten successfully\n\n " +
      "NOTE: To see this change in the  web-based plotter you might "+
      "need to quit and restart your browser (or download a new "+
      "stand-alone version)";
  private static String TITLE_OERWRITE_CONFIRMATION = "Overwrite Confirmation";
  private static String MSG_NO_INTERNET_CONNECTION= "No Internet Connection Available";
  private static String TITLE_NO_INTERNET_CONNECTION=  "Error Connecting to Internet";



  //Directory from which to search for all the PEER test files
  String DIR = "GroupTestDataFiles/";
  String FILE_EXTENSION=".dat";

  //Reads the selected test case file. returns the function conatining x,y values
  ArbitrarilyDiscretizedFunc function= new ArbitrarilyDiscretizedFunc();

  //ArrayList to store all the existing Test Case file names
   ArrayList testFiles= new ArrayList();

  //Instance for the PEER Delete window class
  PEER_FileDeleteWindow peerDelete;

  //Instance for the PEER Overwrite window class
  PEER_FileOverwriteWindow peerOverwrite;

  //flag to check if the file is to be overwritten
  private boolean overwriteFlag=false;

  //images for the OpenSHA
  private final static String FRAME_ICON_NAME = "openSHA_Aqua_sm.gif";
  private final static String POWERED_BY_IMAGE = "PoweredBy.gif";

  //static string for the OPENSHA website
  private final static String OPENSHA_WEBSITE="http://www.OpenSHA.org";

  private boolean isStandalone = false;
  private Border border1;
  private Border border2;
  private Border border3;
  private Border border4;
  private Border border5;
  private Border border6;
  private JPanel mainPanel = new JPanel();
  private Border border7;
  private JPanel titlePanel = new JPanel();
  private Border border8;
  private JPanel dataPanel = new JPanel();
  private JButton submitButton = new JButton();
  private JTextField fileNameText = new JTextField();
  private JComboBox testComboBox = new JComboBox();
  private JLabel dataSubmLabel = new JLabel();
  private JLabel jLabel4 = new JLabel();
  private JLabel jLabel3 = new JLabel();
  private JTextArea messageTextArea = new JTextArea();
  private JLabel jLabel1 = new JLabel();
  private JTextArea yTextArea = new JTextArea();
  private JLabel xLabel = new JLabel();
  private JScrollPane jScrollPane2 = new JScrollPane();
  private JScrollPane jScrollPane1 = new JScrollPane();
  private JTextArea xTextArea = new JTextArea();
  private JLabel jLabel2 = new JLabel();
  private JPanel deletePanel = new JPanel();
  private Border border9;
  private JLabel jLabel5 = new JLabel();
  private JLabel jLabel6 = new JLabel();
  private JButton deleteFileButton = new JButton();
  private JLabel jLabel7 = new JLabel();
  private JLabel jLabel8 = new JLabel();
  private GridBagLayout gridBagLayout3 = new GridBagLayout();
  private JLabel directionsLabel = new JLabel();
  private JLabel imgLabel = new JLabel();
  private GridBagLayout gridBagLayout1 = new GridBagLayout();
  //Get a parameter value
  public String getParameter(String key, String def) {
    return isStandalone ? System.getProperty(key, def) :
      (getParameter(key) != null ? getParameter(key) : def);
  }

  //Construct the applet
  public PEER_TestResultsSubmissionApplet() {
  }
  //Initialize the applet
  public void init() {
    try {
      jbInit();
    }
    catch(Exception e) {
      e.printStackTrace();
    }
   searchTestFiles();
   createFunction();
   setXValues();


  }


  //Component initialization
  private void jbInit() throws Exception {
    border1 = new EtchedBorder(EtchedBorder.RAISED,new Color(248, 254, 255),new Color(121, 124, 136));
    border2 = new EtchedBorder(EtchedBorder.RAISED,new Color(248, 254, 255),new Color(121, 124, 136));
    border3 = BorderFactory.createLineBorder(Color.white,2);
    border4 = BorderFactory.createLineBorder(Color.white,2);
    border5 = BorderFactory.createLineBorder(Color.black,2);
    border6 = BorderFactory.createLineBorder(SystemColor.controlText,1);
    border7 = BorderFactory.createEtchedBorder(new Color(248, 254, 255),new Color(121, 124, 136));
    border8 = new EtchedBorder(EtchedBorder.RAISED,new Color(248, 254, 255),new Color(121, 124, 136));
    border9 = new EtchedBorder(EtchedBorder.RAISED,new Color(248, 254, 255),new Color(121, 124, 136));
    this.setSize(new Dimension(704, 597));
    this.getContentPane().setLayout(null);


    mainPanel.setLayout(null);
    mainPanel.setBackground(Color.white);
    mainPanel.setBorder(border7);
    mainPanel.setBounds(new Rectangle(0, 0, 704, 597));
    titlePanel.setBackground(Color.white);
    titlePanel.setBounds(new Rectangle(-2, 0, 704, 38));
    titlePanel.setLayout(gridBagLayout3);
    dataPanel.setBackground(Color.white);
    dataPanel.setBorder(BorderFactory.createEtchedBorder());
    dataPanel.setBounds(new Rectangle(-2, 38, 704, 439));
    dataPanel.setLayout(null);
    submitButton.setBackground(new Color(200, 200, 230));
    submitButton.setBounds(new Rectangle(598, 382, 83, 45));
    submitButton.setFont(new java.awt.Font("Dialog", 1, 12));
    submitButton.setForeground(new Color(80, 80, 133));
    submitButton.setText("Submit");
    submitButton.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        submitButton_actionPerformed(e);
      }
    });
    fileNameText.setBackground(new Color(200, 200, 230));
    fileNameText.setFont(new java.awt.Font("Dialog", 1, 11));
    fileNameText.setForeground(new Color(80, 80, 133));
    fileNameText.setBounds(new Rectangle(176, 381, 180, 25));
    testComboBox.setBackground(new Color(200, 200, 230));
    testComboBox.setFont(new java.awt.Font("Dialog", 1, 12));
    testComboBox.setForeground(new Color(80, 80, 133));
    testComboBox.setBounds(new Rectangle(175, 332, 181, 22));
    dataSubmLabel.setFont(new java.awt.Font("Dialog", 1, 16));
    dataSubmLabel.setForeground(new Color(80, 80, 133));
    dataSubmLabel.setToolTipText("");
    dataSubmLabel.setHorizontalAlignment(SwingConstants.CENTER);
    dataSubmLabel.setHorizontalTextPosition(SwingConstants.CENTER);
    dataSubmLabel.setText("Data Submission");
    dataSubmLabel.setBounds(new Rectangle(33, 8, 251, 37));
    jLabel4.setFont(new java.awt.Font("Dialog", 1, 12));
    jLabel4.setForeground(new Color(80, 80, 133));
    jLabel4.setText("Instructions:");
    jLabel4.setVerticalAlignment(SwingConstants.TOP);
    jLabel4.setBounds(new Rectangle(18, 47, 140, 20));
    jLabel3.setFont(new java.awt.Font("Dialog", 1, 12));
    jLabel3.setForeground(new Color(80, 80, 133));
    jLabel3.setText("Enter Your Identifier:");
    jLabel3.setBounds(new Rectangle(18, 377, 165, 29));
    messageTextArea.setBackground(new Color(200, 200, 230));
    messageTextArea.setFont(new java.awt.Font("Dialog", 1, 11));
    messageTextArea.setForeground(new Color(80, 80, 133));
    messageTextArea.setBorder(BorderFactory.createLineBorder(Color.black));
    messageTextArea.setMinimumSize(new Dimension(359, 120));
    messageTextArea.setPreferredSize(new Dimension(361, 120));
    messageTextArea.setEditable(false);
    messageTextArea.setLineWrap(true);
    messageTextArea.setWrapStyleWord(true);
    messageTextArea.setBounds(new Rectangle(18, 69, 338, 234));
    messageTextArea.setText(MSG_INSTRUCTIONS);
    messageTextArea.setEditable(false);
    jLabel1.setFont(new java.awt.Font("Dialog", 1, 12));
    jLabel1.setForeground(new Color(80, 80, 133));
    jLabel1.setText("Select Test Case:");
    jLabel1.setBounds(new Rectangle(19, 319, 172, 31));
    yTextArea.setBackground(new Color(200, 200, 230));
    yTextArea.setFont(new java.awt.Font("Dialog", 1, 11));
    yTextArea.setForeground(new Color(80, 80, 133));
    xLabel.setFont(new java.awt.Font("Dialog", 1, 12));
    xLabel.setForeground(new Color(80, 80, 133));
    xLabel.setText("X:");
    xLabel.setBounds(new Rectangle(388, 47, 44, 20));
    xTextArea.setBackground(new Color(200, 200, 230));
    xTextArea.setFont(new java.awt.Font("Dialog", 1, 11));
    xTextArea.setForeground(new Color(80, 80, 133));
    jLabel2.setFont(new java.awt.Font("Dialog", 1, 12));
    jLabel2.setForeground(new Color(80, 80, 133));
    jLabel2.setText("Y:");
    jLabel2.setBounds(new Rectangle(482, 43, 44, 24));
    deletePanel.setBackground(Color.white);
    deletePanel.setBorder(border9);
    deletePanel.setBounds(new Rectangle(-2, 477, 704, 87));
    deletePanel.setLayout(gridBagLayout1);
    jLabel5.setFont(new java.awt.Font("Dialog", 1, 16));
    jLabel5.setForeground(new Color(80, 80, 133));
    jLabel5.setHorizontalAlignment(SwingConstants.CENTER);
    jLabel5.setHorizontalTextPosition(SwingConstants.CENTER);
    jLabel5.setText("PEER PSHA-Test Results Submission/Deletion Form");
    jLabel6.setText("Data Deletion");
    jLabel6.setHorizontalTextPosition(SwingConstants.CENTER);
    jLabel6.setHorizontalAlignment(SwingConstants.CENTER);
    jLabel6.setForeground(new Color(80, 80, 133));
    jLabel6.setFont(new java.awt.Font("Dialog", 1, 16));
    deleteFileButton.setBackground(new Color(200, 200, 230));
    deleteFileButton.setFont(new java.awt.Font("Dialog", 1, 12));
    deleteFileButton.setForeground(new Color(80, 80, 133));
    deleteFileButton.setMaximumSize(new Dimension(71, 45));
    deleteFileButton.setMinimumSize(new Dimension(71, 45));
    deleteFileButton.setPreferredSize(new Dimension(71, 45));
    deleteFileButton.setHorizontalTextPosition(SwingConstants.CENTER);
    deleteFileButton.setText("Delete ");
    deleteFileButton.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        deleteFileButton_actionPerformed(e);
      }
    });
    jLabel7.setForeground(new Color(80, 80, 133));
    jLabel7.setText("(Password Protected)");
    jLabel8.setFont(new java.awt.Font("Dialog", 1, 12));
    jLabel8.setForeground(new Color(80, 80, 133));
    jLabel8.setText("Select Test Case:");
    jLabel8.setBounds(new Rectangle(18, 325, 168, 30));

    //loading the OpenSHA Logo
    directionsLabel.setForeground(new Color(80, 80, 133));
    directionsLabel.setHorizontalAlignment(SwingConstants.RIGHT);
    directionsLabel.setText("Click button and follow directions ");
    imgLabel.setIcon(new ImageIcon(FileUtils.loadImage(this.POWERED_BY_IMAGE)));
    imgLabel.setBounds(new Rectangle(196, 564, 238, 29));
    imgLabel.addMouseListener(new java.awt.event.MouseAdapter() {
      public void mouseClicked(MouseEvent e) {
        imgLabel_mouseClicked(e);
      }
    });
    imgLabel.setHorizontalAlignment(SwingConstants.CENTER);
    jScrollPane2.setBounds(new Rectangle(482, 69, 115, 348));
    jScrollPane1.setBounds(new Rectangle(381, 69, 82, 348));
    dataPanel.add(dataSubmLabel, null);
    dataPanel.add(messageTextArea, null);
    dataPanel.add(jLabel4, null);
    dataPanel.add(testComboBox, null);
    dataPanel.add(jLabel8, null);
    dataPanel.add(jLabel3, null);
    dataPanel.add(fileNameText, null);
    dataPanel.add(xLabel, null);
    dataPanel.add(jScrollPane1, null);
    dataPanel.add(submitButton, null);
    dataPanel.add(jScrollPane2, null);
    dataPanel.add(jLabel2, null);
    jScrollPane2.getViewport().add(yTextArea, null);
    mainPanel.add(deletePanel, null);
    jScrollPane1.getViewport().add(xTextArea, null);
    mainPanel.add(dataPanel, null);
    deletePanel.add(directionsLabel,  new GridBagConstraints(0, 1, 1, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(14, 39, 3, 0), 67, 13));
    deletePanel.add(deleteFileButton,   new GridBagConstraints(1, 1, 2, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(0, 7, 3, 318), 14, 0));
    deletePanel.add(jLabel6,  new GridBagConstraints(0, 0, 2, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(-1, 229, 0, 0), 27, 16));
    deletePanel.add(jLabel7,  new GridBagConstraints(2, 0, 1, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(6, 0, 7, 185), 21, 6));
    mainPanel.add(titlePanel, null);
    titlePanel.add(jLabel5,  new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(3, 41, 1, 132), 83, 16));
    mainPanel.add(imgLabel, null);
    this.getContentPane().add(mainPanel, null);
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
  //Main method
  public static void main(String[] args) {
    PEER_TestResultsSubmissionApplet applet = new PEER_TestResultsSubmissionApplet();
    applet.isStandalone = true;
    JFrame frame = new JFrame();
    //EXIT_ON_CLOSE == 3
    frame.setDefaultCloseOperation(3);
    frame.setTitle("PEER Test Data Submission Applet");
    frame.getContentPane().add(applet, BorderLayout.CENTER);
    applet.init();
    applet.start();
    frame.setSize(400,610);
    Dimension d = Toolkit.getDefaultToolkit().getScreenSize();
    frame.setLocation((d.width - frame.getSize().width) / 2, (d.height - frame.getSize().height) / 2);
    frame.setVisible(true);
  }

  //static initializer for setting look & feel
  static {
    try {
      UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
    }
    catch(Exception e) {
    }
  }



  /**
   * This function looks for all the test cases files within the directory
   * and stores their name in ArrayList
   */
  private  void searchTestFiles(){
    // ArrayList is needed for the sorted list
    ArrayList testCaseList1 = new ArrayList(); // this list saves SET 1 test case from 1 to 9
    ArrayList testCaseList2 = new ArrayList(); // this list saves SET 1 test case 10 and 11
    ArrayList testCaseList3 = new ArrayList(); // this list saves SET 2 test cases
    try{
      // files.log contains all the files uploaded so far
      InputStream input = PEER_TestResultsSubmissionApplet.class.getResourceAsStream("/"+DIR+"files.log");
      DataInputStream dataStream = new DataInputStream(input);
      String line;
      while((line=dataStream.readLine())!=null) {
        if(line.endsWith(FILE_EXTENSION)) testFiles.add(line);
        else continue;

        // this is needed to add a spce between test case and site
        int index=line.indexOf("_");
        String testCases = line.substring(0,index);

        boolean isTenOrEleven = false;
        boolean flag = false;
        boolean isSet2 = false;

        //check whether this is Set 2
         if(testCases.indexOf("Set2")>-1)  isSet2 = true;

        // check wther this is test case 10 or 11
        if((testCases.indexOf("10")>-1) || (testCases.indexOf("11")>-1))
          isTenOrEleven = true;
        // check in list 1
        if(!isTenOrEleven && !isSet2) { // if this is case from 1 through 9
          Iterator it = testCaseList1.iterator();
          while(it.hasNext()) {
            // check whether this set has already been added to list
            if(((String)it.next()).equalsIgnoreCase(testCases)) {
              flag = true;
              break;
            }
          }
          if(!flag) testCaseList1.add(testCases);
        }


        // check in list 2 whether the case exists
       if(isTenOrEleven && !isSet2) { // if this is case 10 or 11
         Iterator it = testCaseList2.iterator();
         while(it.hasNext()) {
           // check whether this set has already been added to list
           if(((String)it.next()).equalsIgnoreCase(testCases)) {
             flag = true;
             break;
           }
         }
         if(!flag) testCaseList2.add(testCases);
        }

        // check in list 3 whether the case exists
        if(isSet2) { // if this is Set2 case
         Iterator it = testCaseList3.iterator();
         while(it.hasNext()) {
           // check whether this set has already been added to list
           if(((String)it.next()).equalsIgnoreCase(testCases)) {
             flag = true;
             break;
           }
         }
         if(!flag) testCaseList3.add(testCases);
        }
      }
      Collections.sort(testCaseList1);
      Collections.sort(testCaseList2);
      Collections.sort(testCaseList3);

      // add to the combo box
      Iterator it =  testCaseList1.iterator();
      while(it.hasNext()) testComboBox.addItem(it.next());
      it =  testCaseList2.iterator();
      while(it.hasNext()) testComboBox.addItem(it.next());
      it =  testCaseList3.iterator();
      while(it.hasNext()) testComboBox.addItem(it.next());

    }catch(Exception e) {
      e.printStackTrace();
    }

   }

  /**
   * this method shows the X Values in the TextArea
   */
  private void setXValues(){
    ListIterator it=function.getXValuesIterator();
    StringBuffer st = new StringBuffer();
    while(it.hasNext()){
       st.append(it.next().toString());
       st.append('\n');
    }
    System.out.println("X Values  are:"+st.toString());
    xTextArea.setText(st.toString());
    xTextArea.setEditable(false);
  }


  /**
   * This method is called when the submit button is clicked
   * Provides Error checking to se that user has entered all the valid
   * values in the parameters
   */
  private void submitButton() throws RuntimeException{

    //creating the new file name in which function data has to be stored.
    String fileName =new  String(testComboBox.getSelectedItem().toString());
    boolean flag = true;
    overwriteFlag=false;
    fileName=fileName.concat("_");
    fileName=fileName.concat(fileNameText.getText());
    fileName=fileName.concat(".dat");
    int size= testFiles.size();

    //checking for the Y-values input by the user
    boolean yValFlag = getYValues();
    if(!yValFlag) return ;

    //checking if the fileName already exists, if so then ask user to input another fileName
    for(int i=0;i<size;++i){
      if(fileName.equals(testFiles.get(i).toString())){
        flag=false;
        break;
      }
    }

    //if the person wants to add new data file
    if(flag){
      function.setName(fileName);
      //false in the arguments determines whether the file is to be overwritten or
      //new file is to be added
      peerOverwrite = new PEER_FileOverwriteWindow(this,fileName,false);
      peerOverwrite.setLocation(this.getAppletXAxisCenterCoor()-60,this.getAppletYAxisCenterCoor()-50);
      peerOverwrite.pack();
      peerOverwrite.setVisible(true);
    }
    else{
      //if someone wants to overwrite the existing data file.
      int flag1=JOptionPane.showConfirmDialog(this,MSG_ALREADY_EXISTS,
          TITLE_INFORMATION, JOptionPane.OK_CANCEL_OPTION);
      int found=0;
      //user wants to overwrite
      if(flag1 ==JOptionPane.OK_OPTION)  found=1;
      else {
        //user does not want to overwrite
          overwriteFlag=false;
          fileNameText.setText("");
        }
        //Overwrite window
        if(found==1)  {
            peerOverwrite = new PEER_FileOverwriteWindow(this,fileName,true);
            peerOverwrite.setLocation(this.getAppletXAxisCenterCoor()-60,this.getAppletYAxisCenterCoor()-50);
            peerOverwrite.pack();
            peerOverwrite.setVisible(true);
            overwriteFlag=true;
        }
      }
  }

  /**
   * This method gets the Y values entered by the user and updates the ArbDiscretizedFunc
   * with these Y values.
   */
  private boolean getYValues(){

    String yValues= new String(yTextArea.getText());
    //checking if the TextArea where values are to be entered is empty.
    if(yValues.equals("")){
      JOptionPane.showMessageDialog(this, MSG_ENTER_Y_VALUES ,
                                    this.TITLE_INPUT_ERROR,
                                    JOptionPane.ERROR_MESSAGE);
      return false;
    }
    //if the user has entered the Y Values in the TextArea.
    else{
      ArrayList vt = new ArrayList();
      //getting each Y value and adding to the ArrayList.
      StringTokenizer st = new StringTokenizer(yValues.trim(),"\n");
      while(st.hasMoreTokens())
        vt.add(st.nextToken());

      //checking if the vector size is 20, which are number of X values we have
      int size = vt.size();
      if(size!= function.getNum()){
        JOptionPane.showMessageDialog(this,MSG_INCORRECT_Y_VALUES,
                                      this.TITLE_INPUT_ERROR,
                                      JOptionPane.ERROR_MESSAGE);
        return false;
      }
      else{
        for(int i=0;i<size;++i)
          //updating the function with the Y-values entered by the user.
          function.set(i,Double.parseDouble(vt.get(i).toString().trim()));
      }
    }
    return true;
  }


  /**
   * initialises the function with the x and y values
   * the y values are modified with the values entered by the user
   */
  private void createFunction(){
    function.set(.001,1);
    function.set(.01,1);
    function.set(.05,1);
    function.set(.15,1);
    function.set(.1,1);
    function.set(.2,1);
    function.set(.25,1);
    function.set(.3,1);
    function.set(.4,1);
    function.set(.5,1);
    function.set(.6,1);
    function.set(.7,1);
    function.set(.8,1);
    function.set(.9,1);
    function.set(1.0,1);
    function.set(1.1,1);
    function.set(1.2,1);
    function.set(1.3,1);
    function.set(1.4,1);
    function.set(1.5,1);
  }


  /**
   * This method is called if the submit button is clicked.
   * It checks if the information is filled correctly in all the parameters
   * and if everthing has been correctly entered this applet sets-up connection
   * with the servlet.
   * @param e
   */
  void submitButton_actionPerformed(ActionEvent e) {
    //checks if user has entered the filename
    boolean flag = true;

    try{
      if(fileNameText.getText().trim().equals("")){
        flag = false;
        JOptionPane.showMessageDialog(this,MSG_MISSING_IDENTIFIER,
                                      this.TITLE_INPUT_ERROR,
                                      JOptionPane.ERROR_MESSAGE);
      }
      else{
        int indexofSpace = fileNameText.getText().indexOf(" ");
        int indexofDot = fileNameText.getText().indexOf(".");
        int indexofUnderScore = fileNameText.getText().indexOf("_");
        if(indexofSpace !=-1){
          fileNameText.setText("");
          throw new RuntimeException(this.MSG_SPACES_IDENTIFIER);
        }
        if(indexofUnderScore !=-1){
          fileNameText.setText("");
          throw new RuntimeException(this.MSG_UNDERSCORE_IDENTIFIER);
        }
        if(indexofDot !=-1){
          fileNameText.setText("");
          throw new RuntimeException(this.MSG_DOT_IDENTIFIER);
        }
        submitButton();
      }
    }catch(RuntimeException ee){
      JOptionPane.showMessageDialog(this,new String(ee.getMessage()),
                                    this.TITLE_INPUT_ERROR,JOptionPane.ERROR_MESSAGE);
    }
  }


  /**
   * Frame added to show the user that data processing going on
   * @param frame : Passed when we open connection with the server and it is doing
   * some processing.
   * @param msg : Message to be displayed in the frame
   */

  void showInformationFrame(JFrame frame,String msg){

    frame.setTitle(this.TITLE_INFORMATION);
    JLabel label =new JLabel(msg);
    frame.getContentPane().setLayout(new GridBagLayout());
    frame.getContentPane().add(label, new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
        ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(1, 2, 1, 2), 290,50));
    frame.setLocation(getAppletXAxisCenterCoor()-60,getAppletYAxisCenterCoor()-50);
    frame.setVisible(true);
    frame.setVisible(true);
    label.paintImmediately(label.getBounds());
  }


  /**
   * sets up the connection with the servlet on the server (scec.usc.edu)
   */
  void openConnection() {

    //Frame added to show the user that data processing going on

    JFrame frame = new JFrame();
    showInformationFrame(frame,this.MSG_ADDING_FILE);

    //vector which contains all the X and Y values from the function  to be send to the
    //servlet.
    ArrayList vt =new ArrayList();

    int size = function.getNum();
    for(int i=0;i<size;i++){
      String temp= new String(function.getX(i) +" "+function.getY(i));
      vt.add(temp);
    }

    //Name of the PEER file to be added
    String fileName = function.getName();

    try{
      if(D) System.out.println("starting to make connection with servlet");
      URL PEER_TestServlet = new
                            URL("http://scec.usc.edu:9999/examples/servlet/PEER_InputFilesServlet");


      URLConnection servletConnection = PEER_TestServlet.openConnection();
      if(D) System.out.println("connection established");

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

      if(D){
        System.out.println("Function is:"+function.toString());
        System.out.println("Function Name:"+function.getName());
        System.out.println("Function Number:"+function.getNum());
      }
      //sending the "Add" string to servlet to tell it to create a new data file
      outputToServlet.writeObject(new String("Add"));

      // sending the name of the new file name to be created by the servlet
      outputToServlet.writeObject(fileName);

      //sending the vector of values to be input in the file, to the servlet
      outputToServlet.writeObject(vt);
      outputToServlet.flush();
      outputToServlet.close();

      // Receive the "destroy" from the servlet after it has received all the data
      ObjectInputStream inputToServlet = new
      ObjectInputStream(servletConnection.getInputStream());

     String temp=inputToServlet.readObject().toString();

     if(D) System.out.println("Receiving the Input from the Servlet:"+temp);
     inputToServlet.close();
     //displaying the user the addition  has ended
     JOptionPane.showMessageDialog(this,this.MSG_FILE_ADDED,
                                   this.TITLE_ADD_CONFIRMATION,JOptionPane.OK_OPTION);

     //adding the file to the vector as well as the combo box that
     //displays the files that can be deleted
     testFiles.add(new String(fileName));
     frame.dispose();
    }catch (Exception e) {
      System.out.println("Exception in connection with servlet:" +e);
      e.printStackTrace();
    }
  }

  /**
   * Opens the connection with the servlet
   * @param fileName = file to be deleted is sent to the servlet
   */
  void openDeleteConnection(String fileName) {


    //Frame added to show the user that data processing going on

    JFrame frame = new JFrame();
    showInformationFrame(frame,this.MSG_DELETING_FILE);
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

      //sending the "Delete" string to servlet to tell it to delete data file
      outputToServlet.writeObject(new String("Delete"));

      // sending the name of the new file name to be created by the servlet
      outputToServlet.writeObject(fileName);

      outputToServlet.flush();
      outputToServlet.close();

      // Receive the "destroy" from the servlet after it has received all the data
      ObjectInputStream inputToServlet = new
          ObjectInputStream(servletConnection.getInputStream());

      String temp=inputToServlet.readObject().toString();

      if(D)
        System.out.println("Receiving the Input from the Servlet:"+temp);
      inputToServlet.close();
      //displaying the user the deletion  has ended
      JOptionPane.showMessageDialog(this,this.MSG_FILE_OVERWRITTEN,
                                   this.TITLE_DELETE_CONFIRMATION,
                                   JOptionPane.OK_OPTION);


      //removing the deleted file from the vector as well as the combo box that
      //displays the files that can be deleted
      int size=testFiles.size();
      for(int i=0;i<size;++i)
        if(testFiles.get(i).toString().equals(fileName))
          testFiles.remove(i);
      peerDelete.updateFileNames(testFiles);
      frame.dispose();
    }catch (Exception e) {
      System.out.println("Exception in connection with servlet:" +e);
      e.printStackTrace();
    }
  }


  /**
   * Opens the connection with the servlet to check password
   * @param password= to see if the user has entered the correct password
   * for deletion of file
   */
    public boolean checkPassword(String password) {

      try{
        if(D) System.out.println("starting to make connection with servlet");
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

        //sending the "Delete" string to servlet to tell it to check the password
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

        if(D) System.out.println("Receiving the Input from the Servlet:"+temp);
        inputToServlet.close();
        if(temp.equalsIgnoreCase("success"))return true;
        else return false;
      }catch (Exception e) {
        System.out.println("Exception in connection with servlet:" +e);
        e.printStackTrace();
      }
      return false;
    }


    /**
     * This method establishes the connection with the servlet and is activated
     * if the existing data file has to be overwritten.
     * @param fileName: Name of the file to be overwritten
     */
    void openOverwriteConnection(String fileName) {

      overwriteFlag=false;

      //Frame added to show the user that data processing going on
      JFrame frame = new JFrame();
      showInformationFrame(frame,MSG_FILE_OVERWRITE);
      //vector which contains all the X and Y values from the function  to be send to the
      //servlet.
      ArrayList vt =new ArrayList();
      int size = function.getNum();
      for(int i=0;i<size;i++){
        String temp= new String(function.getX(i) +" "+function.getY(i));
        vt.add(temp);
      }

      try{
        if(D) System.out.println("starting to make connection with servlet");
        URL PEER_TestServlet = new
                               URL("http://scec.usc.edu:9999/examples/servlet/PEER_InputFilesServlet");

        URLConnection servletConnection = PEER_TestServlet.openConnection();
        if(D) System.out.println("connection established");

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

        if(D){
          System.out.println("Function is:"+function.toString());
          System.out.println("Function Name:"+function.getName());
          System.out.println("Function Number:"+function.getNum());
        }

        //sending the "Overwrite" string to servlet to tell it to create a new data file
        outputToServlet.writeObject(new String("Overwrite"));

        // sending the name of the file to be overwritten
        outputToServlet.writeObject(fileName);

        //sending the vector of values to be input in the file, to the servlet
        outputToServlet.writeObject(vt);
        outputToServlet.flush();
        outputToServlet.close();

        // Receive the "destroy" from the servlet after it has received all the data
        ObjectInputStream inputToServlet = new
            ObjectInputStream(servletConnection.getInputStream());

        String temp=inputToServlet.readObject().toString();

        if(D) System.out.println("Receiving the Input from the Servlet:"+temp);
        inputToServlet.close();
        //displaying the user the addition  has ended
        JOptionPane.showMessageDialog(this,this.MSG_FILE_OVERWRITTEN,
                                      this.TITLE_OERWRITE_CONFIRMATION,
                                      JOptionPane.OK_OPTION);
        frame.dispose();
      }catch (Exception e) {
        System.out.println("Exception in connection with servlet:" +e);
        e.printStackTrace();
      }
    }


  /**
   * When the user wants to delete the PEER data file from the server
   * @param e
   */
  void deleteFileButton_actionPerformed(ActionEvent e) {

     peerDelete = new PEER_FileDeleteWindow(this,testFiles);
     peerDelete.setLocation(getAppletXAxisCenterCoor()-60,getAppletYAxisCenterCoor()-50);
     peerDelete.pack();
     peerDelete.setVisible(true);
  }

  /**
   * gets the Applets X-axis center coordinates
   * @return
   */
  private int getAppletXAxisCenterCoor() {
    return (this.getX()+this.getWidth())/2;
  }

  /**
   * gets the Applets Y-axis center coordinates
   * @return
   */
  private int getAppletYAxisCenterCoor() {
    return (this.getY() + this.getHeight())/2;
  }

  void imgLabel_mouseClicked(MouseEvent e) {
    try{
    this.getAppletContext().showDocument(new URL(OPENSHA_WEBSITE),"_blank");
    }catch(java.net.MalformedURLException ee){
      JOptionPane.showMessageDialog(this,
                                    this.MSG_NO_INTERNET_CONNECTION,
                                    this.TITLE_NO_INTERNET_CONNECTION,
                                    JOptionPane.OK_OPTION);
    }
  }
  void imgLabel_mousePressed(MouseEvent e) {

  }
  void imgLabel_mouseReleased(MouseEvent e) {

  }
  void imgLabel_mouseEntered(MouseEvent e) {

  }
  void imgLabel_mouseExited(MouseEvent e) {

  }

}
