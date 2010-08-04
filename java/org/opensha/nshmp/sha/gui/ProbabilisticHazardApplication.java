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

package org.opensha.nshmp.sha.gui; 

import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Container;
import java.awt.Dimension;
import java.awt.FlowLayout;
import java.awt.Font;
import java.awt.Graphics;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.PrintJob;
import java.awt.Rectangle;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.ItemEvent;
import java.awt.event.ItemListener;
import java.awt.event.WindowEvent;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Properties;

import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JComboBox;
import javax.swing.JDialog;
import javax.swing.JFileChooser;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JMenu;
import javax.swing.JMenuBar;
import javax.swing.JMenuItem;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JSplitPane;
import javax.swing.JTextArea;
import javax.swing.JTextPane;
import javax.swing.UIManager;
import javax.swing.WindowConstants;
import javax.swing.border.BevelBorder;
import javax.swing.border.Border;
import javax.swing.border.TitledBorder;

import org.opensha.commons.util.DataUtil;
import org.opensha.nshmp.sha.gui.api.ProbabilisticHazardApplicationAPI;
import org.opensha.nshmp.sha.gui.beans.ASCE7_GuiBean;
import org.opensha.nshmp.sha.gui.beans.AnalysisOptionsGuiBeanAPI;
import org.opensha.nshmp.sha.gui.beans.IBC_GuiBean;
import org.opensha.nshmp.sha.gui.beans.IRC_GuiBean;
import org.opensha.nshmp.sha.gui.beans.NEHRP_GuiBean;
import org.opensha.nshmp.sha.gui.beans.NFPA_GuiBean_Wrapper;
import org.opensha.nshmp.sha.gui.beans.ProbHazCurvesGuiBean;
import org.opensha.nshmp.sha.gui.beans.UHS_GuiBean;
import org.opensha.nshmp.sha.gui.infoTools.AddProjectNameDateWindow;
import org.opensha.nshmp.sha.gui.infoTools.NSHMP_MapViewFrame;
import org.opensha.nshmp.util.GlobalConstants;
import org.opensha.nshmp.util.MapUtil;
import org.opensha.nshmp.util.Versioner;


/**
 * <p>Title:ProbabilisticHazardApplication </p>
 *
 * <p>Description: This application allows users to obtain hazard curves,
 * uniform hazard response spectra and design parameters for the design
 * documents listed below:
 * <ul>
 * <li> Probabilistic Hazard curves.
 * <li> Probabilistic Uniform Hazard Response Spectra.
 * <li> NEHRP Recommended Provisions for Seismic Regulations for New Buildings and Other Structure.
 * <li> FEMA 273,MCE Guidelines for the Seismic Rehabilitation of Buildings.
 * <li> FEMA 356,Prestandard and Commentary for the Seismic Rehabilitation of Buildings.
 * <li> International Building Code
 * <li> International Residential Code
 * <li> International Existing Building Code
 * <li> NFPA 5000 Building construction and safety code
 * <li> ASCE 7 standard , Minimum Design Loads for Building and other structures.
 * </ul>
 * </p>
 * @author  Ned Field, Nitin Gupta and E.V Leyendecker
 * @version 1.0
 */
