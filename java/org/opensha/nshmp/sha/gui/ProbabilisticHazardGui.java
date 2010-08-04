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
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;

import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JDialog;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JMenu;
import javax.swing.JMenuBar;
import javax.swing.JMenuItem;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextPane;
import javax.swing.SwingConstants;
import javax.swing.UIManager;
import javax.swing.border.Border;
import javax.swing.border.TitledBorder;

import org.opensha.nshmp.util.GlobalConstants;
import org.opensha.nshmp.util.Versioner;

import edu.stanford.ejalbert.BrowserLauncher;

/**
 * <p>Title: ProbabilisticHazardGui</p>
 *
 * <p>Description: This window is launched whenever the user starts the
 * application for the first time. This window provides user with brief
 * explaination of what user can expect from this application.</p>
 *
 * @author Ned Field, Nitin Gupta, E.V.Leyendecker
 * @version 1.0
 */
public class ProbabilisticHazardGui
    extends JFrame {
  private static final long serialVersionUID = 0xFD99A29;
  JPanel screenPanel = new JPanel();
  JTextPane applicationInfoText = new JTextPane();
  JButton exitButton = new JButton();
  Border border1 = BorderFactory.createEmptyBorder();
  Border border2 = new TitledBorder(border1, "custom");
  TitledBorder titledBorder1 = new TitledBorder("");
  JButton okButton = new JButton();
  JLabel jLabel1 = new JLabel();
  JLabel jLabel2 = new JLabel();
  GridBagLayout gridBagLayout1 = new GridBagLayout();
  JDialog revisions;

  //Objects for the 'file' and 'help' menus in welcome pop-up.
  JMenuBar applicationMenu = new JMenuBar();
  JMenu fileMenu = new JMenu();
  JMenu helpMenu = new JMenu();
  JMenuItem fileExitMenu = new JMenuItem();
  //JMenuItem filePrintMenu = new JMenuItem();
  //JMenuItem fileSaveMenu = new JMenuItem();
  //JMenuItem fileAddProjNameMenu = new JMenuItem();
  //JMenuItem helpAnalysisOptionExplainationMenu = new JMenuItem();
  JMenuItem helpAbout = new JMenuItem();

	private static Versioner versioner;
	private static final String DOWNLOAD_PAGE = "http://earthquake.usgs.gov/research/hazmaps/design/";

  private JLabel imgLabel = new JLabel(GlobalConstants.USGS_LOGO_ICON);
  private GridBagLayout gridBagLayout2 = new GridBagLayout();
  private BorderLayout borderLayout1 = new BorderLayout();

  public ProbabilisticHazardGui(boolean isCurrent) {
    try {
      jbInit(isCurrent);
    }
    catch (Exception exception) {
      exception.printStackTrace();
    }
  }

  public ProbabilisticHazardGui() {
    try {
      jbInit(true);
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

  private void jbInit(boolean isCurrent) throws Exception {
    getContentPane().setLayout(borderLayout1);
    screenPanel.setLayout(gridBagLayout2);
    applicationInfoText.setBackground(UIManager.getColor("Panel.background"));
    applicationInfoText.setFont(new java.awt.Font("Arial", 0, 13));
    applicationInfoText.setEditable(false);

//    exitButton.setText("Exit");
    /*exitButton.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        exitButton_actionPerformed(e);
      }
    });*/

    if (isCurrent) {
	 	okButton.setText("Okay");
    	okButton.addActionListener(new java.awt.event.ActionListener() {
      	public void actionPerformed(ActionEvent e) {
        	okButton_actionPerformed(e);
      	}
    	});
	  } else {
	  	 okButton.setText("Download");
		 okButton.addActionListener(new java.awt.event.ActionListener() {
		 	public void actionPerformed(ActionEvent e) {
				okButton_notCurrent(e);
			}
		});
	  }

    fileMenu.setText("File");
    helpMenu.setText("Help");
    fileExitMenu.setText("Exit");
    //fileSaveMenu.setText("Save");
    //filePrintMenu.setText("Print");
    //fileAddProjNameMenu.setText("Add Name & Date");
    helpAbout.setText("About");

    fileExitMenu.addActionListener(new java.awt.event.ActionListener() {
	public void actionPerformed(ActionEvent e) {
	  fileExitMenu_actionPerformed(e);
	  }
	});

    helpAbout.addActionListener(new java.awt.event.ActionListener() {
	public void actionPerformed(ActionEvent e) {
	  helpAbout_actionPerformed(e);
	  }
	});

    applicationMenu.add(fileMenu);
    applicationMenu.add(helpMenu);
    fileMenu.add(fileExitMenu);
    helpMenu.add(helpAbout);

    jLabel1.setFont(new java.awt.Font("Dialog", 1, 20));
    jLabel1.setForeground(Color.red);
    jLabel1.setHorizontalAlignment(SwingConstants.CENTER);
    jLabel1.setHorizontalTextPosition(SwingConstants.CENTER);
    if (isCurrent) {
	 	jLabel1.setText("Seismic Hazard Curves, Response Parameters");
    	jLabel2.setText("and Design Parameters");
	  } else {
	 	jLabel1.setText("New Version Available  (" + versioner.getServerVersionNumber() + ")");
    	jLabel2.setText("Please Update Your Version of the Application");
	 } 

    jLabel2.setFont(new java.awt.Font("Dialog", 1, 20));
    jLabel2.setForeground(Color.red);
    jLabel2.setHorizontalAlignment(SwingConstants.CENTER);
    jLabel2.setHorizontalTextPosition(SwingConstants.CENTER);
    applicationInfoText.setBorder(null);
    screenPanel.setMaximumSize(new Dimension(600, 600));
    imgLabel.setMaximumSize(new Dimension(200, 75));
    imgLabel.setMinimumSize(new Dimension(200, 75));
    imgLabel.setPreferredSize(new Dimension(200, 75));
    setJMenuBar(applicationMenu);
    screenPanel.add(applicationInfoText,  new GridBagConstraints(0, 2, 2, 1, 1.0, 1.0
            ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(2, 10, 0, 6), 0, 0));
    screenPanel.add(jLabel1,  new GridBagConstraints(0, 0, 2, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(0, 10, 0, 6), 0, 0));
    screenPanel.add(jLabel2,  new GridBagConstraints(0, 1, 2, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(0, 10, 0, 6), 0, 0));
    screenPanel.add(imgLabel,  new GridBagConstraints(0, 4, 1, 1, 0.0, 0.0
            ,GridBagConstraints.SOUTHWEST, GridBagConstraints.NONE, new Insets(0, 0, 3, 3), 0, 0));
    screenPanel.add(okButton,  new GridBagConstraints(0, 4, 1, 1, 0.0, 0.0
            ,GridBagConstraints.SOUTHEAST, GridBagConstraints.NONE, new Insets(0, 475, 3, 0), 0, 0));
    //screenPanel.add(exitButton,  new GridBagConstraints(1, 3, 1, 1, 0.0, 0.0
    //         ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(23, 17, 0, 72), 0, 0));
    this.getContentPane().add(screenPanel, BorderLayout.CENTER);
		this.getRootPane().setDefaultButton(okButton);
    applicationInfoText.setContentType("text/html");
    if (isCurrent) {
	 	applicationInfoText.setText(
        "This application allows the user to obtain hazard curves, " +
			"uniform hazard response spectra, and design parameters for " +
			"sites in the 50 United States, Puerto Rico and the U.S. Virgin " +
			"Islands.  Additionally, design parameters are available for Guam " +
			"and American Samoa.  Ground motion maps are also included in " +
			"PDF format.<pre>\r\n</pre>Detailed explanation of the analyses available is " +
			"included in the help menu.  Click on Okay to begin " +
			"calculation.<pre>\r\n</pre><i>Correct application of the data obtained " +
			"from the use of this program and/or the maps is the " +
			"responsibility of the user.  This software is not a " +
			"substitute for technical knowledge of seismic design and/or " +
			"analysis.</i>");
	} else {
		applicationInfoText.setText(versioner.getUpdateMessage());
	}
    this.setTitle("Seismic Hazard Curves and Uniform Hazard Response Spectra - v" + versioner.getClientVersionNumber());
    this.setSize(new Dimension(576, 450));
    //screenPanel.setSize(new Dimension(600, 500));
    Dimension d = Toolkit.getDefaultToolkit().getScreenSize();
    this.setLocation( (d.width - this.getSize().width) / 2,
                     (d.height - this.getSize().height) / 2);
   setIconImage(GlobalConstants.USGS_LOGO_ONLY_ICON.getImage());
}

	public static void main(String[] args) {
	 	ProbabilisticHazardGui app;
		versioner = new Versioner();
		if ( versioner.check() ) {
    		app = new ProbabilisticHazardGui(versioner.versionCheck());
			app.setVisible(true);
		} else {
			JOptionPane.showMessageDialog(null, "Could not establish a connection to the server.\n" +
				"Our server may be temporarily down, please try again later.\n" +
				"If the problem persists, contact emartinez@usgs.gov", "Connection Failure", 
				JOptionPane.ERROR_MESSAGE);
			System.exit(0);
		}
	}

/*  private void exitButton_actionPerformed(ActionEvent actionEvent) {
    System.exit(0);
  }*/

  private void okButton_actionPerformed(ActionEvent actionEvent) {
    this.dispose();
    ProbabilisticHazardApplication app = new ProbabilisticHazardApplication();
    app.setVisible(true);

  }

	private void okButton_notCurrent(ActionEvent actionEvent) {
		this.dispose();
		try {
		    BrowserLauncher bl = new BrowserLauncher();
			bl.openURLinBrowser(DOWNLOAD_PAGE);
		} catch (Exception ex) {
			JOptionPane.showMessageDialog(null, "Could not open the download page.  Please visit:\n\n\t" +
				DOWNLOAD_PAGE + "\n\nto update your version" +
				" of this application.", "Failed to Open Page", JOptionPane.INFORMATION_MESSAGE);
		} finally {
			System.exit(0);
		}
	}

  /**
   *File | Exit action performed
   *
   *@param actionEvent ActionEvent
   *
   */
  private void fileExitMenu_actionPerformed(ActionEvent actionEvent) {
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
   *Help | About
   *
   *@param actionEvent ActionEvent
   *
   */
  private void helpAbout_actionPerformed(ActionEvent actionEvent) {
	//Ask E.V. for the help files so we can implement in some version of this application.
		Object [] options = { "Okay", "Revision History" };
		String title = "Earthquake Ground Motion Tool";
		String message = GlobalConstants.getAbout();
		int optionType = JOptionPane.DEFAULT_OPTION;
		int msgType = JOptionPane.INFORMATION_MESSAGE;

		int answer = JOptionPane.showOptionDialog(this, message, title, optionType,
																msgType, null, options, options[0]);
		if (answer == 1) { // Details was clicked

			if ( revisions == null ) {
				// Create the text pane
				JTextPane details = new JTextPane();
				details.setContentType("text/html");
				details.setEditable(false);
				details.setText(versioner.getAllUpdates());
	
				// Create the scroll pane
				JScrollPane revScrollPane = new JScrollPane();
				revScrollPane.getViewport().add(details, null);
				details.setCaretPosition(0);
	
				// Create the Dialog window
				Container parent = this;
				while ( !(parent instanceof JFrame) && parent != null) {
					parent = parent.getParent();
				}
				revisions = new JDialog( (JFrame) parent);
				revisions.setModal(true);
				revisions.setSize(400, 200);
				revisions.getContentPane().setLayout(new GridBagLayout());
				revisions.getContentPane().add(revScrollPane, new GridBagConstraints(
					0, 0, 1, 1, 1.0, 1.0, GridBagConstraints.CENTER, GridBagConstraints.BOTH,
					new Insets(4, 4, 4, 4), 0, 0));
				revisions.setLocation(this.getLocation());
				revisions.setTitle(title);
			}
			revisions.setVisible(true);
		}
  }

  
  
}
