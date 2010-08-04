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

package org.opensha.sha.calc.IM_EventSet.v03.gui;

import java.awt.BorderLayout;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.File;
import java.io.IOException;
import java.text.ParseException;
import java.util.ArrayList;

import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JComboBox;
import javax.swing.JFileChooser;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JSeparator;
import javax.swing.JTextField;

import org.opensha.commons.data.siteData.SiteDataAPI;
import org.opensha.commons.data.siteData.SiteDataValue;
import org.opensha.commons.geo.Location;
import org.opensha.sha.calc.IM_EventSet.v03.SiteFileLoader;

public class SiteImporterPanel extends JPanel implements ActionListener {
	
	private JLabel formatLabel = new JLabel();
	private JButton reverseButton = new JButton("Swap lat/lon");
	private JButton addButton = new JButton("Add Site Data Column");
	private JButton removeButton = new JButton("Remove Site Data Column");
	private JComboBox typeChooser; 
	
	private JComboBox measChooser;
	private JLabel measLabel = new JLabel("Site Data Measurement Type: ");
	
	private JTextField fileField = new JTextField();
	private JButton browseButton = new JButton("Browse");
	private JFileChooser chooser;
	
	private boolean lonFirst = false;
	
	private ArrayList<String> siteDataTypes = new ArrayList<String>();
	
	private ArrayList<Location> locs;
	private ArrayList<ArrayList<SiteDataValue<?>>> valsList;
	
	public SiteImporterPanel() {
		this.setLayout(new BoxLayout(this, BoxLayout.Y_AXIS));
		
		typeChooser = new JComboBox(AddSiteDataPanel.siteDataTypes.toArray());
		
		updateLabel();
		
		reverseButton.addActionListener(this);
		addButton.addActionListener(this);
		removeButton.addActionListener(this);
		removeButton.setEnabled(false);
		
		JPanel buttonPanel = new JPanel(new BorderLayout());
		buttonPanel.add(reverseButton, BorderLayout.WEST);
		JPanel rightButtonPanel = new JPanel();
		rightButtonPanel.setLayout(new BoxLayout(rightButtonPanel, BoxLayout.X_AXIS));
		rightButtonPanel.add(typeChooser);
		rightButtonPanel.add(addButton);
		rightButtonPanel.add(removeButton);
		buttonPanel.add(rightButtonPanel, BorderLayout.EAST);
		
		String measTypes[] = new String[2];
		measTypes[0] = SiteDataAPI.TYPE_FLAG_INFERRED;
		measTypes[1] = SiteDataAPI.TYPE_FLAG_MEASURED;
		measChooser = new JComboBox(measTypes);
		JPanel measPanel = new JPanel();
		measPanel.setLayout(new BoxLayout(measPanel, BoxLayout.X_AXIS));
		measLabel.setEnabled(false);
		measChooser.setEnabled(false);
		measPanel.add(measLabel);
		measPanel.add(measChooser);
		JPanel newMeasPanel = new JPanel();
		newMeasPanel.add(measPanel);
		
		JPanel labelPanel = new JPanel();
		labelPanel.setLayout(new BoxLayout(labelPanel, BoxLayout.X_AXIS));
		labelPanel.add(formatLabel);
		this.add(labelPanel);
		JPanel newButtonPanel = new JPanel();
		newButtonPanel.add(buttonPanel);
		this.add(newButtonPanel);
		this.add(newMeasPanel);
		this.add(new JSeparator(JSeparator.HORIZONTAL));
		
		JPanel browsePanel = new JPanel(new BorderLayout());
		browsePanel.add(fileField, BorderLayout.CENTER);
		browsePanel.add(browseButton, BorderLayout.EAST);
		fileField.setColumns(40);
		browseButton.addActionListener(this);
		JPanel newBrowsePanel = new JPanel();
		newBrowsePanel.add(browsePanel);
		
		this.add(newBrowsePanel);
		this.setSize(700, 150);
	}
	
	private void updateLabel() {
		String label = "File format: ";
		if (lonFirst)
			label += "<Latitude> <Longitude>";
		else
			label += "<Longitude> <Latitude>";
		
		for (String dataType : siteDataTypes) {
			label += " <" + dataType + ">";
		}
		formatLabel.setText(label);
	}

	public void actionPerformed(ActionEvent e) {
		if (e.getSource().equals(reverseButton)) {
			lonFirst = !lonFirst;
		} else if (e.getSource().equals(addButton)) {
			int selected = typeChooser.getSelectedIndex();
			siteDataTypes.add((String)typeChooser.getSelectedItem());
			typeChooser.removeItemAt(selected);
		} else if (e.getSource().equals(removeButton)) {
			int index = siteDataTypes.size() - 1;
			typeChooser.addItem(siteDataTypes.get(index));
			siteDataTypes.remove(index);
		} else if (e.getSource().equals(browseButton)) {
			if (chooser == null)
				chooser = new JFileChooser();
			int returnVal = chooser.showOpenDialog(this);
			if (returnVal == JFileChooser.APPROVE_OPTION) {
				File file = chooser.getSelectedFile();
				fileField.setText(file.getAbsolutePath());
			}
		}
		addButton.setEnabled(typeChooser.getItemCount() > 0);
		boolean hasTypes = siteDataTypes.size() > 0;
		measLabel.setEnabled(hasTypes);
		measChooser.setEnabled(hasTypes);
		removeButton.setEnabled(hasTypes);
		updateLabel();
	}
	
	public File getSelectedFile() {
		String fileName = fileField.getText();
		File file = new File(fileName);
		return file;
	}
	
	public void importFile(File file) throws IOException, ParseException {
		SiteFileLoader loader = new SiteFileLoader(lonFirst, (String)measChooser.getSelectedItem(), siteDataTypes);
		
		loader.loadFile(file);
		
		locs = loader.getLocs();
		valsList = loader.getValsList();
	}
	
	public ArrayList<Location> getLocs() {
		return locs;
	}

	public ArrayList<ArrayList<SiteDataValue<?>>> getValsList() {
		return valsList;
	}
	
	public static void main(String args[]) {
		JFrame frame = new JFrame();
		frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		frame.setContentPane(new SiteImporterPanel());
		frame.setSize(700, 150);
		
		frame.setVisible(true);
	}

}
