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

import org.opensha.commons.gui.ConsoleWindow;

public class StepManager {

	protected StepsPanel panel;
	
	protected Loadable parent, next;
	
	protected ArrayList<Step> steps = new ArrayList<Step>();
	
	ConsoleWindow console;
	
	public StepManager(Loadable parent, Loadable next, ConsoleWindow console) {
		this.parent = parent;
		this.next = next;
		this.console = console;
	}
	
	public void init() {
		panel = new StepsPanel(steps, parent, next, console);
	}
	
	public JPanel getPanel() {
		return panel;
	}
	
}
