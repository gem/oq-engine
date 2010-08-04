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

package org.opensha.nshmp.sha.gui.beans;

import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.util.ArrayList;

import javax.swing.JPanel;

import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ConstrainedStringParameterEditor;

/**
 * <p>Title: DataSetSelectionGuiBean</p>
 *
 * <p>Description: Allows user to select from the choices of various analysis types.</p>
 * @author : Ned Field, Nitin Gupta and E.V. Leyendecker
 * @version 1.0
 */
public class DataSetSelectionGuiBean {

  //Parameters that allows for the selection for the choices of edition.
  private StringParameter editionChoicesParam;
  public static final String EDITION_PARAM_NAME = "Data Edition";

  //Parameters that allows for the selection for the choices of geographic region.
  private StringParameter geographicRegionSelectionParam;
  public final static String GEOGRAPHIC_REGION_SELECTION_PARAM_NAME =
      "Geographic Region";

  private JPanel editorPanel;

  private ConstrainedStringParameterEditor regionEditor;
  private ConstrainedStringParameterEditor editionEditor;

  public DataSetSelectionGuiBean() {
  }

  /**
   * Creating the Editor for user to choose the Geographic Region and Data edition
   */
  public void createDataSetEditor() {

    editorPanel = new JPanel();
    editorPanel.setLayout(new GridBagLayout());
    editorPanel.add(regionEditor, new GridBagConstraints(0, 0, 0, 1, 1.0, 1.0
        , GridBagConstraints.NORTH, GridBagConstraints.HORIZONTAL,
        new Insets(2, 2, 2, 2), 0, 0));
    editorPanel.add(editionEditor, new GridBagConstraints(0, 1, 0, 1, 1.0, 1.0
        , GridBagConstraints.NORTH, GridBagConstraints.HORIZONTAL,
        new Insets(2, 2, 2, 2), 0, 0));
    editorPanel.setMinimumSize(new Dimension(0,0));
  }

  /**
   * Returns the parameter list editor that holds the Parameter List
   * @return JPanel
   */
  public JPanel getDatasetSelectionEditor() {
    return editorPanel;
  }

  /**
   * Returns the selected geographic region parameter
   * @return String
   */
  public String getSelectedGeographicRegion() {
    return (String) geographicRegionSelectionParam.getValue();
  }

  /**
   * Returns the selected geographic region parameter
   * @return String
   */
  public String getSelectedDataSetEdition() {
	String r = (String) editionChoicesParam.getValue();
	//if(r.equals(GlobalConstants.NFPA_2003)) {
	//	r = GlobalConstants.ASCE_2002;
	//} else if (r.equals(GlobalConstants.NFPA_2006)) {
	//	r = GlobalConstants.ASCE_2005;
	//}
  
	return r;
    //return (String) editionChoicesParam.getValue();
  }

  /*
   * Creating the parameter that allows user to choose the geographic region list
   *
   */
  public void createGeographicRegionSelectionParameter(ArrayList
      supportedRegionList) {

    geographicRegionSelectionParam = new StringParameter(
        GEOGRAPHIC_REGION_SELECTION_PARAM_NAME,
        supportedRegionList, (String) supportedRegionList.get(0));

      try{
        regionEditor = new ConstrainedStringParameterEditor(
            geographicRegionSelectionParam);
				regionEditor.getValueEditor().setToolTipText(
					"Click on the geographic region name to select the region " +
					"where the site is located.");
      }catch(Exception e){
        e.printStackTrace();
      }
  }

	/**
	 * Returns the editionEditor
	 *
	 * @return ConstrainedStringParameterEditor
	 */
	public ConstrainedStringParameterEditor getEditionEditor() {
		return editionEditor;
	}			

	/**
	 * Returns the regionEditor
	 *
	 * @return ConstrainedStringParameterEditor
	 */
	public ConstrainedStringParameterEditor getRegionEditor() {
		return regionEditor;
	}

  /**
   *
   * @return ParameterAPI
   */
  public ParameterAPI getGeographicRegionSelectionParameter() {
    return geographicRegionSelectionParam;
  }

  /**
   *
   * @return ParameterAPI
   */
  public ParameterAPI getEditionSelectionParameter() {
    return editionChoicesParam;
  }

  /**
   * Creates the Parameter that allows user to select  the Editions based on the
   * selected Analysis and choosen geographic region.
   */
  public void createEditionSelectionParameter(ArrayList supportedEditionList) {
    if(editorPanel !=null)
      editorPanel.remove(editionEditor);

    editionChoicesParam = new StringParameter(EDITION_PARAM_NAME,
                                              supportedEditionList,
                                              (String) supportedEditionList.get(
                                                  0));
    try{
      editionEditor = new ConstrainedStringParameterEditor(editionChoicesParam);
			editionEditor.getValueEditor().setToolTipText(
				"Click on the year to select the item of interest.");
    }catch(Exception e){
      e.printStackTrace();
    }
    if (editorPanel != null) {
      editorPanel.add(editionEditor, new GridBagConstraints(0, 1, 0, 1, 1.0, 1.0
          , GridBagConstraints.NORTH, GridBagConstraints.HORIZONTAL,
          new Insets(2, 2, 2, 2), 0, 0));
      editorPanel.updateUI();
    }

  }

}
