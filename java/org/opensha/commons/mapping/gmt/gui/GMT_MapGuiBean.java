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

package org.opensha.commons.mapping.gmt.gui;

import java.awt.GridBagLayout;
import java.util.ListIterator;

import javax.swing.JOptionPane;

import org.opensha.commons.data.XYZ_DataSetAPI;
import org.opensha.commons.exceptions.GMT_MapException;
import org.opensha.commons.exceptions.RegionConstraintException;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.mapping.gmt.GMT_MapGenerator;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.editor.ParameterListEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.sha.gui.infoTools.ImageViewerWindow;



/**
 * <p>Title: GMT_MapGuiBean</p>
 * <p>Description: This class generates and displays a GMT map for an XYZ dataset using
 * the settings in the GMT_SettingsControlPanel. It displays the image file in a JPanel.
 * </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author: Ned Field, Nitin Gupta & Vipin Gupta
 * @version 1.0
 */

public class GMT_MapGuiBean extends ParameterListEditor implements
    ParameterChangeListener {

  /**
   * Name of the class
   */
  protected final static String C = "MapGuiBean";

  // for debug purpose
  protected final static boolean D = false;


  protected final static String GMT_TITLE = new String("Map Attributes");

  //instance of the GMT Control Panel to get the GMT parameters value.
  protected GMT_MapGenerator gmtMap= new GMT_MapGenerator();


  private GridBagLayout gridBagLayout1 = new GridBagLayout();

  //boolean flag to check if we need to show the Map in a seperate window
  protected boolean showMapInSeperateWindow = true;

  //name of the image file( or else full URL to image file if using the webservice)
  protected String imgName=null;

  //name of the directory in which to store all the map and its related data.
  protected String dirName = null;


  /**
   * Class constructor accepts the GMT parameters list
   * @param api : Instance of the application using this Gui Bean.
   */
  public GMT_MapGuiBean() {

    try {
      //initialise the param list and editor for the GMT Map Params and Editors
      initParamListAndEditor();
    }
    catch(Exception e) {
      e.printStackTrace();
    }
  }



  protected void initParamListAndEditor(){
    //get the adjustableParam List from the GMT_MapGenerator
    ListIterator it=gmtMap.getAdjustableParamsIterator();
    parameterList = new ParameterList();
    while(it.hasNext())
      parameterList.addParameter((ParameterAPI)it.next());
    editorPanel.removeAll();
    addParameters();
    setTitle(GMT_TITLE);
    parameterList.getParameter(GMT_MapGenerator.COLOR_SCALE_MODE_NAME).addParameterChangeListener(this);
    parameterList.getParameter(GMT_MapGenerator.CUSTOM_SCALE_LABEL_PARAM_CHECK_NAME).addParameterChangeListener(this);
    changeColorScaleModeValue(GMT_MapGenerator.COLOR_SCALE_MODE_DEFAULT);
    //making the map using GMT service ( making this param false, as not allowing
    //the user to set its value)
    getParameterEditor(GMT_MapGenerator.GMT_WEBSERVICE_NAME).setVisible(false);

    //making the Custom Scale Label Param invisible when application is started
    getParameterEditor(GMT_MapGenerator.SCALE_LABEL_PARAM_NAME).setVisible(false);
  }

  /**
   *
   * @param regionParamsFlag: boolean flag to check if the region params are to be shown in the
   */
  public void showRegionParams(boolean regionParamsFlag) {
      getParameterEditor(GMT_MapGenerator.MAX_LAT_PARAM_NAME).setVisible(regionParamsFlag);
      getParameterEditor(GMT_MapGenerator.MIN_LAT_PARAM_NAME).setVisible(regionParamsFlag);
      getParameterEditor(GMT_MapGenerator.MAX_LON_PARAM_NAME).setVisible(regionParamsFlag);
      getParameterEditor(GMT_MapGenerator.MIN_LON_PARAM_NAME).setVisible(regionParamsFlag);
      getParameterEditor(GMT_MapGenerator.GRID_SPACING_PARAM_NAME).setVisible(regionParamsFlag);
  }

  /**
   * private function that initialises the region params for the GMT plot region
   * @param minLat
   * @param maxLat
   * @param minLon
   * @param maxLon
   * @param gridSpacing
   */
  public void setRegionParams(double minLat,double maxLat,double minLon,double maxLon,
                               double gridSpacing){
    if(D) System.out.println(C+" setGMTRegionParams: " +minLat+"  "+maxLat+"  "+minLon+"  "+maxLon);
    getParameterList().getParameter(GMT_MapGenerator.MIN_LAT_PARAM_NAME).setValue(new Double(minLat));
    getParameterList().getParameter(GMT_MapGenerator.MAX_LAT_PARAM_NAME).setValue(new Double(maxLat));
    getParameterList().getParameter(GMT_MapGenerator.MIN_LON_PARAM_NAME).setValue(new Double(minLon));
    getParameterList().getParameter(GMT_MapGenerator.MAX_LON_PARAM_NAME).setValue(new Double(maxLon));
    getParameterList().getParameter(GMT_MapGenerator.GRID_SPACING_PARAM_NAME).setValue(new Double(gridSpacing));
  }


  /**
   * this function listens for parameter change
   * @param e
   */
  public void parameterChange(ParameterChangeEvent e) {
    String name = e.getParameterName();
    if(name.equalsIgnoreCase(GMT_MapGenerator.COLOR_SCALE_MODE_NAME))
      changeColorScaleModeValue((String)e.getNewValue());
    else if(name.equalsIgnoreCase(GMT_MapGenerator.CUSTOM_SCALE_LABEL_PARAM_CHECK_NAME)){
      boolean boolVal = ((Boolean)e.getNewValue()).booleanValue();
      showCustomScaleLabel(boolVal);
    }
  }


  /**
   * If user chooses to give own custom label then it makes the ScaleLabel parameter
   * visible to the user.
   * @param showLabel boolean checks if custom label needed.
   */
  protected void showCustomScaleLabel(boolean showLabel) {
    getParameterEditor(GMT_MapGenerator.SCALE_LABEL_PARAM_NAME).setVisible(
        showLabel);
  }

  /**
   * If user chooses Manual or "From Data" color mode, then min and max color limits
   * have to be set Visible and invisible respectively
   * @param val
   */
  protected void changeColorScaleModeValue(String val) {
    if(val.equalsIgnoreCase(GMT_MapGenerator.COLOR_SCALE_MODE_FROMDATA)) {
      getParameterEditor(GMT_MapGenerator.COLOR_SCALE_MAX_PARAM_NAME).setVisible(false);
      getParameterEditor(GMT_MapGenerator.COLOR_SCALE_MIN_PARAM_NAME).setVisible(false);
    } else {
      getParameterEditor(GMT_MapGenerator.COLOR_SCALE_MAX_PARAM_NAME).setVisible(true);
      getParameterEditor(GMT_MapGenerator.COLOR_SCALE_MIN_PARAM_NAME).setVisible(true);
    }
  }
  
  public GriddedRegion getEvenlyGriddedGeographicRegion() throws RegionConstraintException {
	  return gmtMap.getEvenlyGriddedGeographicRegion();
  }

  /**
   * this function generates and displays a GMT map for an XYZ dataset using
   * the settings in the GMT_SettingsControlPanel.
   * @param xyzVals : Object for the XYZ values
   * @param metadata : Associated Metadata for the values.
   */
  public void makeMap(XYZ_DataSetAPI xyzVals, String metadataAsHTML) {

    // boolean gmtServerCheck = ((Boolean)gmtMap.getAdjustableParamsList().getParameter(gmtMap.GMT_WEBSERVICE_NAME).getValue()).booleanValue();
    boolean gmtServerCheck = true;
    if (gmtServerCheck) {
      //imgName=gmtMap.makeMapUsingWebServer(xyzVals);
      try {
        imgName = gmtMap.makeMapUsingServlet(xyzVals, " ", metadataAsHTML, dirName);
        metadataAsHTML += "<br><p>Click:  " + "<a href=\"" + gmtMap.getGMTFilesWebAddress() +
           "\">" + "here" + "</a>" +" (" + gmtMap.getGMTFilesWebAddress() + ") to download files. They will be deleted at midnight</p>";
      }
      catch (GMT_MapException e) {
        JOptionPane.showMessageDialog(this, e.getMessage(),
                                      "Incorrect GMT params ",
                                      JOptionPane.INFORMATION_MESSAGE);
        return;
      }
      catch (RuntimeException e) {
        e.printStackTrace();
        JOptionPane.showMessageDialog(this, e.getMessage(), "Server Problem",
                                      JOptionPane.INFORMATION_MESSAGE);
        return;
      }
    }
    else {
      try {
        imgName = gmtMap.makeMapLocally(xyzVals, " ", metadataAsHTML, dirName);
      }
      catch (GMT_MapException e) {
        JOptionPane.showMessageDialog(this, e.getMessage(),
                                      "Incorrect GMT params ",
                                      JOptionPane.INFORMATION_MESSAGE);
        return;
      }
      catch (RuntimeException e) {
        JOptionPane.showMessageDialog(this, e.getMessage());
        return;
      }
    }

    //checks to see if the user wants to see the Map in a seperate window or not
    if (this.showMapInSeperateWindow) {
      //adding the image to the Panel and returning that to the applet
      ImageViewerWindow imgView = new ImageViewerWindow(imgName, metadataAsHTML,
          gmtServerCheck);
    }
    dirName = null;
  }


  /**
   * Flag to determine whether to show the Map in a seperate pop up window
   * @param flag
   */
  public void setMapToBeShownInSeperateWindow(boolean flag){
    this.showMapInSeperateWindow = flag;
  }


  /**
   * return the GMT_MapGenerator object
   * @return
   */
  public GMT_MapGenerator getGMTObject() {
    return this.gmtMap;
  }


  /**
   * sets the directory name to generate the maps and shakemap related data in this
   * directory.
   */
  public void setDirectoryName(String dirName){
    this.dirName = dirName;
 }

}
