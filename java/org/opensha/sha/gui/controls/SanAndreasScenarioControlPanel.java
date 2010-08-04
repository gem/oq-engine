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

package org.opensha.sha.gui.controls;


import java.awt.Component;
import java.util.ArrayList;

import org.opensha.commons.geo.Location;
import org.opensha.commons.mapping.gmt.GMT_MapGenerator;
import org.opensha.commons.param.editor.ParameterEditor;
import org.opensha.commons.param.editor.ParameterListEditor;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.faultSurface.SimpleFaultData;
import org.opensha.sha.gui.beans.AttenuationRelationshipGuiBean;
import org.opensha.sha.gui.beans.EqkRupSelectorGuiBean;
import org.opensha.sha.gui.beans.EqkRuptureCreationPanel;
import org.opensha.sha.gui.beans.MapGuiBean;
import org.opensha.sha.gui.beans.SitesInGriddedRectangularRegionGuiBean;
import org.opensha.sha.imr.attenRelImpl.Field_2000_AttenRel;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGV_Param;
import org.opensha.sha.imr.param.OtherParams.ComponentParam;
import org.opensha.sha.param.SimpleFaultParameter;
import org.opensha.sha.param.editor.SimpleFaultParameterEditor;
import org.opensha.sha.param.editor.gui.SimpleFaultParameterEditorPanel;


/**
 * <p>Title: PuenteHillsScenarioControlPanelUsingEqkRuptureCreation</p>
 * <p>Description: Sets the param value to replicate the official scenario shakemap
 * for the Puente Hill Scenario (http://www.trinet.org/shake/Puente_Hills_se)</p>
 * @author : Edward (Ned) Field and Nitin Gupta
 * @version 1.0
 */

public class SanAndreasScenarioControlPanel extends ConfirmDialogControlPanel {

	public static final String NAME = "Set Params for SAF Shakeout Quake Scenario";
	public static final String MESSAGE = "Are you sure to set the parameters"+
										" for a San Andreas scenario?";

	//for debugging
	protected final static boolean D = false;


	private EqkRupSelectorGuiBean erfGuiBean;
	private AttenuationRelationshipGuiBean imrGuiBean;
	private SitesInGriddedRectangularRegionGuiBean regionGuiBean;
	private MapGuiBean mapGuiBean;

	private SimpleFaultData sanAndreasFaultData;
	private double aveDipDir;

	//default magnitude.
	private double magnitude = 7.8;

	/**
	 * Accepts 3 params for the EqkRupSelectorGuiBean, AttenuationRelationshipGuiBean, SitesInGriddedRectangularRegionGuiBean
	 * from the applet.
	 * @param erfGuiBean
	 * @param imrGuiBean
	 * @param regionGuiBean
	 * @param MapGuiBean
	 */
	public SanAndreasScenarioControlPanel(EqkRupSelectorGuiBean erfGuiBean,
			AttenuationRelationshipGuiBean imrGuiBean, SitesInGriddedRectangularRegionGuiBean regionGuiBean,
			MapGuiBean mapGuiBean, Component parent) {
		super(NAME, MESSAGE, parent);
		//getting the instance for variuos GuiBeans from the applet required to set the
		//default values for the Params for the Puente Hills Scenario.
		this.erfGuiBean = erfGuiBean;
		this.imrGuiBean = imrGuiBean;
		this.regionGuiBean = regionGuiBean;
		this.mapGuiBean = mapGuiBean;
	}
	
	public void doinit() {
		mkFaultTrace();
	}

