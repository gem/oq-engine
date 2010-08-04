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

package org.opensha.sha.calc.hazardMap.old.applet;

import java.lang.reflect.InvocationTargetException;
import java.util.ArrayList;

import javax.swing.BoxLayout;
import javax.swing.JPanel;

import org.opensha.commons.exceptions.RegionConstraintException;
import org.opensha.commons.geo.Region;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.gui.beans.ERF_GuiBean;
import org.opensha.sha.gui.beans.IMR_GuiBean;
import org.opensha.sha.gui.beans.IMR_GuiBeanAPI;
import org.opensha.sha.gui.beans.IMT_GuiBean;
import org.opensha.sha.gui.beans.SitesInGriddedRegionGuiBean;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;

public class HazardStep extends JPanel implements IMR_GuiBeanAPI {
	
	/**
	 *  The object class names for all the supported Eqk Rup Forecasts
	 */
	public final static String FRANKEL_ADJ_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.Frankel96.Frankel96_AdjustableEqkRupForecast";
	public final static String FRANKEL_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.Frankel96.Frankel96_EqkRupForecast";
	public final static String FRANKEL02_ADJ_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.Frankel02.Frankel02_AdjustableEqkRupForecast";
	public final static String WG02_ERF_LIST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.WG02.WG02_ERF_Epistemic_List";
	public final static String WGCEP_UCERF1_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF1.WGCEP_UCERF1_EqkRupForecast";
	public final static String PEER_AREA_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.PEER_TestCases.PEER_AreaForecast";
	public final static String PEER_NON_PLANAR_FAULT_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.PEER_TestCases.PEER_NonPlanarFaultForecast";
	public final static String PEER_MULTI_SOURCE_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.PEER_TestCases.PEER_MultiSourceForecast";
	public final static String PEER_LOGIC_TREE_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.PEER_TestCases.PEER_LogicTreeERF_List";
	//public final static String STEP_FORECAST_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.step.STEP_EqkRupForecast";
	public final static String STEP_ALASKA_ERF_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.step.STEP_AlaskanPipeForecast";
	public final static String POISSON_FAULT_ERF_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.FloatingPoissonFaultERF";
	public final static String SIMPLE_FAULT_ERF_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.PoissonFaultERF";
	public final static String POINT_SRC_FORECAST_CLASS_NAME="org.opensha.sha.earthquake.rupForecastImpl.PointSourceERF";
	public final static String POINT2MULT_VSS_FORECAST_CLASS_NAME="org.opensha.sha.earthquake.rupForecastImpl.Point2MultVertSS_Fault.Point2MultVertSS_FaultERF";
	public final static String POINT2MULT_VSS_ERF_LIST_CLASS_NAME="org.opensha.sha.earthquake.rupForecastImpl.Point2MultVertSS_Fault.Point2MultVertSS_FaultERF_List";
	public final static String WG02_ERF_CLASS_NAME = "org.opensha.sha.earthquake.rupForecastImpl.WG02.WG02_EqkRupForecast";
	public final static String WGCEP_UCERF_2_CLASS_NAME="org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.UCERF2";
	public final static String WGCEP_UCERF_2_EPISTEMIC_LIST_CLASS_NAME="org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.UCERF2_TimeIndependentEpistemicList";
	public final static String WGCEP_AVG_UCERF_2_CLASS_NAME="org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.MeanUCERF2.MeanUCERF2";
//	public final static String YUCCA_MOUNTAIN_CLASS_NAME="org.opensha.sha.earthquake.rupForecastImpl.YuccaMountain.YuccaMountainERF";
//	public final static String YUCCA_MOUNTAIN_ERF_LIST_CLASS_NAME="org.opensha.sha.earthquake.rupForecastImpl.YuccaMountain.YuccaMountainERF_List";
	
	private ERF_GuiBean erfBean;
	private IMR_GuiBean imrGuiBean;
	private IMT_GuiBean imtGuiBean;
	
	private SitesInGriddedRegionGuiBean sitesGuiBean;
	
	private JPanel imPanel = new JPanel();
	
	public HazardStep(SitesInGriddedRegionGuiBean sitesGuiBean) {
		super();
		
		this.setLayout(new BoxLayout(this, BoxLayout.X_AXIS));
		
		this.sitesGuiBean = sitesGuiBean;
		
		erfBean = createERF_GUI_Bean();
		imrGuiBean = createIMR_GUI_Bean();
		imtGuiBean = createIMT_GUI_Bean();
		
		imPanel.setLayout(new BoxLayout(imPanel, BoxLayout.Y_AXIS));
		imPanel.add(imrGuiBean);
		imPanel.add(imtGuiBean);
		
		this.add(erfBean);
		this.add(imPanel);
	}
	
