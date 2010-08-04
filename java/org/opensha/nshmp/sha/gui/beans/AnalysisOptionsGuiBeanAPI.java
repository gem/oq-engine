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

import javax.swing.JPanel;

/**
 * <p>Title: AnalysisOptionsGuiBeanAPI</p>
 *
 * <p>Description: This interface is implemented by all the Analysis Option
 * Gui Beans. For eg: Gui Bean(NEHRP_GuiBean) for the NEHRP analysis option selection
 * implements this GUI bean. This has been done becuase application can show the
 * GUIbean in the main application without knowing which GUI bean it is actually
 * calling. As all GUI beans for analysis option implements this interface, so
 * application just create instance the instance of this interface and contact
 * the GUI beans using this interface</p>
 *
 * @author Ned Field, Nitin Gupta and E.V.Leyendecker
 * @version 1.0
 */
public interface AnalysisOptionsGuiBeanAPI {

  /**
   * Gets the panel for the Gui Bean for the selected analysis option in the
   * application.
   */
  public JPanel getGuiBean();

  /**
   * Clears the Data window
   */
  public void clearData();

  /**
   *
   * @return String
   */
  public String getData();

  /**
   * Returns the selected Region
   * @return String
   */
  public String getSelectedRegion();

  /**
   * Returns the selected data edition
   * @return String
   */
  public String getSelectedDataEdition();


}
