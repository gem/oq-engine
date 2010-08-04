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

import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JPanel;

public class ChooserDialog extends JFrame implements ActionListener {
	
	CyberShakeDBManagementApp app;

	JPanel mainPanel = new JPanel();
	
	JButton curves = new JButton("Manage Hazard Curves");
	JButton amps = new JButton("Manage Peak Amplitudes");
	JButton sites = new JButton("Manage Sites");
	
	public ChooserDialog(CyberShakeDBManagementApp app) {
		super("CyberShake DB Management Application");
		
		this.app = app;
		
		mainPanel.setLayout(new BoxLayout(mainPanel, BoxLayout.Y_AXIS));
		
		sites.addActionListener(this);
		amps.addActionListener(this);
		curves.addActionListener(this);
		
		mainPanel.add(sites);
		mainPanel.add(amps);
		mainPanel.add(curves);
		
		this.setContentPane(mainPanel);
		
		this.setSize(400, 300);
		
		this.setLocationRelativeTo(null);
		
		this.setDefaultCloseOperation(EXIT_ON_CLOSE);
	}

	public void actionPerformed(ActionEvent e) {
		if (e.getSource() == curves) {
			app.showCurvesGUI();
		} else if (e.getSource() == amps) {
			app.showAmpsGUI();
		}else if (e.getSource() == sites) {
			app.showSitesGUI();
		}
	}
	
}
