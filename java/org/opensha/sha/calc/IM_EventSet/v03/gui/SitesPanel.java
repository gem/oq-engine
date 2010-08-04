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
import java.awt.Dimension;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.File;
import java.io.IOException;
import java.text.ParseException;
import java.util.ArrayList;
import java.util.Arrays;

import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JList;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.ListSelectionModel;
import javax.swing.event.ListSelectionEvent;
import javax.swing.event.ListSelectionListener;

import org.opensha.commons.data.siteData.SiteDataAPI;
import org.opensha.commons.data.siteData.SiteDataValue;
import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.geo.Location;

public class SitesPanel extends JPanel implements ListSelectionListener, ActionListener {
	
	protected JList sitesList;
	protected JList siteDataList;
	
	protected JButton addSiteButton = new JButton("Add Site");
	protected JButton removeSiteButton = new JButton("Remove Site(s)");
	protected JButton importSitesButton = new JButton("Import Sites From File");
	
	protected JButton addDataButton = new JButton("Add Site Data Value");
	protected JButton removeDataButton = new JButton("Remove Site Data Value(s)");
	
	private ArrayList<Location> locs;
	private ArrayList<ArrayList<SiteDataValue<?>>> dataLists;
	
	private SiteImporterPanel imp;
	
	public SitesPanel() {
		super();
		this.setLayout(new BoxLayout(this, BoxLayout.Y_AXIS));
		
		locs = new ArrayList<Location>();
		dataLists = new ArrayList<ArrayList<SiteDataValue<?>>>();

		sitesList = new JList();
		sitesList.setSelectionMode(ListSelectionModel.MULTIPLE_INTERVAL_SELECTION);
		sitesList.setSelectedIndex(0);
		sitesList.addListSelectionListener(this);
		
		JScrollPane listScroller = new JScrollPane(sitesList);
		listScroller.setPreferredSize(new Dimension(250, 650));
		
		JPanel northPanel = new JPanel(new BorderLayout());
		northPanel.add(new JLabel("Sites"), BorderLayout.NORTH);
		northPanel.add(listScroller, BorderLayout.CENTER);
		
		JPanel buttonPanel = new JPanel(new BorderLayout());
		JPanel leftButtonPanel = new JPanel();
		leftButtonPanel.setLayout(new BoxLayout(leftButtonPanel, BoxLayout.X_AXIS));
		leftButtonPanel.add(addSiteButton);
		leftButtonPanel.add(removeSiteButton);
		buttonPanel.add(leftButtonPanel, BorderLayout.WEST);
		buttonPanel.add(importSitesButton, BorderLayout.EAST);
		removeSiteButton.setEnabled(false);
		addSiteButton.addActionListener(this);
		removeSiteButton.addActionListener(this);
		importSitesButton.addActionListener(this);
		
		northPanel.add(buttonPanel, BorderLayout.SOUTH);
		
		siteDataList = new JList();
		siteDataList.setSelectionMode(ListSelectionModel.MULTIPLE_INTERVAL_SELECTION);
		siteDataList.setSelectedIndex(0);
		siteDataList.addListSelectionListener(this);
		
		JScrollPane dataListScroller = new JScrollPane(siteDataList);
		dataListScroller.setPreferredSize(new Dimension(250, 150));
		
		JPanel southPanel = new JPanel(new BorderLayout());
		southPanel.add(new JLabel("Site Data Values"), BorderLayout.NORTH);
		southPanel.add(dataListScroller, BorderLayout.CENTER);
		
		JPanel dataButtonPanel = new JPanel();
		dataButtonPanel.setLayout(new BoxLayout(dataButtonPanel, BoxLayout.X_AXIS));
		dataButtonPanel.add(addDataButton);
		dataButtonPanel.add(removeDataButton);
		removeDataButton.setEnabled(false);
		addDataButton.addActionListener(this);
		removeDataButton.addActionListener(this);
		
		southPanel.add(dataButtonPanel, BorderLayout.SOUTH);
		
		rebuildSiteList();
		
		this.add(northPanel);
		this.add(southPanel);
	}