public class ProbabilisticHazardApplication
    extends JFrame implements ProbabilisticHazardApplicationAPI {

  JPanel contentPane;
  
  private static final long serialVersionUID = 0xAAB2823;
  
  JMenuBar applicationMenu = new JMenuBar();
  JMenu fileMenu = new JMenu();
  JMenu helpMenu = new JMenu();
  JMenuItem fileExitMenu = new JMenuItem();
  JMenuItem filePrintMenu = new JMenuItem();
  JMenuItem fileSaveMenu = new JMenuItem();
  JMenuItem fileAddProjNameMenu = new JMenuItem();
  JMenuItem helpAnalysisOptionExplainationMenu = new JMenuItem();
  JMenuItem helpExcelFileFormatMenu = new JMenuItem();
  JMenu helpSiteLocationNotes = new JMenu();
  JMenu helpUS_TerritoryNotes = new JMenu();
  JMenuItem helpAbout = new JMenuItem();
  JMenuItem siteLocNotesLatLonAcc = new JMenuItem();
  JMenuItem siteLocNotesZipCodeCaution = new JMenuItem();
  JMenuItem usTerrPuertoRico = new JMenuItem();
  JMenuItem usTerrGuam = new JMenuItem();
  JDialog revs;


  // height and width of the applet
  private final static int W = 900;
  private final static int H = 660;
  JPanel jPanel1 = new JPanel();
  JSplitPane mainSplitPane = new JSplitPane();
  JLabel analysisOptionLabel = new JLabel();
  JComboBox analysisOptionSelectionCombo = new JComboBox();
  JSplitPane dataSplitPane = new JSplitPane();
  JScrollPane dataScrollPane = new JScrollPane();
  JScrollPane parametersScrollPane = new JScrollPane();
  JPanel buttonPanel = new JPanel();
  JTextArea dataTextArea = new JTextArea();
  BorderLayout borderLayout1 = new BorderLayout();
  BorderLayout borderLayout2 = new BorderLayout();
  BorderLayout borderLayout3 = new BorderLayout();
  JButton clearDataButton = new JButton();
  JButton viewMapsButton = new JButton();
  FlowLayout flowLayout1 = new FlowLayout();
  private JButton explainButton = new JButton();
  GridBagLayout gridBagLayout1 = new GridBagLayout();
  private JDialog frame;
  private JTextPane explainationText;
  private JTextPane analysisText;
  private JScrollPane analysisScrollPane;
  private Versioner versioner;

  //some tooltip text strings for buttons
	protected String clearDataToolTip = 
				"Clear the content of the output list box.";
	protected String viewMapsToolTip = "View Maps.";

  private JLabel imgLabel = new JLabel(GlobalConstants.USGS_LOGO_ICON);

  Border border9 = BorderFactory.createBevelBorder(BevelBorder.LOWERED,
      Color.white, Color.white, new Color(98, 98, 98), new Color(140, 140, 140));
  TitledBorder outputBorder = new TitledBorder(border9,
                                               "Output for All Calculations");

  //instance of the gui bean for the selected analysis option
  private AnalysisOptionsGuiBeanAPI guiBeanAPI;

  //This HashMap adds Guibeans for the selected Analysis options
  private HashMap<String, AnalysisOptionsGuiBeanAPI> analysisOptionHash = new HashMap<String, AnalysisOptionsGuiBeanAPI>();
  //saves which was the last selected analysis option
  private String previousSelectedAnalysisOption;
  BorderLayout borderLayout4 = new BorderLayout();
  private GridBagLayout gridBagLayout2 = new GridBagLayout();

  private AddProjectNameDateWindow projectNameWindow;

  //Map Viewing Capability
  private NSHMP_MapViewFrame mapViewFrame;

  public ProbabilisticHazardApplication() {
    try {
      setDefaultCloseOperation(EXIT_ON_CLOSE);
		versioner = new Versioner();
      jbInit();
      setIconImage(GlobalConstants.USGS_LOGO_ONLY_ICON.getImage());
      //setExplainationForSelectedAnalysisOption(previousSelectedAnalysisOption);
      createGuiBeanInstance();
    }
    catch (Exception exception) {
      exception.printStackTrace();
    }
  }

  //static initializer for setting look & feel
  static {
    try {
      UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
    }
    catch (Exception e) {
    }
  }

  /**
   * Component initialization.
   *
   * @throws java.lang.Exception
   */
  private void jbInit() throws Exception {
    contentPane = (JPanel) getContentPane();
    contentPane.setLayout(borderLayout1);
    setTitle("Seismic Hazard Curves and Uniform Hazard Response Spectra");
    this.setDefaultCloseOperation(WindowConstants.DO_NOTHING_ON_CLOSE);
    this.addWindowListener(new java.awt.event.WindowAdapter() {
      public void windowClosing(WindowEvent e) {
        this_windowClosing(e);
      }
    });
    fileMenu.setText("File");
    helpMenu.setText("Help");
    fileExitMenu.setText("Exit");
    fileSaveMenu.setText("Save");
    filePrintMenu.setText("Print");
    fileAddProjNameMenu.setText("Add Name & Date");
    helpAnalysisOptionExplainationMenu.setText("Analysis Option Explanation");
    helpExcelFileFormatMenu.setText("Batch File Format");
    helpSiteLocationNotes.setText("Site Location Notes");
    helpUS_TerritoryNotes.setText("U.S. Territory Notes");
    helpAbout.setText("About");
    siteLocNotesLatLonAcc.setText("Latitude-Longitude Accuracy");
    siteLocNotesZipCodeCaution.setText("Zip Code Caution");
    usTerrGuam.setText("Guam/Tutuila Region Message");
    usTerrPuertoRico.setText("Puerto Rico/Virgin Islands");
    fileExitMenu.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        fileExitMenu_actionPerformed(e);
      }
    });
    fileSaveMenu.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        fileSaveMenu_actionPerformed(e);
      }
    });

    fileAddProjNameMenu.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        fileAddProjNameMenu_actionPerformed(e);
      }
    });


    filePrintMenu.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        filePrintMenu_actionPerformed(e);
      }
    });

    helpAnalysisOptionExplainationMenu.addActionListener(new java.awt.event.ActionListener() {
          public void actionPerformed(ActionEvent e) {
            helpAnalysisOptionExplainationMenu_actionPerformed(e);
          }
    });

    helpExcelFileFormatMenu.addActionListener(new java.awt.event.ActionListener() {
    	public void actionPerformed(ActionEvent e) {
    		helpExcelFileFormatMenu_actionPerformed(e);
    	}
    });
    
    siteLocNotesLatLonAcc.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        siteLocNotesLatLonAcc_actionPerformed(e);
      }
    });

    siteLocNotesZipCodeCaution.addActionListener(new java.awt.event.
                                                 ActionListener() {
      public void actionPerformed(ActionEvent e) {
        siteLocNotesZipCodeCaution_actionPerformed(e);
      }
    });

    helpAbout.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        helpAbout_actionPerformed(e);
      }
    });

    usTerrPuertoRico.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        usTerrPuertoRico_actionPerformed(e);
      }
    });

    usTerrGuam.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        usTerrGuam_actionPerformed(e);
      }
    });

    /*usTerrGuam.addActionListener(new java.awt.event.ActionListener() {
         public void actionPerformed(ActionEvent e) {
           usTerrGuam_actionPerformed(e);
         }
    });

    usTerrGuam.addActionListener(new java.awt.event.ActionListener() {
     public void actionPerformed(ActionEvent e) {
       usTerrGuam_actionPerformed(e);
     }
   });
*/


    jPanel1.setLayout(gridBagLayout1);
    mainSplitPane.setOrientation(JSplitPane.HORIZONTAL_SPLIT);
    mainSplitPane.setForeground(Color.black);
    analysisOptionLabel.setFont(new java.awt.Font("Arial", Font.PLAIN, 15));
    analysisOptionLabel.setForeground(Color.red);
    analysisOptionLabel.setText("Select Analysis Option:");
    analysisOptionSelectionCombo.setFont(new java.awt.Font("Arial", Font.PLAIN,
        15));
    analysisOptionSelectionCombo.setForeground(Color.BLUE);

    //adding the supported Analysis option to the combo selection
    ArrayList supportAnalysisOptions = GlobalConstants.
        getSupportedAnalysisOptions();
    int size = supportAnalysisOptions.size();

    for (int i = 0; i < size; ++i) {
      analysisOptionSelectionCombo.addItem(supportAnalysisOptions.get(i));
    }
    previousSelectedAnalysisOption = (String) supportAnalysisOptions.get(0);

    analysisOptionSelectionCombo.addItemListener(new ItemListener() {
      public void itemStateChanged(ItemEvent itemEvent) {
        analysisOptionSelectionCombo_itemStateChanged(itemEvent);
      }
    });

    dataSplitPane.setOrientation(JSplitPane.VERTICAL_SPLIT);
    dataSplitPane.setBorder(outputBorder);
    dataSplitPane.setMinimumSize(new Dimension(10,10));
    outputBorder.setTitleColor(Color.RED);
    dataTextArea.setText("");
		dataTextArea.setToolTipText("Output for analysis.");
		dataTextArea.setFont(new Font("Monospaced", Font.PLAIN, 12));

    buttonPanel.setLayout(gridBagLayout2);
    clearDataButton.setText("Clear Data");
		clearDataButton.setToolTipText(clearDataToolTip);
    viewMapsButton.setText("View Maps");
		viewMapsButton.setToolTipText(viewMapsToolTip);

    explainButton.addActionListener(new ActionListener() {
      public void actionPerformed(ActionEvent actionEvent) {
        explainButton_actionPerformed(actionEvent);
      }
    });
    clearDataButton.addActionListener(new ActionListener() {
      public void actionPerformed(ActionEvent actionEvent) {
        clearDataButton_actionPerformed(actionEvent);
      }
    });

    viewMapsButton.addActionListener(new ActionListener() {
      public void actionPerformed(ActionEvent actionEvent) {
        viewMapsButton_actionPerformed(actionEvent);
      }
    });

    applicationMenu.add(fileMenu);
    applicationMenu.add(helpMenu);
    fileMenu.add(fileSaveMenu);
    fileMenu.add(fileAddProjNameMenu);
    fileMenu.add(filePrintMenu);
    fileMenu.add(fileExitMenu);
    helpMenu.add(helpAnalysisOptionExplainationMenu);
    helpMenu.add(helpExcelFileFormatMenu);
    helpMenu.add(helpSiteLocationNotes);
    helpMenu.add(helpUS_TerritoryNotes);
    helpMenu.add(helpAbout);
    helpSiteLocationNotes.add(siteLocNotesLatLonAcc);
    helpSiteLocationNotes.add(siteLocNotesZipCodeCaution);
    helpUS_TerritoryNotes.add(usTerrPuertoRico);
    helpUS_TerritoryNotes.add(usTerrGuam);
    mainSplitPane.add(dataSplitPane, JSplitPane.RIGHT);
    parametersScrollPane.setHorizontalScrollBarPolicy(JScrollPane.HORIZONTAL_SCROLLBAR_NEVER);
    parametersScrollPane.setVerticalScrollBarPolicy(JScrollPane.VERTICAL_SCROLLBAR_NEVER);
    mainSplitPane.add(parametersScrollPane, JSplitPane.LEFT);
    dataSplitPane.add(dataScrollPane, JSplitPane.TOP);
    dataSplitPane.add(buttonPanel, JSplitPane.BOTTOM);
    contentPane.add(jPanel1, java.awt.BorderLayout.CENTER);

    buttonPanel.setMinimumSize(new Dimension(0,0));
    dataScrollPane.getViewport().add(dataTextArea, null);

    explainButton.setText("Description");
    buttonPanel.add(imgLabel, new GridBagConstraints(0, 1, 2, 2, 1.0, 1.0
        , GridBagConstraints.NORTH, GridBagConstraints.NONE,
        new Insets(2, 60, 0, 60), 0, 0));
    buttonPanel.add(viewMapsButton, new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
        , GridBagConstraints.NORTH, GridBagConstraints.EAST,
        new Insets(4, 120, 0, 0), 0, 0));
    buttonPanel.add(clearDataButton,
                    new GridBagConstraints(1, 0, 1, 1, 1.0, 1.0
                                           , GridBagConstraints.NORTH,
                                           GridBagConstraints.WEST,
                                           new Insets(4, 12, 0, 120), 0, 0));

    jPanel1.add(analysisOptionLabel,
                new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
                                       , GridBagConstraints.EAST,
                                       GridBagConstraints.NONE,
                                       new Insets(9, 4, 0, 0), 0, 0));
    jPanel1.add(analysisOptionSelectionCombo,
                new GridBagConstraints(1, 0, 1, 1, 1.0, 0.0
                                       , GridBagConstraints.CENTER,
                                       GridBagConstraints.HORIZONTAL,
                                       new Insets(9, 0, 0, 0), 0, 0));
    jPanel1.add(explainButton, new GridBagConstraints(2, 0, 1, 1, 0.0, 0.0
        , GridBagConstraints.EAST, GridBagConstraints.NONE,
        new Insets(6, 4, 2, 60), 0, 0));
    jPanel1.add(mainSplitPane, new GridBagConstraints(0, 1, 3, 1, 1.0, 1.0
        , GridBagConstraints.CENTER, GridBagConstraints.BOTH,
        new Insets(10, 8, 5, 10), 0, 0));
    parametersScrollPane.getViewport().setLayout(new BorderLayout());
    setJMenuBar(applicationMenu);
    Dimension d = Toolkit.getDefaultToolkit().getScreenSize();
    setSize(W,H);
    this.setLocation( (d.width - this.getSize().width) / 2, 0);
    mainSplitPane.setDividerLocation(390);
    dataSplitPane.setDividerLocation(414);
		analysisOptionSelectionCombo.setSelectedIndex(2);
    buttonPanel.updateUI();
    contentPane.updateUI();
  }

  /**
   * File | Exit action performed.
   *
   * @param actionEvent ActionEvent
   */
  void fileExitMenu_actionPerformed(ActionEvent actionEvent) {

    closeWindow();
  }

  private void closeWindow() {
    int option = JOptionPane.showConfirmDialog(this,
                                               "Do you really want to exit the application?\n" +
                                               "You will lose any unsaved data",
                                               "Closing Application",
                                               JOptionPane.OK_CANCEL_OPTION);
    if (option == JOptionPane.OK_OPTION) {
      System.exit(0);
    }
    return;

  }

  /**
   * File | Save action performed.
   *
   * @param actionEvent ActionEvent
   */
  void fileSaveMenu_actionPerformed(ActionEvent actionEvent) {
    save();
  }

  /**
   * File | Add Name and Date to the Data action performed.
   *
   * @param actionEvent ActionEvent
   */
  void fileAddProjNameMenu_actionPerformed(ActionEvent actionEvent) {
    if(projectNameWindow ==null){
      projectNameWindow = new AddProjectNameDateWindow();
    }
    projectNameWindow.setVisible(true);
  }

  /**
   * Help | Explaination to all the Analysis Options
   *
   * @param actionEvent ActionEvent
   */
  void helpAnalysisOptionExplainationMenu_actionPerformed(ActionEvent
      actionEvent) {

    JDialog analysisOptionExpFrame;
    //Panel Parent
    Container parent = this;
    /*
     This loops over all the parent of this class until the parent is Frame(applet)
          this is required for the passing in the JDialog to keep the focus on the adjustable params
          frame
     */
    while (! (parent instanceof JFrame) && parent != null) {
      parent = parent.getParent();
    }

    analysisOptionExpFrame = new JDialog( (JFrame) parent);
    analysisOptionExpFrame.setModal(true);
    analysisOptionExpFrame.setSize(500, 350);
    analysisOptionExpFrame.getContentPane().setLayout(new GridBagLayout());
    analysisText = new JTextPane();
    analysisText.setContentType("text/html");
    analysisText.setText(GlobalConstants.getAllExplainationsForAnalysisOption());
	analysisText.setEditable(false);
	analysisText.setCaretPosition(0);
    analysisScrollPane = new JScrollPane();
    analysisScrollPane.getViewport().add(analysisText, null);
		analysisScrollPane.scrollRectToVisible(new Rectangle(10,10,1,1));

    analysisOptionExpFrame.getContentPane().add(analysisScrollPane,
                                                new GridBagConstraints(0, 0, 1, 1,
        1.0, 1.0
        , GridBagConstraints.CENTER, GridBagConstraints.BOTH,
        new Insets(4, 4, 4, 4), 0, 0));
    analysisOptionExpFrame.setLocation( (getSize().width -
                                         analysisOptionExpFrame.getWidth()) / 3,
                                       (getSize().height -
                                        analysisOptionExpFrame.getHeight()) / 3);
    analysisOptionExpFrame.setTitle("Analysis Options Explanation");
    analysisOptionExpFrame.setVisible(true);
  }

  /**
   * Help | Explain the batch file format.
   */
  void helpExcelFileFormatMenu_actionPerformed(ActionEvent event) {
	  String batchFileHelp = "<h2>Batch files should be in Microsoft Excel format.</h2>" +
	  
	  "<p>These files consist of three basic columns. Latitude, Longitude, and Site Class (optional)." +
	  "The columns should be in the first three columns in the spreadsheet in the first sheet in the workbook." +
	  "Each column should contain relevant values.</p><ul>" +
	  "<li>Latitude: Decimal value.</li>" +
	  "<li>Longitude: Decimal value. (Use negative for Western longitudes.)</li>" +
	  "<li>Site  Class (optional): For SM and SD values and spectra only. Single Character (A-D). If not specified, then 'D' is used.</li>" +
	  "</ul><p>All fields must be properly formatted for their respective data types and formula values are not allowed. " +
	  "Also, the first row in each column should be a header column. This value will be ignored even if you put valid inputs you would like calculated into it." +
	  "The number of rows is limited to 1,000.</p>" +
	  "<h3>Example</h3>" +
	  "<table border=\"1\" cellpadding=\"2\" cellspacing=\"0\">" +
	  "<tr><th>Latitude</th><th>Longitude</th><th>Site Class</th></tr>" +
	  "<tr><td>35.0</td><td>-118.2</td><td>C</td></tr>" +
	  "<tr><td>34.2</td><td>-90.4</td><td>&nbsp</td></tr>" +
	  "</table>" +
	  "<p>The Input Batch File can also be used for the Output File, without overwriting any data.</p>" +
	  "<p>The \"Grid Spacing Basis\" column in the output provides the grid spacing, in degrees, of the underlying data points that are the basis for the " +
	  "interpolated values returned. The other columns in the output should be self-explanatory.</p>";
	  
	  String batchFileTitle = "Excel (Batch) File Format";
	  
	  showMsgBox(batchFileHelp, batchFileTitle, 400, 700);
  }
  /**
   * Help | Explaination to all the Analysis Options
   *
   * @param actionEvent ActionEvent
   */
  void siteLocNotesLatLonAcc_actionPerformed(ActionEvent
                                             actionEvent) {

    String infoMsg = "The user should use values of the latitude and longitude "+
        "with sufficient accuracy to locate the site. For guidance, a latitude "+
        "increment of 0.1 degreee is about 11km. The longitude increment varies "+
        "but in the central part of the 48 states an increment of 0.1 degree is "+
      " about 9 km.";
    showMsgBox(infoMsg,"Latitude-Longitude Caution", 350,150) ;
  }


  private void showMsgBox(String infoMsg, String heading,int width, int height){
    JDialog analysisOptionExpFrame;
    //Panel Parent
    Container parent = this;
    /*
     This loops over all the parent of this class until the parent is Frame(applet)
     this is required for the passing in the JDialog to keep the focus on the adjustable params
     frame
     */
    while (! (parent instanceof JFrame) && parent != null) {
      parent = parent.getParent();
    }

    analysisOptionExpFrame = new JDialog( (JFrame) parent);
    analysisOptionExpFrame.setModal(true);
    analysisOptionExpFrame.setSize(width, height);
    analysisOptionExpFrame.getContentPane().setLayout(new GridBagLayout());
    analysisText = new JTextPane();
    analysisText.setContentType("text/html");
    analysisText.setBackground(UIManager.getColor("Panel.background"));
    analysisText.setText(infoMsg);
    analysisText.setEditable(false);

    analysisOptionExpFrame.getContentPane().add(analysisText,
                                                new GridBagConstraints(0, 0, 1,
        1,
        1.0, 1.0
        , GridBagConstraints.CENTER, GridBagConstraints.BOTH,
        new Insets(4, 4, 4, 4), 0, 0));
    analysisOptionExpFrame.setLocation( (getSize().width -
                                         analysisOptionExpFrame.getWidth()) / 2,
                                       (getSize().height -
                                        analysisOptionExpFrame.getHeight()) / 2);
    analysisOptionExpFrame.setTitle(heading);
    analysisOptionExpFrame.setVisible(true);

  }





  /**
   * Help | Explaination to all the Analysis Options
   *
   * @param actionEvent ActionEvent
   */
  void siteLocNotesZipCodeCaution_actionPerformed(ActionEvent
      actionEvent) {
  String infoMsg = "In some regions, there can be substantial variation "+
      "between the spectral values at a zip code centroid and those at individual "+
      "structures at some sites and excessively conservative designs at other sites.\n\n"+
      "For those regions where substantial variation in projected ground motion may occur "+
      "across a zip code designers should consider using latitude and longitude as a reference "+
      "for site location when determining ground motion parameters.";
    showMsgBox(infoMsg,"Zip Code Caution",380,225) ;
  }

  /**
   * Help | Explaination to all the Analysis Options
   *
   * @param actionEvent ActionEvent
   */
  void helpAbout_actionPerformed(ActionEvent
      actionEvent) {
		//Ask E.V. for the help files so we can implement in some version of this application.
      Object [] options = { "Okay", "Revision History" };
      String title = "Earthquake Ground Motion Tool";
      String message = GlobalConstants.getAbout();
      int optionType = JOptionPane.DEFAULT_OPTION;
      int msgType = JOptionPane.INFORMATION_MESSAGE;
  
      int answer = JOptionPane.showOptionDialog(this, message, title, optionType,
                                                msgType, null, options, options[0]);
      if (answer == 1) { // Details was clicked
			if ( revs == null ) {
         	// Create the text pane
         	JTextPane det = new JTextPane();
         	det.setContentType("text/html");
         	det.setEditable(false);
         	det.setText(versioner.getAllUpdates());
  	
         	// Create the scroll pane
         	JScrollPane revPane = new JScrollPane();
         	revPane.getViewport().add(det, null);
         	det.setCaretPosition(0);
    	
         	// Create the Dialog window
         	Container parent = this;
         	while ( !(parent instanceof JFrame) && parent != null) {
            	parent = parent.getParent();
         	}
         	revs = new JDialog( (JFrame) parent);
         	revs.setModal(true);
         	revs.setSize(400, 200);
         	revs.getContentPane().setLayout(new GridBagLayout());
         	revs.getContentPane().add(revPane, new GridBagConstraints(
            	0, 0, 1, 1, 1.0, 1.0, GridBagConstraints.CENTER, GridBagConstraints.BOTH,
            	new Insets(4, 4, 4, 4), 0, 0));
         	revs.setLocation(this.getLocation());
         	revs.setTitle(title);
			}
         revs.setVisible(true);
      } 
  }


  /**
   * Help | Explaination to all the Analysis Options
   *
   * @param actionEvent ActionEvent
   */
  void usTerrPuertoRico_actionPerformed(ActionEvent
                                        actionEvent) {
    String infoMsg = "Region values for Puerto Rico and the U.S. Virgin Islands are constant, "+
        "although there are variations within the region, for Editions through 2000. In these "+
        "cases the latitude, longitude and zip code boxes are labeled \"Not Available\". Do not "+
        "enter latitude-longitude or zip code values. Simply click on \"Calculate Ss and S1\" "+
        "to obtain values in these cases.\n\nLatitude and Longitude values are registered for "+
        "Puerto Rico and the U.S.Virgin Islands beginning with the 2003 Edition. In these cases the "+
        "latitude and longitude boxes are empty and site locations must be entered to obtain site values. "+
        "Values are not yet available for Zip Codes.";
    showMsgBox(infoMsg,"PRVI Region Message",440,250);

  }


  /**
   * Help | Explaination to all the Analysis Options
   *
   * @param actionEvent ActionEvent
   */
  void usTerrGuam_actionPerformed(ActionEvent
                                  actionEvent) {
    String infoMsg = "Regional values for Guam and Tutuilla are constant for each region. "+
        "In these cases the latitude, longitude, and zip code boxes are labeled \"Not Available\". "+
        "Do not enter latitude,longitude and zip code values. Simply click on "+
        "\"Calculate Ss and S1\" to obtain values in these cases.";
    showMsgBox(infoMsg,"Guam/Tutuila Region Message",350,150);
  }


  /**
   * File | Print action performed.
   *
   * @param actionEvent ActionEvent
   */
  void filePrintMenu_actionPerformed(ActionEvent actionEvent) {
    print();
  }

  private void save() {
    JFileChooser fileChooser = new JFileChooser();
    int option = fileChooser.showSaveDialog(this);
    String fileName = null;
	if (option == JFileChooser.APPROVE_OPTION) {
	  fileName = fileChooser.getSelectedFile().getAbsolutePath();
      if (!fileName.endsWith(".txt") ) {
        fileName = fileName + ".txt";
      }
    }
    else {
      return;
    }

	// Add the project name/date to the file
	 String data = "";

    if(projectNameWindow !=null){
      String name = projectNameWindow.getProjectName();
      String date = projectNameWindow.getDate();
      if(name !=null && !name.trim().equals(""))
        data += name + "\n";
      if(date !=null)
        data += date + "\n\n";
    }
	 data += guiBeanAPI.getData();

    DataUtil.save(fileName, data);
  }

  /**
   * Method to print the Data
   */
  private void print() {
    Properties p = new Properties();
    PrintJob pjob = getToolkit().getPrintJob(this, "Printing", p);

	 // Add project name/date to print job
	 String data = "";

    if(projectNameWindow !=null){
      String name = projectNameWindow.getProjectName();
      String date = projectNameWindow.getDate();
      if(name !=null && !name.trim().equals(""))
        data +="Project Name = "+name+"\n";
      if(date !=null)
        data +="Date = "+date +"\n\n";
    }

	 data += guiBeanAPI.getData() + System.getProperty("line.separator");

	
	// Create the print job
    if (pjob != null) {
      Graphics pg = pjob.getGraphics();
      if (pg != null) {
        DataUtil.print(pjob, pg, data);
        pg.dispose();
      }
      pjob.end();
    }
	 
  }

  private void analysisOptionSelectionCombo_itemStateChanged(ItemEvent
      itemEvent) {
    analysisOptionHash.put(previousSelectedAnalysisOption, guiBeanAPI);
    String selectedAnalysisOption = (String) analysisOptionSelectionCombo.
        getSelectedItem();
    guiBeanAPI = (AnalysisOptionsGuiBeanAPI) analysisOptionHash.get(
        selectedAnalysisOption);
    parametersScrollPane.getViewport().removeAll();
    if (guiBeanAPI == null) {
      createGuiBeanInstance();
    }
    else {
      parametersScrollPane.getViewport().add(guiBeanAPI.getGuiBean(),BorderLayout.CENTER);
      parametersScrollPane.updateUI();
    }
    setDataInWindow(guiBeanAPI.getData());
    previousSelectedAnalysisOption = selectedAnalysisOption;
  }

  private void createGuiBeanInstance() {
    String selectedAnalysisOption = (String) (String)
        analysisOptionSelectionCombo.getSelectedItem();
    if (selectedAnalysisOption.equals(GlobalConstants.PROB_HAZ_CURVES)) {
      guiBeanAPI = new ProbHazCurvesGuiBean(this);
    }
    else if (selectedAnalysisOption.equals(GlobalConstants.PROB_UNIFORM_HAZ_RES)) {
      guiBeanAPI = new UHS_GuiBean(this);
    }
    else if (selectedAnalysisOption.equals(GlobalConstants.NEHRP)) {
			guiBeanAPI = new NEHRP_GuiBean(this);
    }
    else if (selectedAnalysisOption.equals(GlobalConstants.NFPA)) {
      guiBeanAPI = new NFPA_GuiBean_Wrapper(this);
    }
    else if (selectedAnalysisOption.equals(GlobalConstants.INTL_BUILDING_CODE)) {
      guiBeanAPI = new IBC_GuiBean(this);
    }
    else if (selectedAnalysisOption.equals(GlobalConstants.
                                           INTL_RESIDENTIAL_CODE)) {
      guiBeanAPI = new IRC_GuiBean(this);
    }
    else if (selectedAnalysisOption.equals(GlobalConstants.ASCE_7)) {
      guiBeanAPI = new ASCE7_GuiBean(this);
    }
    if (guiBeanAPI != null) {
      parametersScrollPane.getViewport().add(guiBeanAPI.getGuiBean(),BorderLayout.CENTER);
    }

    parametersScrollPane.updateUI();
  }


  /**
   * Sets the information from the Gui beans in Data window
   * @param dataInfo String
   */
  public void setDataInWindow(String dataInfo) {
    String data="";
    if(projectNameWindow !=null){
      String name = projectNameWindow.getProjectName();
      String date = projectNameWindow.getDate();
      if(name !=null && !name.trim().equals(""))
        data += name + "\n";
      if(date !=null)
        data += date + "\n\n";
    }

    dataTextArea.setText(data+dataInfo);
    dataTextArea.setEditable(false);
  }

  /**
   *
   * @param actionEvent ActionEvent
   */
  private void explainButton_actionPerformed(ActionEvent actionEvent) {
    String analysisOption = (String) analysisOptionSelectionCombo.getSelectedItem();
    setExplainationForSelectedAnalysisOption(analysisOption);
    //if frame is null the create the frame
    if (frame == null)
      showSelectedAnalysisExplaination();

    frame.setTitle(analysisOption);
    frame.setVisible(true);
  }

  /**
   *
   * @param actionEvent ActionEvent
   */
  private void clearDataButton_actionPerformed(ActionEvent actionEvent) {
    guiBeanAPI.clearData();
    setDataInWindow("");
  }

  /**
   *
   * @param actionEvent ActionEvent
   */
  private void viewMapsButton_actionPerformed(ActionEvent actionEvent) {
		/*try {
			org.opensha.util.BrowserLauncher.openURL(
				"http://earthquake.usgs.gov/research/hazmaps/pdfs/");
		} catch (Exception e) {
			e.printStackTrace();
			JOptionPane.showMessageDialog(this, "Failed to open page.", "Error",
				JOptionPane.ERROR_MESSAGE);
		}*/
	//}
    String selectedRegion = guiBeanAPI.getSelectedRegion();
    String selectedEdition = guiBeanAPI.getSelectedDataEdition();
    MapUtil.createMapList(selectedRegion,selectedEdition);
    String[] mapInfo = MapUtil.getSupportedMapInfo();
    String[] mapDataFiles = MapUtil.getSupportedMapFiles();
    if(mapDataFiles.length ==0){
     JOptionPane.showMessageDialog(this,"No Maps available for for the selected choice.\n"+
         "Please select some other region or edition to view the Maps.","Map Display Message",
          JOptionPane.INFORMATION_MESSAGE);
      return;
    }
    else{
      if (mapViewFrame == null)
        mapViewFrame = new NSHMP_MapViewFrame(mapInfo, mapDataFiles);
      else
        mapViewFrame.createListofAvailableMaps(mapInfo, mapDataFiles);
      mapViewFrame.setVisible(true);
    }
  }


  /**
   *
   *
   */
  private void showSelectedAnalysisExplaination() {

    //Panel Parent
    Container parent = this;
    /*This loops over all the parent of this class until the parent is Frame(applet)
         this is required for the passing in the JDialog to keep the focus on the adjustable params
         frame*/
    while (! (parent instanceof JFrame) && parent != null) {
      parent = parent.getParent();
    }

    frame = new JDialog( (JFrame) parent);
    frame.setModal(true);
    frame.setSize(400, 200);
    frame.getContentPane().setLayout(new GridBagLayout());

    frame.getContentPane().add(explainationText,
                               new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
        , GridBagConstraints.CENTER, GridBagConstraints.BOTH,
        new Insets(4, 4, 4, 4), 0, 0));
    frame.setLocation((getSize().width - frame.getWidth())/3 , (getSize().height - frame.getHeight())/ 3);
  }

  /**
   *
   * @param selectedAnalysisOption String : Selected Analysis option
   */
  private void setExplainationForSelectedAnalysisOption(String
      selectedAnalysisOption) {

    if(explainationText == null){
      explainationText = new JTextPane();
      explainationText.setContentType("text/html");
      explainationText.setEditable(false);
    }
    explainationText.setText(GlobalConstants.
                             getExplainationForSelectedAnalysisOption(
        selectedAnalysisOption));
  }

  void this_windowClosing(WindowEvent e) {
    closeWindow();
  }
}
