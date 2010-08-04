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

import java.util.ArrayList;

import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.WC1994_MagLengthRelationship;
import org.opensha.commons.mapping.gmt.GMT_MapGenerator;
import org.opensha.commons.param.editor.ParameterEditor;
import org.opensha.sha.earthquake.rupForecastImpl.FloatingPoissonFaultERF;
import org.opensha.sha.gui.beans.ERF_GuiBean;
import org.opensha.sha.gui.beans.EqkRupSelectorGuiBean;
import org.opensha.sha.gui.beans.EqkRuptureFromERFSelectorPanel;
import org.opensha.sha.gui.beans.IMR_GuiBean;
import org.opensha.sha.gui.beans.IMT_GuiBean;
import org.opensha.sha.gui.beans.MapGuiBean;
import org.opensha.sha.gui.beans.SitesInGriddedRectangularRegionGuiBean;
import org.opensha.sha.imr.attenRelImpl.ShakeMap_2003_AttenRel;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.OtherParams.ComponentParam;
import org.opensha.sha.magdist.SingleMagFreqDist;
import org.opensha.sha.param.MagFreqDistParameter;
import org.opensha.sha.param.SimpleFaultParameter;
import org.opensha.sha.param.editor.MagFreqDistParameterEditor;
import org.opensha.sha.param.editor.gui.SimpleFaultParameterEditorPanel;

/**
 * <p>Title: PuenteHillsScenarioTestControlPanel</p>
 * <p>Description: Sets the param value to replicate the official scenario shakemap
 * for the Puente Hill Scenario (http://www.trinet.org/shake/Puente_Hills_se)</p>
 * @author : Edward (Ned) Field and Nitin Gupta
 * @version 1.0
 */

public class PuenteHillsScenarioTestControlPanel {

  private EqkRupSelectorGuiBean erfGuiBean;
  private IMR_GuiBean imrGuiBean;
  private SitesInGriddedRectangularRegionGuiBean regionGuiBean;
  private MapGuiBean mapGuiBean;
  private IMT_GuiBean imtGuiBean;

  //class default constructor
  /**
   * Accepts 3 params for the EqkRupSelectorGuiBean, IMR_GuiBean, SitesInGriddedRectangularRegionGuiBean
   * from the applet.
   * @param erfGuiBean
   * @param imrGuiBean
   * @param regionGuiBean
   * @param MapGuiBean
   * @param IMT_GuiBean
   */
  public PuenteHillsScenarioTestControlPanel(EqkRupSelectorGuiBean erfGuiBean, IMR_GuiBean imrGuiBean,
      SitesInGriddedRectangularRegionGuiBean regionGuiBean, MapGuiBean mapGuiBean, IMT_GuiBean imtGuiBean) {
    //getting the instance for variuos GuiBeans from the applet required to set the
    //default values for the Params for the Puente Hills Scenario.
    this.erfGuiBean = erfGuiBean;
    this.imrGuiBean = imrGuiBean;
    this.regionGuiBean = regionGuiBean;
    this.mapGuiBean = mapGuiBean;
    this.imtGuiBean = imtGuiBean;
    //setParamsForPuenteHillsScenario();
  }

