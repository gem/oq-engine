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
import java.awt.Color;
import java.awt.Dimension;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.Date;

import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JProgressBar;
import javax.swing.JSeparator;

import org.opensha.sha.calc.hazardMap.old.CalculationStatus;
import org.opensha.sha.calc.hazardMap.old.HazardMapJobCreator;
import org.opensha.sha.calc.hazardMap.old.servlet.DatasetID;
import org.opensha.sha.calc.hazardMap.old.servlet.StatusServletAccessor;

public class StatusPanel extends JPanel implements StepActivatedListener, ActionListener {
	
	StatusServletAccessor statusAccessor = new StatusServletAccessor(StatusServletAccessor.SERVLET_URL);
	
	HazardMapApplet parent;
	
	private String startName = "Curves Submitted";
	private String calcName = "Curves Calculated";
	private String retrieveName = "Curves Retrieved";
	
	JProgressBar startProgress = new JProgressBar();
	JProgressBar calcProgress = new JProgressBar();
	JProgressBar retrieveProgress = new JProgressBar();
	
	JLabel statusLabel = new JLabel("Current Status: ");
	JLabel dateLabel = new JLabel("Last Updated: ");
	JLabel idLabel = new JLabel("Dataset Name: ");
	
	JLabel statusMessage = new JLabel();
	JLabel dateMessage = new JLabel();
	JLabel idMessage = new JLabel();
	
	JPanel topPanel = new JPanel();
	JPanel idPanel = new JPanel();
	JPanel statusPanel = new JPanel();
	JPanel datePanel = new JPanel();
	JPanel barPanel = new JPanel();
	
	JButton refreshButton = new JButton("Refresh");
	
	public StatusPanel(HazardMapApplet parent) {
		super(new BorderLayout());
		
		this.parent = parent;
		
		startProgress.setStringPainted(true);
		calcProgress.setStringPainted(true);
		retrieveProgress.setStringPainted(true);
		
		startProgress.setEnabled(false);
		calcProgress.setEnabled(false);
		retrieveProgress.setEnabled(false);
		
		topPanel.setLayout(new BoxLayout(topPanel, BoxLayout.Y_AXIS));
		
		statusPanel.setLayout(new BoxLayout(statusPanel, BoxLayout.X_AXIS));
		statusPanel.add(statusLabel);
		statusPanel.add(statusMessage);
		
		idPanel.setLayout(new BoxLayout(idPanel, BoxLayout.X_AXIS));
		idPanel.add(idLabel);
		idPanel.add(idMessage);
		
		datePanel.setLayout(new BoxLayout(datePanel, BoxLayout.X_AXIS));
		datePanel.add(dateLabel);
		datePanel.add(dateMessage);
		
		topPanel.add(idPanel);
		topPanel.add(statusPanel);
		topPanel.add(datePanel);
		
		this.add(topPanel, BorderLayout.NORTH);
		
		barPanel.setLayout(new BoxLayout(barPanel, BoxLayout.Y_AXIS));
		
		startProgress.setPreferredSize(new Dimension(300, 30));
		calcProgress.setPreferredSize(new Dimension(300, 30));
		retrieveProgress.setPreferredSize(new Dimension(300, 30));
		
		startProgress.setForeground(Color.BLUE);
		calcProgress.setForeground(Color.GREEN);
//		retrieveProgress.setForeground(new Color(0, 140, 0));
		retrieveProgress.setForeground(new Color(255, 160, 0));
//		retrieveProgress.setForeground(Color.ORANGE);
		
		barPanel.add(startProgress);
		barPanel.add(new JSeparator());
		barPanel.add(calcProgress);
		barPanel.add(new JSeparator());
		barPanel.add(retrieveProgress);
		barPanel.add(refreshButton);
		
		refreshButton.addActionListener(this);
		
		JPanel panel = new JPanel();
		
		panel.add(barPanel);
		
		this.add(panel, BorderLayout.CENTER);
	}
	
	private void loadStatus() {
		DatasetID id = this.parent.getSelector().getSelectedID();
		
		if (id == null) {
			clearStatus();
			return;
		}
		
		try {
			CalculationStatus status = this.statusAccessor.getStatus(id.getID());
			
			this.setStatus(status, id.getID(), id.getName());
		} catch (Exception e) {
			clearStatus();
			e.printStackTrace();
		}
	}
	
	private void setStatus(CalculationStatus status, String id, String name) {
		if (id.equals(name))
			idMessage.setText(id);
		else
			idMessage.setText(name + " (" + id + ")");
		this.setupProgressBars(status);
		statusMessage.setText(status.getMessage());
		Date date = status.getDate();
		if (date == null) {
			dateMessage.setText("N/A");
		} else {
			String dateStr = HazardMapJobCreator.LINUX_DATE_FORMAT.format(date);
			dateMessage.setText(dateStr);
		}
	}
	
	private void clearStatus() {
		startProgress.setString(startName + " (0/unknown)");
		calcProgress.setString(calcName + " (0/unknown)");
		retrieveProgress.setString(retrieveName + " (0/unknown)");
		
		idMessage.setText("N/A");
		
		startProgress.setValue(0);
		calcProgress.setValue(0);
		retrieveProgress.setValue(0);
		
		statusMessage.setText("Not Started, or Log Files Deleted");
		dateMessage.setText("N/A");
	}
	
	private void setupProgressBars(CalculationStatus status) {
		int total = status.getTotal();
		int start = status.getIp();
		int calc = status.getDone();
		int trans = status.getRetrieved();
		
		if (start > total)
			start = total;
		if (calc > total)
			calc = total;
		if (trans > total)
			trans = total;
		
		startProgress.setMaximum(total);
		startProgress.setValue(start);
		startProgress.setEnabled(true);
		
		startProgress.setString(startName + " (" + start + "/" + total + ")");
		calcProgress.setString(calcName + " (" + calc + "/" + total + ")");
		
		calcProgress.setMaximum(total);
		calcProgress.setValue(calc);
		calcProgress.setEnabled(true);
		
		if (trans < 0) {
			retrieveProgress.setEnabled(false);
			retrieveProgress.setString(retrieveName + " N/A");
		} else {
			retrieveProgress.setMaximum(total);
			retrieveProgress.setValue(trans);
			retrieveProgress.setEnabled(true);
			retrieveProgress.setString(retrieveName + " (" + trans + "/" + total + ")");
		}
	}

	public void stepActivated(Step step) {
		System.out.println("Activated!");
		this.clearStatus();
		this.loadStatus();
	}

	public void actionPerformed(ActionEvent e) {
		if (e.getSource() == refreshButton) {
			this.loadStatus();
		}
	}

}
