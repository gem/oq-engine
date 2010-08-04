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

package org.opensha.sha.gui.infoTools;

import java.awt.BorderLayout;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;

import javax.swing.ButtonGroup;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JRadioButton;
import javax.swing.SwingConstants;

/**
 * <p>Title: HazardMapSubmissionMethods</p>
 * <p>Description: This class gives option to the user to choose the option to
 * select the way he wants to plot the map.</p>
 * @author : Nitin Gupta and Vipin Gupta
 * @created : 4 May, 2004
 * @version 1.0
 */

public class HazardMapSubmissionMethods extends JFrame {


  //String Option to select hazard map calculation method
  public final static String USE_GRID = "Use Grid";
  public final static String USE_MULTIPROCESSOR = "Use Multiprocessor";
  public final static String USE_STANDALONE = "Run as Standalone";

  private JPanel jPanel1 = new JPanel();
  private JRadioButton gridOption = new JRadioButton();
  private JRadioButton threadOption = new JRadioButton();
  private JRadioButton standaloneOption = new JRadioButton();
  private JLabel jLabel1 = new JLabel();

  private ButtonGroup buttonGroup = new ButtonGroup();
  private GridBagLayout gridBagLayout1 = new GridBagLayout();
  private BorderLayout borderLayout1 = new BorderLayout();
  public HazardMapSubmissionMethods() {
    try {
      jbInit();
    }
    catch(Exception e) {
      e.printStackTrace();
    }
  }
  private void jbInit() throws Exception {
    this.getContentPane().setLayout(borderLayout1);
    jPanel1.setLayout(gridBagLayout1);
    gridOption.setText(USE_GRID);
    threadOption.setText(USE_MULTIPROCESSOR);
    standaloneOption.setText(USE_STANDALONE);
    gridOption.setActionCommand(USE_GRID);
    threadOption.setActionCommand(USE_MULTIPROCESSOR);
    standaloneOption.setActionCommand(USE_STANDALONE);
    jLabel1.setFont(new java.awt.Font("Lucida Grande", 1, 15));
    jLabel1.setHorizontalAlignment(SwingConstants.CENTER);
    jLabel1.setHorizontalTextPosition(SwingConstants.RIGHT);
    jLabel1.setText("Select Map Calculation Option");
    this.getContentPane().add(jPanel1, BorderLayout.CENTER);
    jPanel1.add(gridOption,  new GridBagConstraints(0, 1, 1, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(24, 60, 0, 127), 114, 16));
    jPanel1.add(threadOption,  new GridBagConstraints(0, 2, 1, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(17, 60, 0, 127), 46, 16));
    jPanel1.add(standaloneOption,  new GridBagConstraints(0, 3, 1, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(16, 60, 84, 127), 52, 16));
    jPanel1.add(jLabel1,  new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
            ,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(17, 20, 0, 25), 116, 10));
    buttonGroup.add(gridOption);
    buttonGroup.add(threadOption);
    buttonGroup.add(standaloneOption);
    buttonGroup.setSelected(gridOption.getModel(),true);
  }

  /**
   *
   * @returns the selected option String choosen by the user
   * to calculate Hazard Map.
   */
  public String getMapCalculationOption(){
    return buttonGroup.getSelection().getActionCommand();
  }
}
