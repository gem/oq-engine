/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.gui;

import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.text.DecimalFormat;
import java.util.ArrayList;

import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTable;
import javax.swing.table.AbstractTableModel;

import org.opensha.sha.magdist.IncrementalMagFreqDist;

/**
 * Show the C Zones info in a table
 * @author vipingupta
 *
 */
public class C_ZoneDataPanel extends JPanel {
	private C_ZonesDataTableModel cZonesTableModel = new C_ZonesDataTableModel();
	
	public C_ZoneDataPanel() {
		this.setLayout(new GridBagLayout());
		add(new JScrollPane(new JTable(this.cZonesTableModel)),new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0
	      	      ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ));
	}
	
	public void setC_ZonesMFD_List(ArrayList<IncrementalMagFreqDist> cZonesMFD_List) {
		cZonesTableModel.setMFD_List(cZonesMFD_List);
		cZonesTableModel.fireTableDataChanged();
	}
}

/**
 * C-Zones Table Model
 * 
 * @author vipingupta
 *
 */
class C_ZonesDataTableModel extends AbstractTableModel {
	// column names
	private final static String[] columnNames = { "Name", "Rate (M>=5)", "Rate (M>=6.5)", 
		 "Moment Rate"};
	private ArrayList<IncrementalMagFreqDist> cZonesMFD_List;
	private final static DecimalFormat MOMENT_FORMAT = new DecimalFormat("0.000E0");
	private final static DecimalFormat RATE_FORMAT = new DecimalFormat("0.00000");
	
	
	/**
	 * default constructor
	 *
	 */
	public C_ZonesDataTableModel() {
		this(null);
	}
	
	/**
	 * C-Zones data
	 * @param segFaultData
	 */
	public C_ZonesDataTableModel( ArrayList<IncrementalMagFreqDist> cZonesMFD_List) {
		setMFD_List(cZonesMFD_List);
	}
	
	/**
	 * Set C-Zone data  data
	 * @param cZonesMFD_List
	 */
	public void setMFD_List(ArrayList<IncrementalMagFreqDist> cZonesMFD_List) {
		this.cZonesMFD_List = cZonesMFD_List;
	}
	
	/**
	 * Get number of columns
	 */
	public int getColumnCount() {
		return columnNames.length;
	}
	
	/**
	 * Get column name
	 */
	public String getColumnName(int index) {
		return columnNames[index];
	}
	
	/*
	 * Get number of rows
	 * (non-Javadoc)
	 * @see javax.swing.table.TableModel#getRowCount()
	 */
	public int getRowCount() {
		if(this.cZonesMFD_List==null) return 0;
		return this.cZonesMFD_List.size(); 
	}
	
	
	/**
	 * 
	 */
	public Object getValueAt (int rowIndex, int columnIndex) {
		IncrementalMagFreqDist mfd = this.cZonesMFD_List.get(rowIndex);
		switch(columnIndex) {
			case 0:
				return mfd.getName();
			case 1:
				return RATE_FORMAT.format(mfd.getCumRate(5.05));
			case 2:
				return RATE_FORMAT.format(mfd.getCumRate(6.55));
			case 3:
				return MOMENT_FORMAT.format(mfd.getTotalMomentRate());
		}
		return "";
	}
}

