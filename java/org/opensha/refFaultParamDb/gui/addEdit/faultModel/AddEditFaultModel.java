/**
 * 
 */
package org.opensha.refFaultParamDb.gui.addEdit.faultModel;

import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.File;
import java.util.ArrayList;

import javax.swing.JButton;
import javax.swing.JFileChooser;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;

import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ConstrainedStringParameterEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.refFaultParamDb.dao.db.DB_AccessAPI;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.FaultModelDB_DAO;
import org.opensha.refFaultParamDb.dao.db.FaultModelSummaryDB_DAO;
import org.opensha.refFaultParamDb.dao.db.FaultSectionVer2_DB_DAO;
import org.opensha.refFaultParamDb.gui.infotools.SessionInfo;
import org.opensha.refFaultParamDb.gui.view.SectionInfoFileWriter;
import org.opensha.refFaultParamDb.vo.FaultModelSummary;


/**
 * This class allows users to add a new fault model and associate fault sections with the fault models
 * 
 * @author vipingupta
 *
 */
public class AddEditFaultModel extends JPanel implements ActionListener, ParameterChangeListener {
	
	private ArrayList faultModelsList;
	private ArrayList faultSectionsSummaryList;
	private  FaultModelSummaryDB_DAO faultModelDB_DAO;
	private  FaultModelDB_DAO faultModelSectionDB_DAO;
	private  FaultSectionVer2_DB_DAO faultSectionDB_DAO;
	private StringParameter faultModelsParam;
	private final static String AVAILABLE_FAULT_MODEL_PARAM_NAME = "Choose Fault Model";
	private ConstrainedStringParameterEditor faultModelsParamEditor;
	private JButton removeModelButton = new JButton("Remove Model");
	private JButton addModelButton = new JButton("Add Model");
	private JButton updateModelButton = new JButton("Update Model");
	private JButton selectAllButton = new JButton("Select All");
	private JButton deselectAllButton = new JButton("Deselect All");
	private FaultModelTableModel tableModel;
	private FaultModelTable table;
	private final static String TITLE = "Fault Model";
	private JButton saveButton = new JButton("Save All to File");
	private final static String SAVE_BUTTON_TOOL_TIP = "Save All Fault Sections in this Fault Model to a txt file";
	private final static String MSG_ADD_MODEL_SUCCESS = "Model Added Successfully";
	private final static String MSG_REMOVE_MODEL_SUCCESS = "Model Removed Successfully";
	private final static String MSG_UPDATE_MODEL_SUCCESS = "Model Updated Successfully";
	private final static String MSG_NO_FAULT_MODEL_EXISTS = "Currently, there is no Fault Model";
	
	private DB_AccessAPI dbConnection;
	
	public AddEditFaultModel(DB_AccessAPI dbConnection) {
		this.dbConnection = dbConnection;
		faultModelDB_DAO = new FaultModelSummaryDB_DAO(dbConnection);
		faultModelSectionDB_DAO = new FaultModelDB_DAO(dbConnection);
		faultSectionDB_DAO = new FaultSectionVer2_DB_DAO(dbConnection);
		if(SessionInfo.getContributor()==null)  {
			this.addModelButton.setEnabled(false);
			this.removeModelButton.setEnabled(false);
			this.updateModelButton.setEnabled(false);
			this.selectAllButton.setEnabled(false);
			this.deselectAllButton.setEnabled(false);
		}
		else {
			addModelButton.setEnabled(true);
			removeModelButton.setEnabled(true);
			updateModelButton.setEnabled(true);
			this.selectAllButton.setEnabled(true);
			this.deselectAllButton.setEnabled(true);
		}
//		 load alla fault sections
		loadAllFaultSectionsSummary();
		// load all the available fault models
		loadAllFaultModels();
		
		 // add action listeners to the button
		addActionListeners();
		// add components to the GUI
		setupGUI();
	}
	
