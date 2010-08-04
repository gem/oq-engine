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
import java.awt.Component;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.SystemColor;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

import javax.swing.BorderFactory;
import javax.swing.ImageIcon;
import javax.swing.JButton;
import javax.swing.JDialog;
import javax.swing.JEditorPane;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.border.BevelBorder;
import javax.swing.border.Border;
import javax.swing.border.EtchedBorder;
import javax.swing.border.TitledBorder;

import org.opensha.commons.util.FileUtils;

/**
 * <p>Title: ApplicationVersionInfoWindow</p>
 *
 * <p>Description: This class display link to the new version of the application,
 * if the version of application that user is running out of date.
 * </p>
 * @author Ned Field, Nitin Gupta
 * @version 1.0
 */
public class ApplicationVersionInfoWindow
    extends JDialog {

  private final static String message = "A new version of this application is available.  "+
      "Would you like to quit and download the new version?  If so, please be sure to delete your older version.";
  JPanel msgPanel = new JPanel();
  JLabel imgLabel ;
  JTextArea msgPane = new JTextArea();
  Border border1 = BorderFactory.createMatteBorder(6, 6, 6, 6, Color.white);
  Border border2 = BorderFactory.createBevelBorder(BevelBorder.RAISED,
      Color.white, Color.white, new Color(124, 124, 124),
      new Color(178, 178, 178));
  JScrollPane versionUpdateText = new JScrollPane();
  TitledBorder titledBorder1 = new TitledBorder("");
  Border border3 = BorderFactory.createLineBorder(Color.lightGray, 2);
  Border border4 = BorderFactory.createEtchedBorder(EtchedBorder.RAISED,
      Color.white, new Color(178, 178, 178));
  Border border5 = BorderFactory.createEtchedBorder(EtchedBorder.RAISED,
      Color.white, new Color(178, 178, 178));
  JEditorPane updateVersionInfo = new JEditorPane();
  JButton yesButton = new JButton();
  JButton noButton = new JButton();
  BorderLayout borderLayout1 = new BorderLayout();
  GridBagLayout gridBagLayout1 = new GridBagLayout();
  GridBagLayout gridBagLayout2 = new GridBagLayout();
  BorderLayout borderLayout2 = new BorderLayout();
  private String title = "Application version";
  //URL string to the application
  private String urlToApp;
  //URL to the page that has info for the version update of the application
  private String urlToVersionUpdatePage;

  /**
   *
   * @param appURL String : String URL to the application
   * @param updatePageURL String URL to the page that has info for the version update of the application
   * @param title String Message Title
   * @param parent Component Application from which this window is launched
   */
  public ApplicationVersionInfoWindow(String appURL, String updatePageURL,String title,Component parent) {
    urlToApp = appURL;
    urlToVersionUpdatePage = updatePageURL;

    try {
      jbInit();
      setDefaultCloseOperation(DISPOSE_ON_CLOSE);
    }
    catch (Exception exception) {
      exception.printStackTrace();
    }
    this.title = title;
    this.setTitle(title);
    // show the window at center of the parent component
    setLocation(parent.getX() + parent.getWidth() / 2,
                     parent.getY() + parent.getHeight() / 2);
  }


  private void jbInit() throws Exception {
    this.setModal(true);
    this.getContentPane().setLayout(borderLayout2);
    msgPanel.setLayout(gridBagLayout2);
    msgPane.setBackground(SystemColor.window);
    imgLabel = new JLabel(new ImageIcon(FileUtils.loadImage("icons/info_icon.jpg")));
    msgPane.setBorder(border2);
    versionUpdateText.getViewport().setBackground(SystemColor.desktop);
    versionUpdateText.setBorder(border5);
    yesButton.setText("Yes");
    yesButton.addActionListener(new ActionListener() {
      public void actionPerformed(ActionEvent actionEvent) {
        yesButton_actionPerformed(actionEvent);
      }
    });

    noButton.addActionListener(new ActionListener() {
      public void actionPerformed(ActionEvent actionEvent) {
        noButton_actionPerformed(actionEvent);
      }
    });

    noButton.setText("No");
    versionUpdateText.getViewport().add(updateVersionInfo);
    msgPanel.add(imgLabel, new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
                                                  , GridBagConstraints.WEST,
                                                  GridBagConstraints.NONE,
                                                  new Insets(2, 2, 2, 2), 0,
                                                  0));
    msgPanel.add(msgPane, new GridBagConstraints(1, 0, 2, 1, 1.0, 1.0
                                                 , GridBagConstraints.CENTER,
                                                 GridBagConstraints.BOTH,
                                                 new Insets(4, 4,4, 4), 0, 0));
    msgPanel.add(noButton, new GridBagConstraints(2, 2, 1, 1, 0.0, 0.0
        , GridBagConstraints.CENTER, GridBagConstraints.NONE,
        new Insets(0, 6, 12, 38), 26, 0));
    msgPanel.add(yesButton, new GridBagConstraints(1, 2, 1, 1, 0.0, 0.0
        , GridBagConstraints.CENTER, GridBagConstraints.NONE,
        new Insets(0, 91, 12, 0), 26, 0));
    msgPanel.add(versionUpdateText, new GridBagConstraints(0, 1, 3, 1, 1.0, 1.0
        , GridBagConstraints.CENTER, GridBagConstraints.BOTH,
        new Insets(8, 6, 0, 3), 0, 260));
    this.getContentPane().add(msgPanel, java.awt.BorderLayout.CENTER);
    msgPane.setText(this.message);
    msgPane.setLineWrap(true);
    msgPane.setWrapStyleWord(true);
    updateVersionInfo.setContentType("text/html");
    updateVersionInfo.setPage(urlToVersionUpdatePage);
    this.setSize(450,500);
    //this.pack();
  }


  public void noButton_actionPerformed(ActionEvent actionEvent) {
    this.dispose();
  }

  public void yesButton_actionPerformed(ActionEvent actionEvent) {
    try {
    	edu.stanford.ejalbert.BrowserLauncher.openURL(urlToApp);
    }
    catch (Exception ex) {
      ex.printStackTrace();
    }
    System.exit(0);

  }
}
