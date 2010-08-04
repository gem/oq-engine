package org.opensha.sha.gui;

import static org.junit.Assert.*;

import java.util.ListIterator;

import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.gem.GEM1.scratch.ZhaoEtAl_2006_AttenRel;
import org.opensha.sha.earthquake.rupForecastImpl.Frankel96.Frankel96_AdjustableEqkRupForecast;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.GEM1SouthAmericaERF;
import org.opensha.sha.gui.beans.ERF_GuiBean;
import org.opensha.sha.gui.beans.IMR_MultiGuiBean;
import org.opensha.sha.gui.beans.IMT_NewGuiBean;
import org.opensha.sha.gui.beans.Site_GuiBean;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.attenRelImpl.CB_2008_AttenRel;
import org.opensha.sha.imr.attenRelImpl.CY_2008_AttenRel;
import org.opensha.sha.imr.param.SiteParams.DepthTo1pt0kmPerSecParam;
import org.opensha.sha.imr.param.SiteParams.DepthTo2pt5kmPerSecParam;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;
import org.opensha.sha.util.TectonicRegionType;

public class TestHazardCurveMultiIMRs {
	
	HazardCurveLocalModeApplication app;
	ERF_GuiBean erfGui;
	IMR_MultiGuiBean imrGui;
	IMT_NewGuiBean imtGui;
	Site_GuiBean siteGui;

	@BeforeClass
	public static void setUpBeforeClass() throws Exception {
		
	}

	@Before
	public void setUp() throws Exception {
		app = new HazardCurveLocalModeApplication();
		app.checkAppVersion();
		app.init();
		app.setTitle("Hazard Curve Local mode Application "+"("+HazardCurveLocalModeApplication.getAppVersion()+")" );
		app.setVisible(true);
		app.createCalcInstance();
		
		erfGui = app.getEqkRupForecastGuiBeanInstance();
		imrGui = app.getIMRGuiBeanInstance();
		imtGui = app.getIMTGuiBeanInstance();
		siteGui = app.getSiteGuiBeanInstance();
	}
	
	@Test
	public void testMultiTect() {
		erfGui.getParameter(ERF_GuiBean.ERF_PARAM_NAME).setValue(Frankel96_AdjustableEqkRupForecast.NAME);
		assertFalse("Multi IMR check box should not visible now", imrGui.isCheckBoxVisible());
		
		erfGui.getParameter(ERF_GuiBean.ERF_PARAM_NAME).setValue(GEM1SouthAmericaERF.NAME);
		assertTrue("Multi IMR check box should be visible now", imrGui.isCheckBoxVisible());
		
		imrGui.setMultipleIMRs(true);
		imrGui.setIMR(CB_2008_AttenRel.NAME, TectonicRegionType.ACTIVE_SHALLOW);
		imrGui.setIMR(CY_2008_AttenRel.NAME, TectonicRegionType.STABLE_SHALLOW);
		imrGui.setIMR(ZhaoEtAl_2006_AttenRel.NAME, TectonicRegionType.SUBDUCTION_INTERFACE);
		imrGui.setIMR(ZhaoEtAl_2006_AttenRel.NAME, TectonicRegionType.SUBDUCTION_SLAB);
		
		ParameterList siteParamList = siteGui.getParameterListEditor().getParameterList();
		
		
		// make sure that every IMR site param is in the GUI
		for (ScalarIntensityMeasureRelationshipAPI imr : imrGui.getIMRMap().values()) {
			ListIterator<ParameterAPI<?>> mySiteParamsIt = imr.getSiteParamsIterator();
			
			while (mySiteParamsIt.hasNext()) {
				ParameterAPI<?> mySiteParam = mySiteParamsIt.next();
				assertTrue("Site param '" + mySiteParam.getName() + "' not in site GUI!",
						siteParamList.containsParameter(mySiteParam.getName()));
			}
		}
		
		Double vs30_val = 189.0;
		Double depth2_5_val = 1.9;
		Double depth1_0_val = 350.0;
		
		siteParamList.getParameter(Vs30_Param.NAME).setValue(vs30_val);
		siteParamList.getParameter(DepthTo2pt5kmPerSecParam.NAME).setValue(depth2_5_val);
		siteParamList.getParameter(DepthTo1pt0kmPerSecParam.NAME).setValue(depth1_0_val);
		
		siteParamList.getParameter(Site_GuiBean.LATITUDE).setValue(-33.45);
		siteParamList.getParameter(Site_GuiBean.LONGITUDE).setValue(-70.6666667);
		app.progressCheckBox.setSelected(false);
		app.run();
		
		// make sure that every site param got set correctly in the IMRs!
		for (ScalarIntensityMeasureRelationshipAPI imr : imrGui.getIMRMap().values()) {
			ListIterator<ParameterAPI<?>> mySiteParamsIt = imr.getSiteParamsIterator();
			
			System.out.println("Testing site params for " + imr.getName());
			
			while (mySiteParamsIt.hasNext()) {
				ParameterAPI<?> mySiteParam = mySiteParamsIt.next();
				System.out.println(mySiteParam.getName() + ": " + mySiteParam.getValue());
				if (mySiteParam.getName().equals(Vs30_Param.NAME)) {
					assertEquals("Vs30 not equal!", vs30_val, (Double)mySiteParam.getValue());
				} else if (mySiteParam.getName().equals(DepthTo2pt5kmPerSecParam.NAME)) {
					assertEquals("Depth 2.5 not equal!", depth2_5_val, (Double)mySiteParam.getValue());
				} else if (mySiteParam.getName().equals(DepthTo1pt0kmPerSecParam.NAME)) {
					assertEquals("Depth 1.0 not equal!", depth1_0_val, (Double)mySiteParam.getValue());
				}
			}
		}
	}

}
