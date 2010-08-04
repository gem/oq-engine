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
 * <p>Title: PlottingOptionControl</p>
 * <p>Description: This class provides user with the option of adding new hazardcurves
 * to the existing set or plotting on the top of existing. Both these options work in the
 * following manner:
 * 1)Ploting on top of the existing dataset : This is just addition of new dataset
 * with the existing in a new color. Now if the existing dataset is Epistemic_List,
 * newly added dataset can a new set of Epistemic list curves or a simple hazard curve.
 * If the new dataste is from the simple hazard curve then just add that to the existing in a
 * different color. But if the new dataset is a Epistemic list then add this list
 * to the exisiting in a different color, with mean and fractile in unique color too, meaning
 * different from the earlier dataset color.
 *
 * 2)Adding to existing dataset: this option only works for the epistemic list.
 * This option won't work and will automatically get (1) option, if user is trying
 * to add 2 different epistemic lists. Once addition has been performed then
 * new set of fractiles and mean would be computed and plotted removing the earlier
 * set.</p>
 * @author : Ned Field, Nitin Gupta and Vipin Gupta
 * @created : September 3, 2004
 * @version 1.0
 */

public class PlottingOptionControl extends ControlPanel {

	public static final String NAME = "Set new dataset plotting option";

	//String Option to select map calculation method
	public final static String ADD_TO_EXISTING = "Add to existing dataset";
	public final static String PLOT_ON_TOP = "Plot on top of existing dataset";

	private JPanel jPanel1 = new JPanel();
	private JRadioButton addToExistingOption = new JRadioButton();
	private JRadioButton plotOnTopOfExistingOption = new JRadioButton();
	private JLabel jLabel1 = new JLabel();

	private ButtonGroup buttonGroup = new ButtonGroup();
	private BorderLayout borderLayout1 = new BorderLayout();
	private GridBagLayout gridBagLayout1 = new GridBagLayout();

	private Component parentComponent;
	private JFrame frame;
	
	public PlottingOptionControl(Component parentComponent) {
		super(NAME);
		this.parentComponent = parentComponent;
	}
	
	public void doinit() {
		frame = new JFrame();
		// show the window at center of the parent component
		frame.setLocation(parentComponent.getX()+parentComponent.getWidth()/2,
				parentComponent.getY()+parentComponent.getHeight()/2);
		try {
			//creating the GUI components to show the plotting options.
			jbInit();
		}
		catch(Exception e) {
			e.printStackTrace();
		}
	}

	private void jbInit() throws Exception {
		frame.getContentPane().setLayout(borderLayout1);
		jPanel1.setLayout(gridBagLayout1);
		addToExistingOption.setText(ADD_TO_EXISTING);
		plotOnTopOfExistingOption.setText(PLOT_ON_TOP);
		addToExistingOption.setActionCommand(ADD_TO_EXISTING);
		plotOnTopOfExistingOption.setActionCommand(PLOT_ON_TOP);
		jLabel1.setFont(new java.awt.Font("Lucida Grande", 1, 15));
		jLabel1.setHorizontalAlignment(SwingConstants.CENTER);
		jLabel1.setHorizontalTextPosition(SwingConstants.CENTER);
		jLabel1.setText("Select plotting option");
		frame.getContentPane().add(jPanel1, BorderLayout.CENTER);
		jPanel1.add(plotOnTopOfExistingOption,  new GridBagConstraints(0, 1, 1, 1, 0.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(19, 53, 0, 31), 51, 16));
		jPanel1.add(addToExistingOption,  new GridBagConstraints(0, 2, 1, 1, 0.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(0, 53, 25, 80), 46, 16));
		jPanel1.add(jLabel1,  new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(24, 10, 0, 31), 90, 10));
		buttonGroup.add(plotOnTopOfExistingOption);
		buttonGroup.add(addToExistingOption);
		buttonGroup.setSelected(plotOnTopOfExistingOption.getModel(),true);
	}

	/**
	 *
	 * @returns the selected option String choosen by the user
	 * to calculate Hazard Map.
	 */
	public String getSelectedOption(){
		return buttonGroup.getSelection().getActionCommand();
	}

	/**
	 * sets the selected option to plot the map
	 * @param option
	 */
	public void setSelectedOption(String option){
		if(option.equals(this.ADD_TO_EXISTING))
			buttonGroup.setSelected(addToExistingOption.getModel(),true);
		else if(option.equals(this.PLOT_ON_TOP))
			buttonGroup.setSelected(plotOnTopOfExistingOption.getModel(),true);
	}

	@Override
	public Window getComponent() {
		return frame;
	}
}
