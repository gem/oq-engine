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

package org.opensha.sha.cybershake.gui;

import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;

import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JComboBox;
import javax.swing.JComponent;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JTextField;

import org.opensha.sha.cybershake.db.CybershakeSite;
import org.opensha.sha.cybershake.db.CybershakeSiteInfo2DB;
import org.opensha.sha.cybershake.db.CybershakeSiteManager;
import org.opensha.sha.cybershake.db.CybershakeSiteType;
import org.opensha.sha.cybershake.db.DBAccess;
import org.opensha.sha.cybershake.db.ERF2DB;
import org.opensha.sha.cybershake.db.MeanUCERF2_ToDB;
import org.opensha.sha.cybershake.db.SiteInfo2DB;
import org.opensha.sha.earthquake.EqkRupForecast;

public class SingleSiteAddEditGUI extends JFrame implements ActionListener {
	
	DBAccess db;
	
	SiteInfo2DB site2db;
	ERF2DB erf2db;
	
	SitesTableModel model;
	
	ArrayList<CybershakeSiteType> types;
	
	JTextField shortNameField = new JTextField();
	JTextField longNameField = new JTextField();
	JTextField latField = new JTextField();
	JTextField lonField = new JTextField();
	JTextField cutoffField = new JTextField(CybershakeSiteInfo2DB.CUT_OFF_DISTANCE + "");
	
	JComboBox typeBox = new JComboBox();
	
	JButton addEditButton;
	
	JPanel mainPanel = new JPanel();
	
	boolean edit;
	
	CybershakeSite origSite;
	
	public SingleSiteAddEditGUI(DBAccess db, SitesTableModel model, CybershakeSite site) {
		super("Add a CyberShake Site");
		
		this.db = db;
		site2db = new SiteInfo2DB(db);
		erf2db = new ERF2DB(db);
		
		this.origSite = site;
		
		this.model = model;
		
		types = site2db.getSiteTypes();
		
		for (CybershakeSiteType type : types) {
			typeBox.addItem(type.getName());
		}
		
		if (site == null) {
			edit = false;
			addEditButton = new JButton("Add Site!");
		} else {
			edit = true;
			addEditButton = new JButton("Edit Site!");
			shortNameField.setText(site.short_name);
			shortNameField.setEditable(false);
			longNameField.setText(site.name);
			latField.setText(site.lat + "");
			latField.setEditable(false);
			lonField.setText(site.lon + "");
			lonField.setEditable(false);
			cutoffField.setText(site2db.getSiteCutoffDistance(site.id) + "");
			cutoffField.setEditable(false);
			
			if (site.type_id >= 0) {
				for (int i=0; i<types.size(); i++) {
					CybershakeSiteType type = types.get(i);
					if (site.type_id == type.getID()) {
						typeBox.setSelectedIndex(i);
						break;
					}
				}
			}
		}
		
		addEditButton.addActionListener(this);
		
		mainPanel.setLayout(new BoxLayout(mainPanel, BoxLayout.Y_AXIS));
		
		mainPanel.add(createLabelPanel("Short Name: ", shortNameField));
		mainPanel.add(createLabelPanel("Long Name: ", longNameField));
		mainPanel.add(createLabelPanel("Latitude: ", latField));
		mainPanel.add(createLabelPanel("Longitude: ", lonField));
		mainPanel.add(createLabelPanel("Cutoff Distance (km): ", cutoffField));
		mainPanel.add(createLabelPanel("Type: ", typeBox));
		
		mainPanel.add(addEditButton);
		
		this.setContentPane(mainPanel);
		
		this.setSize(300, 600);
		
		this.setLocationRelativeTo(null);
	}
	
	public static EqkRupForecast loadERF() {
		return MeanUCERF2_ToDB.createUCERF2ERF();
	}
	
	private JPanel createLabelPanel(String label, JComponent comp) {
		JPanel panel = new JPanel();
		
		panel.setLayout(new BoxLayout(panel, BoxLayout.X_AXIS));
		
		panel.add(new JLabel(label));
		panel.add(comp);
		
		return panel;
	}
	
	private void showAddError(String message) {
		JOptionPane.showMessageDialog(this, message, "Site Cannot Be Added", JOptionPane.ERROR_MESSAGE);
	}
	
	private String getLongName() {
		String longName = longNameField.getText().trim();
		
		if (!isLongNameValid(longName)) {
			showAddError("Long name must be at least 2 characters");
			return null;
		}
		return longName;
	}
	
