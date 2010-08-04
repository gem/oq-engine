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

package org.opensha.sha.calc.hazardMap.old.applet;

import java.awt.BorderLayout;
import java.awt.Dimension;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.File;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.util.ArrayList;

import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JComponent;
import javax.swing.JFileChooser;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JSeparator;
import javax.swing.JTextField;

import org.dom4j.Document;
import org.opensha.commons.exceptions.RegionConstraintException;
import org.opensha.commons.util.FileUtils;
import org.opensha.commons.util.XMLUtils;

public class SubmitPanel extends JPanel implements ActionListener {
	
	private JLabel nameLabel = new JLabel("Dateset Name (Optional)");
	private JTextField nameField = new JTextField();
	private JLabel emailLabel = new JLabel("Email address(s)");
	private JTextField emailField = new JTextField();
	
	private JButton submitButton = new JButton("Submit Calculation");
	private JButton saveButton = new JButton("Save Calculation Parameters");
	
	private JFileChooser chooser = null;
	
	CreateDataManager manager;
	
	JPanel panel = new JPanel();
	
	public SubmitPanel(CreateDataManager manager) {
		super(new BorderLayout());
		panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
		
		this.manager = manager;
		
		panel.add(leftRightBox(nameLabel, nameField));
		nameField.setColumns(30);
		panel.add(leftRightBox(emailLabel, emailField));
		emailField.setColumns(30);
		
		panel.add(saveButton);
		panel.add(submitButton);
		
		panel.setMaximumSize(new Dimension(300, 200));
		
		JPanel panel2 = new JPanel();
		panel2.add(panel);
		
		submitButton.addActionListener(this);
		saveButton.addActionListener(this);
		
		this.add(panel2, BorderLayout.CENTER);
	}
	
	private JPanel leftRightBox(JComponent left, JComponent right) {
		JPanel panel = new JPanel();
		
		panel.setLayout(new BoxLayout(panel, BoxLayout.X_AXIS));
		
		panel.add(left);
		panel.add(new JSeparator());
		panel.add(right);
		
		JPanel panel2 = new JPanel();
		
		panel2.add(panel);
		
		return panel2;
	}

	public void actionPerformed(ActionEvent e) {
		if (e.getSource() == submitButton) {
			manager.submit(nameField.getText(), emailField.getText());
		} else if (e.getSource() == saveButton) {
			try {
				Document doc = manager.getSubmitDoc(nameField.getText(), emailField.getText());
				
				if (chooser == null) {
					chooser = new JFileChooser();
				}
				
				int retVal = chooser.showSaveDialog(this);
				
				if (retVal == JFileChooser.APPROVE_OPTION) {
					File file = chooser.getSelectedFile();
					
					XMLUtils.writeDocumentToFile(file.getAbsolutePath(), doc);
					
					ArrayList<String> lines = FileUtils.loadFile(file.getAbsolutePath());
					for (String line : lines) {
						System.out.println(line);
					}
				}
			} catch (InvocationTargetException e1) {
				// TODO Auto-generated catch block
				e1.printStackTrace();
			} catch (RuntimeException e1) {
				// TODO Auto-generated catch block
				e1.printStackTrace();
			} catch (RegionConstraintException e1) {
				// TODO Auto-generated catch block
				e1.printStackTrace();
			} catch (IOException e1) {
				// TODO Auto-generated catch block
				e1.printStackTrace();
			}
		}
	}

}