	/**
	 * This make the faultTrace from the fault section database that is being maintained by UCERF project
	 * via email by vipin on 01/20/07:
	 * Here are the fault sections that need to be combined:

	San Andreas (Mojave S)
	-118.508948,34.698495
	-118.103936,34.547849
	-117.753579,34.402927
	-117.549,34.3163
	upper depth = 0;
	lower depth = 13.1
	dip = 90
	rake = 180

	San Andreas (San Bernardino N)
	-117.549,34.3163
	-117.451,34.2709
	-117.388692,34.232843
	-117.274161,34.173137
	-117.222023,34.150027
	upper depth = 0;
	lower depth = 12.8
	dip = 90
	rake = 180


	San Andreas (San Bernardino S)
	-117.222023,34.150027
	-117.067674,34.092795
	-117.0139,34.073768
	-116.90235,34.033837
	-116.873541,34.011347
	-116.819795,33.959114
	upper depth = 0;
	lower depth = 12.8
	dip = 90
	rake = 180

	San Andreas (San Gorgonio Pass-Garnet HIll)
	-116.24629,33.78825
	-116.383007,33.848518
	-116.426527,33.848123
	-116.516889,33.884664
	-116.584856,33.907018
	-116.623871,33.917569
	-116.685809,33.944163
	-116.778598,33.937411
	-116.801391,33.953154
	upper depth = 0;
	lower depth = 12.8
	dip = 58
	rake = NA

	San Andreas (Coachella) rev
	-116.24629,33.78825
	-115.71192,33.35009
	upper depth = 0;
	lower depth = 11.1
	dip = 90
	rake = 180

	 */
	private void mkFaultTrace() {
		FaultTrace faultTrace1 =  new FaultTrace("San Andreas Fault Trace(Mojave S)");
		//San Andreas (Mojave S)
		faultTrace1.add(new Location(34.698495,-118.508948));
		faultTrace1.add(new Location(34.547849,-118.103936));
		faultTrace1.add(new Location(34.402927,-117.753579));
		faultTrace1.add(new Location(34.3163,-117.549));
		SimpleFaultData faultData1 = new SimpleFaultData(90,13.1,0,faultTrace1);

		//San Andreas (San Bernardino N)
		FaultTrace faultTrace2 =  new FaultTrace("San Andreas (San Bernardino N)");
		faultTrace2.add(new Location(34.3163,-117.549));
		faultTrace2.add(new Location(34.2709,-117.451));
		faultTrace2.add(new Location(34.232843,-117.388692));
		faultTrace2.add(new Location(34.173137,-117.274161));
		faultTrace2.add(new Location(34.150027,-117.222023));
		SimpleFaultData faultData2 = new SimpleFaultData(90,12.8,0,faultTrace2);

		//San Andreas (San Bernardino S)
		FaultTrace faultTrace3 =  new FaultTrace("San Andreas (San Bernardino S)");
		faultTrace3.add(new Location(34.150027,-117.222023));
		faultTrace3.add(new Location(34.092795,-117.067674));
		faultTrace3.add(new Location(34.073768,-117.0139));
		faultTrace3.add(new Location(34.033837,-116.90235));
		faultTrace3.add(new Location(34.011347,-116.873541));
		faultTrace3.add(new Location(33.959114,-116.819795));
		SimpleFaultData faultData3 = new SimpleFaultData(90,12.8,0,faultTrace3);

		//San Andreas (San Gorgonio Pass-Garnet HIll)
		FaultTrace faultTrace4 =  new FaultTrace("San Andreas (San Gorgonio Pass-Garnet HIll)");
		faultTrace4.add(new Location(33.78825,-116.24629));
		faultTrace4.add(new Location(33.848518,-116.383007));
		faultTrace4.add(new Location(33.848123,-116.426527));
		faultTrace4.add(new Location(33.884664,-116.516889));
		faultTrace4.add(new Location(33.907018,-116.584856));
		faultTrace4.add(new Location(33.917569,-116.623871));
		faultTrace4.add(new Location(33.944163,-116.685809));
		faultTrace4.add(new Location(33.937411,-116.778598));
		faultTrace4.add(new Location(33.953154,-116.801391));
		SimpleFaultData faultData4 = new SimpleFaultData(58,12.8,0,faultTrace4);

		//San Andreas (Coachella) rev
		FaultTrace faultTrace5 =  new FaultTrace("San Andreas (Coachella) rev");
		faultTrace5.add(new Location(33.78825,-116.24629));
		faultTrace5.add(new Location(33.35009,-115.71192));
		SimpleFaultData faultData5 = new SimpleFaultData(90,11.1,0,faultTrace5);

		ArrayList<SimpleFaultData> faultList = new ArrayList<SimpleFaultData>();
		faultList.add(faultData1);
		faultList.add(faultData2);
		faultList.add(faultData3);
		faultList.add(faultData4);
		faultList.add(faultData5);
		sanAndreasFaultData = SimpleFaultData.getCombinedSimpleFaultData(faultList);
	}