	private IMR_GuiBean createIMR_GUI_Bean() {
		return new IMR_GuiBean(this);
	}
	
	private IMT_GuiBean createIMT_GUI_Bean() {
		AttenuationRelationship attenRel = (AttenuationRelationship)imrGuiBean.getSelectedIMR_Instance();
		return new IMT_GuiBean(attenRel,attenRel.getSupportedIntensityMeasuresIterator());
	}
	
	private ERF_GuiBean createERF_GUI_Bean() {
		ArrayList<String> erf_Classes = new ArrayList<String>();

		erf_Classes.add(FRANKEL_ADJ_FORECAST_CLASS_NAME);
		erf_Classes.add(FRANKEL_FORECAST_CLASS_NAME);
		erf_Classes.add(FRANKEL02_ADJ_FORECAST_CLASS_NAME);
//		erf_Classes.add(YUCCA_MOUNTAIN_CLASS_NAME);
//		erf_Classes.add(YUCCA_MOUNTAIN_ERF_LIST_CLASS_NAME);
		erf_Classes.add(WGCEP_UCERF_2_CLASS_NAME);
		erf_Classes.add(WGCEP_UCERF_2_EPISTEMIC_LIST_CLASS_NAME);
		erf_Classes.add(WGCEP_AVG_UCERF_2_CLASS_NAME);
		erf_Classes.add(WG02_ERF_LIST_CLASS_NAME);
		erf_Classes.add(WGCEP_UCERF1_CLASS_NAME);
		erf_Classes.add(PEER_AREA_FORECAST_CLASS_NAME);
		erf_Classes.add(PEER_NON_PLANAR_FAULT_FORECAST_CLASS_NAME);
		erf_Classes.add(PEER_MULTI_SOURCE_FORECAST_CLASS_NAME);
		erf_Classes.add(PEER_LOGIC_TREE_FORECAST_CLASS_NAME);
		//erf_Classes.add(STEP_FORECAST_CLASS_NAME);
		erf_Classes.add(STEP_ALASKA_ERF_CLASS_NAME);
		erf_Classes.add(POISSON_FAULT_ERF_CLASS_NAME);
		erf_Classes.add(SIMPLE_FAULT_ERF_CLASS_NAME);
		erf_Classes.add(POINT_SRC_FORECAST_CLASS_NAME);
		erf_Classes.add(POINT2MULT_VSS_FORECAST_CLASS_NAME);
		erf_Classes.add(POINT2MULT_VSS_ERF_LIST_CLASS_NAME);
		try{
			return new ERF_GuiBean(erf_Classes);
		}catch(InvocationTargetException e){
			throw new RuntimeException("Connection to ERF servlets failed");
		}
	}

	/**
	 * Updates the IMT_GuiBean to reflect the chnaged IM for the selected AttenuationRelationship.
	 * This method is called from the IMR_GuiBean to update the application with the Attenuation's
	 * supported IMs.
	 *
	 */
	public void updateIM() {
		//get the selected IMR
		ScalarIntensityMeasureRelationshipAPI imr = imrGuiBean.getSelectedIMR_Instance();
		imtGuiBean.setIM(imr,imr.getSupportedIntensityMeasuresIterator()) ;
	}

	/**
	 * Updates the SitesInGriddedRegionGuiBean to reflect the chnaged SiteParams for the selected AttenuationRelationship.
	 * This method is called from the IMR_GuiBean to update the application with the Attenuation's
	 * Site Params.
	 *
	 */
	public void updateSiteParams() {
		//get the selected IMR
		ScalarIntensityMeasureRelationshipAPI imr = imrGuiBean.getSelectedIMR_Instance();
		sitesGuiBean.replaceSiteParams(imr.getSiteParamsIterator());
		sitesGuiBean.validate();
		sitesGuiBean.repaint();
	}
	
	public EqkRupForecast getERF() throws InvocationTargetException {
		return (EqkRupForecast)erfBean.getSelectedERF_Instance();
	}
	
	public ScalarIntensityMeasureRelationshipAPI getIMR() {
		return imrGuiBean.getSelectedIMR_Instance();
	}
	
	public IMR_GuiBean getIMRGuiBean() {
		return imrGuiBean;
	}
	
	public IMT_GuiBean getIMTGuiBean() {
		return imtGuiBean;
	}
	
	public SitesInGriddedRegionGuiBean createSitesGUIBean(ArrayList<Region> regions) throws RegionConstraintException {
		sitesGuiBean = new SitesInGriddedRegionGuiBean(regions);
		sitesGuiBean.replaceSiteParams(this.getIMR().getSiteParamsIterator());
		return sitesGuiBean;
	}

}
