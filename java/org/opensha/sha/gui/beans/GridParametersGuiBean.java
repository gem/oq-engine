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

package org.opensha.sha.gui.beans;

import java.io.Serializable;
import java.util.ArrayList;

import javax.swing.JOptionPane;

import org.opensha.commons.data.region.SitesInGriddedRegion;
import org.opensha.commons.gridComputing.GridResourcesList;
import org.opensha.commons.gridComputing.ResourceProvider;
import org.opensha.commons.gridComputing.ResourceProviderEditor;
import org.opensha.commons.gridComputing.StorageHost;
import org.opensha.commons.gridComputing.SubmitHost;
import org.opensha.commons.gridComputing.SubmitHostEditor;
import org.opensha.commons.param.BooleanParameter;
import org.opensha.commons.param.IntegerParameter;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterConstraintAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ParameterEditor;
import org.opensha.commons.param.editor.ParameterListEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeFailEvent;
import org.opensha.commons.param.event.ParameterChangeFailListener;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.sha.util.SiteTranslator;


/**
 * <p>Title:SitesInGriddedRectangularRegionGuiBean </p>
 * <p>Description: This creates the Gridded Region parameter Editor with Site Params
 * for the selected Attenuation Relationship in the Application.
 * </p>
 * @author Nitin Gupta & Vipin Gupta
 * @date March 11, 2003
 * @version 1.0
 */



