/**
 * 
 */
package org.opensha.refFaultParamDb.gui.addEdit.deformationModel;

import java.awt.GridBagConstraints;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;

import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JOptionPane;

import org.opensha.commons.data.estimate.Estimate;
import org.opensha.commons.param.editor.estimate.ConstrainedEstimateParameterEditor;
import org.opensha.commons.param.estimate.EstimateConstraint;
import org.opensha.commons.param.estimate.EstimateParameter;
import org.opensha.refFaultParamDb.dao.db.DB_AccessAPI;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.DeformationModelDB_DAO;
import org.opensha.refFaultParamDb.gui.infotools.GUI_Utils;
import org.opensha.refFaultParamDb.gui.infotools.SessionInfo;
import org.opensha.refFaultParamDb.vo.EstimateInstances;

/**
 * @author vipingupta
 *
 */
public class EditAseismicSlipFactor extends JFrame implements ActionListener {
      //	 ASEISMIC SLIP FACTOR
	  private final static String ASEISMIC_SLIP_FACTOR_PARAM_NAME="Aseismic Slip Factor Estimate(0-1, 1=all aseismic)";
	  private final static String ASEISMIC_SLIP_FACTOR="Aseismic Slip Factor";
	  private final static double ASEISMIC_SLIP_FACTOR_MIN=Double.NEGATIVE_INFINITY;
	  private final static double ASEISMIC_SLIP_FACTOR_MAX=Double.POSITIVE_INFINITY;
	  public final static String ASEISMIC_SLIP_FACTOR_UNITS = "";
	  
	  private EstimateParameter aSeismicSlipFactorParam;
	  private ConstrainedEstimateParameterEditor aSeismicSlipFactorParamEditor;
	  private final static String ASEISMIC_SLIP_FACTOR_PARAMS_TITLE = "Aseismic Slip Factor";
	  // update, Cancel Button
	  private JButton okButton = new JButton("OK");
	  private JButton cancelButton = new JButton("Cancel");
	  // deformation model DAO
	  DeformationModelDB_DAO deformationModelDAO;
	  private final static String MSG_UPDATE_SUCCESS = "Aseimsic Slip Factor updated succesfully for fault section in deformation model";
	  private int deformationModelId, faultSectionId;
	  private EstimateInstances aseismicSlipEst;
	  
	  public EditAseismicSlipFactor(DB_AccessAPI dbConnection, int deformationModelId,
			  int faultSectionId, EstimateInstances aseismicSlipEst) {
		  deformationModelDAO = new DeformationModelDB_DAO(dbConnection);
		  this.deformationModelId = deformationModelId;
		  this.faultSectionId = faultSectionId;
		  this.aseismicSlipEst = aseismicSlipEst;
		  this.getContentPane().setLayout(GUI_Utils.gridBagLayout);
		  setTitle(this.ASEISMIC_SLIP_FACTOR_PARAMS_TITLE);
		  makeAseismicSlipParameterAndEditor();
		  addToGUI();
		  if(SessionInfo.getContributor()==null) this.okButton.setEnabled(false);
		  pack();
		  show();
		  
	  }
	  
	  public void actionPerformed(ActionEvent event) {
		  Object source = event.getSource();
		  if(source == this.cancelButton) this.dispose();
		  else if(source == this.okButton) { // update slip rate in database
			  try {
				  // update slip rate in the database
				  deformationModelDAO.updateAseimsicSlipFactor(deformationModelId, faultSectionId,  getAseismicSlipEstimate());
				  JOptionPane.showMessageDialog(this, this.MSG_UPDATE_SUCCESS);
				  this.dispose();
			  }catch(Exception e) {
				  JOptionPane.showMessageDialog(this, e.getMessage());
			  }
		  }
	  }
	  
	  /**
	   * Add GUI components to JFrame
	   *
	   */
	  private void addToGUI() {
		  // slip rate parameter editor
		  this.getContentPane().add(aSeismicSlipFactorParamEditor,
		             new GridBagConstraints(0, 0, 2, 1, 1.0, 1.0
		                                    , GridBagConstraints.CENTER,
		                                    GridBagConstraints.BOTH,
		                                    new Insets(0, 0, 0, 0), 0, 0));
		  // cancel button
		  this.getContentPane().add(this.cancelButton,
		             new GridBagConstraints(0, 1, 1, 1, 1.0, 0.0
		                                    , GridBagConstraints.CENTER,
		                                    GridBagConstraints.NONE,
		                                    new Insets(0, 0, 0, 0), 0, 0));
		  
		  //ok button
		  this.getContentPane().add(this.okButton,
		             new GridBagConstraints(1, 1, 1, 1, 1.0, 0.0
		                                    , GridBagConstraints.CENTER,
		                                    GridBagConstraints.NONE,
		                                    new Insets(0, 0, 0, 0), 0, 0));
		  
		  this.okButton.addActionListener(this);
		  this.cancelButton.addActionListener(this);
	  }
	  
	  /**
	   * Make slip rate parameter and editor
	   *
	   */
	  private void makeAseismicSlipParameterAndEditor() {
		  // slip rate estimate
		   ArrayList allowedEstimates = EstimateConstraint.createConstraintForPositiveDoubleValues();
		   	//aseismic slip factor
		    this.aSeismicSlipFactorParam = new EstimateParameter(ASEISMIC_SLIP_FACTOR_PARAM_NAME,
		        ASEISMIC_SLIP_FACTOR_UNITS, ASEISMIC_SLIP_FACTOR_MIN, ASEISMIC_SLIP_FACTOR_MAX, allowedEstimates);
		    if(aseismicSlipEst!=null && aseismicSlipEst.getEstimate()!=null )
		    	aSeismicSlipFactorParam.setValue(aseismicSlipEst.getEstimate());
		    aSeismicSlipFactorParamEditor = new ConstrainedEstimateParameterEditor(aSeismicSlipFactorParam, true);
	  }
	  
	  /**
	    * Get the slip rate estimate along with units
	    * @return
	    */
	   private  EstimateInstances getAseismicSlipEstimate() {
		   this.aSeismicSlipFactorParamEditor.setEstimateInParameter();
		     return new EstimateInstances((Estimate)this.aSeismicSlipFactorParam.getValue(),
		                                 ASEISMIC_SLIP_FACTOR_UNITS);
	   }
}
