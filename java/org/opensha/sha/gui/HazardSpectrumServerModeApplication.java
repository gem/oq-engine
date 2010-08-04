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

package org.opensha.sha.gui;

import java.awt.Dimension;
import java.awt.Toolkit;
import java.lang.reflect.InvocationTargetException;
import java.net.URL;
import java.rmi.RemoteException;
import java.util.ArrayList;

import org.opensha.commons.util.FileUtils;
import org.opensha.sha.calc.SpectrumCalculator;
import org.opensha.sha.calc.remoteCalc.RemoteResponseSpectrumClient;
import org.opensha.sha.earthquake.EqkRupForecastBaseAPI;
import org.opensha.sha.gui.beans.ERF_GuiBean;
import org.opensha.sha.gui.beans.EqkRupSelectorGuiBean;
import org.opensha.sha.gui.infoTools.ApplicationVersionInfoWindow;
import org.opensha.sha.gui.infoTools.ExceptionWindow;

/**
 * <p>Title: HazardSpectrumServerModeApplication </p>
 *
 * <p>Description: This class allows the  </p>
 *
 * <p>Copyright: Copyright (c) 2002</p>
 *
 * <p>Company: </p>
 *
 * @author Nitin Gupta
 * @version 1.0
 */
public class HazardSpectrumServerModeApplication
    extends HazardSpectrumLocalModeApplication {

  protected final static String appURL = "http://www.opensha.org/applications/hazSpectrumApp/HazardSpectrumServerModeApp.jar";


  /**
   * Returns the Application version
   * @return String
   */
  
  public static String getAppVersion(){
    return version;
  }

  
  
  /**
   * Checks if the current version of the application is latest else direct the
   * user to the latest version on the website.
   */
  protected void checkAppVersion(){
      ArrayList hazCurveVersion = null;
      try {
    	  hazCurveVersion = FileUtils.loadFile(new URL(versionURL));
      }
      catch (Exception ex1) {
        return;
      }
      String appVersionOnWebsite = (String)hazCurveVersion.get(0);
      if(!appVersionOnWebsite.trim().equals(version.trim())){
        try{
          ApplicationVersionInfoWindow messageWindow =
              new ApplicationVersionInfoWindow(appURL,
                                               this.versionUpdateInfoURL,
                                               "App Version Update", this);
          Dimension dim = Toolkit.getDefaultToolkit().getScreenSize();
          messageWindow.setLocation( (dim.width -
                                      messageWindow.getSize().width) / 2,
                                    (dim.height -
                                     messageWindow.getSize().height) / 2);
          messageWindow.setVisible(true);
        }catch(Exception e){
          e.printStackTrace();
        }
      }

    return;

  }  
    
  
  
  /**
   * Initialize the ERF Gui Bean
   */
  protected void initERF_GuiBean() {

    if (erfGuiBean == null) {
      try {
        // create the ERF Gui Bean object
        ArrayList erf_Classes = new ArrayList();
        //adding the RMI based ERF's to the application
        erf_Classes.add(RMI_FRANKEL_ADJ_FORECAST_CLASS_NAME);
        erf_Classes.add(RMI_WGCEP_UCERF1_ERF_CLASS_NAME);
//        erf_Classes.add(RMI_STEP_FORECAST_CLASS_NAME);
        erf_Classes.add(RMI_STEP_ALASKA_ERF_CLASS_NAME);
        erf_Classes.add(RMI_FLOATING_POISSON_FAULT_ERF_CLASS_NAME);
        erf_Classes.add(RMI_FRANKEL02_ADJ_FORECAST_CLASS_NAME);
        erf_Classes.add(RMI_PEER_AREA_FORECAST_CLASS_NAME);
        erf_Classes.add(RMI_PEER_MULTI_SOURCE_FORECAST_CLASS_NAME);
        erf_Classes.add(RMI_PEER_NON_PLANAR_FAULT_FORECAST_CLASS_NAME);
        erf_Classes.add(RMI_POISSON_FAULT_ERF_CLASS_NAME);
        erf_Classes.add(RMI_POINT2MULT_VSS_FORECAST_CLASS_NAME);
        erf_Classes.add(RMI_WG02_ERF_LIST_CLASS_NAME);
        erf_Classes.add(RMI_PEER_LOGIC_TREE_ERF_LIST_CLASS_NAME);
        erf_Classes.add(RMI_POINT2MULT_VSS_ERF_LIST_CLASS_NAME);

        erfGuiBean = new ERF_GuiBean(erf_Classes);
        erfGuiBean.getParameter(erfGuiBean.ERF_PARAM_NAME).
            addParameterChangeListener(this);
      }
      catch (InvocationTargetException e) {
        ExceptionWindow bugWindow = new ExceptionWindow(this, e,
            "ERF's Initialization problem. Rest all parameters are default");
        bugWindow.setVisible(true);
        bugWindow.pack();
        //e.printStackTrace();
        //throw new RuntimeException("Connection to ERF's failed");
      }
    }
    else {
      boolean isCustomRupture = erfRupSelectorGuiBean.isCustomRuptureSelected();
      if (!isCustomRupture) {
        EqkRupForecastBaseAPI eqkRupForecast = erfRupSelectorGuiBean.
            getSelectedEqkRupForecastModel();
        erfGuiBean.setERF(eqkRupForecast);
      }
    }
//    erfPanel.removeAll(); TODO clean
//    erfPanel.add(erfGuiBean, new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0,
//        GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(0,0,0,0), 0, 0));
//
//    erfPanel.updateUI();

  }


  /**
   * Initialize the ERF Rup Selector Gui Bean
   */
  protected void initERFSelector_GuiBean() {

    EqkRupForecastBaseAPI erf = null;
    try {
      erf = erfGuiBean.getSelectedERF();
    }
    catch (InvocationTargetException ex) {
      ex.printStackTrace();
    }
    if(erfRupSelectorGuiBean == null){
      // create the ERF Gui Bean object
      ArrayList erf_Classes = new ArrayList();

      /**
       *  The object class names for all the supported Eqk Rup Forecasts
       */
      erf_Classes.add(RMI_POISSON_FAULT_ERF_CLASS_NAME);
      erf_Classes.add(RMI_FRANKEL_ADJ_FORECAST_CLASS_NAME);
      erf_Classes.add(RMI_WGCEP_UCERF1_ERF_CLASS_NAME);
      erf_Classes.add(RMI_STEP_FORECAST_CLASS_NAME);
      erf_Classes.add(RMI_STEP_ALASKA_ERF_CLASS_NAME);
      erf_Classes.add(RMI_FLOATING_POISSON_FAULT_ERF_CLASS_NAME);
      erf_Classes.add(RMI_FRANKEL02_ADJ_FORECAST_CLASS_NAME);
      erf_Classes.add(RMI_PEER_AREA_FORECAST_CLASS_NAME);
      erf_Classes.add(RMI_PEER_NON_PLANAR_FAULT_FORECAST_CLASS_NAME);
      erf_Classes.add(RMI_PEER_MULTI_SOURCE_FORECAST_CLASS_NAME);
      erf_Classes.add(RMI_WG02_ERF_CLASS_NAME);

      try {
        erfRupSelectorGuiBean = new EqkRupSelectorGuiBean(erf,erf_Classes);
      }
      catch (InvocationTargetException e) {
        throw new RuntimeException("Connection to ERF's failed");
      }
    }
//    erfPanel.removeAll(); TODO clean
//    //erfGuiBean = null;
//    erfPanel.add(erfRupSelectorGuiBean,
//                 new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0,
//                                        GridBagConstraints.CENTER,
//                                        GridBagConstraints.BOTH, new Insets(0,0,0,0), 0,
//                                        0));
//    erfPanel.updateUI();
  }

  /**
   * This method creates the SpectrumCalc s.
   * If the internet connection is available then it creates a remote instances of
   * the calculators on server where the calculations take place, else
   * calculations are performed on the user's own machine.
   */
  protected void createCalcInstance() {
	  try{
		  if (calc == null && isProbabilisticCurve) {
			  calc = (new RemoteResponseSpectrumClient()).getRemoteSpectrumCalc();
			  if(this.calcParamsControl != null)
				  try {
					  calc.setAdjustableParams(calcParamsControl.getAdjustableCalcParams());
				  } catch (RemoteException e) {
					  // TODO Auto-generated catch block
					  e.printStackTrace();
				  }
		  }
		  else if(calc == null && !isProbabilisticCurve) {
			  calc = new SpectrumCalculator();
			  calc.setAdjustableParams(calcParamsControl.getAdjustableCalcParams());
		  }
	  }catch (Exception ex) {
		  ExceptionWindow bugWindow = new ExceptionWindow(this,
				  ex, this.getParametersInfoAsString());
		  bugWindow.setVisible(true);
		  bugWindow.pack();
	  }
  }

  public static void main(String[] args) {
    HazardSpectrumServerModeApplication applet = new
        HazardSpectrumServerModeApplication();
    applet.checkAppVersion();
    applet.init();
    applet.setVisible(true);
  }
}
