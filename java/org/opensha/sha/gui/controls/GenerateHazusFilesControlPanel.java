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

import java.awt.BorderLayout;
import java.awt.Component;
import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.SystemColor;
import java.awt.event.ActionEvent;
import java.util.ArrayList;

import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.JTextPane;

import org.opensha.commons.data.ArbDiscretizedXYZ_DataSet;
import org.opensha.commons.data.XYZ_DataSetAPI;
import org.opensha.sha.gui.beans.IMT_GuiBean;
import org.opensha.sha.gui.infoTools.CalcProgressBar;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGV_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;

/**
 * <p>Title: GenerateHazusFilesControlPanel</p>
 * <p>Description: This class generates the ShapeFiles for the Hazus for the
 * selected Scenario.</p>
 * @author : Ned Field, Nitin Gupta and Vipin Gupta
 * @version 1.0
 */

public class GenerateHazusFilesControlPanel extends JFrame {
  private JPanel jPanel1 = new JPanel();
  private JTextPane infoPanel = new JTextPane();
  private BorderLayout borderLayout1 = new BorderLayout();


  //instance of the application calling this control panel.
  private GenerateHazusFilesConrolPanelAPI application;

  //Stores the XYZ data set for the SA-0.3, SA-1.0, PGA and PGV
  private XYZ_DataSetAPI sa03_xyzdata;
  private XYZ_DataSetAPI sa10_xyzdata;
  private XYZ_DataSetAPI pga_xyzdata;
  private XYZ_DataSetAPI pgv_xyzdata;

  //metadata string for the different IMT required to generate the shapefiles for Hazus.
  private String metadata;
  private JButton generateHazusShapeFilesButton = new JButton();
  private GridBagLayout gridBagLayout1 = new GridBagLayout();
  //Object to get the handle to the IMT Gui Bean
  private IMT_GuiBean imtGuiBean;
  //records if the user has pressed the button to generate the XYZ data to produce
  //the shapefiles for inout to Hazus
  boolean generatingXYZDataForShapeFiles= false;

  //progress bar
  CalcProgressBar calcProgress;

