/**
 * 
 */
package org.opensha.refFaultParamDb.gui.addEdit.deformationModel;

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
import org.opensha.commons.param.editor.StringParameterEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.refFaultParamDb.dao.db.DB_AccessAPI;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.DeformationModelDB_DAO;
import org.opensha.refFaultParamDb.dao.db.DeformationModelSummaryDB_DAO;
import org.opensha.refFaultParamDb.dao.db.FaultSectionVer2_DB_DAO;
import org.opensha.refFaultParamDb.gui.infotools.SessionInfo;
import org.opensha.refFaultParamDb.gui.view.DeformationModelFileWriter;
import org.opensha.refFaultParamDb.vo.DeformationModelSummary;

/**
 * @author vipingupta
 *
 */
public class EditDeformationModel extends JPanel implements ActionListener, ParameterChangeListener {
	private ArrayList deformationModelsList;
	private ArrayList faultSectionsSummaryList;
	private DeformationModelDB_DAO deformationModelDB_DAO;
	private DeformationModelSummaryDB_DAO deformationModelSummaryDB_DAO;
	private  FaultSectionVer2_DB_DAO faultSectionDB_DAO;
	private StringParameter deformationModelsParam;
	private final static String AVAILABLE_DEFORMATION_MODEL_PARAM_NAME = "Choose Deformation Model";
	private ConstrainedStringParameterEditor deformationModelsParamEditor;
	private JButton removeModelButton = new JButton("Remove Model");
	private JButton addModelButton = new JButton("Add Model");
	private DeformationModelTableModel tableModel;
	private DeformationModelTable table;
	private final static String TITLE = "Deformation Model";
	private JButton saveButton = new JButton("Save All to File");
	private final static String SAVE_BUTTON_TOOL_TIP = "Save All Fault Sections in this Fault Model to a txt file";
	private final static String MSG_ADD_MODEL_SUCCESS = "Deformation Model Added Successfully";
	private final static String MSG_REMOVE_MODEL_SUCCESS = "Deformation Model Removed Successfully";
	private final static String MSG_UPDATE_MODEL_SUCCESS = "Deformation Model Updated Successfully";
	private final static String MSG_NO_DEF_MODEL_EXISTS = "Currently, there is no Deformation Model";
	private StringParameter faultModelNameParam = new StringParameter("Fault Model");
	private StringParameterEditor faultModelNameParamEditor;
	private int selectedDeformationModelId;
	private ArrayList faultSectionsIdListInDefModel;
	
	private DB_AccessAPI dbConnection;
	
	public EditDeformationModel(DB_AccessAPI dbConnection) {
		this.dbConnection = dbConnection; 
		deformationModelDB_DAO = new DeformationModelDB_DAO(dbConnection);
		deformationModelSummaryDB_DAO = new DeformationModelSummaryDB_DAO(dbConnection);
		faultSectionDB_DAO = new FaultSectionVer2_DB_DAO(dbConnection);
		tableModel = new DeformationModelTableModel(dbConnection);
		table = new DeformationModelTable(dbConnection, tableModel);
		if(SessionInfo.getContributor()==null)  {
			this.addModelButton.setEnabled(false);
			this.removeModelButton.setEnabled(false);
		}
		else  {
			addModelButton.setEnabled(true);
			removeModelButton.setEnabled(true);
		}
		
		try { // Fault model parameter for displaying
			faultModelNameParamEditor = new StringParameterEditor(faultModelNameParam);
			faultModelNameParamEditor.setEnabled(false);
		}catch(Exception e) {
			e.printStackTrace();
		}
		
		// load all the available fault models
		loadAllDeformationModels();
		
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
		JPanel buttonPanel = getButtonPanel();
		add(buttonPanel,
	             new GridBagConstraints(0, yPos++, 1, 1, 1.0, 1.0
	                                    , GridBagConstraints.CENTER,
	                                    GridBagConstraints.HORIZONTAL,
	                                    new Insets(0, 0, 0, 0), 0, 0));
		
		//		 fault model name
		add(faultModelNameParamEditor,
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
	}

	private JPanel getButtonPanel() {
		// remove model button
		JPanel buttonPanel = new JPanel();
		buttonPanel.setLayout(new GridBagLayout());
		
		buttonPanel.add(this.removeModelButton,
	             new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
	                                    , GridBagConstraints.CENTER,
	                                    GridBagConstraints.NONE,
	                                    new Insets(0, 0, 0, 0), 0, 0));
		// add model button
		buttonPanel.add(this.addModelButton,
	             new GridBagConstraints(1, 0, 1, 1, 1.0, 1.0
	                                    , GridBagConstraints.CENTER,
	                                    GridBagConstraints.NONE,
	                                    new Insets(0, 0, 0, 0), 0, 0));
		//save button
		buttonPanel.add(this.saveButton,
	             new GridBagConstraints(2, 0, 1, 1, 1.0, 1.0
	                                    , GridBagConstraints.CENTER,
	                                    GridBagConstraints.NONE,
	                                    new Insets(0, 0, 0, 0), 0, 0));
		return buttonPanel;
	}
	
