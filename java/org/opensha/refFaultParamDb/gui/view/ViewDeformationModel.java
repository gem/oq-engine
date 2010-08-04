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

import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;

import javax.swing.JFrame;
import javax.swing.JPanel;

import org.opensha.commons.data.estimate.Estimate;
import org.opensha.refFaultParamDb.dao.db.DB_AccessAPI;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.DeformationModelDB_DAO;
import org.opensha.refFaultParamDb.gui.infotools.GUI_Utils;
import org.opensha.refFaultParamDb.gui.infotools.InfoLabel;
import org.opensha.refFaultParamDb.vo.EstimateInstances;


/**
 * This class allows the user to view Slip Rate and aseismic slip factor for 
 * fault sections within a deformation model.
 * This class is presently used to view info about deformation model in SCEC-VDO
 * 
 * @author vipingupta
 *
 */
public class ViewDeformationModel extends JFrame {
	private DeformationModelDB_DAO deformationModelDAO;
	private final static String SLIP_RATE = "Slip Rate (mm/year)";
	private final static String ASEISMIC_SLIP_FACTOR = "Aseismic Slip Factor";

	/**
	 * View the Slip Rate and Aseismic Slip Factor for fault section within a 
	 * deformation model. 
	 * 
	 * @param deformationModelId
	 * @param faultSectionId
	 */
	public ViewDeformationModel(DB_AccessAPI dbConnection, int deformationModelId, int faultSectionId) {
		deformationModelDAO = new DeformationModelDB_DAO(dbConnection);
		
		this.getContentPane().setLayout(new GridBagLayout());
		EstimateInstances asesmicSlipEstInstance  = deformationModelDAO.getAseismicSlipEstimate(deformationModelId, faultSectionId);
		EstimateInstances slipRateEstInstance  = deformationModelDAO.getSlipRateEstimate(deformationModelId, faultSectionId);
		Estimate slipRateEstimate = null, aseismicSlipEstimate=null;
		if(slipRateEstInstance!=null) slipRateEstimate = slipRateEstInstance.getEstimate();
		if(asesmicSlipEstInstance!=null) aseismicSlipEstimate = asesmicSlipEstInstance.getEstimate();
		// view slip rate info
		JPanel slipRatePanel = GUI_Utils.getPanel(new InfoLabel(slipRateEstimate, SLIP_RATE, ""), SLIP_RATE);
		getContentPane().add(slipRatePanel, new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
		        , GridBagConstraints.CENTER, GridBagConstraints.BOTH,
		        new Insets(0, 0, 0, 0), 0, 0));
		// view aseismic slip factor
		JPanel aseicmicSlipPanel = GUI_Utils.getPanel(new InfoLabel(aseismicSlipEstimate, ASEISMIC_SLIP_FACTOR, ""), ASEISMIC_SLIP_FACTOR);
		getContentPane().add(aseicmicSlipPanel, new GridBagConstraints(0, 1, 1, 1, 1.0, 1.0
		        , GridBagConstraints.CENTER, GridBagConstraints.BOTH,
		        new Insets(0, 0, 0, 0), 0, 0));
		this.pack();
		this.show();
	}

	
}
