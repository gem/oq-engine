/**
 * 
 */
package org.opensha.refFaultParamDb.gui.addEdit.deformationModel;

import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;

import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JOptionPane;

import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ConstrainedStringParameterEditor;
import org.opensha.commons.param.editor.StringParameterEditor;
import org.opensha.refFaultParamDb.dao.db.DB_AccessAPI;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.DeformationModelSummaryDB_DAO;
import org.opensha.refFaultParamDb.dao.db.FaultModelSummaryDB_DAO;
import org.opensha.refFaultParamDb.vo.DeformationModelSummary;
import org.opensha.refFaultParamDb.vo.FaultModelSummary;

/**
 * @author vipingupta
 *
 */
public class AddDeformationModel extends JFrame implements ActionListener {
	private final static String DEFORMATION_MODEL_PARAM_NAME = "Deformation Model";
	private StringParameter deformationModelParam;
	private JButton okButton = new JButton("OK");
	private JButton cancelButton = new JButton("Cancel");
	private final static String MSG_NO_FAULT_MODELS_AVAILABLE = "No fault models exist. Fault model should be created before creating deformation model";
	private final static String MSG_DEF_MODEL_NAME_MISSING = "Deformation model name is missing";
	private final static String MSG_DEF_MODEL_ADD_SUCCESS = "Deformation Model added successfully to the database";
	private ArrayList faultModelsList;
	private  FaultModelSummaryDB_DAO faultModelDB_DAO;
	private DeformationModelSummaryDB_DAO defModelSummaryDB_DAO;
	private StringParameter faultModelsParam;
	private final static String AVAILABLE_FAULT_MODEL_PARAM_NAME = "Choose Fault Model";
	private EditDeformationModel editDeformationModel;
	
	public AddDeformationModel(DB_AccessAPI dbConnection, EditDeformationModel editDeformationModel) {
		faultModelDB_DAO = new FaultModelSummaryDB_DAO(dbConnection);
		defModelSummaryDB_DAO = new DeformationModelSummaryDB_DAO(dbConnection);
		this.editDeformationModel = editDeformationModel;
		getContentPane().setLayout(new GridBagLayout());
		makeDeformationModelNameParam(); // make deformation model parameter
		try {
			loadAllFaultModels(); // load fault models
		}catch(Exception e) {
			JOptionPane.showMessageDialog(this, e.getMessage());
			this.dispose();
			return;
		}
		addButtons(); // Add buttons
		this.pack();
		this.show();
	}
	
	/**
	 * Add the Ok and Cancel buttons to the GUI
	 *
	 */
	private void addButtons() {
		// OK Button
		getContentPane().add(okButton,
				new GridBagConstraints(0, 2, 1, 1, 1.0, 1.0
						, GridBagConstraints.CENTER,
						GridBagConstraints.NONE,
						new Insets(0, 0, 0, 0), 0, 0));
		// cancel button
		getContentPane().add(cancelButton,
				new GridBagConstraints(1, 2, 1, 1, 1.0, 1.0
						, GridBagConstraints.CENTER,
						GridBagConstraints.NONE,
						new Insets(0, 0, 0, 0), 0, 0));
		okButton.addActionListener(this);
		cancelButton.addActionListener(this);
	}
	
	/**
	 * When OK or cancel button is clicked
	 */
	public void actionPerformed(ActionEvent event) {
		Object source = event.getSource();
		if(source == this.okButton) {
			String defModelName = (String)this.deformationModelParam.getValue();
			// check that deformation model name is not blank
			if(defModelName.equalsIgnoreCase("")) {
				JOptionPane.showMessageDialog(this, MSG_DEF_MODEL_NAME_MISSING);
				return;
			}
			try {
				// add the deformation model to the database
				defModelSummaryDB_DAO.addDeformationModel(getDeformationModelSummary(defModelName));
				JOptionPane.showMessageDialog(this, MSG_DEF_MODEL_ADD_SUCCESS);
				editDeformationModel.newDeformationModelAdded();
				this.dispose();
			}catch(Exception e) {
				JOptionPane.showMessageDialog(this, e.getMessage());
			}
			
		} else if(source == this.cancelButton) { // close this window on click of cancel button
			this.dispose();
		}
	}
	
	
	/**
	 * Get the deformation model summary
	 * 
	 * @return
	 */
	private DeformationModelSummary getDeformationModelSummary(String deformationModelName) {
		DeformationModelSummary deformationModelSummary = new DeformationModelSummary();
		deformationModelSummary.setDeformationModelName(deformationModelName);
		deformationModelSummary.setFaultModel(getFaultModel((String)faultModelsParam.getValue()));
		return deformationModelSummary;
	}
	
	/**
	 * Get the fault model Id based on Fault model name
	 * @param selectedFaultModel
	 * @return
	 */
	private FaultModelSummary getFaultModel(String selectedFaultModel) {
		for(int i=0; i<this.faultModelsList.size(); ++i) {
			FaultModelSummary faultModel = (FaultModelSummary)faultModelsList.get(i);
			if(faultModel.getFaultModelName().equalsIgnoreCase(selectedFaultModel)) {
				return faultModel;
			}
		}
		return null;
	}
	
	/**
	 * Make StringParameter so that user can type the deformation model parameter name
	 *
	 */
	private void makeDeformationModelNameParam() {
		try {
			deformationModelParam = new StringParameter(DEFORMATION_MODEL_PARAM_NAME,"");
			StringParameterEditor  deformationModelParamEditor = new StringParameterEditor(deformationModelParam);
			getContentPane().add(deformationModelParamEditor,
					new GridBagConstraints(0, 0, 2, 1, 1.0, 1.0
							, GridBagConstraints.CENTER,
							GridBagConstraints.BOTH,
							new Insets(0, 0, 0, 0), 0, 0));
		}catch(Exception e) { e.printStackTrace(); }
	}
	
	
	/**
	 * Load All the available fault models
	 * 
	 */
	private void loadAllFaultModels() {
		faultModelsList = faultModelDB_DAO.getAllFaultModels();
		
		// make a list of fault model names
		ArrayList faultModelNames = new ArrayList();
		for(int i=0; i<faultModelsList.size(); ++i) {
			faultModelNames.add(((FaultModelSummary)faultModelsList.get(i)).getFaultModelName());
		}
		// make parameter and editor
		if(faultModelNames==null || faultModelNames.size()==0)  {
			throw new RuntimeException(MSG_NO_FAULT_MODELS_AVAILABLE);
		}
		
		faultModelsParam = new StringParameter(AVAILABLE_FAULT_MODEL_PARAM_NAME,faultModelNames, (String)faultModelNames.get(0) );
		ConstrainedStringParameterEditor faultModelsParamEditor = new ConstrainedStringParameterEditor(faultModelsParam);
		// fault model selection editor
		getContentPane().add(faultModelsParamEditor,
	             new GridBagConstraints(0, 1, 2, 1, 1.0, 1.0
	                                    , GridBagConstraints.CENTER,
	                                    GridBagConstraints.BOTH,
	                                    new Insets(0, 0, 0, 0), 0, 0));
	}
	
	
}
	

