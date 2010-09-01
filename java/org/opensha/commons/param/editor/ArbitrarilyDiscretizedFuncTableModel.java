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

import java.awt.Color;
import java.awt.Dimension;
import java.text.DecimalFormat;

import javax.swing.JLabel;
import javax.swing.table.AbstractTableModel;
import javax.swing.table.DefaultTableCellRenderer;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;

public class ArbitrarilyDiscretizedFuncTableModel extends AbstractTableModel {
	
	protected boolean D = ArbitrarilyDiscretizedFuncParameterEditor.D;

	private ArbitrarilyDiscretizedFunc func;
	private boolean xEditable = true;
	
	public static DecimalFormat format;
	
	public final static Color disabledColor = new Color(210, 210, 210);
	
	ArbitrarilyDiscretizedFuncTableCellRenderer renderer = null;
	
	static {
		format = new DecimalFormat();
		format.setMaximumFractionDigits(10);
	}

	public ArbitrarilyDiscretizedFuncTableModel(ArbitrarilyDiscretizedFunc func) {
//		System.out.println("Func: " + func);
		this.func = func;
//		this.fireTableDataChanged();
	}
	
	public void updateData(ArbitrarilyDiscretizedFunc newFunc) {
		if (!areFunctionPointsEqual(func, newFunc)) {
			if (D) {
				System.out.println("Update called with new data...");
				System.out.println("Old First: " + func.getX(0) + ", " + func.getY(0));
				System.out.println("New First: " + newFunc.getX(0) + ", " + newFunc.getY(0));
			}
			this.func.clear();
			for (int i=0; i<newFunc.getNum(); i++) {
				double x = newFunc.getX(i);
				double y = newFunc.getY(i);
				func.set(x, y);
			}
			if (D) System.out.println("Update firing event");
			this.fireTableDataChanged();
		} else {
			if (D) {
				System.out.println("Update called with old data");
				System.out.println("Old First: " + func.getX(0) + ", " + func.getY(0));
				System.out.println("New First: " + newFunc.getX(0) + ", " + newFunc.getY(0));
			}
		}
		if (D) System.out.println("Update call DONE");
	}
	
	public static boolean areFunctionPointsEqual(ArbitrarilyDiscretizedFunc func1, ArbitrarilyDiscretizedFunc func2) {
		// we just care about the values here.
		
		// first make sure there's the same number of values
		int size = func1.getNum();
		if (size != func2.getNum())
			return false;
		
		for (int i=0; i<size; i++) {
			double x1 = func1.getX(i);
			double x2 = func2.getX(i);
			
			double y1 = func1.getY(i);
			double y2 = func2.getY(i);
			
			if (x1 != x2 || y1 != y2)
				return false;
		}
		
		return true;
	}
	
	public ArbitrarilyDiscretizedFunc getFunction() {
		return func;
	}

	public int getColumnCount() {
		return 2;
	}

	public void setXEditable(boolean xEditable) {
		this.xEditable = xEditable;
	}

	public int getRowCount() {
		if (func == null) {
			if (D) System.out.println("ROW COUNT ON NULL FUNC!");
			return 0;
		} else {
			int rows = func.getNum();
//			System.out.println("Row Count: " + rows);
			return rows;
		}
	}
	
	public String getColumnName(int column) {
		if (column == 0) {
			String name = func.getXAxisName();
			if (name == null || name.length() == 0)
				name = "x";
			return name;
		} else {
			String name = func.getYAxisName();
			if (name == null || name.length() == 0)
				name = "y";
			return name;
		}
	}
	
	public void removePoint(int index) {
		int indexes[] = new int[1];
		indexes[0] = index;
		this.doRemovePoints(indexes);
		this.fireTableDataChanged();
	}
	
	private void doRemovePoints(int[] indexes) {
		ArbitrarilyDiscretizedFunc old = (ArbitrarilyDiscretizedFunc)func.deepClone();
		func.clear();
		
		for (int i=0; i<old.getNum(); i++) {
			boolean match = false;
			for (int j : indexes) {
				if (i == j) {
					if (D) System.out.println("Removing point: " + i);
					match = true;
					break;
				}
			}
			if (match) {
				continue;
			} else {
				func.set(old.get(i));
			}
		}
	}
	
	public void removePoints(int[] indexes) {
		doRemovePoints(indexes);
		this.fireTableDataChanged();
	}
	
	public void addPoint(double x, double y) {
		func.set(x, y);
		this.fireTableDataChanged();
	}

	public Class<?> getColumnClass(int c) {
		if (true)
			super.getColumnClass(c);
		return Double.class;
	}

	public Object getValueAt(int rowIndex, int columnIndex) {
		if (columnIndex == 0) {
			// X
			return new Double(func.getX(rowIndex));
		} else {
			// Y
			return new Double(func.getY(rowIndex));
		}
	}

	/*
	 * Don't need to implement this method unless your table's
	 * editable.
	 */
	public boolean isCellEditable(int row, int col) {
		if (col == 0 && !xEditable)
			return false;
		return true;
	}
	
	public void setEnabled(boolean isEnabled) {
		ArbitrarilyDiscretizedFuncTableCellRenderer renderer = getRenderer();
		if (isEnabled)
			renderer.setBackground(Color.WHITE);
		else
			renderer.setBackground(disabledColor);
	}

	/**
	 *  This empty implementation is provided so users don't have to implement
	 *  this method if their data model is not editable.
	 *
	 *  @param  aValue   value to assign to cell
	 *  @param  rowIndex   row of cell
	 *  @param  columnIndex  column of cell
	 */
	public void setValueAt(Object aValue, int rowIndex, int columnIndex) {
		double val = (Double)aValue;
		if (columnIndex == 1) {
			// we're changing a Y...easy
			func.set(rowIndex, val);
		} else {
			// we're changing an X...harder
			double origY = func.getY(rowIndex);
			int indexes[] = { rowIndex };
			this.doRemovePoints(indexes);
			func.set(val, origY);
		}
		this.fireTableDataChanged();
	}

	// Based on JTable.DoubleRenderer with modifications to the formatter
	// I have to reimplement some of it because JTable.DoubleRenderer isn't visible
	class ArbitrarilyDiscretizedFuncTableCellRenderer extends DefaultTableCellRenderer.UIResource {
		
		public ArbitrarilyDiscretizedFuncTableCellRenderer() {
			super();
			setHorizontalAlignment(JLabel.RIGHT);
			this.setPreferredSize(new Dimension(20, 8));
		}
		
		
		
		public void setValue(Object value) {
			setText((value == null) ? "" : format.format(value));
		}
		
//		public Dimension getPreferredSize() {
//			return new Dimension(20, 8);
//		}
//		
//		public int getWidth() {
//			return 20;
//		}

	}
	
	public ArbitrarilyDiscretizedFuncTableCellRenderer getRenderer() {
		if (renderer == null)
			renderer = new ArbitrarilyDiscretizedFuncTableCellRenderer();
		return renderer;
	}

}
