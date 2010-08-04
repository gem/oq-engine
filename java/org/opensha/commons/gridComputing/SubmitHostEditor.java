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

package org.opensha.commons.gridComputing;

import java.awt.Dimension;
import java.awt.GridLayout;
import java.util.ArrayList;

import javax.swing.JComponent;
import javax.swing.JDialog;
import javax.swing.JLabel;
import javax.swing.JTextField;

public class SubmitHostEditor extends JDialog {
	
	JTextField name = new JTextField();
	JTextField hostName = new JTextField();
	JTextField path = new JTextField();
	JTextField dependencyPath = new JTextField();
	JTextField forkScheduler = new JTextField();
	JTextField condorPath = new JTextField();
	JTextField transferEnvironment = new JTextField();
	JTextField transferArguments = new JTextField();
	JTextField transferExecutable = new JTextField();
	
	SubmitHost submit;
	
	public SubmitHostEditor(SubmitHost submit) {
		this.submit = submit;
		ArrayList<JComponent> leftCol = new ArrayList<JComponent>();
		ArrayList<JComponent> rightCol = new ArrayList<JComponent>();
		
		leftCol.add(new JLabel("Name"));
		name.setText(submit.getName());
		rightCol.add(name);
		
		leftCol.add(new JLabel("Host Name"));
		hostName.setText(submit.getHostName());
		rightCol.add(hostName);
		
		leftCol.add(new JLabel("Path"));
		path.setText(submit.getPath());
		rightCol.add(path);
		
		leftCol.add(new JLabel("Path To Dependencies"));
		dependencyPath.setText(submit.getDependencyPath());
		rightCol.add(dependencyPath);
		
		leftCol.add(new JLabel("Fork Scheduler"));
		forkScheduler.setText(submit.getForkScheduler());
		rightCol.add(forkScheduler);
		
		leftCol.add(new JLabel("Condor Bin Path"));
		condorPath.setText(submit.getCondorPath());
		rightCol.add(condorPath);
		
		leftCol.add(new JLabel("Globus Environment"));
		transferEnvironment.setText(submit.getTransferEnvironment());
		rightCol.add(transferEnvironment);
		
		leftCol.add(new JLabel("GridFTP Transfer Arguments"));
		transferArguments.setText(submit.getTransferArguments());
		rightCol.add(transferArguments);
		
		leftCol.add(new JLabel("Kickstart Executable Path"));
		transferExecutable.setText(submit.getTransferExecutable());
		rightCol.add(transferExecutable);
		
		this.createGUI(leftCol, rightCol);
		this.setDefaultCloseOperation(JDialog.DISPOSE_ON_CLOSE);
		this.setTitle("Submit Host");
//		this.pack();
	}
	
	public void createGUI(ArrayList<JComponent> leftCol, ArrayList<JComponent> rightCol) {
		int num = leftCol.size();
		
		this.setLayout(new GridLayout(num, 2));
		
		for (int i=0; i<leftCol.size(); i++) {
			JComponent left = leftCol.get(i);
			JComponent right = rightCol.get(i);
			
			this.add(left);
			this.add(right);
		}
		
		this.setPreferredSize(new Dimension(200, 500));
		this.setSize(new Dimension(500, 300));
	}
	
	public SubmitHost getSubmitHost() {
		String name = this.name.getText();
		String hostName = this.hostName.getText();
		String path = this.path.getText();
		String dependencyPath = this.dependencyPath.getText();
		String forkScheduler = this.forkScheduler.getText();
		String condorPath = this.condorPath.getText();
		String transferEnvironment = this.transferEnvironment.getText();
		String transferArguments = this.transferArguments.getText();
		String transferExecutable = this.transferExecutable.getText();
		
		return new SubmitHost(name, hostName, path, dependencyPath, forkScheduler, condorPath, transferEnvironment, transferArguments, transferExecutable);
	}

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		SubmitHost submit = SubmitHost.INTENSITY;
		SubmitHostEditor editor = new SubmitHostEditor(submit);
		
		editor.setVisible(true);

	}

}