public class GridParametersGuiBean extends ParameterListEditor implements
ParameterChangeFailListener, ParameterChangeListener, Serializable {

	// for debug purposes
	protected final static String C = "GridParametersGuiBean";


	// title for site paramter panel
	public final static String GRIDDED_SITE_PARAMS = "Set Gridded Region Params";
	
	public final static String CUSTOM_PARAM_NAME = "Custom";
	
	ResourceProvider currentRP = null;
	ResourceProviderEditor currentRPEditor = null;
	
	SubmitHost currentSubmit = null;
	SubmitHostEditor currentSubmitEditor = null;

	ArrayList<ResourceProvider> rpList = new ArrayList<ResourceProvider>();
	ArrayList<SubmitHost> submitList = new ArrayList<SubmitHost>();
	
	// Presets
	private StringParameter rpPresets;
	private StringParameter submitPresets;
	
	// Job Params
	private IntegerParameter sitesPerJob = new IntegerParameter("Site Per Job", 0, Integer.MAX_VALUE);
	private IntegerParameter maxWallTime = new IntegerParameter("Maximum Time Per Job", 0, 999);
	private BooleanParameter saveERF = new BooleanParameter("Save ERF to File?", true);
	
	public static final String SUBMIT_HOST_PARAM_NAME = "Submit Host Presets";

	//SiteTranslator
	SiteTranslator siteTrans = new SiteTranslator();

	//instance of class EvenlyGriddedRectangularGeographicRegion
	private SitesInGriddedRegion gridRectRegion;
	
	public GridParametersGuiBean(GridResourcesList resources) {
		this.init(resources);
	}

	/**
	 * constuctor which builds up mapping between IMRs and their related sites
	 */
	public GridParametersGuiBean() {
		
		ArrayList<ResourceProvider> rpList = new ArrayList<ResourceProvider>();
		
		rpList.add(ResourceProvider.HPC());
		rpList.add(ResourceProvider.ABE_GLIDE_INS());
		rpList.add(ResourceProvider.ABE_NO_GLIDE_INS());
		rpList.add(ResourceProvider.DYNAMIC());
		rpList.add(ResourceProvider.ORNL());
		
		ArrayList<SubmitHost> submitList = new ArrayList<SubmitHost>();
		
		submitList.add(SubmitHost.AFTERSHOCK);
		
		ArrayList<StorageHost> storageList = new ArrayList<StorageHost>();
		
		storageList.add(StorageHost.HPC);
		
		this.init(new GridResourcesList(rpList, submitList, storageList));
	}
	
	private void init(GridResourcesList resources) {
		rpList = resources.getResourceProviders();
		
		this.currentRP = rpList.get(0);
		
		ArrayList<String> rpPresetsStr = new ArrayList<String>();
		for (ResourceProvider preset : rpList) {
			rpPresetsStr.add(preset.getName());
		}
		rpPresetsStr.add(GridParametersGuiBean.CUSTOM_PARAM_NAME);
		
		submitList = resources.getSubmitHosts();
		
		this.currentSubmit = submitList.get(0);
		
		ArrayList<String> submitPresetsStr = new ArrayList<String>();
		for (SubmitHost preset : submitList) {
			submitPresetsStr.add(preset.getName());
		}
		submitPresetsStr.add(GridParametersGuiBean.CUSTOM_PARAM_NAME);
		
		this.sitesPerJob.setValue(100);
		this.maxWallTime.setValue(240);
		
		rpPresets = new StringParameter("Resource Provider Presets", rpPresetsStr);
		rpPresets.setValue(currentRP.getName());
		rpPresets.addParameterChangeListener(this);
		
		submitPresets = new StringParameter(SUBMIT_HOST_PARAM_NAME, submitPresetsStr);
		submitPresets.setValue(currentSubmit.getName());
		submitPresets.addParameterChangeListener(this);

		// add the longitude and latitude paramters
		parameterList = new ParameterList();
		parameterList.addParameter(rpPresets);
		parameterList.addParameter(submitPresets);
		parameterList.addParameter(sitesPerJob);
		parameterList.addParameter(maxWallTime);
		parameterList.addParameter(saveERF);
		editorPanel.removeAll();
		addParameters();

		try {
			jbInit();
		}catch(Exception e) {
			e.printStackTrace();
		}
	}
	
	public void setSubmitHostsVisible(boolean visible) {
		ParameterEditor editor = this.getParameterEditor(SUBMIT_HOST_PARAM_NAME);
		editor.setVisible(visible);
	}

	/**
	 * Shown when a Constraint error is thrown on a ParameterEditor
	 *
	 * @param  e  Description of the Parameter
	 */
	public void parameterChangeFailed( ParameterChangeFailEvent e ) {


		String S = C + " : parameterChangeFailed(): ";



		StringBuffer b = new StringBuffer();

		ParameterAPI param = ( ParameterAPI ) e.getSource();


		ParameterConstraintAPI constraint = param.getConstraint();
		String oldValueStr = e.getOldValue().toString();
		String badValueStr = e.getBadValue().toString();
		String name = param.getName();

		b.append( "The value ");
		b.append( badValueStr );
		b.append( " is not permitted for '");
		b.append( name );
		b.append( "'.\n" );
		b.append( "Resetting to ");
		b.append( oldValueStr );
		b.append( ". The constraints are: \n");
		b.append( constraint.toString() );

		JOptionPane.showMessageDialog(
				this, b.toString(),
				"Cannot Change Value", JOptionPane.INFORMATION_MESSAGE
		);
	}

	/**
	 * This function is called when value a parameter is changed
	 * @param e Description of the parameter
	 */
	public void parameterChange(ParameterChangeEvent e){
		ParameterAPI param = ( ParameterAPI ) e.getSource();

		if(param == rpPresets) {
			String name = (String)rpPresets.getValue();
			if (name.equals(GridParametersGuiBean.CUSTOM_PARAM_NAME)) {
				if (currentRPEditor == null) {
					currentRPEditor = new ResourceProviderEditor(currentRP);
					currentRPEditor.setLocationRelativeTo(this);
				}
				currentRPEditor.setVisible(true);
			} else {
				for (ResourceProvider preset : rpList) {
					if (name.equals(preset.getName())) {
						this.currentRP = preset;
						if (currentRPEditor != null) {
							currentRPEditor.setVisible(false);
							currentRPEditor = null;
						}
						break;
					}
				}
			}
		}
		
		if(param == submitPresets) {
			String name = (String)submitPresets.getValue();
			if (name.equals(GridParametersGuiBean.CUSTOM_PARAM_NAME)) {
				if (currentSubmitEditor == null) {
					currentSubmitEditor = new SubmitHostEditor(currentSubmit);
					currentSubmitEditor.setLocationRelativeTo(this);
				}
				currentSubmitEditor.setVisible(true);
			} else {
				for (SubmitHost preset : submitList) {
					if (name.equals(preset.getName())) {
						this.currentSubmit = preset;
						if (currentSubmitEditor != null) {
							currentSubmitEditor.setVisible(false);
							currentSubmitEditor = null;
						}
						break;
					}
				}
			}
		}
		
	}
	
	public int get_sitesPerJob() {
		return (Integer)this.sitesPerJob.getValue();
	}
	
	public int get_maxWallTime() {
		return (Integer)this.maxWallTime.getValue();
	}
	
	public boolean get_saveERF() {
		return (Boolean)this.saveERF.getValue();
	}
	
	public ResourceProvider get_resourceProvider() {
		return this.currentRP;
	}
	
	public SubmitHost get_submitHost() {
		return this.currentSubmit;
	}
}
