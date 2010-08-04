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

import java.util.ArrayList;

import javax.swing.JPanel;

public class Step {
	
	private JPanel panel;
	private String title;
	
	private StepsPanel stepsPanel;
	
	ArrayList<StepActivatedListener> listeners = new ArrayList<StepActivatedListener>();
	
	public Step(JPanel panel, String title) {
		this.panel = panel;
		this.title = title;
	}

	public JPanel getPanel() {
		return panel;
	}

	public String getTitle() {
		return title;
	}
	
	public void setTitle(String title) {
		this.title = title;
	}
	
	public void setActivated() {
		for (StepActivatedListener listener : listeners) {
			listener.stepActivated(this);
		}
	}
	
	public void addStepActivatedListener(StepActivatedListener listener) {
		listeners.add(listener);
	}
	
	public void removeStepActivatedListener(StepActivatedListener listener) {
		listeners.remove(listener);
	}
	
	public void removeAllStepActivatedListeners() {
		listeners.clear();
	}

	public StepsPanel getStepsPanel() {
		return stepsPanel;
	}

	public void setStepsPanel(StepsPanel stepsPanel) {
		this.stepsPanel = stepsPanel;
	}
}