	public void valueChanged(ListSelectionEvent e) {
		if (e.getSource().equals(sitesList)) {
			// value changed in the sites list
			rebuildSiteDataList();
		} else {
			// value changed in the site data list
			checkEnableRemoveSiteData();
		}
	}
	
	private void checkEnableRemoveSite() {
		removeSiteButton.setEnabled(!sitesList.isSelectionEmpty());
	}
	
	private void checkEnableRemoveSiteData() {
		boolean enable = !siteDataList.isSelectionEmpty() && !sitesList.isSelectionEmpty()
							&& getSingleSelectedIndex() >= 0;
		removeDataButton.setEnabled(enable);
	}
	
	protected void addSite(Location loc, ArrayList<SiteDataValue<?>> data) {
		this.locs.add(loc);
		if (data == null) {
			data = new ArrayList<SiteDataValue<?>>();
		}
		this.dataLists.add(data);
		this.rebuildSiteList();
	}
	
	private void addSiteDataValue(int i, SiteDataValue<?> val) {
		this.dataLists.get(i).add(val);
	}
	
	public void clear() {
		locs.clear();
		dataLists.clear();
		this.rebuildSiteList();
	}
	
	private void removeSite(int i) {
		locs.remove(i);
		dataLists.remove(i);
		this.rebuildSiteList();
	}
	
	private void removeSite(int indices[]) {
		Arrays.sort(indices);
		for (int i=indices.length-1; i>=0; i--) {
			locs.remove(i);
			dataLists.remove(i);
		}
		this.rebuildSiteList();
	}
	
	private void removeSiteData(int i, int indices[]) {
		ArrayList<SiteDataValue<?>> dataVals = dataLists.get(i);
		Arrays.sort(indices);
		for (int j=indices.length-1; j>=0; j--) {
			dataVals.remove(j);
		}
		this.rebuildSiteDataList();
	}
	
	private void rebuildSiteList() {
		Object data[] = new String[locs.size()];
		for (int i=0; i<locs.size(); i++) {
			Location loc = locs.get(i);
			data[i] = (i+1) + ". " + loc.getLatitude() + ", " + loc.getLongitude();
		}
//		System.out.println("rebuilding with length " + data.length);
		sitesList.setListData(data);
		checkEnableRemoveSite();
		rebuildSiteDataList();
		this.validate();
	}
	
	private int getSingleSelectedIndex() {
		int[] selection = sitesList.getSelectedIndices();
		if (selection.length > 1)
			return -1;
		return selection[0];
	}
	
	private void rebuildSiteDataList() {
		if (sitesList.isSelectionEmpty()) {
			Object data[] = new String[1];
			data[0] = "(no site(s) selected)";
			siteDataList.setListData(data);
			return;
		}
		int index = getSingleSelectedIndex();
		if (index < 0) {
			Object data[] = new String[1];
			data[0] = "(multiple selected)";
			siteDataList.setListData(data);
			return;
		}
		ArrayList<SiteDataValue<?>> vals = dataLists.get(index);
		Object data[] = new String[vals.size()];
		for (int i=0; i<vals.size(); i++) {
			SiteDataValue<?> val = vals.get(i);
			data[i] = getDataListString(i, val);
		}
		siteDataList.setListData(data);
		checkEnableRemoveSite();
		checkEnableRemoveSiteData();
	}
	
	public static String getDataListString(int index, SiteDataValue<?> val) {
		return (index+1) + ". " + val.getDataType() + ": " + val.getValue();
	}
	
