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
import java.awt.Font;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.Window;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.StringTokenizer;

import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;

/**
 * <p>Title: XY_ValuesControlPanel</p>
 *
 * <p>Description: This class allows user to enter X and Y values.
 * Each line represents one XY value and each XY value should be space seperated.</p>
 *
 * @author :Nitin Gupta
 * @version 1.0
 */
public class XY_ValuesControlPanel
extends ControlPanel {
	
	public static final String NAME = "Set external XY dataset";

	JPanel jPanel1 = new JPanel();
	BorderLayout borderLayout1 = new BorderLayout();
	JScrollPane xyDatasetScrollPane = new JScrollPane();
	JLabel jLabel1 = new JLabel();
	JTextArea xyDatasetText = new JTextArea();
	JTextArea metadataText = new JTextArea();
	JLabel jLabel2 = new JLabel();
	JScrollPane metadataScrollPane = new JScrollPane();
	JButton okButton = new JButton();
	JButton cancelButton = new JButton();
	//instance of the aplication using this control panel.
	CurveDisplayAppAPI application;
	private GridBagLayout gridBagLayout1 = new GridBagLayout();
	
	private JFrame frame;
	private Component parent;

	public XY_ValuesControlPanel(Component parent, CurveDisplayAppAPI api) {
		super(NAME);
		application = api;
		this.parent = parent;
	}
	
	public void doinit() {
		frame = new JFrame();
		try {
			jbInit();
		}
		catch (Exception exception) {
			exception.printStackTrace();
		}
		frame.pack();
		// show the window at center of the parent component
		frame.setLocation(parent.getX()+parent.getWidth()/2,
				parent.getY());
	}

	private void jbInit() throws Exception {
		frame.getContentPane().setLayout(borderLayout1);
		cancelButton.addActionListener(new
				XY_ValuesControlPanel_cancelButton_actionAdapter(this));
		okButton.addActionListener(new XY_ValuesControlPanel_okButton_actionAdapter(this));
		frame.setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE);
		frame.getContentPane().add(jPanel1, java.awt.BorderLayout.CENTER);
		jLabel1.setFont(new java.awt.Font("Arial", Font.BOLD, 16));
		jLabel1.setText("Enter XY Dataset:");
		jLabel2.setFont(new java.awt.Font("Arial", Font.BOLD, 16));
		jLabel2.setText("Enter Metadata:");
		okButton.setText("OK");
		cancelButton.setText("Cancel");
		xyDatasetScrollPane.getViewport().add(xyDatasetText);
		metadataScrollPane.getViewport().add(metadataText);
		jPanel1.setLayout(gridBagLayout1);
		jPanel1.add(xyDatasetScrollPane,  new GridBagConstraints(0, 1, 2, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(0, 38, 0, 105), 185, 331));
		jPanel1.add(jLabel1,  new GridBagConstraints(0, 0, 2, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(28, 38, 0, 107), 66, 16));
		jPanel1.add(jLabel2,  new GridBagConstraints(0, 2, 2, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(20, 38, 0, 120), 68, 19));
		jPanel1.add(metadataScrollPane,  new GridBagConstraints(0, 3, 2, 1, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(0, 38, 0, 20), 270, 136));
		jPanel1.add(cancelButton,  new GridBagConstraints(1, 4, 1, 1, 0.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(12, 34, 18, 34), 19, 1));
		jPanel1.add(okButton,  new GridBagConstraints(0, 4, 1, 1, 0.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(12, 64, 18, 0), 19, 1));
		frame.setSize(new Dimension(250, 500));
		frame.setTitle("New Dataset Control Panel");
	}

	public void cancelButton_actionPerformed(ActionEvent actionEvent) {
		frame.dispose();
	}

	public void okButton_actionPerformed(ActionEvent actionEvent) {
		try{
			application.addCurve(getX_Values());
			frame.dispose();
		}catch(NumberFormatException ex){
			JOptionPane.showMessageDialog(frame,ex.getMessage(),"Error",JOptionPane.ERROR_MESSAGE);
			return;
		}
		catch(RuntimeException ex){
			JOptionPane.showMessageDialog(frame,ex.getMessage(),"Error",JOptionPane.ERROR_MESSAGE);
			return;
		}
	}


	/**
	 *
	 * sets the  XY dataset values in ArbitrarilyDiscretizedFunc from the text area
	 */
	private ArbitrarilyDiscretizedFunc getX_Values()
	throws NumberFormatException,RuntimeException{
		ArbitrarilyDiscretizedFunc function = new ArbitrarilyDiscretizedFunc();
		String str = xyDatasetText.getText();
		StringTokenizer st = new StringTokenizer(str,"\n");
		while(st.hasMoreTokens()){

			StringTokenizer st1 = new StringTokenizer(st.nextToken());
			int numVals = st1.countTokens();
			if(numVals !=2)
				throw new RuntimeException("Each line should have just one X and "+
				"one Y value, which are space seperated");
			double tempX_Val=0;
			double tempY_Val=0;
			try{
				tempX_Val = Double.parseDouble(st1.nextToken());
				tempY_Val = Double.parseDouble(st1.nextToken());
			}catch(NumberFormatException e){
				throw new NumberFormatException("X and Y Values entered must be valid numbers");
			}
			function.set(tempX_Val,tempY_Val);
		}
		function.setName("(manually entered XY data)");
		String metadata = metadataText.getText();
		if(metadata == null || metadata.equals(""))
			function.setInfo(" ");
		else
			function.setInfo(metadata);
		return function;
	}

	@Override
	public Window getComponent() {
		return frame;
	}
}

class XY_ValuesControlPanel_okButton_actionAdapter
implements ActionListener {
	private XY_ValuesControlPanel adaptee;
	XY_ValuesControlPanel_okButton_actionAdapter(XY_ValuesControlPanel adaptee) {
		this.adaptee = adaptee;
	}

	public void actionPerformed(ActionEvent actionEvent) {
		adaptee.okButton_actionPerformed(actionEvent);
	}
}

class XY_ValuesControlPanel_cancelButton_actionAdapter
implements ActionListener {
	private XY_ValuesControlPanel adaptee;
	XY_ValuesControlPanel_cancelButton_actionAdapter(XY_ValuesControlPanel
			adaptee) {
		this.adaptee = adaptee;
	}

	public void actionPerformed(ActionEvent actionEvent) {
		adaptee.cancelButton_actionPerformed(actionEvent);
	}
}
