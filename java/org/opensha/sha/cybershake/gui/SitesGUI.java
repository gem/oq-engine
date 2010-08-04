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

import java.awt.BorderLayout;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;

import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JSeparator;
import javax.swing.JTable;
import javax.swing.ListSelectionModel;
import javax.swing.event.ListSelectionEvent;
import javax.swing.event.ListSelectionListener;

import org.opensha.sha.cybershake.db.CybershakeSite;
import org.opensha.sha.cybershake.db.CybershakeSiteManager;
import org.opensha.sha.cybershake.db.DBAccess;

public class SitesGUI extends JFrame implements ActionListener, ListSelectionListener {
	
	public static final int MAX_SHORT_NAME_CHARS = 5;
	
	DBAccess db;
	
	JPanel mainPanel = new JPanel(new BorderLayout());
	
	JPanel bottomPanel = new JPanel();
	
	JButton editButton = new JButton("Edit Site");
	JButton insertButton = new JButton("Add Site");
	JButton batchAddButton = new JButton("Add Site(s) from File");
	JButton deleteButton = new JButton("Delete Site(s)");
	JButton reloadButton = new JButton("Reload Sites");
	
	SitesTableModel model;
	JTable table;
	
	private boolean readOnly = false;
	
	private SingleSiteAddEditGUI addGUI = null;
	private BatchSiteAddGUI batchAddGUI = null;

	public SitesGUI(DBAccess db) {
		super("CyberShake Sites");
		
		this.db = db;
		this.readOnly = db.isReadOnly();
		
		model = new SitesTableModel(db);
		
		table = new JTable(model);
		
		JScrollPane scrollpane = new JScrollPane(table);
		
		bottomPanel.setLayout(new BoxLayout(bottomPanel, BoxLayout.X_AXIS));
		
		table.getSelectionModel().addListSelectionListener(this);
		
		reloadButton.addActionListener(this);
		
		insertButton.addActionListener(this);
		insertButton.setEnabled(!readOnly);
		
		batchAddButton.addActionListener(this);
		batchAddButton.setEnabled(!readOnly);
		
		editButton.addActionListener(this);
		editButton.setEnabled(false);
		
		deleteButton.addActionListener(this);
		deleteButton.setEnabled(false);
		
		bottomPanel.add(reloadButton);
		bottomPanel.add(new JSeparator());
		bottomPanel.add(insertButton);
		bottomPanel.add(new JSeparator());
		bottomPanel.add(batchAddButton);
		bottomPanel.add(new JSeparator());
		bottomPanel.add(editButton);
		bottomPanel.add(new JSeparator());
		bottomPanel.add(deleteButton);
		
		mainPanel.add(scrollpane, BorderLayout.CENTER);
		mainPanel.add(bottomPanel, BorderLayout.SOUTH);
		
		this.setContentPane(mainPanel);
		
		this.setSize(900, 600);
		
		this.setLocationRelativeTo(null);
		
		this.setDefaultCloseOperation(HIDE_ON_CLOSE);
	}
	
	public void actionPerformed(ActionEvent e) {
		if (e.getSource() == reloadButton) {
			model.reloadSites();
		} else if (e.getSource() == deleteButton) {
			ListSelectionModel lsm = table.getSelectionModel();
			
			ArrayList<Integer> rows = new ArrayList<Integer>();
			
			for (int i=lsm.getMinSelectionIndex(); i<=lsm.getMaxSelectionIndex(); i++) {
				if (lsm.isSelectedIndex(i)) {
					rows.add(i);
				}
			}
			
			ArrayList<CybershakeSite> sitesToDelete = new ArrayList<CybershakeSite>();
			
			for (int row : rows) {
				sitesToDelete.add(model.getSiteAtRow(row));
			}
			
			for (CybershakeSite site : sitesToDelete) {
				deleteSite(site);
				model.reloadSites();
			}
		} else if (e.getSource() == insertButton) {
			if (addGUI == null)
				addGUI = new SingleSiteAddEditGUI(db, model, null);
			
			addGUI.setVisible(true);
		} else if (e.getSource() == batchAddButton) {
			if (batchAddGUI == null)
				batchAddGUI = new BatchSiteAddGUI(db, model);
			
			batchAddGUI.setVisible(true);
		} else if (e.getSource() == editButton) {
			ListSelectionModel lsm = table.getSelectionModel();
			CybershakeSite site = model.getSiteAtRow(lsm.getMinSelectionIndex());
			
			SingleSiteAddEditGUI edit = new SingleSiteAddEditGUI(db, model, site);
			
			edit.setVisible(true);
		}
	}
	
	public void valueChanged(ListSelectionEvent e) {
		// if it's in the middle of a change, ignore
		if (e.getValueIsAdjusting())
			return;
		
		ListSelectionModel lsm = table.getSelectionModel();
		boolean isSingle = lsm.getMinSelectionIndex() == lsm.getMaxSelectionIndex();
		
		if (lsm.isSelectionEmpty()) {
			deleteButton.setEnabled(false);
			editButton.setEnabled(false);
		} else {
			deleteButton.setEnabled(!readOnly);
			editButton.setEnabled(!readOnly && isSingle);
		}
	}
	
	public boolean deleteSite(CybershakeSite site) {
		// make sure they really want to do this!
		
		String title = "Really delete CyberShake Site?";
		String message = "Are you sure that you want to delete site: " + site.getFormattedName() + "?\n\n" +
				"This will also delete the following for this site:\n" +
				" * Peak Amplitudes\n" +
				" * Hazard Curves\n" +
				" * Regional Bounds\n" +
				" * Site Ruptures\n\n" +
				"This cannot be undone!!!";
		int response = JOptionPane.showConfirmDialog(null, message, title, JOptionPane.YES_NO_OPTION);
		
		if (response != JOptionPane.YES_OPTION)
			return false;
		
		return CybershakeSiteManager.deleteCybershakeSite(db, site);
	}

}
