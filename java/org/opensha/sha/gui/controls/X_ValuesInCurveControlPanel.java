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
import java.awt.Color;
import java.awt.Component;
import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.Window;
import java.awt.event.ActionEvent;
import java.text.DecimalFormat;
import java.util.ListIterator;
import java.util.StringTokenizer;

import javax.swing.JButton;
import javax.swing.JComboBox;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.JTextField;
import javax.swing.SwingConstants;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.sha.gui.infoTools.IMT_Info;


/**
 * <p>Title: X_ValuesInCurveControlPanel</p>
 * <p>Description: Provides the user to input his own set of X-Values for the
 * HazardCurve</p>
 * @author : Ned Field, Nitin Gupta and Vipin Gupta
 * @version 1.0
 */

public class X_ValuesInCurveControlPanel extends ControlPanel {
	
	public static final String NAME = "Set X values for Hazard Curve Calc.";

	//static Strings for the Different X Vlaues that the user can choose from.
	public final static String PEER_X_VALUES = "PEER Test-Case Values";
	public final static String USGS_PGA_X_VALUES = "USGS-2002 PGA Values";
	public final static String USGS_SA_01_AND_02_X_VALUES = "USGS-2002 SA Values for 0.1 and 0.2sec";
	public final static String USGS_SA_X_VALUES = "USGS-2002 SA 0.3,0.4,0.5 and 1.0 Values";
	public final static String CUSTOM_VALUES = "Custom Values";
	public final static String DEFAULT = "DEFAULT";
	public final static String MIN_MAX_NUM = "Enter Min, Max and Num";


	private JPanel jPanel1 = new JPanel();
	private JLabel xValuesLabel = new JLabel();
	private JScrollPane xValuesScrollPane = new JScrollPane();
	private JTextArea xValuesText = new JTextArea();

	//function containing x,y values
	ArbitrarilyDiscretizedFunc function;
	private JButton doneButton = new JButton();
	private JComboBox xValuesSelectionCombo = new JComboBox();
	private JLabel minLabel = new JLabel();
	private JLabel maxLabel = new JLabel();
	private JLabel numLabel = new JLabel();
	private JTextField minText = new JTextField();
	private JTextField maxText = new JTextField();
	private JTextField numText = new JTextField();
	private JButton setButton = new JButton();
	private GridBagLayout gridBagLayout1 = new GridBagLayout();
	private BorderLayout borderLayout1 = new BorderLayout();


	private DecimalFormat format = new DecimalFormat("0.000000##");

	//instance of the application implementing the X_ValuesInCurveControlPanelAPI
	CurveDisplayAppAPI api;

	//Stores the imt selected by the user
	private String imt;
	
	private Component parent;
	private JFrame frame;

	/**
	 * Class constructor
	 * @param parent : Takes the Application instance to get its dimensions
	 * @param api : Takes the instance of the application implementing the
	 * X_ValuesInCurveControlPanelAPI to get the IMT value from the application, to
	 * show the the default X values based on IMT selected in the application.
	 */
	public X_ValuesInCurveControlPanel(Component parent, CurveDisplayAppAPI api) {
		super(NAME);
		this.api = api;
		this.parent = parent;
		
	}
	
	public void doinit() {
		frame = new JFrame();
		imt  = api.getSelectedIMT();
		try {
			jbInit();
			// show the window at center of the parent component
			frame.setLocation(parent.getX()+parent.getWidth()/2,
					parent.getY());


		}
		catch(Exception e) {
			e.printStackTrace();
		}
		format.setMaximumFractionDigits(6);
		//initialise the function with the PEER values
		generateXValues();
	}
	
