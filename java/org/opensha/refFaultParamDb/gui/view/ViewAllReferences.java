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

package org.opensha.refFaultParamDb.gui.view;

import java.awt.Color;
import java.awt.Component;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;

import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JScrollPane;
import javax.swing.JTable;
import javax.swing.JTextArea;
import javax.swing.SwingConstants;
import javax.swing.table.DefaultTableModel;
import javax.swing.table.TableCellRenderer;

import org.opensha.refFaultParamDb.dao.db.DB_AccessAPI;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.ReferenceDB_DAO;
import org.opensha.refFaultParamDb.vo.Reference;
import org.opensha.sha.gui.infoTools.CalcProgressBar;

/**
 * <p>Title: ViewAllReferences.java </p>
 * <p>Description: View a list of all the references (both short citation as well as
 * full bibliographic reference) in the database. </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class ViewAllReferences extends JFrame implements ActionListener {
  private final static String columnNames[] = {"Author", "Year", "Full Bibliographic Reference", "Qfault Ref Id"};
  private JLabel referencesLabel = new JLabel();
  private JTable referencesTable;
  private JButton refreshButton = new JButton();
  private JButton closeButton = new JButton();
  private JScrollPane referencesScrollPane = new JScrollPane();
  private GridBagLayout gridBagLayout1 = new GridBagLayout();
  // references DAO
  private ReferenceDB_DAO referenceDAO;
  private final static String MSG_MINUTE_TO_LOAD = " May take a minute to load ........";
  private CalcProgressBar progressBar = new CalcProgressBar("Getting References", MSG_MINUTE_TO_LOAD);
  private final static String TITLE = "All References";
  public ViewAllReferences(DB_AccessAPI dbConnection) {
	  referenceDAO = new ReferenceDB_DAO(dbConnection);
    try {
      progressBar.setVisible(true);
      jbInit();
      makeReferencesTable();
      addActionListeners();
      setTitle(TITLE);
      pack();
      this.setLocationRelativeTo(null);
      this.setVisible(true);
      progressBar.setVisible(false);
    }
    catch(Exception e) {
      e.printStackTrace();
    }
  }

  public void actionPerformed(ActionEvent event) {
    Object source = event.getSource();
    if(source == this.closeButton) this.dispose();
    else if(source == this.refreshButton) makeReferencesTable();
  }

  private void addActionListeners() {
    refreshButton.addActionListener(this);
    this.closeButton.addActionListener(this);
  }

  private void makeReferencesTable() {
    if(referencesTable!=null) this.referencesScrollPane.remove(referencesTable);
    referencesTable = new JTable(new ChatTableModel(getReferencesInfo(), this.columnNames));
    referencesTable.setRowHeight(referencesTable.getRowHeight()+40);
    referencesTable.setRowSelectionAllowed(false);
    referencesTable.getColumnModel().getColumn(2).setCellRenderer(new TextAreaRenderer());
    referencesScrollPane.getViewport().add(referencesTable, null);
  }

  /**
   * Get all the references from the database
   * @return
   */
  private Object[][] getReferencesInfo() {
    ArrayList allReferences = referenceDAO.getAllReferences();
    int numRefs = allReferences.size();
    Object[][] tableData = new Object[numRefs][columnNames.length];
    for(int i=0; i<numRefs; ++i) {
      Reference ref = (Reference)allReferences.get(i);
      tableData[i][0] = ref.getRefAuth();
      tableData[i][1] = ref.getRefYear();
      tableData[i][2] = ref.getFullBiblioReference();
      tableData[i][3] = new Integer(ref.getQfaultReferenceId());
    }
    return tableData;
  }


  private void jbInit() throws Exception {
    referencesLabel.setFont(new java.awt.Font("Dialog", 1, 15));
    referencesLabel.setForeground(new Color(100, 100, 130));
    referencesLabel.setHorizontalAlignment(SwingConstants.CENTER);
    referencesLabel.setText("All References");
    this.getContentPane().setLayout(gridBagLayout1);
    refreshButton.setText("Refresh");
    closeButton.setText("Close");
    this.getContentPane().add(referencesLabel,  new GridBagConstraints(0, 0, 2, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(10, 10, 0, 15), 273, 10));
    this.getContentPane().add(refreshButton,  new GridBagConstraints(1, 2, 1, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(6, 51, 0, 8), 11, 1));
    this.getContentPane().add(closeButton,  new GridBagConstraints(0, 3, 1, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(10, 158, 8, 0), 40, 7));
    this.getContentPane().add(referencesScrollPane,  new GridBagConstraints(0, 1, 2, 1, 1.0, 1.0
            ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(0, 10, 0, 8), -73, -44));
  }

}

 class TextAreaRenderer extends JScrollPane implements TableCellRenderer {
   private JTextArea textArea = new JTextArea();
   public TextAreaRenderer() {
     this.getViewport().add(textArea, null);
   }

   public Component getTableCellRendererComponent(JTable jTable,
       Object obj, boolean isSelected, boolean hasFocus, int row,
       int column) {
    textArea.setLineWrap(true);
    textArea.setWrapStyleWord(true);
    textArea.setText((String)obj);
    return this;
   }
 }



/**
 * Extends the DefaultTableModel, but makes all cells uneditable.
 */
class ChatTableModel extends DefaultTableModel {
  public ChatTableModel(Object[][] data, Object[] columnNames) {
    super(data,columnNames);
  }

  public boolean isCellEditable(int row, int column) {
    return false;
  }
}
