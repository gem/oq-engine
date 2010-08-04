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
import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.ArrayList;
import java.util.StringTokenizer;

import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JComboBox;
import javax.swing.JFileChooser;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JTextArea;
import javax.swing.JTextField;
import javax.swing.event.DocumentEvent;
import javax.swing.event.DocumentListener;

import org.opensha.commons.util.FileUtils;
import org.opensha.sha.cybershake.db.CybershakeSite;
import org.opensha.sha.cybershake.db.CybershakeSiteManager;
import org.opensha.sha.cybershake.db.CybershakeSiteType;
import org.opensha.sha.cybershake.db.DBAccess;
import org.opensha.sha.cybershake.db.ERF2DB;
import org.opensha.sha.cybershake.db.SiteInfo2DB;
import org.opensha.sha.earthquake.EqkRupForecast;

public class BatchSiteAddGUI extends JFrame implements ActionListener, DocumentListener {
	
	private JButton browseButton = new JButton("Select File");
	private JTextField fileField = new JTextField();
	
	private JComboBox typeBox = new JComboBox();
	private ArrayList<CybershakeSiteType> types;
	private JLabel typeLabel = new JLabel("Default Site Type: ");
	
	private SitesTableModel model;
	private DBAccess db;
	
	private SiteInfo2DB site2db;
	private ERF2DB erf2db;
	
	private JTextArea label = new JTextArea();
	
	private JPanel mainPanel = new JPanel();
	
	private JButton addButton = new JButton("Add Site(s)");
	
	private JFileChooser chooser = null;
	
	public BatchSiteAddGUI(DBAccess db, SitesTableModel model) {
		super("Add CyberShake Sites from File");
		
		this.model = model;
		this.db = db;
		
		site2db = new SiteInfo2DB(db);
		erf2db = new ERF2DB(db);
		
		mainPanel.setLayout(new BoxLayout(mainPanel, BoxLayout.Y_AXIS));
		
		setLabelText();
		mainPanel.add(label);
		
		JPanel browsePanel = new JPanel();
		browsePanel.setLayout(new BoxLayout(browsePanel, BoxLayout.X_AXIS));
		browsePanel.add(fileField);
		fileField.getDocument().addDocumentListener(this);
		fileField.addActionListener(this);
		browseButton.addActionListener(this);
		browsePanel.add(browseButton);
		mainPanel.add(browsePanel);
		
		types = site2db.getSiteTypes();
		for (CybershakeSiteType type : types) {
			typeBox.addItem(type.getName());
		}
		JPanel typePanel = new JPanel();
		typePanel.setLayout(new BoxLayout(typePanel, BoxLayout.X_AXIS));
		typePanel.add(typeLabel);
		typePanel.add(typeBox);
		mainPanel.add(typePanel);
		
		addButton.addActionListener(this);
		addButton.setEnabled(false);
		mainPanel.add(addButton);
		
		this.setContentPane(mainPanel);
		
		this.setSize(500, 300);
		
		this.setLocationRelativeTo(null);
	}
	
	private void setLabelText() {
		String text = "Each line of the file must be in the following format:" +
				"\nSHORT_NAME \"LONG_NAME\" LAT LON CUTOFF_DISTANCE [SITE_TYPE_ID]" +
				"\nFor Example:" +
				"\nSITE \"My Test Site\" 34 -118 200" +
				"\nSITE2 \"My Other Test Site\" 34 -118 200 4" +
				"\n\nEmpty lines, or lines beginning with '#' will be ignored";
		
		label.setEditable(false);
		
		this.label.setText(text);
	}
	
	private static CybershakeCutoffSite getSiteForLine(String line, int defaultType) {
		// first we need to grab the description, then we can use a tokenizer
		int firstQuote = line.indexOf("\"");
		String quoteSub = line.substring(firstQuote + 1);
		int lastQuote = quoteSub.indexOf("\"");
		String longName = quoteSub.substring(0, lastQuote);
		if (!SingleSiteAddEditGUI.isLongNameValid(longName))
			return null;
		
		// now remove the name from the line
		line = line.replaceAll("\"" + longName + "\"", "");
//		System.out.println("new line: " + line);
		
		StringTokenizer tok = new StringTokenizer(line);
		
		if (tok.countTokens() < 4)
			return null;
		
		String shortName = tok.nextToken();
		if (!SingleSiteAddEditGUI.isShortNameValid(shortName))
			return null;
		
		try {
			Double lat = Double.parseDouble(tok.nextToken());
			if (!SingleSiteAddEditGUI.isLatValid(lat))
				return null;
			
			Double lon = Double.parseDouble(tok.nextToken());
			if (!SingleSiteAddEditGUI.isLonValid(lon))
				return null;
			
			Double cutoff = Double.parseDouble(tok.nextToken());
			if (!SingleSiteAddEditGUI.isCutoffValid(cutoff))
				return null;
			
			int typeID = defaultType;
			
			if (tok.hasMoreTokens()) {
				typeID = Integer.parseInt(tok.nextToken());
			}
			
			CybershakeCutoffSite site = new CybershakeCutoffSite(-1, lat, lon, longName, shortName, typeID, cutoff);
			
//			System.out.println("Loaded site: " + site);
			
			return site;
		} catch (NumberFormatException e) {
			e.printStackTrace();
			return null;
		}
	}
	