	private void jbInit() throws Exception {
		xValuesLabel.setHorizontalAlignment(SwingConstants.CENTER);
		xValuesLabel.setHorizontalTextPosition(SwingConstants.CENTER);
		doneButton.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				doneButton_actionPerformed(e);
			}
		});

		//jPanel1.setPreferredSize(new Dimension(300, 500));
		minLabel.setForeground(Color.black);
		minLabel.setText("Min :");
		maxLabel.setForeground(Color.black);
		maxLabel.setText("Max :");
		numLabel.setForeground(Color.black);
		numLabel.setText("Num :");
		setButton.setText("Set Values");
		setButton.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				setButton_actionPerformed(e);
			}
		});
		xValuesSelectionCombo.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				xValuesSelectionCombo_actionPerformed(e);
			}
		});
		frame.getContentPane().setLayout(borderLayout1);
		jPanel1.setMinimumSize(new Dimension(300, 350));
		jPanel1.setPreferredSize(new Dimension(340, 430));
		frame.setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE);
		frame.getContentPane().add(jPanel1, BorderLayout.CENTER);
		jPanel1.setLayout(gridBagLayout1);
		jPanel1.add(xValuesLabel,  new GridBagConstraints(0, 0, 3, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(6, 15, 0, 68), 7, 0));
		jPanel1.add(xValuesScrollPane,  new GridBagConstraints(0, 2, 1, 5, 1.0, 1.0
				,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(17, 28, 15, 0), 87, 400));
		jPanel1.add(xValuesSelectionCombo,  new GridBagConstraints(0, 1, 3, 1, 1.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL, new Insets(9, 15, 0, 74), 94, 0));
		xValuesScrollPane.getViewport().add(xValuesText, null);

		jPanel1.add(numLabel,  new GridBagConstraints(1, 4, 1, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(9, 35, 0, 0), 10, 9));
		jPanel1.add(minText,  new GridBagConstraints(2, 2, 1, 1, 1.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(54, 0, 0, 26), 84, 9));
		jPanel1.add(maxText,  new GridBagConstraints(2, 3, 1, 1, 1.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(11, 0, 0, 26), 84, 9));
		jPanel1.add(numText,  new GridBagConstraints(2, 4, 1, 1, 1.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.HORIZONTAL, new Insets(8, 0, 0, 26), 84, 9));
		jPanel1.add(doneButton,     new GridBagConstraints(1, 6, 2, 1, 0.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(100, 30, 20, 68), 12, 20));
		jPanel1.add(maxLabel,  new GridBagConstraints(1, 3, 1, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(12, 35, 0, 0), 13, 9));
		jPanel1.add(setButton,  new GridBagConstraints(1, 5, 2, 1, 0.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(23, 70, 0, 26), 2, 4));
		jPanel1.add(minLabel,  new GridBagConstraints(1, 2, 1, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(56, 35, 0, 0), 13, 9));

		frame.setTitle("X Values Control Panel");
		xValuesText.setBackground(Color.white);
		xValuesText.setForeground(Color.black);
		xValuesText.setLineWrap(false);
		xValuesLabel.setBackground(new Color(200, 200, 230));
		xValuesLabel.setForeground(Color.black);
		xValuesLabel.setText("X-axis (IML) Values for Hazard Curves");
		doneButton.setText("Done");
		frame.setSize(new Dimension(400, 400));
		//adding the variuos choices to the Combo Selection for the X Values
		xValuesSelectionCombo.addItem(DEFAULT);
		xValuesSelectionCombo.addItem(CUSTOM_VALUES);
		xValuesSelectionCombo.addItem(MIN_MAX_NUM);
		xValuesSelectionCombo.addItem(PEER_X_VALUES);
		xValuesSelectionCombo.addItem(USGS_PGA_X_VALUES);
		xValuesSelectionCombo.addItem(USGS_SA_01_AND_02_X_VALUES);
		xValuesSelectionCombo.addItem(USGS_SA_X_VALUES);
		xValuesSelectionCombo.setSelectedItem(DEFAULT);
	}

	/**
	 * initialises the function with the x and y values if the user has chosen the PEER X Vals
	 * the y values are modified with the values entered by the user
	 */
	private void createPEER_Function(){
		function= new ArbitrarilyDiscretizedFunc();
		function.set(.001,1);
		function.set(.01,1);
		function.set(.05,1);
		function.set(.1,1);
		function.set(.15,1);
		function.set(.2,1);
		function.set(.25,1);
		function.set(.3,1);
		function.set(.35,1);
		function.set(.4,1);
		function.set(.45,1);
		function.set(.5,1);
		function.set(.55,1);
		function.set(.6,1);
		function.set(.7,1);
		function.set(.8,1);
		function.set(.9,1);
		function.set(1.0,1);
	}


	/**
	 * initialises the function with the x and y values if the user has chosen the USGS-PGA X Vals
	 * the y values are modified with the values entered by the user
	 */
	private void createUSGS_PGA_Function(){
		function= new ArbitrarilyDiscretizedFunc();
		function.set(.005,1);
		function.set(.007,1);
		function.set(.0098,1);
		function.set(.0137,1);
		function.set(.0192,1);
		function.set(.0269,1);
		function.set(.0376,1);
		function.set(.0527,1);
		function.set(.0738,1);
		function.set(.103,1);
		function.set(.145,1);
		function.set(.203,1);
		function.set(.284,1);
		function.set(.397,1);
		function.set(.556,1);
		function.set(.778,1);
		function.set(1.09,1);
		function.set(1.52,1);
		function.set(2.13,1);
	}


	/**
	 * initialises the function with the x and y values if the user has chosen the USGS-PGA X Vals
	 * the y values are modified with the values entered by the user
	 */
	private void createUSGS_SA_01_AND_02_Function(){
		function= new ArbitrarilyDiscretizedFunc();

		function.set(.005,1);
		function.set(.0075,1);
		function.set(.0113 ,1);
		function.set(.0169,1);
		function.set(.0253,1);
		function.set(.0380,1);
		function.set(.0570,1);
		function.set(.0854,1);
		function.set(.128,1);
		function.set(.192,1);
		function.set(.288,1);
		function.set(.432,1);
		function.set(.649,1);
		function.set(.973,1);
		function.set(1.46,1);
		function.set(2.19,1);
		function.set(3.28,1);
		function.set(4.92,1);
		function.set(7.38,1);

	}

	/**
	 * initialises the function with the x and y values if the user has chosen the USGS-PGA X Vals
	 * the y values are modified with the values entered by the user
	 */
	private void createUSGS_SA_Function(){
		function= new ArbitrarilyDiscretizedFunc();

		function.set(.0025,1);
		function.set(.00375,1);
		function.set(.00563 ,1);
		function.set(.00844,1);
		function.set(.0127,1);
		function.set(.0190,1);
		function.set(.0285,1);
		function.set(.0427,1);
		function.set(.0641,1);
		function.set(.0961,1);
		function.set(.144,1);
		function.set(.216,1);
		function.set(.324,1);
		function.set(.487,1);
		function.set(.730,1);
		function.set(1.09,1);
		function.set(1.64,1);
		function.set(2.46,1);
		function.set(3.69,1);
		function.set(5.54,1);
	}

	/**
	 * initialises the function with the x and y values if the user has chosen the Min Max Num Vals.
	 * The user enters the min, max and num and using that we create the ArbitrarilyDiscretizedFunc
	 * using the log space.
	 */
	private void createFunctionFromMinMaxNum(){
		function  = new ArbitrarilyDiscretizedFunc();
		try{
			//get the min,  max and num values enter by the user.
			int numIMT_Vals = (int)Double.parseDouble(numText.getText().trim());
			double minIMT_Val = Double.parseDouble(minText.getText().trim());
			double maxIMT_Val = Double.parseDouble(maxText.getText().trim());
			if(minIMT_Val >= maxIMT_Val){
				JOptionPane.showMessageDialog(frame,"Min Val should be less than Max Val",
						"Incorrect Input",JOptionPane.ERROR_MESSAGE);
				return;
			}
			double discretizationIMT = (Math.log(maxIMT_Val) - Math.log(minIMT_Val))/(numIMT_Vals-1);
			for(int i=0; i < numIMT_Vals ;++i){
				double xVal =Double.parseDouble(format.format(Math.exp(Math.log(minIMT_Val)+i*discretizationIMT)));
				function.set(xVal,1.0);
			}


		}catch(NumberFormatException e){
			JOptionPane.showMessageDialog(frame,"Must enter a Valid Number",
					"Incorrect Input",JOptionPane.ERROR_MESSAGE);
			return;

		}catch(NullPointerException e){
			JOptionPane.showMessageDialog(frame,"Null not allowed, must enter a valid number",
					"Incorrect Input",JOptionPane.ERROR_MESSAGE);
			return;
		}

	}



	/**
	 * Sets the Control Panel to show the Defualt X values based on the selecetd IMT
	 * @param imt
	 */
	public void useDefaultX_Values(){
		xValuesSelectionCombo.setSelectedItem(DEFAULT);
		frame.repaint();
		frame.validate();
	}

	/**
	 * Shows the custom  X-Values from the application in the control Panel.
	 * @param func: ArbitrarilyDiscretizedFunc function to be shown in the control Panel
	 */
	public void setX_Values(ArbitrarilyDiscretizedFunc func){
		ListIterator lt=func.getXValuesIterator();
		xValuesSelectionCombo.setSelectedItem(CUSTOM_VALUES);
		String st =new String("");
		while(lt.hasNext())
			st += lt.next().toString().trim()+"\n";
		xValuesText.setText(st);
		frame.repaint();
		frame.validate();
	}

	/**
	 * initialise the X values with the default X values in the textArea
	 */
	private void setX_Values(){
		ListIterator lt=function.getXValuesIterator();
		String st =new String("");
		while(lt.hasNext())
			st += lt.next().toString().trim()+"\n";
		this.xValuesText.setText(st);
	}

	/**
	 *
	 * sets the  X values in ArbitrarilyDiscretizedFunc from the text area
	 */
	private void getX_Values()
	throws NumberFormatException,RuntimeException{
		function = new ArbitrarilyDiscretizedFunc();
		String str = this.xValuesText.getText();

		StringTokenizer st = new StringTokenizer(str,"\n");
		while(st.hasMoreTokens()){
			double tempX_Val=0;
			double previousTempX_Val =tempX_Val;
			try{
				tempX_Val=(new Double(st.nextToken().trim())).doubleValue();
				if(tempX_Val < previousTempX_Val)
					throw new RuntimeException("X Values must be entered in increasing  order");
			}catch(NumberFormatException e){
				throw new NumberFormatException("X Values entered must be a valid number");
			}
			function.set(tempX_Val,1);
		}
	}



	private void closeWindow(){

		int flag=0;
		try{
			//sets the X values in the ArbitrarilyDiscretizedFunc
			getX_Values();

			//if the user text area for the X values is empty
			if(xValuesText.getText().trim().equalsIgnoreCase("")){
				JOptionPane.showMessageDialog(frame,"Must enter X values","Invalid Entry",
						JOptionPane.OK_OPTION);
				flag=1;
			}
		}catch(NumberFormatException ee){
			//if user has not entered a valid number in the textArea
			JOptionPane.showMessageDialog(frame,ee.getMessage(),"Invalid Entry",
					JOptionPane.OK_OPTION);
			flag=1;
		}catch(RuntimeException eee){
			//if the user has not entered the X values in increasing order
			JOptionPane.showMessageDialog(frame,eee.getMessage(),"Invalid Entry",
					JOptionPane.OK_OPTION);
			flag=1;
		}
		//if there is no exception occured and user properly entered the X values
		if(flag==0){
			if(!xValuesSelectionCombo.getSelectedItem().equals(this.DEFAULT))
				api.setCurveXValues(function);
			else
				api.setCurveXValues();
			frame.dispose();
		}
	}


	/**
	 * Closes the window when the user is done with entering the x values.
	 * @param e
	 */
	void doneButton_actionPerformed(ActionEvent e) {
		closeWindow();
	}


	//making the GUI visible or invisible based on the selection of "Type of X-Values"
	void xValuesSelectionCombo_actionPerformed(ActionEvent e) {
		String selectedItem = (String)xValuesSelectionCombo.getSelectedItem();
		if(selectedItem.equals(PEER_X_VALUES) || selectedItem.equals(USGS_PGA_X_VALUES) ||
				selectedItem.equals(this.CUSTOM_VALUES) || selectedItem.equals(this.USGS_SA_01_AND_02_X_VALUES) ||
				selectedItem.equals(this.USGS_SA_X_VALUES)){
			maxLabel.setVisible(false);
			minLabel.setVisible(false);
			numLabel.setVisible(false);
			maxText.setVisible(false);
			minText.setVisible(false);
			numText.setVisible(false);
			setButton.setVisible(false);
			xValuesText.setEditable(false);
			if(selectedItem.equals(this.CUSTOM_VALUES))
				xValuesText.setEditable(true);
		}
		else if(selectedItem.equals(this.DEFAULT) || selectedItem.equals(this.MIN_MAX_NUM)){
			maxLabel.setVisible(true);
			minLabel.setVisible(true);
			numLabel.setVisible(true);
			maxText.setVisible(true);
			minText.setVisible(true);
			numText.setVisible(true);
			setButton.setVisible(true);
			this.xValuesText.setEditable(false);
			if(selectedItem.equals(this.DEFAULT)){
				setButton.setVisible(false);
				minText.setEditable(false);
				maxText.setEditable(false);
				numText.setEditable(false);
			}
			if(selectedItem.equals(this.MIN_MAX_NUM)){
				minText.setEditable(true);
				maxText.setEditable(true);
				numText.setEditable(true);
			}
		}
		generateXValues();
	}

	/**
	 * This function initialises the ArbitrarilyDiscretizedFunction with the X Values
	 * and Y Values based on the selection made by the user to choose the X Values.
	 */
	private void generateXValues(){
		String selectedItem = (String)xValuesSelectionCombo.getSelectedItem();
		if(selectedItem.equals(PEER_X_VALUES)){
			createPEER_Function();
			setX_Values();
		}
		else if(selectedItem.equals(USGS_PGA_X_VALUES)){
			createUSGS_PGA_Function();
			setX_Values();
		}
		else if(selectedItem.equals(USGS_SA_01_AND_02_X_VALUES)){
			this.createUSGS_SA_01_AND_02_Function();
			setX_Values();
		}
		else if(selectedItem.equals(USGS_SA_X_VALUES)){
			this.createUSGS_SA_Function();
			setX_Values();
		}
		else if(selectedItem.equals(DEFAULT)){
			//gets the selected IMT from application , is the user was working with custom
			//and then chooses the default then the IMT should be the latest one  selcetd in the application.
			imt = api.getSelectedIMT();
			minText.setText(""+IMT_Info.getMinIMT_Val(imt));
			maxText.setText(""+IMT_Info.getMaxIMT_Val(imt));
			numText.setText(""+IMT_Info.getNumIMT_Val(imt));
			IMT_Info defaultX_Vals = new IMT_Info();
			function = defaultX_Vals.getDefaultHazardCurve(imt);
			setX_Values();
		}
		else if(selectedItem.equals(this.MIN_MAX_NUM))
			xValuesText.setText("");
		else if(selectedItem.equals(this.CUSTOM_VALUES))
			xValuesText.setText("");
	}

	void setButton_actionPerformed(ActionEvent e) {
		createFunctionFromMinMaxNum();
		setX_Values();
	}

	@Override
	public Window getComponent() {
		return frame;
	}

}
