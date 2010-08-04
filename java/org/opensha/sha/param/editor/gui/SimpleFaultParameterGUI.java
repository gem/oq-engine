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

package org.opensha.sha.param.editor.gui;

import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;

import javax.swing.JButton;
import javax.swing.JDialog;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.WindowConstants;

import org.opensha.commons.param.ParameterAPI;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.param.SimpleFaultParameter;

/**
 * <p>Title: SimpleFaultParameterGUI</p>
 * <p>Description: Creates a GUI interface to the EvelyGriddedSurface Parameter.
 * This GUI acts as the intermediatary between the SimpleFaultEditor which is just a
 * simple button and the SimpleFaultEditorPanel which shows the actual values for the parameters.
 * So SimpleFaultEditor gets the access to the values of the parameters using this GUI.</p>
 * @author : Edward Field, Nitin Gupta and Vipin Gupta
 * @created : Aug 3,2003
 * @version 1.0
 */

public class SimpleFaultParameterGUI extends JDialog{
  private JPanel evenlyGriddedSurfacePanel = new JPanel();
  private JScrollPane evenlyGriddedParamsScroll = new JScrollPane();
  private JButton button = new JButton();
  private GridBagLayout gridBagLayout1 = new GridBagLayout();
  private BorderLayout borderLayout1 = new BorderLayout();
  private JPanel parameterPanel = new JPanel();
  private GridBagLayout gridBagLayout2 = new GridBagLayout();



  //Object for the SimpleFaultParameterEditorPanel
  SimpleFaultParameterEditorPanel faultEditorPanel;

  //Constructor that takes the Object for the SimpleFaultParameter
  public SimpleFaultParameterGUI(ParameterAPI surfaceParam) {
    this.setModal(true);
    try {
      jbInit();
    }
    catch(Exception e) {
      e.printStackTrace();
    }

    //creating the object for the SimpleFaultParameter Editor
    faultEditorPanel = new SimpleFaultParameterEditorPanel(surfaceParam);
    parameterPanel.add(faultEditorPanel,  new GridBagConstraints(0, 0, 0, 1, 1.0, 1.0
            ,GridBagConstraints.NORTH, GridBagConstraints.BOTH, new Insets(4, 4, 4, 4), 0, 0));
  }

  public static void main(String[] args) {
    SimpleFaultParameter surfaceParam = new SimpleFaultParameter("Fault-1",null);
    SimpleFaultParameterGUI simpleFaultParameterGUI = new SimpleFaultParameterGUI(surfaceParam);
    simpleFaultParameterGUI.setVisible(true);
    simpleFaultParameterGUI.pack();
  }

  private void jbInit() throws Exception {
    this.getContentPane().setLayout(borderLayout1);
    evenlyGriddedSurfacePanel.setLayout(gridBagLayout1);
    parameterPanel.setLayout(gridBagLayout2);
    evenlyGriddedSurfacePanel.setPreferredSize(new Dimension(300, 450));
    evenlyGriddedParamsScroll.setPreferredSize(new Dimension(300, 450));
    this.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
    this.getContentPane().add(evenlyGriddedSurfacePanel, BorderLayout.CENTER);
    evenlyGriddedSurfacePanel.add(evenlyGriddedParamsScroll,   new GridBagConstraints(0, 0, 0, 1, 1.0, 1.0
            ,GridBagConstraints.NORTH, GridBagConstraints.BOTH, new Insets(4, 4, 4, 4), 0, 0));
    evenlyGriddedSurfacePanel.add(button,  new GridBagConstraints(0, 1, 1, 1, 0.0, 0.0
            ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(4, 4, 4, 4), 0, 0));
    button.setText("Make Simple Fault");
    button.setForeground(new Color(80,80,133));
    button.addActionListener(new java.awt.event.ActionListener() {
     public void actionPerformed(ActionEvent e) {
       button_actionPerformed(e);
     }
    });
    evenlyGriddedParamsScroll.getViewport().add(parameterPanel, null);
    this.setSize(300,450);
    this.setTitle("Simple Fault Parameter Settings");
  }

  void button_actionPerformed(ActionEvent e) {
    boolean disposeFlag = true;
    try{
      faultEditorPanel.setEvenlyGriddedSurfaceFromParams();
    }catch(RuntimeException ee){
      disposeFlag = false;
      ee.printStackTrace();
      JOptionPane.showMessageDialog(this,ee.getMessage(),"Incorrect Input Parameters",JOptionPane.OK_OPTION);
    }

    //donot close the application  if any exception has been thrown by the application
    if(disposeFlag)
      this.dispose();
  }

  /**
   * gets the fault trace for the griddedSurface
   * @return
   */
  public FaultTrace getFaultTrace(){
   return ((SimpleFaultParameter)faultEditorPanel.getParameter()).getFaultTrace();
  }

  /**
   * gets the Upper Siesmogenic depth for the gridded surface
   * @return
   */
  public double getUpperSies(){
    return ((SimpleFaultParameter)faultEditorPanel.getParameter()).getUpperSiesmogenicDepth();
  }

  /**
   * gets the lower Seismogenic depth for the gridded surface
   * @return
   */
  public double getLowerSies(){
    return ((SimpleFaultParameter)faultEditorPanel.getParameter()).getLowerSiesmogenicDepth();
  }

  /**
   * gets the fault Name
   * @return
   */
  public String getFaultName(){
    return ((SimpleFaultParameter)faultEditorPanel.getParameter()).getFaultName();
  }

  /**
   * Intermediate step to call the refreshParamEditor for the SimpleFaultEditorPanel
   * becuase the SimpleFaultEditorPanel is just a simple Editor that shows the
   * button in the window. But when you click the button only then the actual
   * parameter values comes up
   */
  public void refreshParamEditor(){
    faultEditorPanel.refreshParamEditor();
  }

  /**
   * Sets the Value of the SimpleFaultParameter
   * @param param
   */
  public void setParameter(ParameterAPI param){
    faultEditorPanel.setParameter(param);
  }

  /**
   *
   * @returns the Object for the SimpleFaultEditorPanel which actually contains the
   * values of the parameter for the SimpleFaultParameter
   */
  public SimpleFaultParameterEditorPanel getSimpleFaultEditorPanel(){
    return this.faultEditorPanel;
  }

}
