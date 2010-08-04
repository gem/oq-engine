/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.gui;

import java.awt.Color;
import java.awt.Component;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.Point;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.TreeMap;

import javax.swing.JButton;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTable;
import javax.swing.table.AbstractTableModel;
import javax.swing.table.TableCellRenderer;
import javax.swing.table.TableModel;

import org.opensha.commons.data.function.EvenlyDiscretizedFunc;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.FaultSegmentData;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.UnsegmentedSource;
import org.opensha.sha.gui.controls.PlotColorAndLineTypeSelectorControlPanel;
import org.opensha.sha.gui.infoTools.GraphWindow;
import org.opensha.sha.gui.infoTools.GraphWindowAPI;
import org.opensha.sha.gui.infoTools.PlotCurveCharacterstics;
import org.opensha.sha.magdist.IncrementalMagFreqDist;


/**
 * 
 * Show the B faults info in the table
 *  
 * @author vipingupta
 *
 */
public class B_FaultDataPanel extends JPanel {
	private B_FaultDataTableModel bFaultTableModel = new B_FaultDataTableModel();
	
	public B_FaultDataPanel() {
		this.setLayout(new GridBagLayout());
		add(new JScrollPane(new B_Faults_Table(this.bFaultTableModel)),new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0
	      	      ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ));
	}
	
	public void setB_FaultSources(ArrayList bFaultSources) {
		bFaultTableModel.setUnsegmentedSourceList(bFaultSources);
		bFaultTableModel.fireTableDataChanged();
	}
}


/**
 * Segment Table Model
 * 
 * @author vipingupta
 *
 */
class B_FaultDataTableModel extends AbstractTableModel {
	// column names
	private final static String[] columnNames = { "Name", "Mag", "Tot Rate", "Tot Prob",
		"Prob (M>=6.7)", "Slip Rate (mm/yr)", "Area (sq-km)",
		"Length (km)", "Moment Rate", "Ave Aseismicity", "Mag Freq Dist"};
	private ArrayList unsegmentedSourceList;
	private final static DecimalFormat SLIP_RATE_FORMAT = new DecimalFormat("0.#####");
	private final static DecimalFormat AREA_LENGTH_FORMAT = new DecimalFormat("0.#");
	private final static DecimalFormat MOMENT_FORMAT = new DecimalFormat("0.000E0");
	private final static DecimalFormat MAG_FORMAT = new DecimalFormat("0.00");
	private final static DecimalFormat RATE_FORMAT = new DecimalFormat("0.00000");
	private final static DecimalFormat ASEISMSIC_FORMAT = new DecimalFormat("0.00");
	
	
	/**
	 * default constructor
	 *
	 */
	public B_FaultDataTableModel() {
		this(null);
	}
	
	/**
	 * B-fault Fault data
	 * @param segFaultData
	 */
	public B_FaultDataTableModel( ArrayList unsegmentedSourceList) {
		setUnsegmentedSourceList(unsegmentedSourceList);
	}
	
	/**
	 * Set the B-fault fault data
	 * @param segFaultData
	 */
	public void setUnsegmentedSourceList(ArrayList unsegmentedSourceList) {
		if(unsegmentedSourceList==null) {
			this.unsegmentedSourceList = null;
		} else {
			TreeMap map = new TreeMap();
			for(int i=0; i<unsegmentedSourceList.size(); ++i) {
				UnsegmentedSource source = (UnsegmentedSource)unsegmentedSourceList.get(i);
				map.put(source.getFaultSegmentData().getFaultName(), source);
			}
			this.unsegmentedSourceList =   new ArrayList(map.values());
		}
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
		if(this.unsegmentedSourceList==null) return 0;
		return this.unsegmentedSourceList.size(); 
	}
	
	
	/**
	 * 
	 */
	public Object getValueAt (int rowIndex, int columnIndex) {
		if(this.unsegmentedSourceList==null) return "";
		UnsegmentedSource source = (UnsegmentedSource)unsegmentedSourceList.get(rowIndex);
		FaultSegmentData faultSegmentData = source.getFaultSegmentData();
		//{ "Name", "Mag", "Tot Rate","Slip Rate (mm/yr)", "Area (sq-km)",
		//	"Length (km)", "Moment Rate", "Ave Aseismicity"};
		switch(columnIndex) {
			case 0:
				return faultSegmentData.getFaultName();
			case 1:
				return MAG_FORMAT.format(source.getSourceMag());
			case 2:
				return ""+(float)source.getMagFreqDist().getTotalIncrRate();
			case 3:
				return ""+(float)source.computeTotalProbAbove(6.7);
			case 4:
				return ""+(float)source.computeTotalProb();
			case 5: 
				// convert to mm/yr
				return SLIP_RATE_FORMAT.format(faultSegmentData.getTotalAveSlipRate()*1e3);
			case 6:
				// convert to sq km
				return AREA_LENGTH_FORMAT.format(faultSegmentData.getTotalArea()/1e6);
			case 7:
				// convert to km
				return AREA_LENGTH_FORMAT.format(faultSegmentData.getTotalLength()/1e3);
			case 8:
				return MOMENT_FORMAT.format(source.getMomentRate());
			case 9:
				return ASEISMSIC_FORMAT.format(faultSegmentData.getTotalAveAseismicityFactor());
			case 10:
				ArrayList funcs = new ArrayList();
				IncrementalMagFreqDist magFreqDist1 = source.getMagFreqDist();
				magFreqDist1.setName("Mag Freq Dist");
				EvenlyDiscretizedFunc cumFreqDist1 = magFreqDist1.getCumRateDistWithOffset();
				cumFreqDist1.setName("Cumulative Mag Freq Dist");
				funcs.add(magFreqDist1);
				funcs.add(cumFreqDist1);
				
				IncrementalMagFreqDist magFreqDist2 = source.getVisibleSourceMagFreqDist();
				magFreqDist2.setName("Visible Mag Freq Dist (Dashed Lines)");
				EvenlyDiscretizedFunc cumFreqDist2 = magFreqDist2.getCumRateDistWithOffset();
				cumFreqDist2.setName("Visible Cumulative Mag Freq Dist (Dashed Lines)");
				funcs.add(magFreqDist2);
				funcs.add(cumFreqDist2);
				return funcs;
		}
		return "";
	}
}




