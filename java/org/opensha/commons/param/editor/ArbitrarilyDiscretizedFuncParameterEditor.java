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

package org.opensha.commons.param.editor;

import java.awt.BorderLayout;
import java.awt.Dimension;
import java.awt.HeadlessException;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.FocusEvent;

import javax.swing.BorderFactory;
import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTable;
import javax.swing.JTextField;
import javax.swing.SwingConstants;
import javax.swing.border.TitledBorder;
import javax.swing.event.DocumentEvent;
import javax.swing.event.DocumentListener;
import javax.swing.event.TableModelEvent;
import javax.swing.event.TableModelListener;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.exceptions.DataPoint2DException;
import org.opensha.commons.param.ArbitrarilyDiscretizedFuncParameter;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.editor.ArbitrarilyDiscretizedFuncTableModel.ArbitrarilyDiscretizedFuncTableCellRenderer;

/**
 * <b>Title:</b> ArbitrarilyDiscretizedFuncParameterEditor<p>
 *
 * <b>Description:</b> Subclass of ParameterEditor for editing ArbitrarilyDiscretizedFunc.
 * The widget is a JTextArea which allows X and Y values to be filled in.  <p>
 *
 * @author Vipin Gupta, Nitin Gupta
 * @version 1.0
 */
public class ArbitrarilyDiscretizedFuncParameterEditor extends ParameterEditor implements ActionListener, DocumentListener, TableModelListener
{

	/** Class name for debugging. */
	protected final static String C = "DiscretizedFuncParameterEditor";
	/** If true print out debug statements. */
	protected final static boolean D = false;
	
	private ArbitrarilyDiscretizedFuncTableModel tableModel;
	private JTable table;
	
	private JButton addButton;
	private JButton removeButton;
	
	private JTextField xField;
	private JTextField yField;
	
	boolean xDataGood;
	boolean yDataGood;

	private boolean isFocusListenerForX = false;
	
	private ArbitrarilyDiscretizedFuncTableCellRenderer renderer;

	/** No-Arg constructor calls parent constructor */
	public ArbitrarilyDiscretizedFuncParameterEditor() {
		super();
	}

	/**
	 * Constructor that sets the parameter that it edits. An
	 * Exception is thrown if the model is not an DiscretizedFuncParameter <p>
	 */
	public ArbitrarilyDiscretizedFuncParameterEditor(ParameterAPI model) throws Exception {

		super(model);
		String S = C + ": Constructor(model): ";
		if(D) System.out.println(S + "Starting");

//		this.setParameter(model);
		if(D) System.out.println(S.concat("Ending"));

	}

	/**
	 * Whether you want the user to be able to type in the X values
	 * @param isEnabled
	 */
	public void setXEnabled(boolean isEnabled) {
		// TODO: fix
		//      this.xValsTextArea.setEnabled(isEnabled);
	}

	/** This is where the JTextArea is defined and configured. */
	protected void addWidget() {

		String S = C + ": addWidget(): ";
		if(D) System.out.println(S + "Starting");

		// set the value in ArbitrarilyDiscretizedFunc
		ArbitrarilyDiscretizedFunc function = (ArbitrarilyDiscretizedFunc)model.getValue();

		JPanel buttonPanel = new JPanel(new BorderLayout());
		JPanel leftButtonPanel = new JPanel();
		leftButtonPanel.setLayout(new BoxLayout(leftButtonPanel, BoxLayout.X_AXIS));
		
		if (addButton == null) {
			addButton = new JButton("+");
			addButton.addActionListener(this);
			addButton.setEnabled(false);
		}
		if (removeButton == null) {
			removeButton = new JButton("-");
			removeButton.addActionListener(this);
		}
		if (xField == null) {
			xField = new JTextField();
//			xField.addFocusListener(focusListener);
			xField.getDocument().addDocumentListener(this);
			xField.setColumns(4);
			xDataGood = false;
		}
		if (yField == null) {
			yField = new JTextField();
//			yField.addFocusListener(focusListener);
			yField.getDocument().addDocumentListener(this);
			yField.setColumns(4);
			yDataGood = false;
		}
		leftButtonPanel.add(new JLabel("x: "));
		leftButtonPanel.add(xField);
		leftButtonPanel.add(new JLabel("y: "));
		leftButtonPanel.add(yField);
		leftButtonPanel.add(addButton);
		
		buttonPanel.add(leftButtonPanel, BorderLayout.WEST);
		buttonPanel.add(removeButton, BorderLayout.EAST);
		
		tableModel = new ArbitrarilyDiscretizedFuncTableModel(function);
		table = new JTable(tableModel);
		tableModel.addTableModelListener(this);
//		table.setDefaultEditor(Double.class, new ArbitrarilyDiscretizedFuncTableCellEditor());
		renderer = tableModel.getRenderer();
		table.setDefaultRenderer(Double.class, renderer);
		
		JScrollPane scroll = new JScrollPane(table);
		scroll.setPreferredSize(new Dimension(100, 200));

		widgetPanel.setLayout(new BorderLayout());
		widgetPanel.add(scroll, BorderLayout.CENTER);
		widgetPanel.add(buttonPanel, BorderLayout.SOUTH);

		widgetPanel.setBackground(null);
		widgetPanel.validate();
		widgetPanel.repaint();
		if(D) System.out.println(S + "Ending");
	}


