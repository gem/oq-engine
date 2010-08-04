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

package org.opensha.sha.gui.beans;

import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.net.URL;
import java.net.URLConnection;

import javax.swing.JOptionPane;

import org.opensha.commons.data.XYZ_DataSetAPI;
import org.opensha.commons.exceptions.GMT_MapException;
import org.opensha.commons.mapping.gmt.gui.GMT_MapGuiBean;
import org.opensha.commons.param.ParameterList;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.gui.infoTools.ImageViewerWindow;
import org.opensha.sha.gui.servlets.ScenarioShakeMapForHazusGeneratorServlet;
import org.opensha.sha.gui.servlets.ScenarioShakeMapGeneratorServlet;
import org.opensha.sha.mapping.GMT_MapGeneratorForShakeMaps;

/**
 * <p>Title: MapGuiBean</p>
 * <p>Description: This class generates and displays a GMT map for an XYZ dataset using
 * the settings in the GMT_SettingsControlPanel. It displays the image file in a JPanel.
 * This class is used in showing the ScenarioShakeMaps which also defines the rupture surface
 * and does special calculation if the person has choosen to generate the Hazus data.</p>
 * @author: Ned Field, Nitin Gupta & Vipin Gupta
 * @version 1.0
 */

public class MapGuiBean extends GMT_MapGuiBean {

  /**
   * Name of the class
   */
  protected final static String C = "MapGuiBean";


  //some parameter values for hazus, that needs to have specific value for Hazus files generation
  //checking if hazus file generator param is selected, if not then make it selected and the deselect it again
  private boolean hazusFileGeneratorCheck;
  //checking if log map generator param is selected, if yes then make it unselected and the select it again
  boolean generateMapInLogSpace;
  //always making the map color scale from the data if the person has choosen the Hazus control panel
  String mapColorScaleValue;


  /**
   * Class constructor accepts the GMT parameters list
   * @param gmtMap
   */
  public MapGuiBean() {
    gmtMap = null;
    //instance of the GMT Control Panel to get the GMT parameters value.
    gmtMap= new GMT_MapGeneratorForShakeMaps();
    //initialise the param list and editor for the GMT Map Params and Editors
    initParamListAndEditor();
  }


  /**
   * this function generates and displays a GMT map for an XYZ dataset using
   * the settings in the GMT_SettingsControlPanel.
   *
   * @param fileName: name of the XYZ file
   */
  public void makeMap(String xyzVals,EqkRupture eqkRupture,String imt,
                      String metadataAsHTML){

    try{
      // this creates a conection with the server to generate the map on the server
      //after reading the xyz vals file from the server
      try {
        imgName = openConnectionToServerToGenerateShakeMap(xyzVals, eqkRupture,
            imt, metadataAsHTML);
      }
      catch (GMT_MapException ex) {
        JOptionPane.showMessageDialog(this,ex.getMessage(),"Incorrect GMT params ",JOptionPane.INFORMATION_MESSAGE);
        return;
      }
      //webaddr where all the GMT related file for this map resides on server
      String webaddr = imgName.substring(0,imgName.lastIndexOf("/")+1);
      metadataAsHTML += "<br><p>Click:  " + "<a href=\"" + webaddr +
           "\">" + "here" + "</a>" +" to download files. They will be deleted at midnight</p>";
    }catch(RuntimeException e){
      e.printStackTrace();
      JOptionPane.showMessageDialog(this,e.getMessage(),"Server Problem",JOptionPane.INFORMATION_MESSAGE);
      return;
    }

    //checks to see if the user wants to see the Map in a seperate window or not
    if(this.showMapInSeperateWindow){
      //adding the image to the Panel and returning that to the applet
      ImageViewerWindow imgView = new ImageViewerWindow(imgName,metadataAsHTML,true);
    }
    dirName = null;
  }