	/**
	 * Add the various buttons, JTable and paramters to the Panel
	 *
	 */
	private void setupGUI() {
		setLayout(new GridBagLayout());
		int yPos=1; // a list of fault models is present at yPos==0
		
		JPanel adRemoveButtonPanel = getAddRemoveButtonPanel();
		// add/remove model button panel
		add(adRemoveButtonPanel,
	             new GridBagConstraints(0, yPos++, 1, 1, 1.0, 1.0
	                                    , GridBagConstraints.CENTER,
	                                    GridBagConstraints.HORIZONTAL,
	                                    new Insets(0, 0, 0, 0), 0, 0));
		// add table
		add(new JScrollPane(this.table),
	             new GridBagConstraints(0, yPos++, 1, 1, 1.0, 1.0
	                                    , GridBagConstraints.CENTER,
	                                    GridBagConstraints.BOTH,
	                                    new Insets(0, 0, 0, 0), 0, 0));
		// update button
		add(this.getSelectDeselectUpdateButtonPanel(),
	             new GridBagConstraints(0, yPos++, 1, 1, 1.0, 1.0
	                                    , GridBagConstraints.CENTER,
	                                    GridBagConstraints.NONE,
	                                    new Insets(0, 0, 0, 0), 0, 0));
	}
	
	/**
	 * Select All/Deselect All/ update button panel
	 * @return
	 */
	private JPanel getSelectDeselectUpdateButtonPanel() {
		JPanel buttonPanel = new JPanel();
		buttonPanel.setLayout(new GridBagLayout());
		// remove model button
		buttonPanel.add(this.selectAllButton,
	             new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
	                                    , GridBagConstraints.CENTER,
	                                    GridBagConstraints.NONE,
	                                    new Insets(0, 0, 0, 0), 0, 0));
		buttonPanel.add(this.deselectAllButton,
	             new GridBagConstraints(1, 0, 1, 1, 1.0, 1.0
	                                    , GridBagConstraints.CENTER,
	                                    GridBagConstraints.NONE,
	                                    new Insets(0, 0, 0, 0), 0, 0));
		buttonPanel.add(this.updateModelButton,
	             new GridBagConstraints(3, 0, 1, 1, 1.0, 1.0
	                                    , GridBagConstraints.CENTER,
	                                    GridBagConstraints.NONE,
	                                    new Insets(0, 0, 0, 0), 0, 0));
		return buttonPanel;
	}
	
	
	/**
	 * Add/remove button panel
	 * @return
	 */
	private JPanel getAddRemoveButtonPanel() {
		JPanel adRemoveButtonPanel = new JPanel();
		adRemoveButtonPanel.setLayout(new GridBagLayout());
		// remove model button
		adRemoveButtonPanel.add(this.removeModelButton,
	             new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
	                                    , GridBagConstraints.CENTER,
	                                    GridBagConstraints.NONE,
	                                    new Insets(0, 0, 0, 0), 0, 0));
		adRemoveButtonPanel.add(this.addModelButton,
	             new GridBagConstraints(1, 0, 1, 1, 1.0, 1.0
	                                    , GridBagConstraints.CENTER,
	                                    GridBagConstraints.NONE,
	                                    new Insets(0, 0, 0, 0), 0, 0));
		adRemoveButtonPanel.add(this.saveButton,
	             new GridBagConstraints(2, 0, 1, 1, 1.0, 1.0
	                                    , GridBagConstraints.CENTER,
	                                    GridBagConstraints.NONE,
	                                    new Insets(0, 0, 0, 0), 0, 0));
		return adRemoveButtonPanel;
	}
	
	/**
	 * Add action listeners for buttons
	 *
	 */
	private void addActionListeners() {
		removeModelButton.addActionListener(this);
		addModelButton.addActionListener(this);
		updateModelButton.addActionListener(this);
		this.selectAllButton.addActionListener(this);
		this.deselectAllButton.addActionListener(this);
		saveButton.addActionListener(this);
		saveButton.setToolTipText(SAVE_BUTTON_TOOL_TIP);
	}
	
	/**
	 * This function is called when a Button is clicked in this panel, then change the selected fault sections
	 */
	public void actionPerformed(ActionEvent event) {
		Object source = event.getSource();
		try {
			if(source==this.addModelButton) { // add a new model
				// show a Window asking for new model name
				String faultModelName = JOptionPane.showInputDialog(this, "Enter Fault Model Name");
				if(faultModelName==null) return;
				else addFaultModelToDB(faultModelName);
				JOptionPane.showMessageDialog(this, MSG_ADD_MODEL_SUCCESS);
				loadAllFaultModels();
			
			} else if(source == this .removeModelButton) { // remove the model from the database
				String selectedFaultModel = (String)this.faultModelsParam.getValue();
				int faultModelId = this.getFaultModelId(selectedFaultModel);
				this.faultModelDB_DAO.removeFaultModel(faultModelId);
				JOptionPane.showMessageDialog(this, MSG_REMOVE_MODEL_SUCCESS);
				loadAllFaultModels();
			
			} else if(source == this.updateModelButton)  { // update the model in the database
				ArrayList faultSectionIdList = this.tableModel.getSelectedFaultSectionsId();
				String selectedFaultModel = (String)this.faultModelsParam.getValue();
				int faultModelId = this.getFaultModelId(selectedFaultModel);
				this.faultModelSectionDB_DAO.addFaultModelSections(faultModelId, faultSectionIdList);
				JOptionPane.showMessageDialog(this, MSG_UPDATE_MODEL_SUCCESS);
			} else if(source == this.selectAllButton) { // select All 
				 setAllRowsSelection(true);
			} else if(source == this.deselectAllButton) { // deselect all
				setAllRowsSelection(false);
			} else if(source == this.saveButton) { // save to a text file
				JFileChooser fileChooser = new JFileChooser();
				fileChooser.showSaveDialog(this);
				File file = fileChooser.getSelectedFile();
				if(file!=null) writeSectionsToFile(file);
			}
		}catch(Exception e) {
			e.printStackTrace();
			JOptionPane.showMessageDialog(this, e.getMessage());
		}
	}
	
	/**
	 * Write fault sections to a file
	 * @param file
	 */
	private void writeSectionsToFile(File file) {
		ArrayList faultSectionIdList  = this.getFaultSectionIdList();
		int []faultSectionIds = new int[faultSectionIdList.size()];
		for(int i=0; i<faultSectionIdList.size(); ++i) {
			faultSectionIds[i] = ((Integer)faultSectionIdList.get(i)).intValue();
		}
		SectionInfoFileWriter fileWriter = new SectionInfoFileWriter(dbConnection);
		fileWriter.writeForFaultModel(faultSectionIds, file);
	}
	
	 /**
	  * Select/deselect all rows
	  * @param isSelected
	  */
	 private void setAllRowsSelection(boolean isSelected) {
		 int numRows = this.tableModel.getRowCount();
		 Boolean val = new Boolean(isSelected);
		 for(int i=0; i<numRows; ++i)
			 tableModel.setValueAt(val, i, 0);
		 tableModel.fireTableDataChanged();
	 }
	
	/**
	 * Add a fault model name to the database
	 * @param faultModelName
	 */
	private void addFaultModelToDB(String faultModelName) {
		FaultModelSummary faultModel = new FaultModelSummary();
		faultModel.setFaultModelName(faultModelName);
		 this.faultModelDB_DAO.addFaultModel(faultModel);
	}
	
	/**
	 * When a user selects a different fault model
	 */
	public void parameterChange(ParameterChangeEvent event) {
		// whenever chosen fault model changes, also change the displayed fault sections
		setFaultSectionsBasedOnFaultModel();
	}
	
	/**
	 * Set the fault sections based on selected fault model
	 *
	 */
	private void setFaultSectionsBasedOnFaultModel() {
		ArrayList faultSectionIdList = getFaultSectionIdList();
		
		//deselect all the check boxes in the table
		for(int i=0; i<this.tableModel.getRowCount(); ++i)
			tableModel.setValueAt(new Boolean(false), i, 0);
		// only select the check boxes which are part of this fault model
		int numSectionsInFaultModel = faultSectionIdList.size();
		for(int i=0; i<numSectionsInFaultModel; ++i) {
			Integer faultSectionId = (Integer)faultSectionIdList.get(i);
			tableModel.setSelected(faultSectionId.intValue(), true);
		}
		tableModel.fireTableDataChanged();
	}
	
	/**
	 * Get fault section Id list for the current fault model
	 * @return
	 */
	private ArrayList getFaultSectionIdList() {
		String selectedFaultModel  = (String)this.faultModelsParam.getValue();
		// find the fault model id
		int faultModelId=getFaultModelId(selectedFaultModel);
		// get all the fault sections within this fault model
		ArrayList faultSectionIdList = this.faultModelSectionDB_DAO.getFaultSectionIdList(faultModelId);
		return faultSectionIdList;
	}

	/**
	 * Get the fault model Id based on Fault model name
	 * @param selectedFaultModel
	 * @return
	 */
	private int getFaultModelId(String selectedFaultModel) {
		for(int i=0; i<this.faultModelsList.size(); ++i) {
			FaultModelSummary faultModel = (FaultModelSummary)faultModelsList.get(i);
			if(faultModel.getFaultModelName().equalsIgnoreCase(selectedFaultModel)) {
				return faultModel.getFaultModelId();
			}
		}
		return -1;
	}
	
	/**
	 * Load All the available fault models
	 * 
	 */
	private void loadAllFaultModels() {
		faultModelsList = faultModelDB_DAO.getAllFaultModels();
		if(faultModelsParamEditor!=null) this.remove(faultModelsParamEditor);
		this.updateUI();
		// make a list of fault model names
		ArrayList faultModelNames = new ArrayList();
		for(int i=0; i<faultModelsList.size(); ++i) {
			faultModelNames.add(((FaultModelSummary)faultModelsList.get(i)).getFaultModelName());
		}
		// make parameter and editor
		if(faultModelNames==null || faultModelNames.size()==0)  {
			this.updateModelButton.setEnabled(false);
			this.removeModelButton.setEnabled(false);
			JOptionPane.showMessageDialog(this, MSG_NO_FAULT_MODEL_EXISTS);
			return;
		}
		
		// enable the add, remove and update button only if user has read/write access
		if(SessionInfo.getContributor()!=null) {
			this.updateModelButton.setEnabled(true);
			this.removeModelButton.setEnabled(true);
		}
		faultModelsParam = new StringParameter(AVAILABLE_FAULT_MODEL_PARAM_NAME,faultModelNames, (String)faultModelNames.get(0) );
		faultModelsParam.addParameterChangeListener(this);
		setFaultSectionsBasedOnFaultModel();
		faultModelsParamEditor = new ConstrainedStringParameterEditor(faultModelsParam);
		// fault model selection editor
		add(this.faultModelsParamEditor,
	             new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
	                                    , GridBagConstraints.CENTER,
	                                    GridBagConstraints.BOTH,
	                                    new Insets(0, 0, 0, 0), 0, 0));
		this.updateUI();
	}
	
	
	/**
	 * Load faultsectionnames and ids of all the fault sections. Also make the TableModel and Table to view the fault sections
	 *
	 */
	private void loadAllFaultSectionsSummary() {
		faultSectionsSummaryList = faultSectionDB_DAO.getAllFaultSectionsSummary();
		tableModel = new FaultModelTableModel(faultSectionsSummaryList);
		table = new FaultModelTable(dbConnection, tableModel);
	}
	
}