	/**
	 * Main GUI Initialization point. This block of code is updated by JBuilder
	 * when using it's GUI Editor.
	 */
	protected void jbInit() throws Exception {

		// Main component
		titledBorder1 = new TitledBorder(BorderFactory.createLineBorder(FORE_COLOR,1),"");
		titledBorder1.setTitleColor(FORE_COLOR);
		titledBorder1.setTitleFont(DEFAULT_LABEL_FONT);
		titledBorder1.setTitle("Parameter Name");
		border1 = BorderFactory.createCompoundBorder(titledBorder1,BorderFactory.createEmptyBorder(0,0,3,0));
		this.setLayout( GBL );


		// Outermost panel
		outerPanel.setLayout( GBL );
		outerPanel.setBorder(border1);

		// widgetPanel panel init
		//widgetPanel.setBackground( BACK_COLOR );
		widgetPanel.setMinimumSize( WIGET_PANEL_DIM );
		widgetPanel.setPreferredSize( null );


		// nameLabel panel init
		//nameLabel.setBackground( BACK_COLOR );
		nameLabel.setMaximumSize( LABEL_DIM );
		nameLabel.setMinimumSize( LABEL_DIM );
		nameLabel.setPreferredSize( LABEL_DIM );
		nameLabel.setHorizontalAlignment( SwingConstants.LEFT );
		nameLabel.setHorizontalTextPosition( SwingConstants.LEFT );
		nameLabel.setText( LABEL_TEXT );
		nameLabel.setFont( DEFAULT_LABEL_FONT );
		outerPanel.add( widgetPanel, WIDGET_PANEL_GBC );

		this.add( outerPanel, OUTER_PANEL_GBC );

	}





	/**
	 * Called when the user clicks on another area of the GUI outside
	 * this editor panel. This synchornizes the editor text field
	 * value to the internal parameter reference.
	 */
	public void focusLost(FocusEvent e) throws ConstraintException {

		String S = C + ": focusLost(): ";
		if(D) System.out.println(S + "Starting");

		super.focusLost(e);

		focusLostProcessing = false;
		if( keyTypeProcessing == true ) return;
		focusLostProcessing = true;
		setValueInParameter();
		if(!isFocusListenerForX)  {
			// TODO: fix this
			//        	xValsTextArea.addFocusListener(this);
			isFocusListenerForX = true;
		}
		focusLostProcessing = false;
		if(D) System.out.println(S + "Ending");
	}

	private void setValueInParameter() throws DataPoint2DException,
	HeadlessException, NumberFormatException {
		// TODO: fix this
		//      String xValsStr = this.xValsTextArea.getText();
		//      String yValsStr = this.yValsTextArea.getText();
		//
		//      // set the value in ArbitrarilyDiscretizedFunc
		//      ArbitrarilyDiscretizedFunc function = (ArbitrarilyDiscretizedFunc)model.getValue();
		//      function.clear();
		//      StringTokenizer xStringTokenizer = new StringTokenizer(xValsStr,"\n");
		//      StringTokenizer yStringTokenizer = new StringTokenizer(yValsStr,"\n");
		//
		//
		//      while(xStringTokenizer.hasMoreTokens()){
		//        double tempX_Val=0;
		//        double tempY_Val=0;
		//        try{
		//          tempX_Val = Double.parseDouble(xStringTokenizer.nextToken());
		//          tempY_Val = Double.parseDouble(yStringTokenizer.nextToken());
		//        }catch(Exception ex){
		//          JOptionPane.showMessageDialog(this, XY_VALID_MSG);
		//          return;
		//        }
		//        function.set(tempX_Val,tempY_Val);
		//      }
		//
		//      if(yStringTokenizer.hasMoreTokens()) {
		//        JOptionPane.showMessageDialog(this, ONE_XY_VAL_MSG);
		//      }
		refreshParamEditor();
	}

	/** Sets the parameter to be edited. */
	public void setParameter(ParameterAPI model) {
		String S = C + ": setParameter(): ";
		// TODO: fix this
		if(D) System.out.println(S.concat("Starting"));
		if ( (model != null ) && !(model instanceof ArbitrarilyDiscretizedFuncParameter))
			throw new RuntimeException( S + "Input model parameter must be a DiscretizedFuncParameter.");
		super.setParameter(model);
		//        xValsTextArea.setToolTipText("No Constraints");
		//        yValsTextArea.setToolTipText("No Constraints");
		//
		//        String info = model.getInfo();
		//        if( (info != null ) && !( info.equals("") ) ){
		//            this.nameLabel.setToolTipText( info );
		//        }
		//        else this.nameLabel.setToolTipText( null);
		if(D) System.out.println(S.concat("Ending"));
	}

