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
import java.awt.CardLayout;
import java.awt.Font;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;

import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JSeparator;

import org.opensha.commons.gui.ConsoleWindow;

public class StepsPanel extends JPanel implements ActionListener {
	
	JLabel titleLabel;
	JPanel topPanel = new JPanel();
	
	JButton backButton = new JButton("Back");
	JButton nextButton = new JButton("Next");
	JButton consoleButton = null;
	
	CardLayout cl = new CardLayout();
	
	JPanel centerPanel = new JPanel(cl);
	
	JPanel bottomPanel;
	
	Font messageFont = new Font("Message Font", Font.BOLD, 40);
	
	ArrayList<Step> steps;
	
	int numSteps;
	int currentStepIndex;
	
	Step currentStep = null;
	
	Loadable previous;
	Loadable next;
	
	ConsoleWindow console;
	
	public StepsPanel(ArrayList<Step> steps) {
		this(steps, null, null, null);
	}
	
	public StepsPanel(ArrayList<Step> steps, Loadable previous, Loadable next, ConsoleWindow console) {
		super(new BorderLayout());
		if (console != null) {
			consoleButton = new JButton("Show Console");
			consoleButton.addActionListener(this);
		}
		
		this.console = console;
		
		bottomPanel = HazardMapApplet.createBottomPanel(backButton, nextButton, consoleButton);
		
		this.steps = steps;
		this.previous = previous;
		this.next = next;
		numSteps = steps.size();
		
		topPanel.setLayout(new BoxLayout(topPanel, BoxLayout.Y_AXIS));
		
		titleLabel = new JLabel();
		titleLabel.setFont(messageFont);
		
		topPanel.add(titleLabel);
		topPanel.add(new JSeparator());
		
		
		backButton.addActionListener(this);
		nextButton.addActionListener(this);
		
		for (int i=0; i<steps.size(); i++) {
			Step step = steps.get(i);
			centerPanel.add(step.getPanel(), i+"");
			step.setStepsPanel(this);
		}
		
		this.loadStep(0);
		
		this.add(topPanel, BorderLayout.NORTH);
		this.add(bottomPanel, BorderLayout.SOUTH);
		this.add(centerPanel, BorderLayout.CENTER);
	}
	
	public void setNextEnabled(boolean enabled) {
		this.nextButton.setEnabled(enabled);
	}
	
	public void setPreviousEnabled(boolean enabled) {
		this.backButton.setEnabled(enabled);
	}
	
	private void loadStep(int index) {
		// check to see if this is the previous or last (before or after the steps)
		if (index < 0) {
			previous.loadStep();
			return;
		}
		if (index == numSteps) {
			next.loadStep();
			return;
		}
		
		Step step = steps.get(index);
		
		int displayIndex = index + 1;
		
		if (index < 0)
			throw new RuntimeException("Step not in step list: " + step.getTitle());
		
		String title = displayIndex + "/" + numSteps + ": " + step.getTitle();
		
		titleLabel.setText(title);
		
		topPanel.invalidate();
		
		if (displayIndex == 1 && previous == null)
			backButton.setEnabled(false);
		else
			backButton.setEnabled(true);
		
		if (displayIndex == numSteps && next == null)
			nextButton.setEnabled(false);
		else
			nextButton.setEnabled(true);
		
		this.cl.show(centerPanel, index+"");
		
		this.doLayout();
		
		this.currentStep = step;
		this.currentStepIndex = index;
		
		step.setActivated();
	}
	
	public void loadNextStep() {
		this.loadStep(this.currentStepIndex + 1);
	}

	public void actionPerformed(ActionEvent e) {
		Object source = e.getSource();
		
		if (source.equals(backButton)) {
			this.loadStep(currentStepIndex - 1);
		} else if (source.equals(nextButton)) {
			this.loadStep(currentStepIndex + 1);
		} else if (source.equals(consoleButton)) {
			this.console.setVisible(true);
		}
	}
}