/**
* @author vipingupta
*
*/
class B_Faults_Table extends JTable {
	private final static String MFD = "Mag Freq Dist";
	/**
	 * @param dm
	 */
	public B_Faults_Table(TableModel dm) {
		super(dm);
		setColumnSelectionAllowed(true);
		getColumnModel().getColumn(10).setCellRenderer(new ButtonRenderer(MFD));
		addMouseListener(new MouseListener(this));
		// set width of first column 
		//TableColumn col1 = getColumnModel().getColumn(1);
		//col1.setPreferredWidth(125);
       //col1.setMinWidth(26);
       //col1.setMaxWidth(125);
       // set width of second column
       //TableColumn col2 = getColumnModel().getColumn(2);
		//col2.setPreferredWidth(125);
       //col2.setMinWidth(26);
       //col2.setMaxWidth(125);
	}	
}



/**
 * It handles the clicking whenever user clicks on JTable
 * 
 * @author vipingupta
 *
 */
class MouseListener extends MouseAdapter  implements GraphWindowAPI {
	private JTable table;
	private ArrayList funcs;
	//	 SOLID LINES
	protected final PlotCurveCharacterstics PLOT_CHAR1 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
		      Color.BLUE, 2);
	protected final PlotCurveCharacterstics PLOT_CHAR2 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
		      Color.RED, 2);
	// dashed lines
	protected final PlotCurveCharacterstics PLOT_CHAR3 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.DASHED_LINE,
		      Color.BLUE, 2);
	protected final PlotCurveCharacterstics PLOT_CHAR4 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.DASHED_LINE,
		      Color.RED, 2);
	

	
	public MouseListener(JTable table) {
		this.table = table;
	}
	
	public void mouseClicked(MouseEvent event) {
		//System.out.println("Mouse clicked");
		Point p = event.getPoint();
        int row = table.rowAtPoint(p);
        int column = table.columnAtPoint(p); // This is the view column!
        TableModel tableModel = table.getModel();
        if(column==10) { // edit slip rate
        	funcs = (ArrayList)tableModel.getValueAt(row, column);
        	GraphWindow graphWindow= new GraphWindow(this);
    	    graphWindow.setPlotLabel("Mag Rate");
    	    graphWindow.plotGraphUsingPlotPreferences();
    	    //graphWindow.pack();
    	    graphWindow.setVisible(true);;
        }
	}
	
	
	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getCurveFunctionList()
	 */
	public ArrayList getCurveFunctionList() {
		return funcs;
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getXLog()
	 */
	public boolean getXLog() {
		return false;
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getYLog()
	 */
	public boolean getYLog() {
		return false;
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getXAxisLabel()
	 */
	public String getXAxisLabel() {
		return "Mag";
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getYAxisLabel()
	 */
	public String getYAxisLabel() {
		return "Rate";
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getPlottingFeatures()
	 */
	public ArrayList getPlottingFeatures() {
		 ArrayList list = new ArrayList();
		 list.add(this.PLOT_CHAR1);
		 list.add(this.PLOT_CHAR2);
		 list.add(this.PLOT_CHAR3);
		 list.add(this.PLOT_CHAR4);
		 return list;
	}
	

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#isCustomAxis()
	 */
	public boolean isCustomAxis() {
		return false;
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getMinX()
	 */
	public double getMinX() {
		throw new UnsupportedOperationException("Method not implemented yet");
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getMaxX()
	 */
	public double getMaxX() {
		throw new UnsupportedOperationException("Method not implemented yet");
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getMinY()
	 */
	public double getMinY() {
		throw new UnsupportedOperationException("Method not implemented yet");
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getMaxY()
	 */
	public double getMaxY() {
		throw new UnsupportedOperationException("Method not implemented yet");
	}

}	

class ButtonRenderer extends JButton implements TableCellRenderer {

	  public ButtonRenderer(String text) {
	    setText(text);
	  }

	  public Component getTableCellRendererComponent(JTable table, Object value,
	      boolean isSelected, boolean hasFocus, int row, int column) {
	    return this;
	  }
	}


