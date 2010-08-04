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

package org.opensha.refFaultParamDb.gui.infotools;

import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.text.DecimalFormat;

import javax.swing.JPanel;

import org.opensha.commons.gui.TitledBorderPanel;

/**
 * <p>Title: GUI_Utils.java </p>
 * <p>Description: </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class GUI_Utils {
  public final static GridBagLayout gridBagLayout = new GridBagLayout();
  public final static DecimalFormat decimalFormat = new DecimalFormat("0.0####");
  public final static DecimalFormat latFormat = new DecimalFormat("0.0000");
  public final static DecimalFormat lonFormat = new DecimalFormat("0.000");

  /**
   * Get Bordered Panel
   *
   * @param infoLabel
   * @param borderTitle
   * @return
   */
   public static JPanel getPanel(InfoLabel infoLabel, String borderTitle) {
     JPanel panel = new TitledBorderPanel(borderTitle+":");
     panel.setLayout(gridBagLayout);
     panel.add(infoLabel,new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0
         ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ) );
     return panel;
   }

   /**
   * Get Bordered Panel
   *
   * @param infoLabel
   * @param borderTitle
   * @return
   */
   public static JPanel getPanel(String borderTitle) {
     JPanel panel = new TitledBorderPanel(borderTitle+":");
     panel.setLayout(gridBagLayout);
     return panel;
   }

}
