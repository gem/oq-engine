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


import org.opensha.commons.data.XYZ_DataSetAPI;
import org.opensha.sha.imr.AttenuationRelationship;

/**
 * <p>Title: GenerateHazusFilesConrolPanelAPI</p>
 * <p>Description: This interface is the acts as the broker between the
 * application and the GenerateHazusFilesControlPanel</p>
 * @author : Nitin Gupta
 * @version 1.0
 */

public interface GenerateHazusFilesConrolPanelAPI {


  /**
   * This method calculates the probablity or the IML for the selected Gridded Region
   * and stores the value in each vectors(lat-ArrayList, Lon-ArrayList and IML or Prob ArrayList)
   * The IML or prob vector contains value based on what the user has selected in the Map type
   */
  public XYZ_DataSetAPI generateShakeMap();

  /**
   *
   * @returns the selected Attenuationrelationship model within the application
   */
  public AttenuationRelationship getSelectedAttenuationRelationship();


  /**
   * This function sets the Gridded region Sites and the type of plot user wants to see
   * IML@Prob or Prob@IML and it value.
   */
  public void getGriddedSitesAndMapType();

  /**
   * Gets the EqkRupture object from the Eqk Rupture GuiBean
   */
  public void getEqkRupture();

}
