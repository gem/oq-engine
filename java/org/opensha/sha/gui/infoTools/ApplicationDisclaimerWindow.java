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
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.SystemColor;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JDialog;
import javax.swing.JEditorPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.border.BevelBorder;
import javax.swing.border.Border;
import javax.swing.border.EtchedBorder;
import javax.swing.border.TitledBorder;

/**
 * <p>Title: ApplicationDisclaimerWindow</p>
 *
 * <p>Description: This class displays the disclaimer message for the application in a window
 * If user accepts it then he/she can proceed with the application, else application quits.
 * </p>
 * @author Ned Field, Nitin Gupta
 * @version 1.0
 */
public class ApplicationDisclaimerWindow
    extends JDialog {

  JPanel msgPanel = new JPanel();
  JTextArea msgPane = new JTextArea();
  Border border1 = BorderFactory.createMatteBorder(6, 6, 6, 6, Color.white);
  Border border2 = BorderFactory.createBevelBorder(BevelBorder.RAISED,
      Color.white, Color.white, new Color(124, 124, 124),
      new Color(178, 178, 178));
  JScrollPane disclaimerPane = new JScrollPane();
  TitledBorder titledBorder1 = new TitledBorder("");
  Border border3 = BorderFactory.createLineBorder(Color.lightGray, 2);
  Border border4 = BorderFactory.createEtchedBorder(EtchedBorder.RAISED,
      Color.white, new Color(178, 178, 178));
  Border border5 = BorderFactory.createEtchedBorder(EtchedBorder.RAISED,
      Color.white, new Color(178, 178, 178));
  JEditorPane updateVersionInfo = new JEditorPane();
  JButton understandButton = new JButton();
  JButton quitButton = new JButton();
  BorderLayout borderLayout1 = new BorderLayout();
  GridBagLayout gridBagLayout1 = new GridBagLayout();
  //URL string to the application
  private String urlToDisclaimerMsgPage;
  GridBagLayout gridBagLayout2 = new GridBagLayout();
  BorderLayout borderLayout2 = new BorderLayout();

  /**
   *
   * @param appURL String : String URL to the application
   * @param updatePageURL String URL to the page that has info for the version update of the application
   * @param title String Message Title
   * @param parent Component Application from which this window is launched
   */
  public ApplicationDisclaimerWindow(String disclaimerMsgURL) {
	urlToDisclaimerMsgPage = disclaimerMsgURL;

    try {
      jbInit();
      setDefaultCloseOperation(DO_NOTHING_ON_CLOSE);
    }
    catch (Exception exception) {
      exception.printStackTrace();
    }
    this.setTitle("Disclaimer Message");
    // show the window at center of the parent component
    this.setVisible(true);
  }


  private void jbInit() throws Exception {
    this.setModal(true);
    this.setSize(450,300);
    this.getContentPane().setLayout(borderLayout2);
    msgPanel.setLayout(gridBagLayout2);
    msgPane.setBackground(SystemColor.window);
    msgPane.setBorder(border2);
    understandButton.setText("I Understand");
    understandButton.addActionListener(new ActionListener() {
      public void actionPerformed(ActionEvent actionEvent) {
        yesButton_actionPerformed(actionEvent);
      }
    });

    quitButton.addActionListener(new ActionListener() {
      public void actionPerformed(ActionEvent actionEvent) {
        noButton_actionPerformed(actionEvent);
      }
    });
    quitButton.setText("Quit");
    
    disclaimerPane.getViewport().add(updateVersionInfo);

    msgPanel.add(disclaimerPane, new GridBagConstraints(0, 0, 2, 1, 1.0, 1.0
        , GridBagConstraints.CENTER, GridBagConstraints.BOTH,
        new Insets(4, 4, 0, 4), 0, 0));
    msgPanel.add(understandButton, new GridBagConstraints(0, 1, 1, 1, 0.0, 0.0
        , GridBagConstraints.CENTER, GridBagConstraints.NONE,
        new Insets(0, 15, 7, 0), 0, 0));
    msgPanel.add(quitButton, new GridBagConstraints(1, 1, 1, 1, 0.0, 0.0
        , GridBagConstraints.CENTER, GridBagConstraints.NONE,
        new Insets(0, 0, 7, 47), 0, 0));
    this.getContentPane().add(msgPanel, java.awt.BorderLayout.CENTER);

    updateVersionInfo.setContentType("text/html");
    updateVersionInfo.setPage(urlToDisclaimerMsgPage);
    
    
    Dimension d = Toolkit.getDefaultToolkit().getScreenSize();
    setLocation( ( d.width - getSize().width ) / 2, ( d.height - getSize().height ) / 2 );
    //this.pack();
  }


  public void noButton_actionPerformed(ActionEvent actionEvent) {
    System.exit(0);
  }

  public void yesButton_actionPerformed(ActionEvent actionEvent) {
	  this.dispose();
  }
}