  /**
   * this function generates and displays a GMT map for an XYZ dataset using
   * the settings in the GMT_SettingsControlPanel.
   *
   * @param fileName: name of the XYZ file
   */
  public void makeMap(XYZ_DataSetAPI xyzVals,EqkRupture eqkRupture,String imt,
                      String metadataAsHTML){

    boolean gmtServerCheck = ((Boolean)gmtMap.getAdjustableParamsList().getParameter(gmtMap.GMT_WEBSERVICE_NAME).getValue()).booleanValue();
    if(gmtServerCheck){
      //imgName=gmtMap.makeMapUsingWebServer(xyzVals);
      try{
        imgName =((GMT_MapGeneratorForShakeMaps)gmtMap).makeMapUsingServlet(xyzVals,eqkRupture,imt,metadataAsHTML,dirName);
        metadataAsHTML += "<br><p>Click:  " + "<a href=\"" + gmtMap.getGMTFilesWebAddress() +
           "\">" + "here" + "</a>" +" to download files. They will be deleted at midnight</p>";
      }catch(GMT_MapException e){
        JOptionPane.showMessageDialog(this,e.getMessage(),"Incorrect GMT params ",JOptionPane.INFORMATION_MESSAGE);
        return;
      }
      catch(RuntimeException e){
        e.printStackTrace();
        JOptionPane.showMessageDialog(this,e.getMessage(),"Server Problem",JOptionPane.INFORMATION_MESSAGE);
        return;
      }
    }
    else{
      try{
        imgName = ((GMT_MapGeneratorForShakeMaps)gmtMap).makeMapLocally(xyzVals,eqkRupture,imt,metadataAsHTML,dirName);
      }catch(GMT_MapException e){
        JOptionPane.showMessageDialog(this,e.getMessage(),"Incorrect GMT params ",JOptionPane.INFORMATION_MESSAGE);
        return;
      }
      catch (RuntimeException e) {
        JOptionPane.showMessageDialog(this, e.getMessage());
        return;
      }
    }

    //checks to see if the user wants to see the Map in a seperate window or not
    if(this.showMapInSeperateWindow){
      //adding the image to the Panel and returning that to the applet
      ImageViewerWindow imgView = new ImageViewerWindow(imgName,metadataAsHTML,
          gmtServerCheck);
    }
    dirName = null;
  }



  /**
   * this function generates and displays a GMT map for XYZ dataset using
   * the settings in the GMT_SettingsControlPanel.
   *
   * @param fileName: name of the XYZ file
   */
  public void makeHazusShapeFilesAndMap(XYZ_DataSetAPI sa03_xyzVals,XYZ_DataSetAPI sa10_xyzVals,
                      XYZ_DataSetAPI pga_xyzVals, XYZ_DataSetAPI pgv_xyzVals,
                      EqkRupture eqkRupture,String metadataAsHTML){
    String[] imgNames = null;

    //boolean gmtServerCheck = ((Boolean)gmtMap.getAdjustableParamsList().getParameter(gmtMap.GMT_WEBSERVICE_NAME).getValue()).booleanValue();
     // gmtMap.getAdjustableParamsList().getParameter(gmtMap.GMT_WEBSERVICE_NAME).setValue(new Boolean(true));

    //if(gmtServerCheck){
    try {
      imgNames = ( (GMT_MapGeneratorForShakeMaps) gmtMap).
          makeHazusFileSetUsingServlet(sa03_xyzVals, sa10_xyzVals, pga_xyzVals,
                                       pgv_xyzVals, eqkRupture, metadataAsHTML, dirName);
      metadataAsHTML += "<br><p>Click:  " + "<a href=\"" + gmtMap.getGMTFilesWebAddress() +
          "\">" + "here" + "</a>" +" to download files. They will be deleted at midnight</p>";
    }
    catch (GMT_MapException e) {
      JOptionPane.showMessageDialog(this, e.getMessage(), "Incorrect GMT params ",
                                    JOptionPane.INFORMATION_MESSAGE);
      return;
    }
    catch (RuntimeException e) {
      e.printStackTrace();
      JOptionPane.showMessageDialog(this, e.getMessage(), "Server Problem",
                                    JOptionPane.INFORMATION_MESSAGE);
      return;
    }
   // }
    /*else{
      try{
        imgNames = ((GMT_MapGeneratorForShakeMaps)gmtMap).makeHazusFileSetLocally(sa03_xyzVals,sa10_xyzVals, pga_xyzVals,
                                                     pgv_pgvVals,eqkRupture);
      }catch(RuntimeException e){
        JOptionPane.showMessageDialog(this,e.getMessage());
        return;
      }
    }*/

    //checks to see if the user wants to see the Map in a seperate window or not
    if(this.showMapInSeperateWindow){
      //adding the image to the Panel and returning that to the applet
      ImageViewerWindow imgView = new ImageViewerWindow(imgNames,metadataAsHTML,true);
    }
    dirName = null;
    //gmtMap.getAdjustableParamsList().getParameter(gmtMap.GMT_WEBSERVICE_NAME).setValue(new Boolean(gmtServerCheck));
  }