	public static class CybershakeCutoffSite extends CybershakeSite {

		public double cutoff;
		public CybershakeCutoffSite(int id, double lat, double lon,
				String name, String short_name, int type_id, double cutoff) {
			super(id, lat, lon, name, short_name, type_id);
			this.cutoff = cutoff;
		}
		
	}
	
	private ArrayList<CybershakeCutoffSite> getSitesForLines(ArrayList<String> lines, int defaultType) {
		ArrayList<CybershakeCutoffSite> sites = new ArrayList<CybershakeCutoffSite>();
		for (String line : lines) {
			line = line.trim();
			if (line.startsWith("#") || line.length() == 0)
				continue;
			CybershakeCutoffSite site = getSiteForLine(line, defaultType);
			System.out.println("Loaded site: " + site);
			sites.add(site);
		}
		return sites;
	}

	public void actionPerformed(ActionEvent e) {
		if (e.getSource() == addButton) {
			String fileName = fileField.getText();
			File file = new File(fileName);
			if (!file.exists()) {
				System.err.print("File: " + fileName + " doesn't exist!");
				return;
			}
			ArrayList<String> lines = null;
			try {
				lines = FileUtils.loadFile(fileName);
			} catch (FileNotFoundException e1) {
				e1.printStackTrace();
				return;
			} catch (IOException e1) {
				e1.printStackTrace();
				return;
			}
			int defaultType = types.get(typeBox.getSelectedIndex()).getID();
			ArrayList<CybershakeCutoffSite> sites = getSitesForLines(lines, defaultType);
			
			EqkRupForecast erf = SingleSiteAddEditGUI.loadERF();
			
			int erfID = erf2db.getInserted_ERF_ID(erf.getName());
			
			System.out.println("Inserting for ERF ID: " + erfID);
			
			String title = "Confirm Inserting CyberShake Sites";
			String message = "Please review the following details before inserting the site(s):\n\n" +
					" * Number of Sites: " + sites.size() + "\n" +
					" * Default Site Type: " + defaultType + " \n\n" +
					" * ERF ID: " + erfID + " \n" +
					" * ERF Name: " + erf.getName() + " \n\n" +
					"If everything looks correct, hit 'YES' to add site, or 'NO' to cancel";
			int response = JOptionPane.showConfirmDialog(null, message, title, JOptionPane.YES_NO_OPTION);
			if (response == JOptionPane.YES_OPTION) {
				for (CybershakeCutoffSite site : sites) {
					System.out.println("Site: " + site);
					boolean success = CybershakeSiteManager.insertCybershakeSite(db, site, erf, erfID, site.cutoff, site.type_id);
					if (success) {
						model.reloadSites();
					}
				}
			}
			System.out.println("DONE");
		} else if (e.getSource() == browseButton) {
			if (chooser == null) {
				chooser = new JFileChooser();
			}
			
			int retval = chooser.showOpenDialog(this);
			
			if (retval == JFileChooser.APPROVE_OPTION) {
				fileField.setText(chooser.getSelectedFile().getAbsolutePath());
				addButton.setEnabled(fileField.getText().length() > 0);
			}
		}
	}

	public void changedUpdate(DocumentEvent e) {
		addButton.setEnabled(fileField.getText().length() > 0);
	}

	public void insertUpdate(DocumentEvent e) {
		addButton.setEnabled(fileField.getText().length() > 0);
	}

	public void removeUpdate(DocumentEvent e) {
		addButton.setEnabled(fileField.getText().length() > 0);
	}
	
	public static void main(String args[]) {
		System.out.println(BatchSiteAddGUI.getSiteForLine("SITE \"My Test Site\" 34 -118 200 3", 1));
	}

}
