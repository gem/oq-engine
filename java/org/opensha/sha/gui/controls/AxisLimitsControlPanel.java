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

import java.awt.Color;
import java.awt.Component;
import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.Window;
import java.awt.event.ActionEvent;

import javax.swing.JButton;
import javax.swing.JComboBox;
import javax.swing.JDialog;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JTextField;

/**
 * <p>Title: AxisLimitsControlPanel</p>
 *
 * <p>Description: This Class pop up window when custom scale is selecetd for the combo box that enables the
 * user to customise the X and Y Axis scale</p>

 * @author : Nitin Gupta and Vipin Gupta
 * @version 1.0
 */

public class AxisLimitsControlPanel extends ControlPanel {
	
	public static final String NAME = "Set Axis";

	/**
	 * @todo variables
	 */
	private double minX,maxX;
	private double minY,maxY;

	private JPanel panel1 = new JPanel();
	private JLabel jLabel1 = new JLabel();
	private JTextField jTextMinX = new JTextField();
	private JLabel jLabel2 = new JLabel();
	private JTextField jTextMaxX = new JTextField();
	private JLabel jLabel3 = new JLabel();
	private JTextField jTextMinY = new JTextField();
	private JLabel jLabel4 = new JLabel();
	private JTextField jTextMaxY = new JTextField();
	private JButton ok = new JButton();
	private JButton cancel = new JButton();
	private AxisLimitsControlPanelAPI axisLimitAPI;
	private JComboBox rangeComboBox = new JComboBox();
	private JLabel jLabel5 = new JLabel();

	// Axis scale options
	public final static String AUTO_SCALE = "Auto Scale";
	public final static String CUSTOM_SCALE = "Custom Scale";
	private GridBagLayout gridBagLayout1 = new GridBagLayout();
	private GridBagLayout gridBagLayout2 = new GridBagLayout();
	
	private JDialog dialog = new JDialog();
	
	private Component parent;
	
	private String scale;

	/**
	 * Contructor which displays the window so that user can set the X and Y axis
	 * range
	 * @param axisLimitAPI : AxisLimitsControlPanelAPI needs to be implemented
	 * by all the applets which want to use this class
	 * @param component The parent component. This is the parent window on which
	 * this Axis range window will appear, center aligned
	 * @param scale : It can have value "Custom Scale" or "Auto Scale". It specifes
	 * what value to be selected initially when this panel comes up
	 * @param minX : Current minX value in the parent component
	 * @param maxX : Current maxX value in the parent component
	 * @param minY : Current minY value in the parent component
	 * @param maxY : Current maxY value in the parent component
	 */
	public AxisLimitsControlPanel(AxisLimitsControlPanelAPI axisLimitAPI,
			Component parent, String scale,
			double minX, double maxX, double minY, double maxY) {
		super(NAME);
		this.axisLimitAPI= axisLimitAPI;
		this.minX=minX;
		this.minY=minY;
		this.maxX=maxX;
		this.maxY=maxY;
		this.parent = parent;
		this.scale = scale;
	}
	
	@Override
	public void doinit() {
		dialog.setModal(true);
		// show the window at center of the parent component
		dialog.setLocation(parent.getX()+parent.getWidth()/2,
				parent.getY()+parent.getHeight()/2);
		this.rangeComboBox.addItem(AUTO_SCALE);
		this.rangeComboBox.addItem(CUSTOM_SCALE);
		try{
			jbInit();
			this.rangeComboBox.setSelectedItem(scale);
		}catch(Exception e){
			System.out.println("Error Occured while running range combo box: "+e);
		}
	}

	/**
	 * This is called whenever this window is shown again
	 * So, we need to set the params again
	 * @param scale : whether custom scale or auto scale is chosen
	 * @param minX : min X value for graph
	 * @param maxX : max X value for graph
	 * @param minY : min Y value for graph
	 * @param maxY : max Y value for graph
	 */
	public void setParams(String scale, double minX, double maxX, double minY,
			double maxY ) {
		// fill in the parameters in the window
		this.minX=minX;
		this.minY=minY;
		this.maxX=maxX;
		this.maxY=maxY;
		this.jTextMinX.setText(""+this.minX);
		this.jTextMaxX.setText(""+this.maxX);
		this.jTextMinY.setText(""+this.minY);
		this.jTextMaxY.setText(""+this.maxY);
		this.rangeComboBox.setSelectedItem(scale);
		this.scale = scale;

	}

