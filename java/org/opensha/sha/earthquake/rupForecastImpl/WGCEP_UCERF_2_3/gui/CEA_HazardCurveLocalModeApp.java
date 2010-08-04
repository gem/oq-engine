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

package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.gui;


import java.lang.reflect.InvocationTargetException;
import java.util.ArrayList;

import org.opensha.sha.calc.HazardCurveCalculator;
import org.opensha.sha.calc.disaggregation.DisaggregationCalculator;
import org.opensha.sha.earthquake.EqkRupForecastBaseAPI;
import org.opensha.sha.gui.HazardCurveServerModeApplication;
import org.opensha.sha.gui.beans.ERF_GuiBean;
import org.opensha.sha.gui.beans.EqkRupSelectorGuiBean;
import org.opensha.sha.gui.beans.IMR_GuiBean;
import org.opensha.sha.gui.beans.IMR_MultiGuiBean;
import org.opensha.sha.gui.controls.CalculationSettingsControlPanel;
import org.opensha.sha.gui.controls.DisaggregationControlPanel;
import org.opensha.sha.gui.controls.PlottingOptionControl;
import org.opensha.sha.gui.controls.SiteDataControlPanel;
import org.opensha.sha.gui.controls.SitesOfInterestControlPanel;
import org.opensha.sha.gui.controls.XY_ValuesControlPanel;
import org.opensha.sha.gui.controls.X_ValuesInCurveControlPanel;
import org.opensha.sha.gui.infoTools.AttenuationRelationshipsInstance;
import org.opensha.sha.gui.infoTools.ExceptionWindow;
import org.opensha.sha.imr.attenRelImpl.AS_1997_AttenRel;
import org.opensha.sha.imr.attenRelImpl.BA_2008_AttenRel;
import org.opensha.sha.imr.attenRelImpl.BJF_1997_AttenRel;
import org.opensha.sha.imr.attenRelImpl.CB_2008_AttenRel;
import org.opensha.sha.imr.attenRelImpl.Campbell_1997_AttenRel;
import org.opensha.sha.imr.attenRelImpl.Field_2000_AttenRel;
import org.opensha.sha.imr.attenRelImpl.SadighEtAl_1997_AttenRel;

/**
 * <p>Title: CEA_HazardCurveLocalModeApp</p>
 * <p>Description: This application is extension of HazardCurveApplication specific
 * to the California Earthquake Authority that contains a subset of the available
 * IMRs and ERFs.</p>
 * @author : Nitin Gupta and Vipin Gupta
 * @version 1.0
 */

public class CEA_HazardCurveLocalModeApp extends HazardCurveServerModeApplication {

	public final static String FRANKEL02_ADJ_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.Frankel02.Frankel02_AdjustableEqkRupForecast";
	public final static String WGCEP_UCERF1_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF1.WGCEP_UCERF1_EqkRupForecast";
	public final static String WGCEP_AVG_UCERF_2_CLASS_NAME="org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.MeanUCERF2.MeanUCERF2";

	protected final static String appURL = "http://www.opensha.org/applications/hazCurvApp/HazardCurveApp.jar";

	/**
	 * Returns the Application version
	 * @return String
	 */

	public static String getAppVersion(){
		return "1.0";
	}



	/**
	 * No version check for CEA Hazard Curve Calculator
	 */
	protected void checkAppVersion(){

		return;

	}  