  /**
   * Sets the default Parameters in the Application for the Puente Hill Scenario
   */
  public void setParamsForPuenteHillsScenario(){
    //making the ERF Gui Bean Adjustable Param not visible to the user, becuase
    //this control panel will set the values by itself.
    //This is done in the EqkRupSelectorGuiBean
    ParameterEditor paramEditor = erfGuiBean.getParameterEditor(erfGuiBean.RUPTURE_SELECTOR_PARAM_NAME);
    paramEditor.setValue(erfGuiBean.RUPTURE_FROM_EXISTING_ERF);
    paramEditor.refreshParamEditor();
    EqkRuptureFromERFSelectorPanel erfPanel= (EqkRuptureFromERFSelectorPanel)erfGuiBean.getEqkRuptureSelectorPanel();
    erfPanel.showAllParamsForForecast(false);
    //changing the ERF ro SimpleFaultERF
    paramEditor = erfGuiBean.getParameterEditor(erfPanel.ERF_PARAM_NAME);
    paramEditor.setValue(FloatingPoissonFaultERF.NAME);
    paramEditor.refreshParamEditor();

    //Getting the instance for the editor that holds all the adjustable params for the selcetd ERF
    ERF_GuiBean erfParamGuiBean =erfPanel.getERF_ParamEditor();
    //As the Selecetd ERF is simple FaultERF so updating the rake value to -90 (so the ALL or UKNOWN category is used to be consistent with online shakemaps).
    erfParamGuiBean.getERFParameterList().getParameter(FloatingPoissonFaultERF.RAKE_PARAM_NAME).setValue(new Double(-90));
    erfParamGuiBean.getERFParameterList().getParameter(FloatingPoissonFaultERF.MAG_SCALING_REL_PARAM_NAME).setValue(WC1994_MagLengthRelationship.NAME);

    //getting the instance for the SimpleFaultParameterEditorPanel from the GuiBean to adjust the fault Params
    SimpleFaultParameterEditorPanel faultPanel= erfParamGuiBean.getSimpleFaultParamEditor().getParameterEditorPanel();
    //creating the Lat vector for the SimpleFaultParameter
    ArrayList lats = new ArrayList();
    lats.add(new Double(33.92690));
    lats.add(new Double(33.93150));
    lats.add(new Double(33.95410));
    lats.add(new Double(34.05860));

    //creating the Lon vector for the SimpleFaultParameter
    ArrayList lons = new ArrayList();
    lons.add(new Double(-117.86730));
    lons.add(new Double(-118.04320));
    lons.add(new Double(-118.14350));
    lons.add(new Double(-118.29760));

    //creating the dip vector for the SimpleFaultParameter
    ArrayList dips = new ArrayList();
    dips.add(new Double(25));

    //creating the depth vector for the SimpleFaultParameter
    ArrayList depths = new ArrayList();
    depths.add(new Double(5));
    depths.add(new Double(13));

    //setting the FaultParameterEditor with the default values for Puente Hills Scenario
    faultPanel.setAll(((SimpleFaultParameter)faultPanel.getParameter()).DEFAULT_GRID_SPACING,lats,lons,dips,depths,((SimpleFaultParameter)faultPanel.getParameter()).FRANKEL);
    faultPanel.refreshParamEditor();
    //updaing the faultParameter to update the faultSurface
    faultPanel.setEvenlyGriddedSurfaceFromParams();

    //updating the magEditor with the values for the Puente Hills Scenario
    MagFreqDistParameterEditor magEditor = erfParamGuiBean.getMagDistEditor();
    magEditor.getParameter(MagFreqDistParameter.DISTRIBUTION_NAME).setValue(SingleMagFreqDist.NAME);
    magEditor.getParameter(MagFreqDistParameter.SINGLE_PARAMS_TO_SET).setValue(MagFreqDistParameter.MAG_AND_MO_RATE);
    magEditor.getParameter(MagFreqDistParameter.MAG).setValue(new Double(7.1));
    erfParamGuiBean.getERFParameterListEditor().refreshParamEditor();
    // now have the editor create the magFreqDist
    magEditor.setMagDistFromParams();

    //updating the EQK_RupSelectorGuiBean with the Source and Rupture Index respectively.
    //updating the EQK_RupSelectorGuiBean with the Source and Rupture Index respectively.
    erfPanel.setSourceFromSelectedERF(0);
    erfPanel.setRuptureForSelectedSource(0);


    //Updating the IMR Gui Bean with the ShakeMap attenuation relationship.
    imrGuiBean.getParameterList().getParameter(imrGuiBean.IMR_PARAM_NAME).setValue(ShakeMap_2003_AttenRel.NAME);
    imrGuiBean.getSelectedIMR_Instance().getParameter(ComponentParam.NAME).setValue(ComponentParam.COMPONENT_GREATER_OF_TWO_HORZ);
    imrGuiBean.refreshParamEditor();

    //Updating the SitesInGriddedRectangularRegionGuiBean with the Puente Hills resion setting
    regionGuiBean.getParameterList().getParameter(regionGuiBean.MIN_LATITUDE).setValue(new Double(33.2));
    regionGuiBean.getParameterList().getParameter(regionGuiBean.MAX_LATITUDE).setValue(new Double(34.66));
    regionGuiBean.getParameterList().getParameter(regionGuiBean.MIN_LONGITUDE).setValue(new Double(-119.05));
    regionGuiBean.getParameterList().getParameter(regionGuiBean.MAX_LONGITUDE).setValue(new Double(-116.85));
    regionGuiBean.getParameterList().getParameter(regionGuiBean.GRID_SPACING).setValue(new Double(.016667));
    regionGuiBean.getParameterList().getParameter(regionGuiBean.SITE_PARAM_NAME).setValue(regionGuiBean.SET_SITE_USING_WILLS_SITE_TYPE);

    // Set the imt as PGA
    imtGuiBean.getParameterList().getParameter(imtGuiBean.IMT_PARAM_NAME).setValue(PGA_Param.NAME);
    imtGuiBean.refreshParamEditor();

    // Set some of the mapping params:
    mapGuiBean.getParameterList().getParameter(GMT_MapGenerator.GMT_WEBSERVICE_NAME).setValue(new Boolean(true));
    mapGuiBean.getParameterList().getParameter(GMT_MapGenerator.LOG_PLOT_NAME).setValue(new Boolean(false));
    mapGuiBean.refreshParamEditor();
  }
}