	void jbInit() throws Exception {
		rangeComboBox.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				rangeComboBox_actionPerformed(e);
			}
		});
		panel1.setLayout(gridBagLayout1);
		dialog.setTitle("Axis Control Panel");
		panel1.add(jLabel5,  new GridBagConstraints(2, 0, 1, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(14, 0, 0, 0), 17, 11));
		panel1.add(rangeComboBox,  new GridBagConstraints(3, 0, 3, 1, 1.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL, new Insets(14, 0, 0, 67), -30, 0));
		panel1.add(jTextMinY,  new GridBagConstraints(1, 2, 2, 1, 1.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(8, 0, 0, 0), 82, 3));
		panel1.add(jTextMinX,  new GridBagConstraints(1, 1, 2, 1, 1.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(10, 0, 0, 0), 84, 3));
		panel1.add(ok,   new GridBagConstraints(4, 3, 1, 1, 0.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(0, 19, 5, 11), 0, 3));
		panel1.add(cancel,    new GridBagConstraints(5, 3, 1, 1, 0.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(0, 0, 5, 9), 10, 3));
		panel1.add(jLabel2,  new GridBagConstraints(4, 1, 1, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(11, 36, 0, 0), 17, 3));
		panel1.add(jLabel4,  new GridBagConstraints(4, 2, 1, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(10, 37, 6, 0), 15, -2));
		panel1.add(jTextMaxX,  new GridBagConstraints(5, 1, 1, 1, 1.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(10, 0, 0, 9), 72, 3));
		panel1.add(jTextMaxY,  new GridBagConstraints(5, 2, 1, 1, 1.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(0, 0, 0, 9), 72, 3));
		panel1.add(jLabel3,  new GridBagConstraints(0, 2, 1, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(12, 11, 0, 0), 14, 0));
		panel1.add(jLabel1,  new GridBagConstraints(0, 1, 2, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(11, 11, 0, 0), 26, 3));
		jLabel1.setForeground(Color.black);
		jLabel1.setText("Min X:");
		jLabel2.setForeground(Color.black);
		jLabel2.setText("Max X:");
		jLabel3.setForeground(Color.black);
		jLabel3.setText("Min Y:");
		jLabel4.setForeground(Color.black);
		jLabel4.setText("Max Y:");
		ok.setText("OK");
		ok.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				ok_actionPerformed(e);
			}
		});
		cancel.setText("Cancel");
		cancel.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				cancel_actionPerformed(e);
			}
		});
		dialog.getContentPane().setLayout(gridBagLayout2);
		panel1.setMaximumSize(new Dimension(348, 143));
		dialog.setDefaultCloseOperation(JDialog.DISPOSE_ON_CLOSE);
		dialog.setResizable(false);
		this.jTextMinX.setText(""+this.minX);
		this.jTextMaxX.setText(""+this.maxX);
		this.jTextMinY.setText(""+this.minY);
		this.jTextMaxY.setText(""+this.maxY);

		rangeComboBox.setFont(new java.awt.Font("Dialog", 1, 12));
		jLabel5.setForeground(Color.black);
		jLabel5.setText("Axis Scale:");
		dialog.getContentPane().add(panel1,  new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(1, 1, 6, 6), -49, 5));
	}


	/**
	 * This function also calls the setYRange and setXRange functions of application
	 * which sets the range of the axis based on the user input
	 *
	 * @param e= this event occur when the Ok button is clicked on the custom axis popup window
	 */
	void ok_actionPerformed(ActionEvent e) {
		String selectedRange = this.rangeComboBox.getSelectedItem().toString();
		if(selectedRange.equalsIgnoreCase(this.AUTO_SCALE)) { // if auto scale is selected
			axisLimitAPI.setAutoRange();
			dialog.dispose();
		}
		else { // if custom scale is selected
			try {
				double xMin=Double.parseDouble(this.jTextMinX.getText());
				double xMax=Double.parseDouble(this.jTextMaxX.getText());
				double yMin=Double.parseDouble(this.jTextMinY.getText());
				double yMax=Double.parseDouble(this.jTextMaxY.getText());

				// check whether xMin<=xMax and yMin<=yMax)
				if(xMin>=xMax){
					JOptionPane.showMessageDialog(dialog,new String("Max X must be greater than Min X"),new String("Check Axis Range"),JOptionPane.ERROR_MESSAGE);
					return;
				}
				if(yMin>=yMax){
					JOptionPane.showMessageDialog(dialog,new String("Max Y must be greater than Min Y"),new String("Check Axis Range"),JOptionPane.ERROR_MESSAGE);
					return;
				}
				axisLimitAPI.setAxisRange(xMin, xMax, yMin, yMax);
				dialog.dispose();
			} catch(Exception ex) {
				System.out.println("Exception:"+ex);
				JOptionPane.showMessageDialog(dialog,new String("Text Entered must be a valid numerical value"),new String("Check Axis Range"),JOptionPane.ERROR_MESSAGE);
			}
		}
	}

	/**
	 *
	 * @param e= this event occurs to destroy the popup window if the user has selected cancel option
	 */
	void cancel_actionPerformed(ActionEvent e) {
		dialog.dispose();
	}

	/**
	 * This is called when user selects "Auto scale" or "Custom scale" option
	 * @param e
	 */
	void rangeComboBox_actionPerformed(ActionEvent e) {
		String selectedRange = this.rangeComboBox.getSelectedItem().toString();
		if(selectedRange.equalsIgnoreCase(this.AUTO_SCALE)) {
			// if auto scale is selected disable the text boxes
			this.jTextMinX.setEnabled(false);
			this.jTextMaxX.setEnabled(false);
			this.jTextMinY.setEnabled(false);
			this.jTextMaxY.setEnabled(false);
		}
		else {
			// if custom scale is selected enable the text boxes
			this.jTextMinX.setEnabled(true);
			this.jTextMaxX.setEnabled(true);
			this.jTextMinY.setEnabled(true);
			this.jTextMaxY.setEnabled(true);
		}
	}

	@Override
	public Window getComponent() {
		return dialog;
	}
}
