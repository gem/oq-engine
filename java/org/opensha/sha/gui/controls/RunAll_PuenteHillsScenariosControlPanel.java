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
import java.util.StringTokenizer;

import org.opensha.commons.util.RunScript;
import org.opensha.sha.gui.beans.ERF_GuiBean;
import org.opensha.sha.gui.beans.EqkRupSelectorGuiBean;
import org.opensha.sha.gui.beans.EqkRuptureFromERFSelectorPanel;
import org.opensha.sha.gui.beans.IMR_GuiBean;
import org.opensha.sha.imr.attenRelImpl.AS_1997_AttenRel;
import org.opensha.sha.imr.attenRelImpl.BJF_1997_AttenRel;
import org.opensha.sha.imr.attenRelImpl.CB_2003_AttenRel;
import org.opensha.sha.imr.attenRelImpl.Field_2000_AttenRel;
import org.opensha.sha.imr.attenRelImpl.SadighEtAl_1997_AttenRel;
import org.opensha.sha.imr.attenRelImpl.ShakeMap_2003_AttenRel;
import org.opensha.sha.magdist.SingleMagFreqDist;
import org.opensha.sha.param.MagFreqDistParameter;
import org.opensha.sha.param.editor.MagFreqDistParameterEditor;

/**
 * <p>Title: RunAll_PuenteHillsScenariosControlPanel</p>
 * <p>Description: Automate the process of running all the scenarios for the
 * Puente Hills.</p>
 * @author : Edward (Ned) Field and Nitin Gupta
 * @version 1.0
 */

public class RunAll_PuenteHillsScenariosControlPanel {


  //ArrayList to store the magnitudes
  ArrayList magnitudes = new ArrayList();
  ArrayList attenuationRelationships = new ArrayList();

  //instance of the application using this control panel
  RunAll_PuenteHillsScenariosControlPanelAPI application;

  /**
   * Class Constructor
   * @param puenteHillsControl
   */
  public RunAll_PuenteHillsScenariosControlPanel(RunAll_PuenteHillsScenariosControlPanelAPI api){
    application = api;
    //adding the magnitudes to the ArrayList List
    magnitudes.add(new Double(7.1));
    magnitudes.add(new Double(7.2));
    magnitudes.add(new Double(7.3));
    magnitudes.add(new Double(7.4));
    magnitudes.add(new Double(7.5));

    //adding the supported AttenuationRelationshipsName to the ArrayList List
    attenuationRelationships.add(AS_1997_AttenRel.NAME);
    attenuationRelationships.add(BJF_1997_AttenRel.NAME);
    attenuationRelationships.add(CB_2003_AttenRel.NAME);
    attenuationRelationships.add(Field_2000_AttenRel.NAME);
    attenuationRelationships.add(SadighEtAl_1997_AttenRel.NAME);
    attenuationRelationships.add(ShakeMap_2003_AttenRel.NAME);
  }


  /**
   * Runs all the cases for the Puente Hill Scenarios
   * @param puenteHillsControl
   * @param hazusControl: Handle to the class to generate the shape files for input to Hazus
   * @param imrGuiBean
   */
  public void runAllScenarios(PuenteHillsScenarioControlPanel puenteHillsControl,
                              GenerateHazusFilesControlPanel hazusControl,IMR_GuiBean imrGuiBean,
                              EqkRupSelectorGuiBean erfGuiBean){
    String COMMAND_PATH = "/bin/";
    int magSize = magnitudes.size();
    int attenRelSize = attenuationRelationships.size();
    String[] command ={"sh","-c",""};
    hazusControl.getRegionAndMapType();
    for(int i=0;i<magSize;++i){

      //set the magnitude
      EqkRuptureFromERFSelectorPanel erfPanel = (EqkRuptureFromERFSelectorPanel)erfGuiBean.getEqkRuptureSelectorPanel();
      ERF_GuiBean erfParamGuiBean =erfPanel.getERF_ParamEditor();
      MagFreqDistParameterEditor magEditor = erfParamGuiBean.getMagDistEditor();
      magEditor.getParameter(MagFreqDistParameter.DISTRIBUTION_NAME).setValue(SingleMagFreqDist.NAME);
      magEditor.getParameter(MagFreqDistParameter.SINGLE_PARAMS_TO_SET).setValue(MagFreqDistParameter.MAG_AND_MO_RATE);
      magEditor.getParameter(MagFreqDistParameter.MAG).setValue(new Double(((Double)magnitudes.get(i)).doubleValue()));
      erfParamGuiBean.getERFParameterListEditor().refreshParamEditor();
      magEditor.setMagDistFromParams();
      //updating the EQK_RupSelectorGuiBean with the Source and Rupture Index respectively.
      erfPanel.setSourceFromSelectedERF(0);
      erfPanel.setRuptureForSelectedSource(0);
      erfPanel.getHypocenterLocationsForSelectedRupture();

      for(int j=0;j<attenRelSize;++j){
        imrGuiBean.getParameterEditor(imrGuiBean.IMR_PARAM_NAME).setValue(attenuationRelationships.get(j));
        //calls the Hazus Control method to generate the XYZ datset for generating shapefiles
        //for hazus.
        hazusControl.generateShapeFilesForHazus();
        application.addButton();
        // Make a directory and move all the files into it
        StringTokenizer st = new StringTokenizer((String)attenuationRelationships.get(j));
        String dirName = "PH_"+st.nextToken()+"_"+((Double)magnitudes.get(i)).doubleValue();

        ArrayList scriptLines = new ArrayList();
        command[2] = COMMAND_PATH+"mkdir "+dirName;
        RunScript.runScript(command);
//        command[2] = COMMAND_PATH+"mv *.txt *.ps *.jpg *.shx *.shp *.dbf  "+dirName;
        command[2] = COMMAND_PATH+"mv *map*  "+dirName;
        RunScript.runScript(command);
      }
    }

  }

}
