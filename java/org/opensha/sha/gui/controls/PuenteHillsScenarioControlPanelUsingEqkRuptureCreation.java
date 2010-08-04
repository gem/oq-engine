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


import java.awt.Component;
import java.util.ArrayList;

import org.opensha.commons.geo.LocationVector;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.commons.mapping.gmt.GMT_MapGenerator;
import org.opensha.commons.param.editor.ParameterEditor;
import org.opensha.commons.param.editor.ParameterListEditor;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.gui.beans.AttenuationRelationshipGuiBean;
import org.opensha.sha.gui.beans.EqkRupSelectorGuiBean;
import org.opensha.sha.gui.beans.EqkRuptureCreationPanel;
import org.opensha.sha.gui.beans.MapGuiBean;
import org.opensha.sha.gui.beans.SitesInGriddedRectangularRegionGuiBean;
import org.opensha.sha.imr.attenRelImpl.ShakeMap_2003_AttenRel;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.OtherParams.ComponentParam;
import org.opensha.sha.param.SimpleFaultParameter;
import org.opensha.sha.param.editor.SimpleFaultParameterEditor;
import org.opensha.sha.param.editor.gui.SimpleFaultParameterEditorPanel;


/**
 * <p>Title: PuenteHillsScenarioControlPanelUsingEqkRuptureCreation</p>
 * <p>Description: Sets the param value to replicate the official scenario shakemap
 * for the Puente Hill Scenario (http://www.trinet.org/shake/Puente_Hills_se)</p>
 * @author : Edward (Ned) Field and Nitin Gupta
 * @version 1.0
 */

public class PuenteHillsScenarioControlPanelUsingEqkRuptureCreation extends ConfirmDialogControlPanel {

	public static final String NAME = "Set Params for Puente Hills Scenario";
	public static final String MESSAGE = "Are you sure to set the parameters"+
							" for a Puente Hills scenario?";

	//for debugging
	protected final static boolean D = false;


	private EqkRupSelectorGuiBean erfGuiBean;
	private AttenuationRelationshipGuiBean imrGuiBean;
	private SitesInGriddedRectangularRegionGuiBean regionGuiBean;
	private MapGuiBean mapGuiBean;

	private FaultTrace faultTrace;
	private double aveDipDir;

	//default magnitude.
	private double magnitude = 7.1;

	/**
	 * Accepts 3 params for the EqkRupSelectorGuiBean, AttenuationRelationshipGuiBean, SitesInGriddedRectangularRegionGuiBean
	 * from the applet.
	 * @param erfGuiBean
	 * @param imrGuiBean
	 * @param regionGuiBean
	 * @param MapGuiBean
	 */
	public PuenteHillsScenarioControlPanelUsingEqkRuptureCreation(EqkRupSelectorGuiBean erfGuiBean,
			AttenuationRelationshipGuiBean imrGuiBean, SitesInGriddedRectangularRegionGuiBean regionGuiBean,
			MapGuiBean mapGuiBean, Component parent) {
		super(NAME, MESSAGE, parent);
		//getting the instance for variuos GuiBeans from the applet required to set the
		//default values for the Params for the Puente Hills Scenario.
		this.erfGuiBean = erfGuiBean;
		this.imrGuiBean = imrGuiBean;
		this.regionGuiBean = regionGuiBean;
		this.mapGuiBean = mapGuiBean;
	}

	public void doinit() {
		mkFaultTrace();
	}