  /**
   * this function generates and displays a GMT map for XYZ dataset using
   * the settings in the GMT_SettingsControlPanel.
   *
   * @param fileName: name of the XYZ file
   */
  public void makeHazusShapeFilesAndMap(String sa03_xyzVals,String sa10_xyzVals,
                      String pga_xyzVals, String pgv_xyzVals,
                      EqkRupture eqkRupture,String metadataAsHTML){
    String[] imgNames = null;
    try{
      try {
        imgNames = openConnectionToServerToGenerateShakeMapForHazus(
            sa03_xyzVals, sa10_xyzVals,
            pga_xyzVals, pgv_xyzVals, eqkRupture, metadataAsHTML);
      }
      catch (GMT_MapException ex) {
        JOptionPane.showMessageDialog(this,ex.getMessage(),"Incorrect GMT params",JOptionPane.INFORMATION_MESSAGE);
        return;
      }
      //webaddr where all the GMT related file for this map resides on server
      String webaddr = imgNames[0].substring(0,imgNames[0].lastIndexOf("/")+1);
      /*imgNames =((GMT_MapGeneratorForShakeMaps)gmtMap).makeHazusFileSetUsingServlet(sa03_xyzVals,sa10_xyzVals, pga_xyzVals,
          pgv_xyzVals,eqkRupture,metadata);*/
      metadataAsHTML += "<br><p>Click:  " + "<a href=\"" + webaddr +
          "\">" + "here" + "</a>" +" to download files. They will be deleted at midnight</p>";
    }catch(RuntimeException e){
      e.printStackTrace();
      JOptionPane.showMessageDialog(this,e.getMessage(),"Server Problem",JOptionPane.INFORMATION_MESSAGE);
      return;
    }

    //checks to see if the user wants to see the Map in a seperate window or not
    if(this.showMapInSeperateWindow){
      //adding the image to the Panel and returning that to the applet
      ImageViewerWindow imgView = new ImageViewerWindow(imgNames,metadataAsHTML,true);
    }

    dirName = null;
  }




  /**
   * This Method changes the value of the following GMT parameters to specific for Hazus:
   * Log Plot Param is selected to Linear plot
   * Make Hazus File Param is set to true
   * Map color scale param value is set always from data.
   * The changes to the parameters on specific for the Hazus and needs to reverted
   * back to the original values ,using the function setGMT_ParamsChangedForHazusToOriginalValue().
   * after map has been generated.
   */
  public void setGMT_ParamsForHazus(){

    //instance of the GMT parameter list
    ParameterList paramList = gmtMap.getAdjustableParamsList();

    //checking if hazus file generator param is selected, if not then make it selected and the deselect it again
    hazusFileGeneratorCheck = ((Boolean)paramList.getParameter(GMT_MapGeneratorForShakeMaps.HAZUS_SHAPE_PARAM_NAME).getValue()).booleanValue();
    if(!hazusFileGeneratorCheck)
      paramList.getParameter(GMT_MapGeneratorForShakeMaps.HAZUS_SHAPE_PARAM_NAME).setValue(new Boolean(true));


    //checking if log map generator param is selected, if yes then make it unselected and the select it again
    generateMapInLogSpace = ((Boolean)paramList.getParameter(GMT_MapGeneratorForShakeMaps.LOG_PLOT_NAME).getValue()).booleanValue();
    if(generateMapInLogSpace)
      paramList.getParameter(GMT_MapGeneratorForShakeMaps.LOG_PLOT_NAME).setValue(new Boolean(false));

    //always making the map color scale from the data if the person has choosen the Hazus control panel
    mapColorScaleValue = (String)paramList.getParameter(GMT_MapGeneratorForShakeMaps.COLOR_SCALE_MODE_NAME).getValue();
    if(!mapColorScaleValue.equals(GMT_MapGeneratorForShakeMaps.COLOR_SCALE_MODE_FROMDATA))
      paramList.getParameter(GMT_MapGeneratorForShakeMaps.COLOR_SCALE_MODE_NAME).setValue(GMT_MapGeneratorForShakeMaps.COLOR_SCALE_MODE_FROMDATA);

  }

