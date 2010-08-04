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

import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JLabel;
import javax.swing.JList;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.ListSelectionModel;
import javax.swing.event.ListSelectionEvent;
import javax.swing.event.ListSelectionListener;

public abstract class NamesListPanel extends JPanel implements ListSelectionListener, ActionListener {
	
	protected JList namesList;
	
	protected JButton addButton = new JButton("Add");
	protected JButton removeButton = new JButton("Remove");
	
	public NamesListPanel(JPanel lowerPanel, String label) {
		super(new BorderLayout());
		
		namesList = new JList();
		namesList.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
		namesList.setSelectedIndex(0);
		namesList.addListSelectionListener(this);
		
		JScrollPane listScroller = new JScrollPane(namesList);
		listScroller.setPreferredSize(new Dimension(250, 150));
		
		JPanel northPanel = new JPanel(new BorderLayout());
		northPanel.add(new JLabel(label), BorderLayout.NORTH);
		northPanel.add(listScroller, BorderLayout.CENTER);
		
		JPanel buttonPanel = new JPanel();
		buttonPanel.setLayout(new BoxLayout(buttonPanel, BoxLayout.X_AXIS));
		buttonPanel.add(addButton);
		buttonPanel.add(removeButton);
		removeButton.setEnabled(false);
		addButton.addActionListener(this);
		removeButton.addActionListener(this);
		
		northPanel.add(buttonPanel, BorderLayout.SOUTH);
		
		this.add(northPanel, BorderLayout.NORTH);
		
		if (lowerPanel != null)
			setLowerPanel(lowerPanel);
	}
	
	public void setLowerPanel(JPanel lowerPanel) {
		this.add(lowerPanel, BorderLayout.CENTER);
		this.validate();
	}
	
	public void valueChanged(ListSelectionEvent e) {
		removeButton.setEnabled(shouldEnableRemoveButton());
	}

	public void actionPerformed(ActionEvent e) {
		if (e.getSource() == addButton) {
			addButton_actionPerformed();
			addButton.setEnabled(shouldEnableAddButton());
		} else if (e.getSource() == removeButton) {
			removeButton_actionPerformed();
			removeButton.setEnabled(shouldEnableRemoveButton());
			addButton.setEnabled(shouldEnableAddButton());
		}
	}
	
	public abstract void addButton_actionPerformed();
	
	public abstract void removeButton_actionPerformed();
	
	public abstract boolean shouldEnableAddButton();
	
	public boolean shouldEnableRemoveButton() {
		return !namesList.isSelectionEmpty();
	}

}
