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
import java.awt.Font;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;

import javax.swing.BorderFactory;
import javax.swing.Box;
import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JSeparator;

import org.opensha.commons.gui.ConsoleWindow;

public class OptionPanel extends JPanel implements ActionListener {
	
	JLabel messageLabel;
	JPanel messagePanel = new JPanel();
	
	Font messageFont = new Font("Message Font", Font.BOLD, 40);
	Font buttonFont = new Font("Button Font", Font.BOLD, 20);
	
	JButton backButton = new JButton("Back");
	JButton consoleButton = null;
	JPanel bottomPanel;
	
	JPanel buttonPanel = new JPanel();
	
	OptionPanelListener listener;
	
	ConsoleWindow console;
	
	public OptionPanel(String message, ArrayList<String> options, OptionPanelListener listener, ConsoleWindow console) {
		super(new BorderLayout());
		
		if (console != null) {
			consoleButton = new JButton("Show Console");
			consoleButton.addActionListener(this);
		}
		this.console = console;
		
		bottomPanel = HazardMapApplet.createBottomPanel(backButton, null, consoleButton);
		
		this.listener = listener;
		
		messageLabel = new JLabel(message);
		messageLabel.setFont(messageFont);
		
		buttonPanel.setLayout(new BoxLayout(buttonPanel, BoxLayout.Y_AXIS));
		messagePanel.setLayout(new BoxLayout(messagePanel, BoxLayout.Y_AXIS));
		
		buttonPanel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));
		
		backButton.addActionListener(this);
		
		messagePanel.add(messageLabel);
		messagePanel.add(new JSeparator());
		
		
		
		if (options.size() == 0) {
			throw new RuntimeException("At least 1 option must be supplied!");
		}
		
		for (String option : options) {
			JButton button = new JButton(option);
			button.setFont(buttonFont);
			buttonPanel.add(button);
			buttonPanel.add(Box.createRigidArea(new Dimension(0, 10)));
			button.addActionListener(this);
		}
		
		this.add(messagePanel, BorderLayout.NORTH);
		this.add(buttonPanel, BorderLayout.CENTER);
		this.add(bottomPanel, BorderLayout.SOUTH);
	}
	
	public JPanel getButtonPanel() {
		return buttonPanel;
	}
	
	public void setBackEnabled(boolean enabled) {
		backButton.setEnabled(enabled);
	}

	public void actionPerformed(ActionEvent e) {
		Object source = e.getSource();
		if (source.equals(backButton)) {
			listener.optionSelected(HazardMapApplet.BACK_OPTION);
		} else if (source.equals(consoleButton)) {
			this.console.setVisible(true);
		} else if (source instanceof JButton) {
			JButton button = (JButton)source;
			listener.optionSelected(button.getText());
		}
	}

}
