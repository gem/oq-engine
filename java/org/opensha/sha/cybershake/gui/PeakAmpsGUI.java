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
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JSeparator;
import javax.swing.JTable;
import javax.swing.ListSelectionModel;
import javax.swing.event.ListSelectionEvent;
import javax.swing.event.ListSelectionListener;

import org.opensha.sha.cybershake.db.CybershakeRun;
import org.opensha.sha.cybershake.db.DBAccess;

public class PeakAmpsGUI extends JFrame implements ActionListener, ListSelectionListener {

	DBAccess db;
	
	JPanel mainPanel = new JPanel(new BorderLayout());
	
	JPanel bottomPanel = new JPanel();
	
	JButton deleteButton = new JButton("Delete Amps");
	JButton countButton = new JButton("Load Count");
	JButton reloadButton = new JButton("Reload Amps");
	
	PeakAmpsTableModel model;
	JTable table;
	
	private boolean readOnly = false;
	
	public PeakAmpsGUI(DBAccess db) {
		super("Peak Amplitudes");
		
		this.db = db;
		this.readOnly = db.isReadOnly();
		
		model = new PeakAmpsTableModel(db);
		
		table = new JTable(model);
		
		JScrollPane scrollpane = new JScrollPane(table);
		
		bottomPanel.setLayout(new BoxLayout(bottomPanel, BoxLayout.X_AXIS));
		
		table.getSelectionModel().addListSelectionListener(this);
		deleteButton.addActionListener(this);
		deleteButton.setEnabled(false);
		
		reloadButton.addActionListener(this);
		
		countButton.addActionListener(this);
		countButton.setEnabled(false);
		
		bottomPanel.add(reloadButton);
		bottomPanel.add(new JSeparator());
		bottomPanel.add(countButton);
		bottomPanel.add(new JSeparator());
		bottomPanel.add(deleteButton);
		
		mainPanel.add(scrollpane, BorderLayout.CENTER);
		mainPanel.add(bottomPanel, BorderLayout.SOUTH);
		
		this.setContentPane(mainPanel);
		
		this.setSize(900, 600);
		
		this.setLocationRelativeTo(null);
		
		this.setDefaultCloseOperation(HIDE_ON_CLOSE);
	}
	
	private ArrayList<Integer> getSelectedRows() {
		ListSelectionModel lsm = table.getSelectionModel();
		
		ArrayList<Integer> rows = new ArrayList<Integer>();
		
		for (int i=lsm.getMinSelectionIndex(); i<=lsm.getMaxSelectionIndex(); i++) {
			if (lsm.isSelectedIndex(i)) {
				rows.add(i);
			}
		}
		
		return rows;
	}

	public void actionPerformed(ActionEvent e) {
		if (e.getSource() == reloadButton) {
			this.model.reloadAmps();
		} else if (e.getSource() == deleteButton) {
			ArrayList<Integer> rows = getSelectedRows();
			
			for (int row : rows) {
				CybershakeRun amps = model.getAmpsAtRow(row);
				System.out.println("Deleting amps: " + amps);
				
				int num = this.model.deleteAmps(amps);
				if (num == 0)
					System.err.println("Error deleting amps (or user cancelled): " + amps);
			}
			model.reloadAmps();
		} else if (e.getSource() == countButton) {
			ArrayList<Integer> rows = getSelectedRows();
			
			for (int row : rows) {
				this.model.loadCount(row);
				
				this.model.fireTableCellUpdated(row, PeakAmpsTableModel.NUM_COLUMNS - 1);
			}
		}
	}

	public void valueChanged(ListSelectionEvent e) {
		// if it's in the middle of a change, ignore
		if (e.getValueIsAdjusting())
			return;
		
		ListSelectionModel lsm = table.getSelectionModel();
		
		if (lsm.isSelectionEmpty()) {
			deleteButton.setEnabled(false);
			countButton.setEnabled(false);
		} else {
			deleteButton.setEnabled(!readOnly);
			countButton.setEnabled(true);
		}
	}
}