  /**
   * This method reverts back the settings of the gmt parameters those were set specifically
   * for the Hazus files generation. This has been added seperately so that metadata can
   * show changed value of the parameters, so the user should be able to know the actual
   * parameter setting using which map was computed.
   */
  public void setGMT_ParamsChangedForHazusToOriginalValue(){
    //instance of the GMT parameter list
    ParameterList paramList = gmtMap.getAdjustableParamsList();

    //reverting the value for the Hazus file generation to the what was before the selection of the Hazus control panel.
    if(!hazusFileGeneratorCheck)
      paramList.getParameter(GMT_MapGeneratorForShakeMaps.HAZUS_SHAPE_PARAM_NAME).setValue(new Boolean(false));

    //reverting the value for the Log file generation to the what was before the selection of the Hazus control panel.
    if(generateMapInLogSpace)
      paramList.getParameter(GMT_MapGeneratorForShakeMaps.LOG_PLOT_NAME).setValue(new Boolean(true));

    //reverting the value for the map color generation to the what was before the selection of the Hazus control panel.
    if(!mapColorScaleValue.equals(GMT_MapGeneratorForShakeMaps.COLOR_SCALE_MODE_FROMDATA))
      paramList.getParameter(GMT_MapGeneratorForShakeMaps.COLOR_SCALE_MODE_NAME).setValue(mapColorScaleValue);

  }


  /**
   * Oening the connection to the Server to generate the maps
   * @param xyzVals
   * @param eqkRupture
   * @param imt
   * @param metadata
   * @return
   */
  private String openConnectionToServerToGenerateShakeMap(String xyzVals,
      EqkRupture eqkRupture,String imt,String metadata) throws GMT_MapException{
    String webaddr=null;
    try{
      if(D) System.out.println("starting to make connection with servlet");
      URL gmtMapServlet = new
                          URL(ScenarioShakeMapGeneratorServlet.SERVLET_URL);


      URLConnection servletConnection = gmtMapServlet.openConnection();
      if(D) System.out.println("connection established");

      // inform the connection that we will send output and accept input
      servletConnection.setDoInput(true);
      servletConnection.setDoOutput(true);

      // Don't use a cached version of URL connection.
      servletConnection.setUseCaches (false);
      servletConnection.setDefaultUseCaches (false);
      // Specify the content type that we will send binary data
      servletConnection.setRequestProperty ("Content-Type","application/octet-stream");

      ObjectOutputStream outputToServlet = new
          ObjectOutputStream(servletConnection.getOutputStream());

      //sending the GMT_MapGenerattor ForShakeMaps object to the servlet
      outputToServlet.writeObject(gmtMap);

      //sending the file of the XYZ file to read the XYZ object from.
      outputToServlet.writeObject(xyzVals);

      //sending the rupture object to the servlet
      outputToServlet.writeObject(eqkRupture);

      //sending the selected IMT to the server.
      outputToServlet.writeObject(imt);

      //sending the metadata of the map to the server.
      outputToServlet.writeObject(metadata);

      //sending the directory name to the servlet
      outputToServlet.writeObject(dirName);

      outputToServlet.flush();
      outputToServlet.close();

      // Receive the "actual webaddress of all the gmt related files"
      // from the servlet after it has received all the data
      ObjectInputStream inputToServlet = new
          ObjectInputStream(servletConnection.getInputStream());


      Object messageFromServlet = inputToServlet.readObject();
      inputToServlet.close();
      if(messageFromServlet instanceof String){
        webaddr = (String) messageFromServlet;
        if(D) System.out.println("Receiving the Input from the Servlet:"+webaddr);
      }
      else if(messageFromServlet instanceof GMT_MapException)
        throw (GMT_MapException)messageFromServlet;

      else if(messageFromServlet instanceof RuntimeException)
        throw (RuntimeException)messageFromServlet;

    }catch(GMT_MapException e){
            throw new GMT_MapException(e.getMessage());
    }catch (RuntimeException e){
      throw new RuntimeException(e.getMessage());
    }
    catch (Exception e) {
      e.printStackTrace();
      throw new RuntimeException("Server is down , please try again later");
    }
    return webaddr;
  }



