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
import java.awt.event.ActionListener;

import javax.swing.ImageIcon;
import javax.swing.JButton;
import javax.swing.JDialog;
import javax.swing.JEditorPane;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.UIManager;
import javax.swing.event.HyperlinkEvent;
import javax.swing.event.HyperlinkListener;

import org.opensha.commons.util.FileUtils;

/**
 * <p>Title: MessageDialog</p>
 *
 * <p>Description: This class is used to display messages to users.</p>
 * @author Ned Field, Nitin Gupta
 * @version 1.0
 */
public class MessageDialog
    extends JDialog implements HyperlinkListener{



  JPanel panel1 = new JPanel();
  private JLabel imgLabel = new JLabel(new ImageIcon(FileUtils.loadImage("icons/error_icon.png")));
  JButton okButton = new JButton();
  JButton cancelButton = new JButton();
  JEditorPane messageEditor = new JEditorPane();
  GridBagLayout gridBagLayout1 = new GridBagLayout();
  BorderLayout borderLayout1 = new BorderLayout();




  public MessageDialog(String message, String title,Component parent) {
    try {
      jbInit();
      setDefaultCloseOperation(DISPOSE_ON_CLOSE);
    }
    catch (Exception exception) {
      exception.printStackTrace();
    }
    this.setTitle(title);
    messageEditor.setText(message);
    // show the window at center of the parent component
    setLocation(parent.getX() + parent.getWidth() / 2,
                     parent.getY() + parent.getHeight() / 2);
  }



  /** This method implements HyperlinkListener.  It is invoked when the user
   * clicks on a hyperlink, or move the mouse onto or off of a link
   **/
  public void hyperlinkUpdate(HyperlinkEvent e) {
    HyperlinkEvent.EventType type = e.getEventType();  // what happened?
    if (type == HyperlinkEvent.EventType.ACTIVATED) {     // Click!
      try{
    	  edu.stanford.ejalbert.BrowserLauncher.openURL(e.getURL().toString());
      }catch(Exception ex) { ex.printStackTrace(); }

      //displayPage(e.getURL());   // Follow the link; display new page
    }
  }


  private void jbInit() throws Exception {
    this.setModal(true);
    panel1.setLayout(gridBagLayout1);
    this.getContentPane().setLayout(borderLayout1);
    cancelButton.setText("Cancel");
    cancelButton.addActionListener(new ActionListener() {
      public void actionPerformed(ActionEvent actionEvent) {
        cancelButton_actionPerformed(actionEvent);
      }
    });
    messageEditor.setBackground(UIManager.getColor("ProgressBar.background"));
    messageEditor.setContentType("text/html");
    messageEditor.setEditable(false);
    messageEditor.setMinimumSize(new Dimension(0, 0));
    okButton.setText("OK");
    panel1.add(messageEditor, new GridBagConstraints(1, 0, 2, 1, 1.0, 1.0
        , GridBagConstraints.CENTER, GridBagConstraints.BOTH,
        new Insets(4, 20, 4, 4), 0, 0));
    panel1.add(imgLabel, new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
                                                 , GridBagConstraints.WEST,
                                                 GridBagConstraints.NONE,
                                                 new Insets(1, 15, 1, 1), 0,
                                                 0));
    this.getContentPane().add(panel1, java.awt.BorderLayout.CENTER);
    panel1.add(okButton, new GridBagConstraints(1, 1, 1, 1, 1.0, 1.0
                                                , GridBagConstraints.CENTER,
                                                GridBagConstraints.NONE,
                                                new Insets(4, 70, 4, 0), 22,
                                                -3));
    panel1.add(cancelButton, new GridBagConstraints(2, 1, 1, 1, 1.0, 1.0
        , GridBagConstraints.CENTER, GridBagConstraints.NONE,
        new Insets(4, 5, 4, 80), 22, -3));
    okButton.addActionListener(new ActionListener() {
      public void actionPerformed(ActionEvent actionEvent) {
        okButton_actionPerformed(actionEvent);
      }
    });

    cancelButton.addActionListener(new ActionListener() {
      public void actionPerformed(ActionEvent actionEvent) {
        cancelButton_actionPerformed(actionEvent);
      }
    });
    messageEditor.addHyperlinkListener(this);
    this.setSize(360,140);
  }

  public void okButton_actionPerformed(ActionEvent actionEvent) {
    this.dispose();
  }

  public void cancelButton_actionPerformed(ActionEvent actionEvent) {
    this.dispose();
  }
}