	/**
	 * Add action listeners for buttons
	 *
	 */
	private void addActionListeners() {
		removeModelButton.addActionListener(this);
		addModelButton.addActionListener(this);
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
				new AddDeformationModel(dbConnection, this);
			} else if(source == this .removeModelButton) { // remove the model from the database
				String selectedDeformationModel = (String)this.deformationModelsParam.getValue();
				int deformationModelId = this.getDeformationModelSummary(selectedDeformationModel).getDeformationModelId();
				this.deformationModelSummaryDB_DAO.removeDeformationModel(deformationModelId);
				JOptionPane.showMessageDialog(this, MSG_REMOVE_MODEL_SUCCESS);
				loadAllDeformationModels();
			
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
	 * Write fault sections to the file
	 * 
	 * @param file
	 */
	private void writeSectionsToFile(File file) {
		DeformationModelFileWriter defModelWriter = new DeformationModelFileWriter(dbConnection);
		defModelWriter.writeForDeformationModel(this.selectedDeformationModelId, file, true);
	}
	
	/**
	 * this function is called when a new deformation model is added to the database.
	 *
	 */
	public void newDeformationModelAdded() {
		loadAllDeformationModels();
	}
	
	
	/**
	 * When a user selects a different deformation model
	 */
	public void parameterChange(ParameterChangeEvent event) {
		// whenever chosen deformation model changes, also change the displayed fault sections
		setFaultSectionsBasedOnDefModel();
	}
	
	/**
	 * Set the fault sections based on selected deformation model
	 *
	 */
	private void setFaultSectionsBasedOnDefModel() {
		String selectedDefModel  = (String)this.deformationModelsParam.getValue();
		DeformationModelSummary defModelSummary = getDeformationModelSummary(selectedDefModel);
		// find the deformation model id
		selectedDeformationModelId=defModelSummary.getDeformationModelId();
		this.faultModelNameParam.setValue(defModelSummary.getFaultModel().getFaultModelName());
		faultModelNameParamEditor.refreshParamEditor();
		// get the Defomation Model from database based on user selected deformation model
		faultSectionsIdListInDefModel = this.deformationModelDB_DAO.getFaultSectionIdsForDeformationModel(selectedDeformationModelId);
		tableModel.setDeformationModel(selectedDeformationModelId, faultSectionsIdListInDefModel);
		tableModel.fireTableDataChanged();
	}

	/**
	 * Get the deformation model Id based on deformation model name
	 * @param selectedDeformationModel
	 * @return
	 */
	private DeformationModelSummary getDeformationModelSummary(String selectedDeformationModel) {
		for(int i=0; i<this.deformationModelsList.size(); ++i) {
			DeformationModelSummary deformationModel = (DeformationModelSummary)deformationModelsList.get(i);
			if(deformationModel.getDeformationModelName().equalsIgnoreCase(selectedDeformationModel)) {
				return deformationModel;
			}
		}
		return null;
	}
	
	/**
	 * Load All the available deformation models
	 * 
	 */
	private void loadAllDeformationModels() {
		deformationModelsList = this.deformationModelSummaryDB_DAO.getAllDeformationModels();
		if(deformationModelsParamEditor!=null) this.remove(deformationModelsParamEditor);
		this.updateUI();
		// make a list of fault model names
		ArrayList deformationModelNames = new ArrayList();
		for(int i=0; i<deformationModelsList.size(); ++i) {
			deformationModelNames.add(((DeformationModelSummary)deformationModelsList.get(i)).getDeformationModelName());
		}
		
		// make parameter and editor
		if(deformationModelNames==null || deformationModelNames.size()==0)  {
			this.removeModelButton.setEnabled(false);
			faultModelNameParam.setValue("");
			faultModelNameParamEditor.refreshParamEditor();
			JOptionPane.showMessageDialog(this, MSG_NO_DEF_MODEL_EXISTS);
			return;
		}
		
		// enable the add, remove and update button only if user has read/write access
		if(SessionInfo.getContributor()!=null) {
			this.removeModelButton.setEnabled(true);
		}
		
		deformationModelsParam = new StringParameter(AVAILABLE_DEFORMATION_MODEL_PARAM_NAME,deformationModelNames, (String)deformationModelNames.get(0) );
		deformationModelsParam.addParameterChangeListener(this);
		deformationModelsParamEditor = new ConstrainedStringParameterEditor(deformationModelsParam);
		// fault model selection editor
		add(this.deformationModelsParamEditor,
	             new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
	                                    , GridBagConstraints.CENTER,
	                                    GridBagConstraints.HORIZONTAL,
	                                    new Insets(0, 0, 0, 0), 0, 0));
		setFaultSectionsBasedOnDefModel();
		this.updateUI();
	}
	

}