  /**
   * Oening the connection to the Server to generate the maps for Hazus
   * @param xyzVals
   * @param eqkRupture
   * @param imt
   * @param metadata
   * @return
   */
  private String[] openConnectionToServerToGenerateShakeMapForHazus(String sa_03xyzVals,
      String sa_10xyzVals,String pga_xyzVals,String pgv_xyzVals,EqkRupture eqkRupture,String metadata)
  throws GMT_MapException{
    Object webaddr=null;
    try{
      if(D) System.out.println("starting to make connection with servlet");
      URL gmtMapServlet = new
                          URL(ScenarioShakeMapForHazusGeneratorServlet.SERVLET_URL);


      URLConnection servletConnection = gmtMapServlet.openConnection();
      if(D) System.out.println("connection established");

      // inform the connection that we will send output and accept input
      servletConnection.setDoInput(true);
      servletConnection.setDoOutput(true);

      // Don't use a cached version of URL connection.
      servletConnection.setUseCaches (false);
      servletConnection.setDefaultUseCaches (false);
      // Specify the content type that we will send binary data
      servletConnection.setRequestProperty ("Content-Type","application/octet-stream");

      ObjectOutputStream outputToServlet = new
          ObjectOutputStream(servletConnection.getOutputStream());

      //sending the GMT_MapGenerattor ForShakeMaps object to the servlet
      outputToServlet.writeObject(gmtMap);

      //sending the file of the XYZ filename for SA_03 to read the XYZ object from.
      outputToServlet.writeObject(sa_03xyzVals);

      //sending the file of the XYZ filename for SA_10 to read the XYZ object from.
      outputToServlet.writeObject(sa_10xyzVals);

      //sending the file of the XYZ filename for PGA to read the XYZ object from.
      outputToServlet.writeObject(pga_xyzVals);

      //sending the file of the XYZ filename for PGV to read the XYZ object from.
      outputToServlet.writeObject(pgv_xyzVals);


      //sending the rupture object to the servlet
      outputToServlet.writeObject(eqkRupture);


      //sending the metadata of the map to the server.
      outputToServlet.writeObject(metadata);

      //sending the directory name to the servlet
      outputToServlet.writeObject(dirName);

      outputToServlet.flush();
      outputToServlet.close();

      // Receive the "actual webaddress of all the gmt related files"
      // from the servlet after it has received all the data
      ObjectInputStream inputToServlet = new
          ObjectInputStream(servletConnection.getInputStream());

      webaddr=(Object)inputToServlet.readObject();
      if(D) System.out.println("Receiving the Input from the Servlet:"+webaddr);
      inputToServlet.close();

      if(webaddr instanceof GMT_MapException)
        throw (GMT_MapException)webaddr;
      else
        return (String[])webaddr;


    }
    catch(GMT_MapException e){
      throw new GMT_MapException(e.getMessage());
    }
    catch (Exception e) {
      e.printStackTrace();
      throw new RuntimeException("Server is down , please try again later");
    }
  }




}
