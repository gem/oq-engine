/**
 * 
 */
package org.opensha.refFaultParamDb.gui.addEdit.deformationModel;

import java.awt.Component;
import java.awt.Point;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;

import javax.swing.JButton;
import javax.swing.JTable;
import javax.swing.table.TableCellRenderer;
import javax.swing.table.TableColumn;
import javax.swing.table.TableModel;

import org.opensha.refFaultParamDb.dao.db.DB_AccessAPI;
import org.opensha.refFaultParamDb.vo.EstimateInstances;

/**
 * @author vipingupta
 *
 */
public class DeformationModelTable extends JTable {
	private final static String SLIP_RATE = "Slip Rate";
	private final static String ASEISMIC_SLIP_FACTOR = "Aseismic Slip Factor";
	/**
	 * @param dm
	 */
	public DeformationModelTable(DB_AccessAPI dbConnection, TableModel dm) {
		super(dm);
		getTableHeader().setReorderingAllowed(false);
		getColumnModel().getColumn(1).setCellRenderer(new ButtonRenderer(SLIP_RATE));
		getColumnModel().getColumn(2).setCellRenderer(new ButtonRenderer(ASEISMIC_SLIP_FACTOR));
		addMouseListener(new MouseListener(dbConnection, this));
		// set width of first column 
		TableColumn col1 = getColumnModel().getColumn(1);
		col1.setPreferredWidth(125);
        //col1.setMinWidth(26);
        //col1.setMaxWidth(125);
        // set width of second column
        TableColumn col2 = getColumnModel().getColumn(2);
		col2.setPreferredWidth(125);
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
class MouseListener extends MouseAdapter {
	private JTable table;
	
	private DB_AccessAPI dbConnection;
	
	public MouseListener(DB_AccessAPI dbConnection, JTable table) {
		this.table = table;
		this.dbConnection = dbConnection;
	}
	
	public void mouseClicked(MouseEvent event) {
		//System.out.println("Mouse clicked");
		Point p = event.getPoint();
        int row = table.rowAtPoint(p);
        int column = table.columnAtPoint(p); // This is the view column!
        DeformationModelTableModel tableModel = (DeformationModelTableModel)table.getModel();
        int deformationModelId = tableModel.getdeformationModelId();
        int faultSectionId =  tableModel.getFaultSectionId(row);
        if(column==1) { // edit slip rate
        	EstimateInstances slipRateEst = (EstimateInstances)tableModel.getValueForSlipAndAseismicFactor(row, column);
        	new EditSlipRate(dbConnection, deformationModelId, faultSectionId, slipRateEst);
        } else if(column==2) { // edit aseismic slip factor
        	EstimateInstances aseismicSlipFactorEst = (EstimateInstances)tableModel.getValueForSlipAndAseismicFactor(row, column);
        	new EditAseismicSlipFactor(dbConnection, deformationModelId, faultSectionId, aseismicSlipFactorEst);
        }
        
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