	public static boolean isShortNameValid(String shortName) {
		if (shortName.contains(" ") || shortName.length() < 2 || shortName.length() > SitesGUI.MAX_SHORT_NAME_CHARS)
			return false;
		return true;
	}
	
	public static boolean isLongNameValid(String longName) {
		if (longName.length() < 2)
			return false;
		return true;
	}
	
	public static boolean isLatValid(double lat) {
		if (lat < -90 || lat > 90)
			return false;
		return true;
	}
	
	public static boolean isLonValid(double lon) {
		if (lon < -180 || lon > 180)
			return false;
		return true;
	}
	
	public static boolean isCutoffValid(double cutoff) {
		if (cutoff <= 0)
			return false;
		return true;
	}
	
	private void insertSite() {
		String shortName = shortNameField.getText().trim();
		
		if (!isShortNameValid(shortName)) {
			showAddError("Short name must be between 2 and " + SitesGUI.MAX_SHORT_NAME_CHARS
					+ " characters\nand cannot contain spaces.");
			return;
		}
		
		String longName = getLongName();
		if (longName == null)
			return;
		
		double lat;
		try {
			lat = Double.parseDouble(latField.getText().trim());
			
			if (!isLonValid(lat)) {
				showAddError(latField.getText().trim() + " must be between -90 and 90");
				return;
			}
		} catch (NumberFormatException e1) {
			showAddError(latField.getText().trim() + " is not a valid number!");
			return;
		}
		
		double lon;
		try {
			lon = Double.parseDouble(lonField.getText().trim());
			
			if (!isLonValid(lon)) {
				showAddError(lonField.getText().trim() + " must be between -180 and 180");
				return;
			}
		} catch (NumberFormatException e1) {
			showAddError(lonField.getText().trim() + " is not a valid number!");
			return;
		}
		
		double cutoff;
		try {
			cutoff = Double.parseDouble(cutoffField.getText().trim());
			
			if (!isCutoffValid(cutoff)) {
				showAddError(cutoffField.getText().trim() + " must be greater than 0");
				return;
			}
		} catch (NumberFormatException e1) {
			showAddError(cutoffField.getText().trim() + " is not a valid number!");
			return;
		}
		
		CybershakeSiteType type = types.get(typeBox.getSelectedIndex());
		
		CybershakeSite site = new CybershakeSite(-1, lat, lon, longName, shortName, type.getID());
		
		System.out.println("Site to be added: " + site);
		
		EqkRupForecast erf = loadERF();
		
		int erfID = erf2db.getInserted_ERF_ID(erf.getName());
		
		System.out.println("Inserting for ERF ID: " + erfID);
		
		String title = "Confirm Inserting CyberShake Site";
		String message = "Please review the following details before inserting the site:\n\n" +
				" * Short Name: " + site.short_name + "\n" +
				" * Long Name: " + site.name + " \n" +
				" * Latitude: " + site.lat + " \n" +
				" * Longitude: " + site.lon + " \n" +
				" * Cutoff Distance: " + cutoff + " \n" +
				" * Site Type: " + type.getName() + " (ID=" + type.getID() + ")" + " \n" +
				" * ERF ID: " + erfID + " \n" +
				" * ERF Name: " + erf.getName() + " \n\n" +
				"If everything looks correct, hit 'YES' to add site, or 'NO' to cancel";
		int response = JOptionPane.showConfirmDialog(null, message, title, JOptionPane.YES_NO_OPTION);
		if (response == JOptionPane.YES_OPTION) {
			boolean success = CybershakeSiteManager.insertCybershakeSite(db, site, erf, erfID, cutoff, type.getID());
			if (success) {
				this.setVisible(false);
			}
			model.reloadSites();
		}
	}
	
	private void editSite() {
		String longName = getLongName();
		if (longName == null)
			return;
		
		if (!longName.equals(origSite.name)) {
			// we need to update the name
			site2db.setSiteLongName(origSite.id, longName);
		}
		
		CybershakeSiteType type = types.get(typeBox.getSelectedIndex());
		if (type.getID() != origSite.type_id) {
			// we need to update the site type
			site2db.setSiteType(origSite.id, type.getID());
		}
		this.setVisible(false);
		model.reloadSites();
	}

	public void actionPerformed(ActionEvent e) {
		if (e.getSource() == addEditButton) {
			if (edit) {
				editSite();
			} else {
				insertSite();
			}
			
		}
	}

}