	/**
	 * Initialize the ERF Gui Bean
	 */
	protected void initERF_GuiBean() {

		if(erfGuiBean == null){
			// create the ERF Gui Bean object
			ArrayList erf_Classes = new ArrayList();

			//adding the client based ERF's to the application
			erf_Classes.add(WGCEP_AVG_UCERF_2_CLASS_NAME);
			erf_Classes.add(WGCEP_UCERF1_CLASS_NAME);
			erf_Classes.add(FRANKEL02_ADJ_FORECAST_CLASS_NAME);


			try {
				erfGuiBean = new ERF_GuiBean(erf_Classes);
				erfGuiBean.getParameter(erfGuiBean.ERF_PARAM_NAME).
				addParameterChangeListener(this);
			}
			catch (InvocationTargetException e) {

				ExceptionWindow bugWindow = new ExceptionWindow(this, e.getStackTrace(),
						"Problem occured " +
						"during initialization the ERF's. All parameters are set to default.");
				bugWindow.setVisible(true);
				bugWindow.pack();
				//e.printStackTrace();
				//throw new RuntimeException("Connection to ERF's failed");
			}
		}
		else{
			boolean isCustomRupture = erfRupSelectorGuiBean.isCustomRuptureSelected();
			if(!isCustomRupture){
				EqkRupForecastBaseAPI eqkRupForecast = erfRupSelectorGuiBean.getSelectedEqkRupForecastModel();
				erfGuiBean.setERF(eqkRupForecast);
			}
		}
		//    erfPanel.removeAll(); TODO clean
		//    erfPanel.add(erfGuiBean, new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0,
		//        GridBagConstraints.CENTER,GridBagConstraints.BOTH, defaultInsets, 0, 0 ));
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
			erf_Classes.add(FRANKEL02_ADJ_FORECAST_CLASS_NAME);
			erf_Classes.add(WGCEP_AVG_UCERF_2_CLASS_NAME);
			erf_Classes.add(WGCEP_UCERF1_CLASS_NAME);


			try {

				erfRupSelectorGuiBean = new EqkRupSelectorGuiBean(erf,erf_Classes);
			}
			catch (InvocationTargetException e) {
				throw new RuntimeException("Connection to ERF's failed");
			}
		}
		else
			erfRupSelectorGuiBean.setEqkRupForecastModel(erf);
		//   erfPanel.removeAll(); TODO clean
		//   //erfGuiBean = null;
		//   erfPanel.add(erfRupSelectorGuiBean, new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0,
		//                GridBagConstraints.CENTER,GridBagConstraints.BOTH, defaultInsets, 0, 0 ));
		//   erfPanel.updateUI();
	}

	/**
	 * This method creates the HazardCurveCalc and Disaggregation Calc(if selected) instances.
	 * Calculations are performed on the user's own machine, no internet connection
	 * is required for it.
	 */
	protected void createCalcInstance(){
		try{
			if(calc == null)
				calc = new HazardCurveCalculator();
			if(disaggregationFlag)
				if(disaggCalc == null)
					disaggCalc = new DisaggregationCalculator();
		}catch(Exception e){

			ExceptionWindow bugWindow = new ExceptionWindow(this,e.getStackTrace(),this.getParametersInfoAsString());
			bugWindow.setVisible(true);
			bugWindow.pack();
			//     e.printStackTrace();
		}
	}

	/**
	 * Initialize the items to be added to the control list
	 */
	protected void initControlList() {
		controlComboBox.addItem(CONTROL_PANELS);
		controlComboBox.addItem(DisaggregationControlPanel.NAME);
		controlComboBox.addItem(CalculationSettingsControlPanel.NAME);
		controlComboBox.addItem(SitesOfInterestControlPanel.NAME);
		controlComboBox.addItem(SiteDataControlPanel.NAME);
		controlComboBox.addItem(X_ValuesInCurveControlPanel.NAME);
		//this.controlComboBox.addItem(MAP_CALC_CONTROL);
		controlComboBox.addItem(PlottingOptionControl.NAME);
		controlComboBox.addItem(XY_ValuesControlPanel.NAME);
	}

	/**
	 * Initialize the IMR Gui Bean
	 */
	protected void initIMR_GuiBean() {
		ArrayList<String> classNames = new ArrayList<String>();
		classNames.add(BA_2008_AttenRel.class.getName());
		classNames.add(CB_2008_AttenRel.class.getName());
		classNames.add(BJF_1997_AttenRel.class.getName());
		classNames.add(AS_1997_AttenRel.class.getName());
		classNames.add(Campbell_1997_AttenRel.class.getName());
		classNames.add(SadighEtAl_1997_AttenRel.class.getName());
		classNames.add(Field_2000_AttenRel.class.getName());

		AttenuationRelationshipsInstance inst = new AttenuationRelationshipsInstance(classNames);

		imrGuiBean = new IMR_MultiGuiBean(inst.createIMRClassInstance(null));
		imrGuiBean.addIMRChangeListener(this);
		// show this gui bean the JPanel
		//     imrPanel.add(this.imrGuiBean,new GridBagConstraints( 0, 0, 1, 1, 1.0, 1.0, TODO clean
		//         GridBagConstraints.CENTER, GridBagConstraints.BOTH, defaultInsets, 0, 0 ));
		//     imrPanel.updateUI();
	}

	public static void main(String[] args) {
		CEA_HazardCurveLocalModeApp applet = new CEA_HazardCurveLocalModeApp();
		applet.checkAppVersion();
		applet.init();
		applet.setTitle("CEA Hazard Curve Calculator "+"("+getAppVersion()+")" );
		applet.setVisible(true);
	}
}
