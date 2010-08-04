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

package org.opensha.nshmp.sha.gui.infoTools;

import java.awt.BorderLayout;
import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.Toolkit;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.GregorianCalendar;

import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JTextField;
import javax.swing.UIManager;

/**
 * <p>Title: AddProjectNameDateWindow</p>
 *
 * <p>Description: This class allows the user to add the project name and date
 * to added to the metadata being shown to the user.</p>
 *
 * @author Ned Field, Nitin Gupta and E.V. Leyendecker
 * @version 1.0
 */
public class AddProjectNameDateWindow
    extends JFrame {

  JPanel panel = new JPanel();
  JLabel nameLabel = new JLabel();
  JTextField dataName = new JTextField();
  JCheckBox dateCheckBox = new JCheckBox();
  BorderLayout borderLayout1 = new BorderLayout();
  GridBagLayout gridBagLayout1 = new GridBagLayout();
  JButton okButton = new JButton();

  public AddProjectNameDateWindow() {
    try {
      jbInit();
    }
    catch (Exception exception) {
      exception.printStackTrace();
    }
  }

  static {
    try {
	   //UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
		 UIManager.setLookAndFeel("apple.laf/AquaLookAndFeel");
	 } catch (Exception e) {	
	 }
  }
	 	
  private void jbInit() throws Exception {
    getContentPane().setLayout(borderLayout1);
    panel.setLayout(gridBagLayout1);
    dateCheckBox.setText("Add Date");
	 okButton.setText("Okay");
	 okButton.addActionListener(new ActionListener() {
	 	public void  actionPerformed(ActionEvent e) {
			okButton_actionPerformed(e);
		}
	 });

    panel.add(dataName, new GridBagConstraints(1, 0, 1, 1, 1.0, 0.0
                                               , GridBagConstraints.WEST,
                                               GridBagConstraints.HORIZONTAL,
                                               new Insets(35, 6, 0, 33), 196, 3));
    panel.add(nameLabel, new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
                                                , GridBagConstraints.WEST,
                                                GridBagConstraints.NONE,
                                                new Insets(35, 23, 0, 0), 16, 8));
    panel.add(dateCheckBox, new GridBagConstraints(0, 1, 2, 1, 0.0, 0.0
        , GridBagConstraints.CENTER,
        GridBagConstraints.NONE,
        new Insets(21, 23, 17, 158),
        57, 5));

	 panel.add(okButton, new GridBagConstraints(0, 1, 2, 1, 0.0, 0.0,
	 	GridBagConstraints.CENTER, GridBagConstraints.NONE,
		new Insets(21, 200, 17, 23), 0, 0));

    getContentPane().add(panel, java.awt.BorderLayout.CENTER);
    nameLabel.setText("Name:");

    this.setName("Add Name and Date to calculated data");
    Dimension d = Toolkit.getDefaultToolkit().getScreenSize();
    setSize(300,120);

	 this.getRootPane().setDefaultButton(okButton);

    this.setLocation( (d.width - this.getSize().width) / 2,
                     (d.height - this.getSize().height) / 3);
  }


  private void okButton_actionPerformed(ActionEvent e) {
  	this.setVisible(false);
  }

  public String getProjectName(){
    return dataName.getText();
  }


  public String getDate(){
    if(dateCheckBox.isSelected()){
      GregorianCalendar calender = new GregorianCalendar();
      return calender.getTime().toString();
    }
    return null;
  }

}
