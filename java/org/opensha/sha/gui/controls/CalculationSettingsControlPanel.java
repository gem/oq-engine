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

import javax.swing.JFrame;

import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.editor.ParameterListEditor;

/**
 * <p>Title: CalculationSettingsControlPanel</p>
 * <p>Description: This class takes the adjustable parameters from the calculators
 * like ScenarioshakeMapCalc and HazardMapCalc and show it in the control panel. </p>
 * @author : Ned Field, Nitin Gupta and Vipin  Gupta
 * @created : June 16, 2004
 * @version 1.0
 */

public class CalculationSettingsControlPanel extends ControlPanel {
	
	public static final String NAME = "Calculation Settings";

	//declaring the instance of the parameterlist and editor.
	private ParameterList paramList;
	private ParameterListEditor editor;
	private BorderLayout borderLayout1 = new BorderLayout();
	//instance of the class implementing PropagationEffectControlPanelAPI interface.
	private CalculationSettingsControlPanelAPI application;
	
	private JFrame frame;
	
	private Component parentComponent;

	/**
	 *
	 * @param api : Instance of the class using this control panel and implmenting
	 * the CalculationSettingsControlPanelAPI.
	 */
	public CalculationSettingsControlPanel(Component parentComponent,CalculationSettingsControlPanelAPI api) {
		super(NAME);
		application = api;
		this.parentComponent = parentComponent;
	}
	
	public void doinit() {
		frame = new JFrame();
		paramList = application.getCalcAdjustableParams();
		editor = new ParameterListEditor(paramList);
		try {
			// show the window at center of the parent component
			frame.setLocation(parentComponent.getX()+parentComponent.getWidth()/2,
					parentComponent.getY()+parentComponent.getHeight()/2);
			jbInit();
		}
		catch(Exception e) {
			e.printStackTrace();
		}
	}
	
	private void jbInit() throws Exception {
		frame.setSize(350,500);
		frame.setTitle("Calculation Settings");
		frame.getContentPane().setLayout(new GridBagLayout());
		frame.getContentPane().add(editor,new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(4, 4, 4, 4), 0, 0));
	}

	public Object getParameterValue(String paramName) {
		return paramList.getValue(paramName);
	}

	public ParameterList getAdjustableCalcParams() {
		return paramList;
	}

	@Override
	public Window getComponent() {
		return frame;
	}


}