	/**
	 * Updates the JTextArea string with the parameter value. Used when
	 * the parameter is set for the first time, or changed by a background
	 * process independently of the GUI. This could occur with a ParameterChangeFail
	 * event.
	 */
	public void refreshParamEditor(){
		ArbitrarilyDiscretizedFunc func = (ArbitrarilyDiscretizedFunc)model.getValue();
		if (D) System.out.println("Refresh param..");
		if ( func != null ) { // show X, Y values from the function
			this.tableModel.updateData(func);
		}
		else {
			if (D) System.out.println("refreshParamEditor: func is null!");
			this.tableModel.updateData(new ArbitrarilyDiscretizedFunc());
		}
		if (D) System.out.println("Refrash param DONE");
		this.repaint();
	}

	/**
	 * It enables/disables the editor according to whether user is allowed to
	 * fill in the values.
	 */
	public void setEnabled(boolean isEnabled) {
		// TODO: fix this
//		this.xValsTextArea.setEnabled(isEnabled);
//		this.yValsTextArea.setEnabled(isEnabled);
		
		this.table.setEnabled(isEnabled);
		this.tableModel.setEnabled(isEnabled);
		this.addButton.setEnabled(isEnabled);
		this.removeButton.setEnabled(isEnabled);
		
//		super.setEnabled(isEnabled);
	}

	public void actionPerformed(ActionEvent e) {
		if (e.getSource() == addButton) {
			// add
			if (D) System.out.print("Adding...");
			double x = Double.parseDouble(xField.getText());
			double y = Double.parseDouble(yField.getText());
			if (D) System.out.println(" " + x + ", " + y);
			tableModel.addPoint(x, y);
		} else if (e.getSource() == removeButton) {
			if (D) System.out.println("Removing...");
			int selected[] = table.getSelectedRows();
			if (selected.length > 0)
				tableModel.removePoints(selected);
		}
	}

	public void changedUpdate(DocumentEvent e) {
		validateAddInput();
	}

	public void insertUpdate(DocumentEvent e) {
		validateAddInput();
	}

	public void removeUpdate(DocumentEvent e) {
		validateAddInput();
	}
	
	private void validateAddInput() {
		if (D) System.out.print("Validating..._");
		try {
			if (D) System.out.print(xField.getText() + "_");
			Double x = Double.parseDouble(xField.getText());
			if (D) System.out.print(yField.getText());
			Double y = Double.parseDouble(yField.getText());
			boolean bad = x.isNaN() || y.isNaN() || x.isInfinite() || y.isInfinite();
			if (D) {
				if (bad)
					System.out.println("_NaN/Inf!");
				else
					System.out.println("_GOOD!");
			}
			addButton.setEnabled(!bad);
		} catch (NumberFormatException e1) {
			if (D) System.out.println("_BAD!");
			addButton.setEnabled(false);
		}
	}

	public void tableChanged(TableModelEvent e) {
		if (D) System.out.println("Table event...");
		this.model.setValue(tableModel.getFunction().deepClone());
		if (D) System.out.println("Table event DONE");
	}

//	@Override
//	public void keyTyped(KeyEvent e) {
//		if (e.getSource() == xField || e.getSource() == yField) {
//			System.out.print("Validating...");
//			try {
//				System.out.print(xField.getText() + "_");
//				Double.parseDouble(xField.getText());
//				System.out.print(yField.getText());
//				Double.parseDouble(yField.getText());
//				System.out.println("GOOD!");
//				addButton.setEnabled(true);
//			} catch (NumberFormatException e1) {
//				System.out.println("BAD!");
//				addButton.setEnabled(false);
//			}
//		} else {
//			super.keyTyped(e);
//		}
//	}
	
	public static void main(String args[]) throws Exception {
		JFrame frame = new JFrame();
		
		ArbitrarilyDiscretizedFunc func = new ArbitrarilyDiscretizedFunc();
		func.set(0.1, 5.5);
		func.set(0.2, 90.5);
		func.set(0.4, 2.5);
		func.set(0.8, 1.5);
		
		ArbitrarilyDiscretizedFuncParameter param = new ArbitrarilyDiscretizedFuncParameter("Param", func);
		
		ArbitrarilyDiscretizedFuncParameterEditor editor = new ArbitrarilyDiscretizedFuncParameterEditor(param);
		
		frame.setSize(500, 500);
		frame.setContentPane(editor);
		frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		frame.setVisible(true);
		editor.validate();
		editor.refreshParamEditor();
	}
}