	/**
	 * This make the faultTrace from the segment-data sent by Andreas Plesch via
	 * email on 3/10/04:
	 */
	private void mkFaultTrace() {

		// NOTE for commments on replaced lines below see:
		// org.opensha.sha.gui.controls.PuenteHillsScenarioControlPanel

		/* Original Segment Data from Andreas Plesch via email on 3/10/04:

    LA_lon  LA_lat  LA_depth
    -118.12273      33.97087 -2979.44
    -118.33585      34.03440 -2363.39
    -118.25737      34.23723 -14965.3
    -118.04988      34.15721 -14532.7

    CH_lon  CH_lat  CH_depth
    -118.04441      33.89454 -3440.82
    -117.86819      33.89952 -2500
    -117.86678      34.13627 -15474.6
    -118.04490      34.09232 -14485

    SF_lon  SF_lat  SF_depth
    -118.01871      33.93282 -3000
    -118.13920      33.90885 -2750
    -118.14720      34.11061 -15068.3
    -118.01795      34.10093 -14479.3
		 */

		Location loc1, loc2, loc3;
		Location finalLoc1, finalLoc2, finalLoc3, finalLoc4 , tempLoc1, tempLoc2, tempLoc3, tempLoc4;
		LocationVector dir1, dir2;
		double hDist,vDist, dip;
		aveDipDir = 0;

		// find the points at 5 and 17 km depths by projecting each edge down
		// also find the final fault trace (by averaging intermediate points)
		// and the ave-dip direction.

		// LA Segment:
		if (D) System.out.println("\nLA Segment:");
		if (D) System.out.println("LA_lon2  LA_lat2  LA_depth2");

		loc1 = new Location(33.97087, -118.12273, 2.97944);
		loc2 = new Location(34.15721, -118.04988, 14.5327);
		dir1 = LocationUtils.vector(loc1, loc2);
		dip = Math.tan(dir1.getVertDistance()/dir1.getHorzDistance());
		//		vDist = loc1.getDepth()-5.0;
		vDist = 5.0 - loc1.getDepth();
		hDist = vDist/Math.atan(dip);
		aveDipDir += dir1.getAzimuth();
		//		dir2 = new LocationVector(vDist, hDist,dir1.getBackAzimuth(),dir1.getAzimuth());
		//	    dir2 = new LocationVector(vDist, hDist,dir1.getAzimuth(),dir1.getBackAzimuth());
		dir2 = new LocationVector(dir1.getAzimuth(), hDist, vDist);
		loc3 = LocationUtils.location(loc1,dir2);
		if (D) System.out.println((float)loc3.getLongitude()+" "+(float)loc3.getLatitude()+" "+(float)loc3.getDepth());
		tempLoc4 = loc3;
		//		vDist = loc1.getDepth()-17.0;
		vDist = 17.0 - loc1.getDepth();
		hDist = vDist/Math.atan(dip);
		//		dir2 = new LocationVector(vDist, hDist,dir1.getBackAzimuth(),dir1.getAzimuth());
		//	    dir2 = new LocationVector(vDist, hDist,dir1.getAzimuth(),dir1.getBackAzimuth());
		dir2 = new LocationVector(dir1.getAzimuth(), hDist, vDist);
		loc3 = LocationUtils.location(loc1,dir2);
		if (D) System.out.println((float)loc3.getLongitude()+" "+(float)loc3.getLatitude()+" "+(float)loc3.getDepth());

		loc1 = new Location(34.03440, -118.33585, 2.36339);
		loc2 = new Location(34.23723, -118.25737, 14.9653);
		dir1 = LocationUtils.vector(loc1, loc2);
		dip = Math.tan(dir1.getVertDistance()/dir1.getHorzDistance());
		//		vDist = loc1.getDepth()-5.0;
		vDist = 5.0 - loc1.getDepth();
		hDist = vDist/Math.atan(dip);
		aveDipDir += dir1.getAzimuth();
		//		dir2 = new LocationVector(vDist, hDist,dir1.getBackAzimuth(),dir1.getAzimuth());
		//	    dir2 = new LocationVector(vDist, hDist,dir1.getAzimuth(),dir1.getBackAzimuth());
		dir2 = new LocationVector(dir1.getAzimuth(), hDist, vDist);
		loc3 = LocationUtils.location(loc1,dir2);
		if (D) System.out.println((float)loc3.getLongitude()+" "+(float)loc3.getLatitude()+" "+(float)loc3.getDepth());
		finalLoc4 = loc3;
		//		vDist = loc1.getDepth()-17.0;
		vDist = 17.0 - loc1.getDepth();
		hDist = vDist/Math.atan(dip);
		//		dir2 = new LocationVector(vDist, hDist,dir1.getBackAzimuth(),dir1.getAzimuth());
		//	    dir2 = new LocationVector(vDist, hDist,dir1.getAzimuth(),dir1.getBackAzimuth());
		dir2 = new LocationVector(dir1.getAzimuth(), hDist, vDist);
		loc3 = LocationUtils.location(loc1,dir2);
		if (D) System.out.println((float)loc3.getLongitude()+" "+(float)loc3.getLatitude()+" "+(float)loc3.getDepth());

		// CH Segment:
		if (D) System.out.println("\nCH Segment:");
		if (D) System.out.println("CH_lon2  CH_lat2  CH_depth2");

		loc1 = new Location(33.89952, -117.86819, 2.500);
		loc2 = new Location(34.13627, -117.86678, 15.4746);
		dir1 = LocationUtils.vector(loc1, loc2);
		dip = Math.tan(dir1.getVertDistance()/dir1.getHorzDistance());
		//		vDist = loc1.getDepth()-5.0;
		vDist = 5.0 - loc1.getDepth();
		hDist = vDist/Math.atan(dip);
		aveDipDir += dir1.getAzimuth();
		//		dir2 = new LocationVector(vDist, hDist,dir1.getBackAzimuth(),dir1.getAzimuth());
		//	    dir2 = new LocationVector(vDist, hDist,dir1.getAzimuth(),dir1.getBackAzimuth());
		dir2 = new LocationVector(dir1.getAzimuth(), hDist, vDist);
		loc3 = LocationUtils.location(loc1,dir2);
		if (D) System.out.println((float)loc3.getLongitude()+" "+(float)loc3.getLatitude()+" "+(float)loc3.getDepth());
		finalLoc1 = loc3;
		//		vDist = loc1.getDepth()-17.0;
		vDist = 17.0 - loc1.getDepth();
		hDist = vDist/Math.atan(dip);
		//		dir2 = new LocationVector(vDist, hDist,dir1.getBackAzimuth(),dir1.getAzimuth());
		//	    dir2 = new LocationVector(vDist, hDist,dir1.getAzimuth(),dir1.getBackAzimuth());
		dir2 = new LocationVector(dir1.getAzimuth(), hDist, vDist);
		loc3 = LocationUtils.location(loc1,dir2);
		if (D) System.out.println((float)loc3.getLongitude()+" "+(float)loc3.getLatitude()+" "+(float)loc3.getDepth());

		loc1 = new Location(33.89454, -118.04441, 3.44082);
		loc2 = new Location(34.09232, -118.04490, 14.485);
		dir1 = LocationUtils.vector(loc1, loc2);
		dip = Math.tan(dir1.getVertDistance()/dir1.getHorzDistance());
		//		vDist = loc1.getDepth()-5.0;
		vDist = 5.0 - loc1.getDepth();
		hDist = vDist/Math.atan(dip);
		aveDipDir += dir1.getAzimuth();
		//		dir2 = new LocationVector(vDist, hDist,dir1.getBackAzimuth(),dir1.getAzimuth());
		//	    dir2 = new LocationVector(vDist, hDist,dir1.getAzimuth(),dir1.getBackAzimuth());
		dir2 = new LocationVector(dir1.getAzimuth(), hDist, vDist);
		loc3 = LocationUtils.location(loc1,dir2);
		if (D) System.out.println((float)loc3.getLongitude()+" "+(float)loc3.getLatitude()+" "+(float)loc3.getDepth());
		tempLoc1 = loc3;
		//		vDist = loc1.getDepth()-17.0;
		vDist = 17.0 - loc1.getDepth();
		hDist = vDist/Math.atan(dip);
		//		dir2 = new LocationVector(vDist, hDist,dir1.getBackAzimuth(),dir1.getAzimuth());
		//	    dir2 = new LocationVector(vDist, hDist,dir1.getAzimuth(),dir1.getBackAzimuth());
		dir2 = new LocationVector(dir1.getAzimuth(), hDist, vDist);
		loc3 = LocationUtils.location(loc1,dir2);
		if (D) System.out.println((float)loc3.getLongitude()+" "+(float)loc3.getLatitude()+" "+(float)loc3.getDepth());




		// SF Segment:
		if (D) System.out.println("\nSF Segment:");
		if (D) System.out.println("SF_lon2  SF_lat2  SF_depth2");

		loc1 = new Location(33.93282, -118.01871, 3.000);
		loc2 = new Location(34.10093, -118.01795, 14.4793);
		dir1 = LocationUtils.vector(loc1, loc2);
		dip = Math.tan(dir1.getVertDistance()/dir1.getHorzDistance());
		//		vDist = loc1.getDepth()-5.0;
		vDist = 5.0 - loc1.getDepth();
		hDist = vDist/Math.atan(dip);
		aveDipDir += dir1.getAzimuth();
		//		dir2 = new LocationVector(vDist, hDist,dir1.getBackAzimuth(),dir1.getAzimuth());
		//	    dir2 = new LocationVector(vDist, hDist,dir1.getAzimuth(),dir1.getBackAzimuth());
		dir2 = new LocationVector(dir1.getAzimuth(), hDist, vDist);
		loc3 = LocationUtils.location(loc1,dir2);
		if (D) System.out.println((float)loc3.getLongitude()+" "+(float)loc3.getLatitude()+" "+(float)loc3.getDepth());
		tempLoc2 = loc3;
		//		vDist = loc1.getDepth()-17.0;
		vDist = 17.0 - loc1.getDepth();
		hDist = vDist/Math.atan(dip);
		//		dir2 = new LocationVector(vDist, hDist,dir1.getBackAzimuth(),dir1.getAzimuth());
		//	    dir2 = new LocationVector(vDist, hDist,dir1.getAzimuth(),dir1.getBackAzimuth());
		dir2 = new LocationVector(dir1.getAzimuth(), hDist, vDist);
		loc3 = LocationUtils.location(loc1,dir2);
		if (D) System.out.println((float)loc3.getLongitude()+" "+(float)loc3.getLatitude()+" "+(float)loc3.getDepth());

		loc1 = new Location(33.90885, -118.13920, 2.750);
		loc2 = new Location(34.11061, -118.14720, 15.0683);
		dir1 = LocationUtils.vector(loc1, loc2);
		dip = Math.tan(dir1.getVertDistance()/dir1.getHorzDistance());
		//		vDist = loc1.getDepth()-5.0;
		vDist = 5.0 - loc1.getDepth();
		hDist = vDist/Math.atan(dip);
		aveDipDir += dir1.getAzimuth();
		//		dir2 = new LocationVector(vDist, hDist,dir1.getBackAzimuth(),dir1.getAzimuth());
		//	    dir2 = new LocationVector(vDist, hDist,dir1.getAzimuth(),dir1.getBackAzimuth());
		dir2 = new LocationVector(dir1.getAzimuth(), hDist, vDist);
		loc3 = LocationUtils.location(loc1,dir2);
		if (D) System.out.println((float)loc3.getLongitude()+" "+(float)loc3.getLatitude()+" "+(float)loc3.getDepth());
		tempLoc3 = loc3;
		//		vDist = loc1.getDepth()-17.0;
		vDist = 17.0 - loc1.getDepth();
		hDist = vDist/Math.atan(dip);
		//		dir2 = new LocationVector(vDist, hDist,dir1.getBackAzimuth(),dir1.getAzimuth());
		//	    dir2 = new LocationVector(vDist, hDist,dir1.getAzimuth(),dir1.getBackAzimuth());
		dir2 = new LocationVector(dir1.getAzimuth(), hDist, vDist);
		loc3 = LocationUtils.location(loc1,dir2);
		if (D) System.out.println((float)loc3.getLongitude()+" "+(float)loc3.getLatitude()+" "+(float)loc3.getDepth());

		finalLoc2 = new Location((tempLoc1.getLatitude()+tempLoc2.getLatitude())/2,
				(tempLoc1.getLongitude()+tempLoc2.getLongitude())/2,
				(tempLoc1.getDepth()+tempLoc2.getDepth())/2);
		finalLoc3 = new Location((tempLoc3.getLatitude()+tempLoc4.getLatitude())/2,
				(tempLoc3.getLongitude()+tempLoc4.getLongitude())/2,
				(tempLoc3.getDepth()+tempLoc4.getDepth())/2);

		if (D) System.out.println("\nFinal Fault Trace:");
		if (D) System.out.println("final_tr_lat final_tr_lon final_tr_depth");
		if (D) System.out.println((float)finalLoc1.getLatitude()+" "+(float)finalLoc1.getLongitude()+" "+(float)finalLoc1.getDepth());
		if (D) System.out.println((float)finalLoc2.getLatitude()+" "+(float)finalLoc2.getLongitude()+" "+(float)finalLoc2.getDepth());
		if (D) System.out.println((float)finalLoc3.getLatitude()+" "+(float)finalLoc3.getLongitude()+" "+(float)finalLoc3.getDepth());
		if (D) System.out.println((float)finalLoc4.getLatitude()+" "+(float)finalLoc4.getLongitude()+" "+(float)finalLoc4.getDepth());

		faultTrace = new FaultTrace("Puente Hills Fault Trace");
		faultTrace.add(finalLoc1);
		faultTrace.add(finalLoc2);
		faultTrace.add(finalLoc3);
		faultTrace.add(finalLoc4);

		aveDipDir /= 6;

		if (D) System.out.println("\nAveDipDir = "+aveDipDir);

		if (D) System.out.println("\n Trace Length = "+faultTrace.getTraceLength());

		FaultTrace tempTr = new FaultTrace("");
		tempTr.add(finalLoc1);
		tempTr.add(finalLoc2);
		if (D) System.out.println("\n new-merged CH seg Length = "+tempTr.getTraceLength());
		tempTr = new FaultTrace("");
		tempTr.add(finalLoc2);
		tempTr.add(finalLoc3);
		if (D) System.out.println("\n new-merged SF seg Length = "+tempTr.getTraceLength());
		tempTr = new FaultTrace("");
		tempTr.add(finalLoc3);
		tempTr.add(finalLoc4);
		if (D) System.out.println("\n new-merged LA seg Length = "+tempTr.getTraceLength());

		tempTr = new FaultTrace("");
		tempTr.add(finalLoc1);
		tempTr.add(tempLoc1);
		if (D) System.out.println("\n new CH seg Length = "+tempTr.getTraceLength());
		tempTr = new FaultTrace("");
		tempTr.add(tempLoc2);
		tempTr.add(tempLoc3);
		if (D) System.out.println("\n new SF seg Length = "+tempTr.getTraceLength());
		tempTr = new FaultTrace("");
		tempTr.add(tempLoc4);
		tempTr.add(finalLoc4);
		if (D) System.out.println("\n new LA seg Length = "+tempTr.getTraceLength());
	}




