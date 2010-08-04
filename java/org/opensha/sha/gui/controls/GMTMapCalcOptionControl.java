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
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.Window;

import javax.swing.ButtonGroup;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JRadioButton;
import javax.swing.SwingConstants;

/**
 * <p>Title: CalcOptionControl</p>
 * <p>Description: This class gives option to the user to choose the option to
 * select the way he wants to do the calculation for the maps. He has the option
 * of either selecting to do the calculation of his local or on the server.</p>
 * @author : Ned Field, Nitin Gupta and Vipin Gupta
 * @created : 7 June, 2004
 * @version 1.0
 */

public class GMTMapCalcOptionControl extends ControlPanel {

	public static final String NAME = "Select Map Calcution Method";

	//String Option to select map calculation method
	public final static String USE_LOCAL = "Use Local";
	public final static String USE_SERVER = "Use Server";

	private JPanel jPanel1 = new JPanel();
	private JRadioButton localCalcOption = new JRadioButton();
	private JRadioButton serverCalcOption = new JRadioButton();
	private JLabel jLabel1 = new JLabel();

	private ButtonGroup buttonGroup = new ButtonGroup();
	private BorderLayout borderLayout1 = new BorderLayout();
	private GridBagLayout gridBagLayout1 = new GridBagLayout();

	private Component parentComponent;
	private JFrame frame;
	
	public GMTMapCalcOptionControl(Component parentComponent) {
		super(NAME);
		this.parentComponent = parentComponent;
	}
	
	public void doinit() {
		frame = new JFrame();
		
		// show the window at center of the parent component
		frame.setLocation(parentComponent.getX()+parentComponent.getWidth()/2,
				parentComponent.getY()+parentComponent.getHeight()/2);
		try {
			//creating the GUI components to show the Calculation options.
			jbInit();
		}
		catch(Exception e) {
			e.printStackTrace();
		}
	}

	private void jbInit() throws Exception {
		frame.getContentPane().setLayout(borderLayout1);
		jPanel1.setLayout(gridBagLayout1);
		localCalcOption.setText(USE_LOCAL);
		serverCalcOption.setText(USE_SERVER);
		localCalcOption.setActionCommand(USE_LOCAL);
		serverCalcOption.setActionCommand(USE_SERVER);
		jLabel1.setFont(new java.awt.Font("Lucida Grande", 1, 15));
		jLabel1.setHorizontalAlignment(SwingConstants.CENTER);
		jLabel1.setHorizontalTextPosition(SwingConstants.CENTER);
		jLabel1.setText("Select Map Calculation Option");
		frame.getContentPane().add(jPanel1, BorderLayout.CENTER);
		jPanel1.add(localCalcOption,  new GridBagConstraints(0, 1, 1, 1, 0.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(24, 90, 0, 132), 51, 16));
		jPanel1.add(serverCalcOption,  new GridBagConstraints(0, 2, 1, 1, 0.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(0, 90, 31, 132), 46, 16));
		jPanel1.add(jLabel1,  new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(12, 3, 0, 16), 121, 10));
		buttonGroup.add(localCalcOption);
		buttonGroup.add(serverCalcOption);
		buttonGroup.setSelected(serverCalcOption.getModel(),true);
	}

	/**
	 *
	 * @returns the selected option String choosen by the user
	 * to calculate Hazard Map.
	 */
	public String getMapCalculationOption(){
		return buttonGroup.getSelection().getActionCommand();
	}

	@Override
	public Window getComponent() {
		return frame;
	}
}
