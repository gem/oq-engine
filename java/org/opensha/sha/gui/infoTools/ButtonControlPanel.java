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

package org.opensha.sha.gui.infoTools;

import java.awt.BorderLayout;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;

import javax.swing.BorderFactory;
import javax.swing.Box;
import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;

import org.jfree.data.Range;
import org.opensha.sha.gui.controls.AxisLimitsControlPanel;
import org.opensha.sha.gui.controls.AxisLimitsControlPanelAPI;
import org.opensha.sha.gui.controls.PlotColorAndLineTypeSelectorControlPanel;
import org.opensha.sha.gui.controls.PlotColorAndLineTypeSelectorControlPanelAPI;

/**
 * <p>Title: ButtonControlPanel</p>
 * <p>Description: This class creates a button Panel for the Applications:
 * HazardCurveApplet, HazardCurveServerModeApp and HazardSpectrum Applet</p>
 * @author : Nitin Gupta
 * @version 1.0
 */

public class ButtonControlPanel extends JPanel implements AxisLimitsControlPanelAPI,
		PlotColorAndLineTypeSelectorControlPanelAPI, PlotControllerAPI,
		ActionListener {

//	JButton button = new JButton();
//	  button.putClientProperty("JButton.buttonType", style);
//	  button.putClientProperty("JButton.segmentPosition", position);
	  


	// message string to be dispalayed if user chooses Axis Scale
	// when a plot doesn't yet exist
	private final static String AXIS_RANGE_NOT_ALLOWED =
		new String("First Choose Add Graph. Then choose Axis Scale option");


	//stores the instance of the application using this ButtonControlPanel
	ButtonControlPanelAPI application;
	
	private JPanel buttonPanel;
	private JPanel checkboxPanel;
	
	private JCheckBox jCheckylog;
	private JCheckBox jCheckxlog;
	private JButton setAxisButton;
	private JButton toggleButton;
	private JButton plotPrefsButton;

	//Axis Range control panel object (creates the instance for the AxisLimitsControl)
	private AxisLimitsControlPanel axisControlPanel;

	//Curve color scheme and its line shape control panel instance
	private PlotColorAndLineTypeSelectorControlPanel plotControl;

	//boolean to check if axis range is auto or custom
	private boolean customAxis = false;
	private int plotLabelFontSize=12, axisLabelFontSize=12, tickLabelFontSize=10;

	public ButtonControlPanel(ButtonControlPanelAPI api) {
		application = api;
		initUI();
	}
	
	private void initUI() {
		setLayout(new BorderLayout());
		setBorder(BorderFactory.createEmptyBorder(8,4,0,4));
//		setMinimumSize(new Dimension(0, 100)); TODO clean
//		setPreferredSize(new Dimension(500, 100));		
		
		plotPrefsButton = new JButton("Plot Prefs");
		plotPrefsButton.addActionListener(this);
		plotPrefsButton.putClientProperty("JButton.buttonType", "segmentedTextured");
		plotPrefsButton.putClientProperty("JButton.segmentPosition", "first");
		plotPrefsButton.putClientProperty("JComponent.sizeVariant","small");
				
		toggleButton = new JButton("Show Data");
		toggleButton.addActionListener(this);
		toggleButton.putClientProperty("JButton.buttonType", "segmentedTextured");
		toggleButton.putClientProperty("JButton.segmentPosition", "middle");
		toggleButton.putClientProperty("JComponent.sizeVariant","small");

		setAxisButton = new JButton("Set Axis");
		setAxisButton.addActionListener(this);
		setAxisButton.putClientProperty("JButton.buttonType", "segmentedTextured");
		setAxisButton.putClientProperty("JButton.segmentPosition", "last");
		setAxisButton.putClientProperty("JComponent.sizeVariant","small");

		buttonPanel = new JPanel();
		buttonPanel.setLayout(new BoxLayout(buttonPanel, BoxLayout.LINE_AXIS));
		
		buttonPanel.add(Box.createHorizontalGlue());
		buttonPanel.add(plotPrefsButton);
		buttonPanel.add(toggleButton);
		buttonPanel.add(setAxisButton);
		buttonPanel.add(Box.createHorizontalGlue());
		
		JLabel logScale  = new JLabel("Log scale: ");
		logScale.putClientProperty("JComponent.sizeVariant","small");
		
		jCheckxlog = new JCheckBox("X");
		jCheckxlog.addActionListener(this);
		jCheckxlog.putClientProperty("JComponent.sizeVariant","small");
		
		jCheckylog = new JCheckBox("Y");
		jCheckylog.addActionListener(this);
		jCheckylog.putClientProperty("JComponent.sizeVariant","small");
		
		checkboxPanel = new JPanel();
		checkboxPanel.setLayout(new BoxLayout(checkboxPanel, BoxLayout.LINE_AXIS));
		
		checkboxPanel.add(Box.createHorizontalGlue());
		checkboxPanel.add(logScale);
		checkboxPanel.add(jCheckxlog);
		checkboxPanel.add(jCheckylog);
		checkboxPanel.add(Box.createHorizontalGlue());
		
		add(buttonPanel, BorderLayout.CENTER);
		add(checkboxPanel, BorderLayout.PAGE_END);
	}


	/* implementation */
	public void actionPerformed(ActionEvent e) {
		Object src = e.getSource();
		if (src.equals(jCheckxlog)) {
			application.setX_Log(jCheckxlog.isSelected());
		} else if (src.equals(jCheckylog)) {
			application.setY_Log(jCheckylog.isSelected());
		} else if (src.equals(setAxisButton)) {
			setAxisAction();
		} else if (src.equals(toggleButton)) {
			application.togglePlot();
		} else if (src.equals(plotPrefsButton)) {
			plotPrefsAction();
		}
	}

	/**
	 * Returns the panel containing buttons so that oter items may be added.
	 * Panel has a <code>BoxLayout</code>.
	 * @return the button panel
	 */
	public JPanel getButtonRow() {
		return buttonPanel;
	}
	
	/**
	 * Returns the panel containing checkboxes so that oter items may be added.
	 * Panel has a <code>BoxLayout</code>.
	 * @return the checkbox panel
	 */
	public JPanel getCheckboxRow() {
		return checkboxPanel;
	}
	
	/**
	 * Sets the text for the toggle button.
	 * @param text to set
	 */
	public  void setToggleButtonText(String text){
		toggleButton.setText(text);
	}

	//Action method when the "Set Axis Range" button is pressed.
	private void setAxisAction() {
		Range xAxisRange = application.getX_AxisRange();
		Range yAxisRange = application.getY_AxisRange();
		if(xAxisRange==null || yAxisRange==null) {
			JOptionPane.showMessageDialog(this,AXIS_RANGE_NOT_ALLOWED);
			return;
		}

		double minX=xAxisRange.getLowerBound();
		double maxX=xAxisRange.getUpperBound();
		double minY=yAxisRange.getLowerBound();
		double maxY=yAxisRange.getUpperBound();
		if(customAxis) { // select the custom scale in the control window
			if(axisControlPanel == null) {
				axisControlPanel=new AxisLimitsControlPanel(this, this,
						AxisLimitsControlPanel.CUSTOM_SCALE, minX,maxX,minY,maxY);
			} else  axisControlPanel.setParams(AxisLimitsControlPanel.CUSTOM_SCALE,
					minX,maxX,minY,maxY);

		}
		else { // select the auto scale in the control window
			if(axisControlPanel == null)
				axisControlPanel=new AxisLimitsControlPanel(this, this,
						AxisLimitsControlPanel.AUTO_SCALE, minX,maxX,minY,maxY);
			else  axisControlPanel.setParams(AxisLimitsControlPanel.AUTO_SCALE,
					minX,maxX,minY,maxY);
		}
		if (!axisControlPanel.isInitialized())
			axisControlPanel.init();
		axisControlPanel.getComponent().pack();
		axisControlPanel.getComponent().setVisible(true);
	}


	/**
	 * plots the curves with defined color,line width and shape.
	 *
	 */
	public void plotGraphUsingPlotPreferences(){
		application.plotGraphUsingPlotPreferences();
	}

	/**
	 * sets the range for X and Y axis
	 * @param xMin : minimum value for X-axis
	 * @param xMax : maximum value for X-axis
	 * @param yMin : minimum value for Y-axis
	 * @param yMax : maximum value for Y-axis
	 *
	 */
	public void setAxisRange(double xMin,double xMax, double yMin, double yMax) {
		application.setAxisRange(xMin,xMax,yMin,yMax);
		customAxis=true;
	}

	/**
	 * set the auto range for the axis. This function is called
	 * from the AxisLimitControlPanel
	 */
	public void setAutoRange() {
		application.setAutoRange();
		customAxis = false;
	}

	/**
	 * Sets the X-Log CheckBox to be selected or deselected based on the flag
	 * @param flag
	 */
	public void setXLog(boolean flag){
		jCheckxlog.setSelected(flag);
	}
	
	public boolean isXLogSelected() {
		return jCheckxlog.isSelected();
	}

	/**
	 * Sets the Y-Log CheckBox to be selected or deselected based on the flag
	 * @param flag
	 */
	public void setYLog(boolean flag){
		jCheckylog.setSelected(flag);
	}
	
	public boolean isYLogSelected() {
		return jCheckylog.isSelected();
	}

	/**
	 * Makes all the component of this button control panel to be disabled or enable
	 * based on the boolean value of the flag
	 * @param flag
	 */
	public void setEnabled(boolean flag){
		jCheckxlog.setEnabled(flag);
		jCheckylog.setEnabled(flag);
		setAxisButton.setEnabled(flag);
		toggleButton.setEnabled(flag);
		plotPrefsButton.setEnabled(flag);
	}

	/**
	 * If button to set the plot Prefernces is "clicked" by user.
	 * @param e
	 */
	private void plotPrefsAction() {
		ArrayList plotFeatures = application.getPlottingFeatures();
		if(plotControl == null) {
			plotControl = new PlotColorAndLineTypeSelectorControlPanel(this,plotFeatures);
			plotControl.setTickLabelFontSize(this.tickLabelFontSize);
			plotControl.setPlotLabelFontSize(this.plotLabelFontSize);
			plotControl.setAxisLabelFontSize(this.axisLabelFontSize);
		}
		else
			plotControl.setPlotColorAndLineType(plotFeatures);
		plotControl.setVisible(true);
	}

	/**
	 *
	 * @returns the axis label font size
	 * Default is 12
	 */
	public int getAxisLabelFontSize(){
		if(plotControl != null)
			return plotControl.getAxisLabelFontSize();
		else
			return this.axisLabelFontSize;
			//return 24;
	}

	/**
	 *
	 * @returns the tick label font
	 * Default is 10
	 */
	public int getTickLabelFontSize(){
		if(plotControl !=null)
			return plotControl.getTickLabelFontSize();
		else
			return this.tickLabelFontSize;
			//return 20;
	}


	/**
	 *
	 * @returns the axis label font size
	 * Default is 12
	 */
	public int getPlotLabelFontSize(){
		if(plotControl != null)
			return plotControl.getPlotLabelFontSize();
		else
			return this.plotLabelFontSize;
			//return 24;

	}

	/**
	 * Set plot label font size
	 * 
	 * @param fontSize
	 */
	public void setPlotLabelFontSize(int fontSize) {
		if(plotControl != null) plotControl.setPlotLabelFontSize(fontSize);
		this.plotLabelFontSize = fontSize;
	}



	/**
	 * Set the tick label font size
	 * 
	 * @param fontSize
	 */
	public void setTickLabelFontSize(int fontSize) {
		if(plotControl != null) plotControl.setTickLabelFontSize(fontSize);
		this.tickLabelFontSize = fontSize;
	}
	
	/**
	 * Set the axis label font size
	 * 
	 * @param fontSize
	 */
	public void setAxisLabelFontSize(int fontSize) {
		if(plotControl != null) plotControl.setAxisLabelFontSize(fontSize);
		this.axisLabelFontSize = fontSize;
	}



	/**
	 * Sets the Plot Preference, button that allows users to set the color codes
	 * and curve plotting preferences.
	 * @param flag
	 */
	public void setPlotPreferencesButtonVisible(boolean flag){
		plotPrefsButton.setVisible(false);
	}

	/**
	 *
	 * @returns the X Axis Label
	 */
	public String getXAxisLabel(){
		return application.getXAxisLabel();
	}

	/**
	 *
	 * @returns Y Axis Label
	 */
	public String getYAxisLabel(){
		return application.getYAxisLabel();
	}

	/**
	 *
	 * @returns plot Title
	 */
	public String getPlotLabel(){
		return application.getPlotLabel();
	}

	/**
	 *
	 * sets  X Axis Label
	 */
	public void setXAxisLabel(String xAxisLabel){
		application.setXAxisLabel(xAxisLabel);
	}

	/**
	 *
	 * sets Y Axis Label
	 */
	public void setYAxisLabel(String yAxisLabel){
		application.setYAxisLabel(yAxisLabel);
	}

	/**
	 *
	 * sets plot Title
	 */
	public void setPlotLabel(String plotTitle){
		application.setPlotLabel(plotTitle);
	}



}