	/**
	 * Sets the default Parameters in the Application for the Puente Hill Scenario
	 */
	@Override
	public void applyControl() {
		//making the ERF Gui Bean Adjustable Param not visible to the user, becuase
		//this control panel will set the values by itself.
		//This is done in the EqkRupSelectorGuiBean
		ParameterEditor paramEditor = erfGuiBean.getParameterEditor(EqkRupSelectorGuiBean.RUPTURE_SELECTOR_PARAM_NAME);
		paramEditor.setValue(EqkRupSelectorGuiBean.CREATE_RUPTURE);
		paramEditor.refreshParamEditor();
		EqkRuptureCreationPanel erfPanel= (EqkRuptureCreationPanel)erfGuiBean.getEqkRuptureSelectorPanel();

		//changing the ERF to SimpleFaultERF
		paramEditor = erfPanel.getParameterEditor(EqkRuptureCreationPanel.SRC_TYP_PARAM_NAME);
		paramEditor.setValue(EqkRuptureCreationPanel.FINITE_SRC_NAME);
		paramEditor.refreshParamEditor();


		// Set rake value to 90 degrees
		erfPanel.getParameter(EqkRuptureCreationPanel.RAKE_PARAM_NAME).setValue(new Double(90));


		double dip = 27;
		double depth1=5, depth2=17;

		//getting the instance for the SimpleFaultParameterEditorPanel from the GuiBean to adjust the fault Params
		SimpleFaultParameterEditorPanel faultPanel= ((SimpleFaultParameterEditor)erfPanel.getParameterEditor(erfPanel.FAULT_PARAM_NAME)).getParameterEditorPanel();
		//creating the Lat vector for the SimpleFaultParameter

		ArrayList<Double> lats = new ArrayList<Double>();
		ArrayList<Double> lons = new ArrayList<Double>();
		for(int i = 0; i<faultTrace.getNumLocations(); i++) {
			lats.add(new Double(faultTrace.get(i).getLatitude()));
			lons.add(new Double(faultTrace.get(i).getLongitude()));
		}

		//creating the dip vector for the SimpleFaultParameter
		ArrayList<Double> dips = new ArrayList<Double>();
		dips.add(new Double(dip));

		//creating the depth vector for the SimpleFaultParameter
		ArrayList<Double> depths = new ArrayList<Double>();
		depths.add(new Double(depth1));
		depths.add(new Double(depth2));

		//setting the FaultParameterEditor with the default values for Puente Hills Scenario
		faultPanel.setAll(((SimpleFaultParameter)faultPanel.getParameter()).DEFAULT_GRID_SPACING,lats,
				lons,dips,depths,((SimpleFaultParameter)faultPanel.getParameter()).STIRLING);

		// set the average dip direction
		// use default which is perp to ave strike.
		//    faultPanel.setDipDirection(aveDipDir);

		//updaing the faultParameter to update the faultSurface
		faultPanel.setEvenlyGriddedSurfaceFromParams();

		erfPanel.getParameter(EqkRuptureCreationPanel.MAG_PARAM_NAME).setValue(new Double(magnitude));
		erfPanel.getParameterListEditor().refreshParamEditor();


		//checking if the single AttenRel is selected
		boolean isSingleAttenRelSelected =imrGuiBean.isSingleAttenRelTypeSelected();
		//if single attenRel gui is not selected then toggle to the single attenRel gui Panel
		if(!isSingleAttenRelSelected)
			imrGuiBean.toggleBetweenSingleAndMultipleAttenRelGuiSelection();
		// Set the imt as PGA
		ParameterListEditor editor = imrGuiBean.getIntensityMeasureParamEditor();
		editor.getParameterList().getParameter(AttenuationRelationshipGuiBean.IMT_PARAM_NAME).setValue(PGA_Param.NAME);
		editor.refreshParamEditor();
		//Updating the IMR Gui Bean with the ShakeMap attenuation relationship
		imrGuiBean.setIMR_Selected(ShakeMap_2003_AttenRel.NAME);
		imrGuiBean.getSelectedIMR_Instance().getParameter(ComponentParam.NAME).setValue(ComponentParam.COMPONENT_AVE_HORZ);
		imrGuiBean.getSingleAttenRelParamListEditor().refreshParamEditor();

		//Updating the SitesInGriddedRectangularRegionGuiBean with the Puente Hills resion setting
		regionGuiBean.getParameterList().getParameter(SitesInGriddedRectangularRegionGuiBean.MIN_LATITUDE).setValue(new Double(33.2));
		regionGuiBean.getParameterList().getParameter(SitesInGriddedRectangularRegionGuiBean.MAX_LATITUDE).setValue(new Double(35.0));
		regionGuiBean.getParameterList().getParameter(SitesInGriddedRectangularRegionGuiBean.MIN_LONGITUDE).setValue(new Double(-119.5));
		regionGuiBean.getParameterList().getParameter(SitesInGriddedRectangularRegionGuiBean.MAX_LONGITUDE).setValue(new Double(-116.18));
		//    regionGuiBean.getParameterList().getParameter(regionGuiBean.GRID_SPACING).setValue(new Double(.1));
		regionGuiBean.getParameterList().getParameter(SitesInGriddedRectangularRegionGuiBean.GRID_SPACING).setValue(new Double(.016667));
		regionGuiBean.getParameterList().getParameter(SitesInGriddedRectangularRegionGuiBean.SITE_PARAM_NAME).setValue(SitesInGriddedRectangularRegionGuiBean.USE_SITE_DATA);


		// Set some of the mapping params:
		mapGuiBean.getParameterList().getParameter(GMT_MapGenerator.GMT_WEBSERVICE_NAME).setValue(new Boolean(true));
		mapGuiBean.getParameterList().getParameter(GMT_MapGenerator.LOG_PLOT_NAME).setValue(new Boolean(false));
		mapGuiBean.getParameterList().getParameter(GMT_MapGenerator.COLOR_SCALE_MODE_NAME).setValue(GMT_MapGenerator.COLOR_SCALE_MODE_FROMDATA);
		mapGuiBean.refreshParamEditor();
	}
}