	private void importSites() {
		if (imp == null)
			imp = new SiteImporterPanel();
		
		int selection = JOptionPane.showConfirmDialog(this, imp, "Import Sites",
				JOptionPane.OK_CANCEL_OPTION);
		if (selection == JOptionPane.OK_OPTION) {
			File file = imp.getSelectedFile();
			if (file.exists()) {
				try {
					imp.importFile(file);
					this.locs.addAll(imp.getLocs());
					this.dataLists.addAll(imp.getValsList());
					this.rebuildSiteList();
				} catch (IOException e1) {
					e1.printStackTrace();
					JOptionPane.showMessageDialog(this, "I/O error reading file!",
							"I/O error reading file!", JOptionPane.ERROR_MESSAGE);
				} catch (ParseException e1) {
					e1.printStackTrace();
					JOptionPane.showMessageDialog(this, e1.getMessage(),
							"Error Parsing File", JOptionPane.ERROR_MESSAGE);
				} catch (NumberFormatException e1) {
					e1.printStackTrace();
					JOptionPane.showMessageDialog(this, e1.getMessage(),
							"Error Parsing Number", JOptionPane.ERROR_MESSAGE);
				} catch (InvalidRangeException e1) {
					e1.printStackTrace();
					JOptionPane.showMessageDialog(this, e1.getMessage(),
							"Invalid location", JOptionPane.ERROR_MESSAGE);
				}
			} else {
				JOptionPane.showMessageDialog(this, "File '" + file.getPath() + "' doesn't exist!",
						"File Not Found", JOptionPane.ERROR_MESSAGE);
			}
		}
	}

	public void actionPerformed(ActionEvent e) {
		if (e.getSource().equals(addSiteButton)) {
			// adding a site
			AddSitePanel siteAdd = new AddSitePanel();
			int selection = JOptionPane.showConfirmDialog(this, siteAdd, "Add Site",
					JOptionPane.OK_CANCEL_OPTION);
			if (selection == JOptionPane.OK_OPTION) {
				Location loc = siteAdd.getSiteLocation();
				ArrayList<SiteDataValue<?>> vals = siteAdd.getDataVals();
				System.out.println("Adding site: " + loc + " (" + vals.size() + " vals)");
				this.addSite(loc, vals);
				rebuildSiteDataList();
			}
		} else if (e.getSource().equals(removeSiteButton)) {
			// removing a site
			int indices[] = sitesList.getSelectedIndices();
			removeSite(indices);
		} else if (e.getSource().equals(addDataButton)) {
			// adding a site data val
			AddSiteDataPanel dataAdd = new AddSiteDataPanel();
			int selection = JOptionPane.showConfirmDialog(this, dataAdd, "Add Site Data Value",
					JOptionPane.OK_CANCEL_OPTION);
			if (selection == JOptionPane.OK_OPTION) {
				try {
					SiteDataValue<?> val = dataAdd.getValue();
					int index = getSingleSelectedIndex();
					this.addSiteDataValue(index, val);
					rebuildSiteDataList();
				} catch (Exception e1) {
					JOptionPane.showMessageDialog(this, "Error adding value:\n" + e1.getMessage(),
							"Error!", JOptionPane.ERROR_MESSAGE);
				}
			}
			rebuildSiteDataList();
		} else if (e.getSource().equals(removeDataButton)) {
			// removing a site data val
			int i = getSingleSelectedIndex();
			if (i >= 0)
				removeSiteData(i, siteDataList.getSelectedIndices());
			checkEnableRemoveSiteData();
		} else if (e.getSource().equals(importSitesButton)) {
			importSites();
		}
	}

	
	/**
	 * tester main method
	 * @param args
	 */
	public static void main(String args[]) {
		JFrame frame = new JFrame();
		frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		frame.setSize(400, 600);
		
		SitesPanel sites = new SitesPanel();
		
		sites.addSite(new Location(34, -118), null);
		ArrayList<SiteDataValue<?>> vals = new ArrayList<SiteDataValue<?>>();
		vals.add(new SiteDataValue<Double>(SiteDataAPI.TYPE_VS30, SiteDataAPI.TYPE_FLAG_INFERRED, 760.0));
		sites.addSite(new Location(34, -118.1), vals);
		
		frame.setContentPane(sites);
		frame.setVisible(true);
	}

	public ArrayList<Location> getLocs() {
		return locs;
	}

	public ArrayList<ArrayList<SiteDataValue<?>>> getDataLists() {
		return dataLists;
	}
}
