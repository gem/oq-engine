/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.gui;

import javax.swing.table.AbstractTableModel;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.UCERF2;

/**
 * @author vipingupta
 * 
 * Table Mode to generate table of contribution of various types of sources at various magnitudes
 *
 */
public class ProbsTableModel extends AbstractTableModel {
	private double[] mags = { 5.0, 6.0, 6.5, 6.7, 7.0, 7.5, 8.0 };
	private String[] columns = { "Mags", "A-Faults", "B-Faults", "Non-CA B-Faults", "C-Zones", "Background", "Total"};
	private DiscretizedFuncAPI data[];
	
	public ProbsTableModel(UCERF2 ucerf2) {
		int numDataCols = columns.length-1;
		data = new DiscretizedFuncAPI[numDataCols];
		for(int i=0; i<numDataCols; ++i)
			data[i] = getDiscretizedFunc();
			
		ucerf2.getTotal_A_FaultsProb(data[0], null);
		ucerf2.getTotal_B_FaultsProb(data[1], null);
		ucerf2.getTotal_NonCA_B_FaultsProb(data[2], null);
		ucerf2.getTotal_C_ZoneProb(data[3], null);
		ucerf2.getTotal_BackgroundProb(data[4], null);
		ucerf2.getTotalProb(data[5], null);
	}
	
	private DiscretizedFuncAPI getDiscretizedFunc() {
		ArbitrarilyDiscretizedFunc func = new ArbitrarilyDiscretizedFunc();
		for(int i=0; i<mags.length; ++i) func.set(mags[i], 1.0);
		return func;
	}
	
	/**
	 * Get number of columns
	 */
	public int getColumnCount() {
		return columns.length;
	}
	
	
	/**
	 * Get column name
	 */
	public String getColumnName(int index) {
		return columns[index];
	}
	
	/*
	 * Get number of rows
	 * (non-Javadoc)
	 * @see javax.swing.table.TableModel#getRowCount()
	 */
	public int getRowCount() {
		return mags.length;
	}
	
	
	/**
	 * 
	 */
	public Object getValueAt (int rowIndex, int columnIndex) {
		double mag = mags[rowIndex];	
		switch(columnIndex) {
			case 0:
				return ""+mags[rowIndex];
			 default:
				return ""+data[columnIndex-1].getY(rowIndex);
		}
	}
}