	/**
	 * Sets the default Parameters in the Application for the Puente Hill Scenario
	 */
	public void applyControl(){
		//making the ERF Gui Bean Adjustable Param not visible to the user, becuase
		//this control panel will set the values by itself.
		//This is done in the EqkRupSelectorGuiBean
		ParameterEditor paramEditor = erfGuiBean.getParameterEditor(erfGuiBean.RUPTURE_SELECTOR_PARAM_NAME);
		paramEditor.setValue(erfGuiBean.CREATE_RUPTURE);
		paramEditor.refreshParamEditor();
		EqkRuptureCreationPanel erfPanel= (EqkRuptureCreationPanel)erfGuiBean.getEqkRuptureSelectorPanel();

		//changing the ERF to SimpleFaultERF
		paramEditor = erfPanel.getParameterEditor(erfPanel.SRC_TYP_PARAM_NAME);
		paramEditor.setValue(erfPanel.FINITE_SRC_NAME);
		paramEditor.refreshParamEditor();


		// Set rake value to 90 degrees
		erfPanel.getParameter(erfPanel.RAKE_PARAM_NAME).setValue(new Double(180));


		//getting the instance for the SimpleFaultParameterEditorPanel from the GuiBean to adjust the fault Params
		SimpleFaultParameterEditorPanel faultPanel= ((SimpleFaultParameterEditor)erfPanel.getParameterEditor(erfPanel.FAULT_PARAM_NAME)).getParameterEditorPanel();
		//creating the Lat vector for the SimpleFaultParameter

		ArrayList lats = new ArrayList();
		ArrayList lons = new ArrayList();
		FaultTrace faultTrace = sanAndreasFaultData.getFaultTrace();
		for(int i = 0; i<faultTrace.getNumLocations(); i++) {
			lats.add(new Double(faultTrace.get(i).getLatitude()));
			lons.add(new Double(faultTrace.get(i).getLongitude()));
		}

		//creating the dip vector for the SimpleFaultParameter
		ArrayList dips = new ArrayList();
		dips.add(new Double(sanAndreasFaultData.getAveDip()));


		//creating the depth vector for the SimpleFaultParameter
		ArrayList depths = new ArrayList();
		depths.add(new Double(sanAndreasFaultData.getUpperSeismogenicDepth()));
		depths.add(new Double(sanAndreasFaultData.getLowerSeismogenicDepth()));

		//setting the FaultParameterEditor with the default values for Puente Hills Scenario
		faultPanel.setAll(((SimpleFaultParameter)faultPanel.getParameter()).DEFAULT_GRID_SPACING,lats,
				lons,dips,depths,((SimpleFaultParameter)faultPanel.getParameter()).STIRLING);

		// set the average dip direction
		// use default which is perp to ave strike.
		//    faultPanel.setDipDirection(aveDipDir);

		//updaing the faultParameter to update the faultSurface
		faultPanel.setEvenlyGriddedSurfaceFromParams();

		erfPanel.getParameter(erfPanel.MAG_PARAM_NAME).setValue(new Double(magnitude));
		erfPanel.getParameterListEditor().refreshParamEditor();


		//checking if the single AttenRel is selected
		boolean isSingleAttenRelSelected =imrGuiBean.isSingleAttenRelTypeSelected();
		//if single attenRel gui is not selected then toggle to the single attenRel gui Panel
		if(!isSingleAttenRelSelected)
			imrGuiBean.toggleBetweenSingleAndMultipleAttenRelGuiSelection();
		// Set the imt as PGA
		ParameterListEditor editor = imrGuiBean.getIntensityMeasureParamEditor();
		editor.getParameterList().getParameter(imrGuiBean.IMT_PARAM_NAME).setValue(PGV_Param.NAME);
		editor.refreshParamEditor();
		//Updating the IMR Gui Bean with the ShakeMap attenuation relationship
		imrGuiBean.setIMR_Selected(Field_2000_AttenRel.NAME);
		imrGuiBean.getSelectedIMR_Instance().getParameter(ComponentParam.NAME).setValue(ComponentParam.COMPONENT_AVE_HORZ);
		imrGuiBean.getSingleAttenRelParamListEditor().refreshParamEditor();

		//Updating the SitesInGriddedRectangularRegionGuiBean with the Puente Hills resion setting
		regionGuiBean.getParameterList().getParameter(regionGuiBean.MIN_LATITUDE).setValue(new Double(32.3));
		regionGuiBean.getParameterList().getParameter(regionGuiBean.MAX_LATITUDE).setValue(new Double(35.5));
		regionGuiBean.getParameterList().getParameter(regionGuiBean.MIN_LONGITUDE).setValue(new Double(-119.5));
		regionGuiBean.getParameterList().getParameter(regionGuiBean.MAX_LONGITUDE).setValue(new Double(-115));
		regionGuiBean.getParameterList().getParameter(regionGuiBean.GRID_SPACING).setValue(new Double(.02));
		regionGuiBean.getParameterList().getParameter(regionGuiBean.SITE_PARAM_NAME).setValue(SitesInGriddedRectangularRegionGuiBean.USE_SITE_DATA);

		regionGuiBean.refreshParamEditor();


		// Set some of the mapping params:
		mapGuiBean.getParameterList().getParameter(GMT_MapGenerator.CPT_FILE_PARAM_NAME).
		setValue(GMT_MapGenerator.CPT_FILE_SHAKEMAP);
		mapGuiBean.getParameterList().getParameter(GMT_MapGenerator.COLOR_SCALE_MODE_NAME).
		setValue(GMT_MapGenerator.COLOR_SCALE_MODE_MANUALLY);
		mapGuiBean.getParameterList().getParameter(GMT_MapGenerator.COLOR_SCALE_MIN_PARAM_NAME).
		setValue(new Double(-0.39));
		mapGuiBean.getParameterList().getParameter(GMT_MapGenerator.COLOR_SCALE_MAX_PARAM_NAME).
		setValue(new Double(2.2));
		mapGuiBean.getParameterList().getParameter(GMT_MapGenerator.SHOW_HIWYS_PARAM_NAME).
		setValue(GMT_MapGenerator.SHOW_HIWYS_ALL);
		mapGuiBean.getParameterList().getParameter(GMT_MapGenerator.GMT_WEBSERVICE_NAME).setValue(new Boolean(true));
		mapGuiBean.getParameterList().getParameter(GMT_MapGenerator.LOG_PLOT_NAME).setValue(new Boolean(true));
		mapGuiBean.refreshParamEditor();
	}
}