  /**
   * Class constructor.
   * This will generate the shapefiles for the input to the Hazus
   * @param parent : parent frame on which to show this control panel
   * @param imrGuiBean :object of IMT_GuiBean to set the imt.
   */
  public GenerateHazusFilesControlPanel(Component parent,IMT_GuiBean imtGui,
                                        GenerateHazusFilesConrolPanelAPI api) {
    imtGuiBean = imtGui;
    // show the window at center of the parent component
    this.setLocation(parent.getX()+parent.getWidth()/2,
                     parent.getY()+parent.getHeight()/2);
    //save the instance of the application
    this.application = api;
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
    this.setTitle("Hazus Shapefiles Control");
    infoPanel.setBackground(SystemColor.menu);
    infoPanel.setEnabled(false);
    String info = new String("This generates a set of Hazus shapefiles (sa-0.3sec,"+
                             " sa-1.0sec, pga and pgv) for the selected Earthquake "+
                             "Rupture and IMR.  Be sure to have selected "+
                             "Average-Horizontal component, and note that PGV in these files "+
                             "is in units of inches/sec (as assumed by Hazus)");
    infoPanel.setPreferredSize(new Dimension(812, 16));
    infoPanel.setEditable(false);
    infoPanel.setText(info);
    jPanel1.setMinimumSize(new Dimension(350, 70));
    jPanel1.setPreferredSize(new Dimension(350, 125));
    generateHazusShapeFilesButton.setText("Generate Hazus Shape Files");
    generateHazusShapeFilesButton.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        generateHazusShapeFilesButton_actionPerformed(e);
      }
    });
    this.getContentPane().add(jPanel1, BorderLayout.CENTER);
    jPanel1.add(infoPanel,  new GridBagConstraints(0, 1, 1, 1, 1.0, 1.0
            ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(0, 42, 19, 41), 0, 0));
    jPanel1.add(generateHazusShapeFilesButton,  new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
            ,GridBagConstraints.NORTH, GridBagConstraints.NONE, new Insets(14, 49, 6, 54), 87, 8));
  }


  /**
   * Generate the dataset to make shapefiles that goes as input to Hazus.
   * For that it iterates over all the following IMT(SA-1sec, SA-0.3sec, PGA and PGV) to
   * create the dataset for them.
   * @param imtGuiBean : instance of the selected IMT
   * @param imr : instance of the selected IMR
   */
  private void generateHazusFiles(AttenuationRelationship imr){

      String sa = SA_Param.NAME;
      String pga = PGA_Param.NAME;
      String pgv = PGV_Param.NAME;

      //Doing for SA
      imtGuiBean.getParameterList().getParameter(imtGuiBean.IMT_PARAM_NAME).setValue(sa);
      //Doing for SA-0.3sec
      imtGuiBean.getParameterList().getParameter(PeriodParam.NAME).setValue(new Double(0.3));
      sa03_xyzdata = application.generateShakeMap();

      metadata = imtGuiBean.getVisibleParameters().getParameterListMetadataString()+"<br>\n";

      //Doing for SA-1.0sec
      imtGuiBean.getParameterList().getParameter(PeriodParam.NAME).setValue(new Double(1.0));
      sa10_xyzdata = application.generateShakeMap();
      metadata += imtGuiBean.getVisibleParameters().getParameterListMetadataString()+"<br>\n";

      //Doing for PGV
      if(imr.isIntensityMeasureSupported(pgv)){
        //if the PGV is supportd by the AttenuationRelationship
        imtGuiBean.getParameterList().getParameter(imtGuiBean.IMT_PARAM_NAME).setValue(pgv);
        pgv_xyzdata = application.generateShakeMap();
        metadata += imtGuiBean.getVisibleParameters().getParameterListMetadataString()+"<br>\n";
      }
      else{
        //if PGV is not supported by the attenuation then use the SA-1sec pd
        //and multiply the value by scaler 37.24*2.54
        ArrayList zVals = sa10_xyzdata.getZ_DataSet();
        int size = zVals.size();
        ArrayList newZVals = new ArrayList();
        for(int i=0;i<size;++i){
          double val = ((Double)zVals.get(i)).doubleValue()*37.24*2.54;
          newZVals.add(new Double(val));
        }
        pgv_xyzdata = new ArbDiscretizedXYZ_DataSet(sa10_xyzdata.getX_DataSet(),
                      sa10_xyzdata.getY_DataSet(), newZVals);
        metadata += "IMT: PGV"+"<br>\n";
      }
      //Doing for PGA
      imtGuiBean.getParameterList().getParameter(imtGuiBean.IMT_PARAM_NAME).setValue(pga);
      pga_xyzdata = application.generateShakeMap();
      metadata += imtGuiBean.getVisibleParameters().getParameterListMetadataString()+"<br>\n";
      calcProgress.showProgress(false);
      calcProgress.dispose();
      imtGuiBean.refreshParamEditor();
  }

  /**
   *
   * @returns the metadata for the IMT GUI if this control panel is selected
   */
  public String getIMT_Metadata(){
    return metadata;
  }


  /**
   *
   * @returns the XYZ data set for the SA-0.3sec
   */
  public XYZ_DataSetAPI getXYZ_DataForSA_03(){
    return sa03_xyzdata;
  }


  /**
   *
   * @return the XYZ data set for the SA-1.0sec
   */
  public XYZ_DataSetAPI getXYZ_DataForSA_10(){
    return sa10_xyzdata;
  }

  /**
   *
   * @return the XYZ data set for the PGA
   */
  public XYZ_DataSetAPI getXYZ_DataForPGA(){
    return pga_xyzdata;
  }

  /**
   *
   * @return the XYZ data set for the PGV
   */
  public XYZ_DataSetAPI getXYZ_DataForPGV(){
    return pgv_xyzdata;
  }

  void generateHazusShapeFilesButton_actionPerformed(ActionEvent e) {
    getRegionAndMapType();
    generateShapeFilesForHazus();
  }

  /**
   * Creates the dataset to generate the shape files that goes as input to Hazus.
   */
  public void generateShapeFilesForHazus(){
    calcProgress = new CalcProgressBar("Hazus Shape file data","Starting Calculation...");
    calcProgress.setProgressMessage("Doing Calculation for the Hazus ShapeFile Data...");
    generateHazusFiles(application.getSelectedAttenuationRelationship());
    //keeps tracks if the user has pressed the button to generate the xyz dataset
    //for prodcing the shapefiles for Hazus.
    generatingXYZDataForShapeFiles = true;
  }

  /**
   * This function sets the Gridded region Sites and the type of plot user wants to see
   * IML@Prob or Prob@IML and it value.
   */
  public void getRegionAndMapType(){
    application.getGriddedSitesAndMapType();
  }

  /**
   *
   * @returns if the user has pressed the button to generate the xyz dataset
   * for prodcing the shapefiles for Hazus
   */
  public boolean isHazusShapeFilesButtonPressed(){
    return generatingXYZDataForShapeFiles;
  }

}
