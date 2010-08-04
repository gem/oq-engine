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

package org.opensha.sha.gui.controls;

import java.awt.BorderLayout;
import java.awt.Component;
import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.Window;

import javax.swing.JCheckBox;
import javax.swing.JFrame;
import javax.swing.JPanel;

/**
 * <p>Title: RunAll_PEER_TestCasesControlPanel</p>
 * <p>Description: This class runs all the PEER tst cases and output the results in a file</p>
 * @author : Edward (Ned) Field, Nitin Gupta and Vipin Gupta
 * @version 1.0
 */

public class RunAll_PEER_TestCasesControlPanel extends ControlPanel {
	
	public static final String NAME = "Run all PEER Test Cases";
	
	private JPanel jPanel1 = new JPanel();
	private JCheckBox runPEERcheck = new JCheckBox();
	private GridBagLayout gridBagLayout1 = new GridBagLayout();
	private BorderLayout borderLayout1 = new BorderLayout();
	
	private JFrame frame;
	
	private Component parent;

	public RunAll_PEER_TestCasesControlPanel(Component parent) {
		super(NAME);
		this.parent = parent;
		
	}
	
	public void doinit() {
		frame = new JFrame();
		try {
			jbInit();
			// show the window at center of the parent component
			frame.setLocation(parent.getX()+parent.getWidth()/2,
					parent.getY()+parent.getHeight()/2);
		}
		catch(Exception e) {
			e.printStackTrace();
		}
	}
	
	private void jbInit() throws Exception {
		frame.getContentPane().setLayout(borderLayout1);
		jPanel1.setLayout(gridBagLayout1);
		runPEERcheck.setText("Click  to run PEER Test Cases (this will take a long time!)");
		frame.setTitle("Run All PEER Test Cases Control Panel");
		jPanel1.setPreferredSize(new Dimension(350,70));
		frame.setSize(350,70);
		frame.getContentPane().add(jPanel1, BorderLayout.SOUTH);
		jPanel1.add(runPEERcheck, new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(76, 65, 95, 96), 36, 14));

	}


	/**
	 *
	 * @returns true if we have to run all the PEER test cases
	 */
	public boolean runAllPEER_TestCases(){
		if(this.runPEERcheck.isSelected())
			return true;
		else
			return false;
	}

	@Override
	public Window getComponent() {
		return frame;
	}

}
