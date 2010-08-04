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

import java.awt.Component;
import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.Window;
import java.awt.event.ActionEvent;
import java.util.ArrayList;
import java.util.StringTokenizer;

import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JComboBox;
import javax.swing.JFrame;
import javax.swing.JOptionPane;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;

import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterConstraintAPI;
import org.opensha.commons.param.event.ParameterChangeFailEvent;
import org.opensha.commons.param.event.ParameterChangeFailListener;
import org.opensha.sha.gui.HazardCurveServerModeApplication;



/**
 * <p>Title: ERF Epistemic List Control Panel</p>
 * <p>Description: This window will allow the user to select the fractile to be
 * plotted for the ERF list</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author unascribed
 * @version 1.0
 */

public class ERF_EpistemicListControlPanel extends ControlPanel
implements ParameterChangeFailListener{
	
	public static final String NAME = "Epistemic List Control";
	
	private JCheckBox allCurvesCheckBox = new JCheckBox();
	private JComboBox fractileComboBox = new JComboBox();

	// static Strings to be shown in Fractile pick list
	public final static String NO_PERCENTILE = "No Fractiles";
	public final static String CUSTOM_FRACTILE = "Plot Fractiles";


	// saving the instance of caller class
	HazardCurveServerModeApplication api;
	private JCheckBox avgCheckBox = new JCheckBox();
	private JScrollPane fractileScrollPane = new JScrollPane();
	private JTextArea fractilesTextArea = new JTextArea();

	//ArrayList to store the fractile Values.
	private ArrayList<Double> fractileValues;
	private JButton updateFractileButton = new JButton();
	private GridBagLayout gridBagLayout1 = new GridBagLayout();

	private JFrame frame;
	private Component parentComponent;

	/**
	 *
	 * @param api : the calling class. It should implement the ERF_EpistemicListControlPanelAPI
	 * @param parentComponent
	 */
	public ERF_EpistemicListControlPanel(HazardCurveServerModeApplication api,
			Component parentComponent) {
		super(NAME);
		this.api = api;
		this.parentComponent = parentComponent;
	}
	
	public void doinit() {
		try {
			frame = new JFrame();
			jbInit();
			initFractileCombo();
			// show the window at center of the parent component
			this.frame.setLocation(parentComponent.getX()+parentComponent.getWidth()/2,
					parentComponent.getY()+parentComponent.getHeight()/2);
			// set the initial values in the caller
			api.setFractileOption(fractileComboBox.getSelectedItem().toString());
			api.setAverageSelected(this.avgCheckBox.isSelected());
			api.setPlotAllCurves(this.allCurvesCheckBox.isSelected());
			api.setFractileOption(fractileComboBox.getSelectedItem().toString());
		}
		catch(Exception e) {
			e.printStackTrace();
		}

		//creating the default custom fractile values list
		ArrayList defaultFractileValues = new ArrayList();
		defaultFractileValues.add(new Double(.05));
		defaultFractileValues.add(new Double(.50));
		defaultFractileValues.add(new Double(.95));
		setCustomFractileValues(defaultFractileValues);
	}
	
	private void jbInit() throws Exception {
		allCurvesCheckBox.setActionCommand("Plot all curves (in one color)");
		allCurvesCheckBox.setSelected(true);
		allCurvesCheckBox.setText("Plot all curves (in one color)");
		allCurvesCheckBox.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				allCurvesCheckBox_actionPerformed(e);
			}
		});
		this.frame.setDefaultCloseOperation(JFrame.HIDE_ON_CLOSE);
		this.frame.setTitle("Epistemic List Control");
		this.frame.getContentPane().setLayout(gridBagLayout1);
		fractileComboBox.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				fractileComboBox_actionPerformed(e);
			}
		});

		avgCheckBox.setText("Plot Average");
		avgCheckBox.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				avgCheckBox_actionPerformed(e);
			}
		});


		updateFractileButton.setText("Update Fractile List");
		updateFractileButton.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				updateFractileButton_actionPerformed(e);
			}
		});
		this.frame.getContentPane().add(fractileComboBox,  new GridBagConstraints(0, 2, 1, 1, 1.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL, new Insets(7, 11, 0, 20), 94, 0));
		this.frame.getContentPane().add(fractileScrollPane,  new GridBagConstraints(0, 3, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(14, 17, 0, 29), 214, 15));
		this.frame.getContentPane().add(updateFractileButton,  new GridBagConstraints(0, 4, 1, 1, 0.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(15, 35, 19, 45), 30, 8));
		this.frame.getContentPane().add(allCurvesCheckBox,  new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(14, 11, 0, 34), 28, 0));
		this.frame.getContentPane().add(avgCheckBox,  new GridBagConstraints(0, 1, 1, 1, 0.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(0, 11, 0, 34), 125, 0));
		fractileScrollPane.getViewport().add(fractilesTextArea, null);


		// set the size
		this.frame.setSize(new Dimension(270, 210));
	}

	/**
	 * Initialize the fractile combo box
	 */
	private void initFractileCombo() {
		fractileComboBox.addItem(NO_PERCENTILE);
		fractileComboBox.addItem(CUSTOM_FRACTILE);
	}

	/**
	 *  Shown when a Constraint error is thrown on Disaggregation ParameterEditor
	 * @param  e  Description of the Parameter
	 */
	public void parameterChangeFailed( ParameterChangeFailEvent e ) {

		StringBuffer b = new StringBuffer();
		ParameterAPI param = ( ParameterAPI ) e.getSource();

		ParameterConstraintAPI constraint = param.getConstraint();
		String oldValueStr = e.getOldValue().toString();
		String badValueStr = e.getBadValue().toString();
		String name = param.getName();


		b.append( "The value ");
		b.append( badValueStr );
		b.append( " is not permitted for '");
		b.append( name );
		b.append( "'.\n" );
		b.append( "Resetting to ");
		b.append( oldValueStr );
		b.append( ". The constraints are: \n");
		b.append( constraint.toString() );

		JOptionPane.showMessageDialog(
				this.frame, b.toString(),
				"Cannot Change Value", JOptionPane.INFORMATION_MESSAGE
		);

	}

	/**
	 * this function is called whenever user selects anything in fractile pick list
	 * @param e
	 */
	void fractileComboBox_actionPerformed(ActionEvent e) {
		String selected = fractileComboBox.getSelectedItem().toString();

		if(selected.equalsIgnoreCase(this.NO_PERCENTILE)){
			fractileScrollPane.setVisible(false);
			updateFractileButton.setVisible(false);
			// set the size
			this.frame.setSize(new Dimension(270, 210));
		}

		else if(selected.equalsIgnoreCase(CUSTOM_FRACTILE)){
			// set the size
			this.frame.setSize(new Dimension(270, 492));
			fractileScrollPane.setVisible(true);
			updateFractileButton.setVisible(true);

			//showing the fractile values( either default or user's last modified values)
			setValuesInFractileTextArea();
		}

		// update the option in the calling class also
		api.setFractileOption(selected);

	}


	/**
	 * If user wants to set the custom values for fractiles from application
	 * @param values
	 */
	public void setCustomFractileValues(ArrayList<Double> values) {
		fractileValues = values;
	}

	/**
	 * this function is called whenever check box for "plotting all curves" is selected
	 * or deselected
	 * @param e
	 */
	void allCurvesCheckBox_actionPerformed(ActionEvent e) {
		// update the value in calling class as well
		api.setPlotAllCurves(this.allCurvesCheckBox.isSelected());
	}

	/**
	 * set the average as selected/deselected in the applet as chosen by the user
	 * @param e
	 */
	void avgCheckBox_actionPerformed(ActionEvent e) {
		api.setAverageSelected(this.avgCheckBox.isSelected());
	}

	void updateFractileButton_actionPerformed(ActionEvent e) {
		boolean errorFlag = false;
		try{
			setCustomFractileValues();
			//if the user text area for the X values is empty
			if(this.fractilesTextArea.getText().trim().equalsIgnoreCase("")){
				JOptionPane.showMessageDialog(this.frame,"Must enter Fractile values","Invalid Entry",
						JOptionPane.OK_OPTION);
				errorFlag = true;
			}
		}catch(NumberFormatException ee){
			errorFlag = true;
			//if user has not entered a valid number in the textArea
			JOptionPane.showMessageDialog(this.frame,ee.getMessage(),"Invalid Entry",
					JOptionPane.OK_OPTION);
		}
		catch(RuntimeException ee){
			errorFlag = true;
			//if user has not entered a invalid Fractil value, it must be between 0 and 1
			JOptionPane.showMessageDialog(this.frame,ee.getMessage(),"Invalid Entry",
					JOptionPane.OK_OPTION);
		}


		//close the window when user has updated the fractile values list.
		if(!errorFlag)
			//this.dispose()
			frame.setVisible(false);
	}

	/**
	 * Gets the fractiles values from Text Area, filled in by user.
	 */
	private void setCustomFractileValues(){
		//getting the fractiles values filled in by the user.
		String str = fractilesTextArea.getText();
		StringTokenizer st = new StringTokenizer(str,"\n");
		fractileValues.clear();
		while(st.hasMoreTokens()){
			double fractileVal = (new Double(st.nextToken().trim())).doubleValue();
			if(fractileVal<1.0 && fractileVal>0)
				fractileValues.add(fractileVal);
			else
				throw new RuntimeException("Fractile value must  be between 0 and 1");
		}
	}

	/**
	 * shows the fractile values in the text area.
	 */
	private void setValuesInFractileTextArea(){
		String fractileVals = "";
		int size = fractileValues.size();
		for(int i=0;i<size;++i){
			fractileVals += fractileValues.get(i)+"\n";
		}
		fractilesTextArea.setText(fractileVals);
	}


	/**
	 *
	 * @returns the fractile values for fractiles needed to be calculated
	 */
	public ArrayList<Double> getSelectedFractileValues(){
		return fractileValues;
	}

	@Override
	public Window getComponent() {
		return frame;
	}

}
