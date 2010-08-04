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

import java.io.BufferedReader;
import java.io.FileReader;
import java.util.StringTokenizer;

import org.opensha.commons.param.editor.ParameterEditor;
import org.opensha.sha.earthquake.rupForecastImpl.Frankel02.Frankel02_AdjustableEqkRupForecast;
import org.opensha.sha.gui.beans.AttenuationRelationshipGuiBean;
import org.opensha.sha.gui.beans.ERF_GuiBean;
import org.opensha.sha.gui.beans.EqkRupSelectorGuiBean;
import org.opensha.sha.gui.beans.EqkRuptureFromERFSelectorPanel;
import org.opensha.sha.gui.beans.MapGuiBean;
import org.opensha.sha.gui.beans.SitesInGriddedRectangularRegionGuiBean;
import org.opensha.sha.imr.attenRelImpl.ShakeMap_2003_AttenRel;

/**
 * <p>Title: SF_BayAreaScenarioControlPanel</p>
 * <p>Description: Sets the param value  of scenario shakemaps for SF Bay Area</p>
 * @author : Edward (Ned) Field and Nitin Gupta
 * @version 1.0
 */

public class SF_BayAreaScenarioControlPanel {

  //for debugging
  protected final static boolean D = false;


  private EqkRupSelectorGuiBean erfGuiBean;
  private AttenuationRelationshipGuiBean imrGuiBean;
  private SitesInGriddedRectangularRegionGuiBean regionGuiBean;
  private MapGuiBean mapGuiBean;
  private GenerateHazusControlPanelForSingleMultipleIMRs hazusControlPanel;


  private final static String fileToRead = "shakemaps_request.txt";


  //class default constructor
  /**
   * Accepts 3 params for the EqkRupSelectorGuiBean, IMR_GuiBean, SitesInGriddedRectangularRegionGuiBean
   * from the applet.
   * @param erfGuiBean
   * @param imrGuiBean
   * @param regionGuiBean
   */
  public SF_BayAreaScenarioControlPanel(EqkRupSelectorGuiBean erfGuiBean, AttenuationRelationshipGuiBean imrGuiBean,
      SitesInGriddedRectangularRegionGuiBean regionGuiBean,MapGuiBean mapGuiBean,
      GenerateHazusControlPanelForSingleMultipleIMRs hazusControl) {
    //getting the instance for variuos GuiBeans from the applet required to set the
    //default values for the Params for the SF Bay Area Scenarios.
    this.erfGuiBean = erfGuiBean;
    this.imrGuiBean = imrGuiBean;
    this.regionGuiBean = regionGuiBean;
    this.mapGuiBean =  mapGuiBean;
    hazusControlPanel = hazusControl;
  }

  /**
   * Sets the default Parameters in the Application for the SF Bay Area Scenarios.
   * Also generate the Hazus data and scenario shakemaps for the SF Bay area.
   */
  public void setParamsForSF_BayAreaScenario(){


    try{

      //checking if the single AttenRel is selected
      boolean isSingleAttenRelSelected =imrGuiBean.isSingleAttenRelTypeSelected();
      //if single attenRel gui is not selected then toggle to the single attenRel gui Panel
      if(!isSingleAttenRelSelected)
        imrGuiBean.toggleBetweenSingleAndMultipleAttenRelGuiSelection();

      //Updating the IMR Gui Bean with the ShakeMap attenuation relationship
      imrGuiBean.setIMR_Selected(ShakeMap_2003_AttenRel.NAME);
      imrGuiBean.getSingleAttenRelParamListEditor().refreshParamEditor();


      //Updating the SitesInGriddedRectangularRegionGuiBean with the Puente Hills resion setting
      regionGuiBean.getParameterList().getParameter(SitesInGriddedRectangularRegionGuiBean.MIN_LATITUDE).setValue(new Double(36.5500));
      regionGuiBean.getParameterList().getParameter(SitesInGriddedRectangularRegionGuiBean.MAX_LATITUDE).setValue(new Double(39.6167));
      regionGuiBean.getParameterList().getParameter(SitesInGriddedRectangularRegionGuiBean.MIN_LONGITUDE).setValue(new Double(-124.7333));
      regionGuiBean.getParameterList().getParameter(SitesInGriddedRectangularRegionGuiBean.MAX_LONGITUDE).setValue(new Double(-120.1333));
      regionGuiBean.getParameterList().getParameter(SitesInGriddedRectangularRegionGuiBean.GRID_SPACING).setValue(new Double(.016667));
      regionGuiBean.getParameterList().getParameter(SitesInGriddedRectangularRegionGuiBean.SITE_PARAM_NAME).setValue(SitesInGriddedRectangularRegionGuiBean.USE_SITE_DATA);
      
      regionGuiBean.refreshParamEditor();

      //making the ERF Gui Bean Adjustable Param not visible to the user, becuase
      //this control panel will set the values by itself.
      //This is done in the EqkRupSelectorGuiBean
      EqkRuptureFromERFSelectorPanel erfPanel = (EqkRuptureFromERFSelectorPanel)erfGuiBean.getEqkRuptureSelectorPanel();
      erfPanel.showAllParamsForForecast(false);

      //changing the ERF to Frankel02_AdjustableEqkRupForecast
      ParameterEditor paramEditor = erfGuiBean.getParameterEditor(erfPanel.ERF_PARAM_NAME);
      paramEditor.setValue(Frankel02_AdjustableEqkRupForecast.NAME);
      paramEditor.refreshParamEditor();

      //Getting the instance for the editor that holds all the adjustable params for the selcetd ERF
      ERF_GuiBean erfParamGuiBean =erfPanel.getERF_ParamEditor();

      //reading the file sent by Paul to generate the shakemaps for defined sources and ruptures
      FileReader fr = new FileReader(fileToRead);
      BufferedReader br = new BufferedReader(fr);

      //reading the fileLine from the , where each line is in following order:
      //source index,rupture index, rupture offset,magnitude,source name
      String fileLines = br.readLine();
      while(fileLines !=null){
        StringTokenizer st = new StringTokenizer(fileLines);
        //getting the source number
        int sourceIndex = Integer.parseInt(st.nextToken().trim());

        //getting the rupture number
        int ruptureIndex =0;
        String rupIndex = st.nextToken().trim();
        ruptureIndex = Integer.parseInt(rupIndex);

        //getting the rupture offset.
        String ruptureOffset = st.nextToken().trim();
        double rupOffset = 100;
        rupOffset = Double.parseDouble(ruptureOffset);

        //discarding the magnitude that we are reading.
        st.nextToken();

        //getting the name of the directory
        String directoryName = st.nextToken().trim();

        fileLines = br.readLine();

        // Set rake value to 90 degrees
        erfParamGuiBean.getERFParameterList().getParameter(Frankel02_AdjustableEqkRupForecast.RUP_OFFSET_PARAM_NAME).setValue(new Double(rupOffset));
        //updating the forecast with the changed parameter settings.
        erfParamGuiBean.getSelectedERF().updateForecast();

        //updating the EQK_RupSelectorGuiBean with the Source and Rupture Index respectively.
        //updating the EQK_RupSelectorGuiBean with the Source and Rupture Index respectively.
        erfPanel.setSourceFromSelectedERF(sourceIndex);
        erfPanel.setRuptureForSelectedSource(ruptureIndex);
        erfPanel.getHypocenterLocationsForSelectedRupture();
        mapGuiBean.setDirectoryName(directoryName);
        hazusControlPanel.runToGenerateShapeFilesAndMaps();
      }
    }catch(Exception e){
      e.printStackTrace();
    }
  }
}

