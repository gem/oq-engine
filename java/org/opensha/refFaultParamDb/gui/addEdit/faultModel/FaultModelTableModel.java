/**
 * 
 */
package org.opensha.refFaultParamDb.gui.addEdit.faultModel;

import java.util.ArrayList;
import java.util.HashMap;

import javax.swing.table.DefaultTableModel;

import org.opensha.refFaultParamDb.gui.infotools.SessionInfo;
import org.opensha.refFaultParamDb.vo.FaultSectionSummary;

/**
 *
 * This table model allows to view the fault sections within a fault model
 * 
 * @author vipingupta
 *
 */
public class FaultModelTableModel extends DefaultTableModel {
    private ArrayList faultSectionsList = new ArrayList();
    private final static String []columnNames = { "Include/Exclude","Info", "Section Name" };
    private Boolean isSelectedRow[];
    private static final long serialVersionUID = 1L;
    private HashMap sectionId_RowIdMapping = new HashMap();

	/**
     * Constructs a new, empty <code>FaultDataModel</code>.
     */
    public FaultModelTableModel(ArrayList  faultSectionsList) {
    	this.faultSectionsList = faultSectionsList;
    	isSelectedRow = new Boolean[faultSectionsList.size()];
    	for(int i=0; i<isSelectedRow.length; ++i)  {
    		isSelectedRow[i] = new Boolean(false);
    		FaultSectionSummary faultSectionSummary = (FaultSectionSummary)faultSectionsList.get(i);
    		sectionId_RowIdMapping.put(new Integer(faultSectionSummary.getSectionId()), new Integer(i) );
    	}
    		
    }

	public int getColumnCount() {
		return columnNames.length;
	}
	
	public Class getColumnClass(int col) {
		if(col==0) return Boolean.class;
		else if(col==1) return String.class;
		else  return String.class;
    }
	

    public int getRowCount() {
    	if(faultSectionsList==null) return 0;
        return faultSectionsList.size();
    }

      public String getColumnName(int col) {
          return columnNames[col];
      }

      public Object getValueAt(int row, int col) {
    	  if(col==0) return isSelectedRow[row];
    	  else if(col==1 || col==2) return ((FaultSectionSummary)faultSectionsList.get(row)).getAsString();
    	  else return null;
      }
      
      /*
       * Don't need to implement this method unless your table's
       * editable.
       */
      public boolean isCellEditable(int row, int col) {
          //Note that the data/cell address is constant,
          //no matter where the cell appears onscreen.
          if (col == 0 && SessionInfo.getContributor()!=null) 
              return true;
           return false;
      }
      
      /**
       * Select/Deselect the check box
       * @param faultSectionId
       * @param val
       */
      public void setSelected(int faultSectionId, boolean val) {
    	  int row = ((Integer)this.sectionId_RowIdMapping.get(new Integer(faultSectionId))).intValue();
    	  setValueAt(new Boolean(val), row, 0);
      }
      
      /**
       * Get a list of selected fault sections
       * @return
       */
      public ArrayList getSelectedFaultSectionsId() {
    	  int numRows = this.getRowCount();
    	  ArrayList selectedSectionsList = new ArrayList();
    	  for(int i=0; i<numRows; ++i) {
    		  if(this.isSelectedRow[i].booleanValue()) {
    			  selectedSectionsList.add(new Integer(((FaultSectionSummary)this.faultSectionsList.get(i)).getSectionId()));
    		  }
    	  }
    	  return selectedSectionsList;
      }
      
      /*
       * Don't need to implement this method unless your table's
       * data can change.
       */
      public void setValueAt(Object value, int row, int col) {	
    	  if(col==0) {
    		  this.isSelectedRow[row] = (Boolean)value;
    	  }  
      }


}
