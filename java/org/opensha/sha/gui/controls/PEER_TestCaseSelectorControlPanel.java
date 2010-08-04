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

import java.awt.Color;
import java.awt.Component;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.Window;
import java.awt.event.ActionEvent;
import java.util.ArrayList;

import javax.swing.JComboBox;
import javax.swing.JFrame;
import javax.swing.JLabel;

import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.PEER_testsMagAreaRelationship;
import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.param.ParameterList;
import org.opensha.sha.calc.HazardCurveCalculator;
import org.opensha.sha.earthquake.rupForecastImpl.FloatingPoissonFaultERF;
import org.opensha.sha.earthquake.rupForecastImpl.PEER_TestCases.PEER_AreaForecast;
import org.opensha.sha.earthquake.rupForecastImpl.PEER_TestCases.PEER_LogicTreeERF_List;
import org.opensha.sha.earthquake.rupForecastImpl.PEER_TestCases.PEER_MultiSourceForecast;
import org.opensha.sha.earthquake.rupForecastImpl.PEER_TestCases.PEER_NonPlanarFaultForecast;
import org.opensha.sha.gui.HazardCurveServerModeApplication;
import org.opensha.sha.gui.beans.ERF_GuiBean;
import org.opensha.sha.gui.beans.IMR_GuiBean;
import org.opensha.sha.gui.beans.IMR_MultiGuiBean;
import org.opensha.sha.gui.beans.IMT_GuiBean;
import org.opensha.sha.gui.beans.IMT_NewGuiBean;
import org.opensha.sha.gui.beans.Site_GuiBean;
import org.opensha.sha.gui.beans.TimeSpanGuiBean;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.attenRelImpl.AS_1997_AttenRel;
import org.opensha.sha.imr.attenRelImpl.Campbell_1997_AttenRel;
import org.opensha.sha.imr.attenRelImpl.SadighEtAl_1997_AttenRel;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncLevelParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncTypeParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.magdist.GaussianMagFreqDist;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.SingleMagFreqDist;
import org.opensha.sha.magdist.YC_1985_CharMagFreqDist;
import org.opensha.sha.param.MagFreqDistParameter;
import org.opensha.sha.param.SimpleFaultParameter;
import org.opensha.sha.param.editor.MagFreqDistParameterEditor;
import org.opensha.sha.param.editor.gui.SimpleFaultParameterEditorPanel;


/**
 *
 * <p>Title: PEER_TestCaseSelectorControlPanel</p>
 * <p>Description: This class creates the a window that contains the
 * list of different PEER tests cases so that a user can make a selection.
 * This class also sets the default parameters for the selected test
 * in the HazardCurveApplet. </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author : Nitin Gupta, Vipin Gupta, and Ned Field
 * @created : Feb 24,2003
 * @version 1.0
 */
public class PEER_TestCaseSelectorControlPanel extends ControlPanel {

	public static final String NAME = "PEER Test Case Selector";
	protected final static String C = "PEER_TestCaseSelectorControlPanel";
	protected final static boolean D = false;


	//Supported PEER Test Cases
	public final static String PEER_TESTS_SET_ONE = "Set1";
	public final static String PEER_TESTS_SET_TWO = "Set2";

	//Test Cases and the Site Lists
	public final static String TEST_CASE_ONE ="Case1";
	public final static String TEST_CASE_TWO ="Case2";
	public final static String TEST_CASE_THREE ="Case3";
	public final static String TEST_CASE_FOUR ="Case4";
	public final static String TEST_CASE_FIVE ="Case5";
	public final static String TEST_CASE_SIX ="Case6";
	public final static String TEST_CASE_SEVEN ="Case7";
	public final static String TEST_CASE_EIGHT_A ="Case8a";
	public final static String TEST_CASE_EIGHT_B ="Case8b";
	public final static String TEST_CASE_EIGHT_C ="Case8c";
	public final static String TEST_CASE_NINE_A ="Case9a";
	public final static String TEST_CASE_NINE_B ="Case9b";
	public final static String TEST_CASE_NINE_C ="Case9c";
	public final static String TEST_CASE_TEN ="Case10";
	public final static String TEST_CASE_ELEVEN ="Case11";
	public final static String TEST_CASE_TWELVE ="Case12";


	//Sites Supported
	public final static String SITE_ONE = "Site1";
	public final static String SITE_TWO = "Site2";
	public final static String SITE_THREE = "Site3";
	public final static String SITE_FOUR = "Site4";
	public final static String SITE_FIVE = "Site5";
	public final static String SITE_SIX = "Site6";
	public final static String SITE_SEVEN = "Site7";

	/* maximum permitted distance between fault and site to consider source in
  hazard analysis for that site; this default value is to allow all PEER test
  cases to pass through
	 */
	private double MAX_DISTANCE = 300;

	// some of the universal parameter settings
	private double GRID_SPACING = 1.0;
	private String FAULT_TYPE = SimpleFaultParameter.STIRLING;

	// various gui beans
	private IMT_NewGuiBean imtGuiBean;
	private IMR_MultiGuiBean imrGuiBean;
	private Site_GuiBean siteGuiBean;
	private ERF_GuiBean erfGuiBean;
	private TimeSpanGuiBean timeSpanGuiBean;
	CalculationSettingsControlPanelAPI application;

	//Stores the test case,
	private String selectedTest;
	private String selectedSite;
	private String selectedSet;
	private JLabel jLabel2 = new JLabel();
	private JComboBox testCaseComboBox = new JComboBox();
	private GridBagLayout gridBagLayout1 = new GridBagLayout();

	//ArrayList to store the peer test cases names
	private ArrayList<String> peerTestSetOne = new ArrayList<String>();
	private ArrayList<String> peerTestSetTwo = new ArrayList<String>();

	//These hold the lats, lons, dips, and depths of the faults used in the FloatingPoissonFaultERF
	private ArrayList fault1and2_Lats, fault1and2_Lons, fault1_Dips, fault2_Dips, fault1_Depths, fault2_Depths;
	private ArrayList faultE_Lats, faultE_Lons, faultE_Dips, faultE_Depths;

	//Instance of the application implementing the PEER_TestCaseSelectorControlPanelAPI
	HazardCurveServerModeApplication api;

	//Stores the X Values for generating the hazard curve using the PEER values.
	ArbitrarilyDiscretizedFunc function = new ArbitrarilyDiscretizedFunc();

	private JFrame frame;
	private Component parent;

	/**
	 * Class Constructor
	 * @param parent : Give the dimensions of the parent class calling it.
	 * @param api : Instance of the application implementing the PEER_TestCaseSelectorControlPanelAPI
	 * @param imrGuiBean
	 * @param siteGuiBean
	 * @param imtGuiBean
	 * @param erfGuiBean
	 * @param timeSpanGuiBean
	 * @param distanceControlPanel
	 */
	public PEER_TestCaseSelectorControlPanel(Component parent, HazardCurveServerModeApplication api,
			IMR_MultiGuiBean imrGuiBean,
			Site_GuiBean siteGuiBean,
			IMT_NewGuiBean imtGuiBean,
			ERF_GuiBean erfGuiBean,
			TimeSpanGuiBean timeSpanGuiBean,
			CalculationSettingsControlPanelAPI application){
		super(NAME);
		
		this.parent = parent;
		this.api = api;
		

		//save the instances of the beans
		this.imrGuiBean = imrGuiBean;
		this.siteGuiBean = siteGuiBean;
		this.imtGuiBean = imtGuiBean;
		this.erfGuiBean = erfGuiBean;
		this.timeSpanGuiBean = timeSpanGuiBean;
		this.application = application;

		
	}
	
	public void doinit() {
		frame = new JFrame();
		if (D) System.out.println(C+" Constructor: starting initializeFaultData()");
		initializeFaultData();

		try {
			jbInit();
		}
		catch(Exception e) {
			e.printStackTrace();
		}
		if (D) System.out.println(C+" Constructor: starting initializeTestsAndSites()");
		// fill the combo box with tests and sites
		initializeTestsAndSites();

		// show the window at center of the parent component
		frame.setLocation(parent.getX()+parent.getWidth()/2,
				parent.getY()+parent.getHeight()/2);

		//function to create the PEER supported X Values
		createPEER_Function();
		//sets the PEER supported X values in the application
		this.setPEER_XValues();
	}

	private void jbInit() throws Exception {
		frame.getContentPane().setLayout(gridBagLayout1);
		jLabel2.setForeground(Color.black);
		jLabel2.setText("Select Test and Site:");
		testCaseComboBox.addActionListener(new java.awt.event.ActionListener() {
			public void actionPerformed(ActionEvent e) {
				testCaseComboBox_actionPerformed(e);
			}
		});
		frame.setTitle("PEER Test Case Selector");
		frame.getContentPane().add(jLabel2,  new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
				,GridBagConstraints.WEST, GridBagConstraints.NONE, new Insets(15, 7, 2, 240), 22, 5));
		frame.getContentPane().add(testCaseComboBox,  new GridBagConstraints(0, 0, 1, 1, 1.0, 0.0
				,GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL, new Insets(7, 145, 2, 13), 92, -1));
	}


	/**
	 * initialises the function with the x and y values if the user wants to work with PEER test cases
	 * So PEER supported  X Vals are used.
	 */
	private void createPEER_Function(){
		function.set(.001,1);
		function.set(.01,1);
		function.set(.05,1);
		function.set(.1,1);
		function.set(.15,1);
		function.set(.2,1);
		function.set(.25,1);
		function.set(.3,1);
		function.set(.35,1);
		function.set(.4,1);
		function.set(.45,1);
		function.set(.5,1);
		function.set(.55,1);
		function.set(.6,1);
		function.set(.7,1);
		//function.set(.75,1);
		function.set(.8,1);
		function.set(.9,1);
		function.set(1.0,1);
		//    function.set(1.1,1);
		//    function.set(1.2,1);
		//function.set(1.25,1);
		//    function.set(1.3,1);
		//    function.set(1.4,1);
		//    function.set(1.5,1);
	}

	/**
	 * This method sets the X values for the hazard Curve to the PEER supported X Values.
	 */
	public void setPEER_XValues(){
		//sets X Value to the PEER supported x vlaues for the hazard curve
		api.setCurveXValues(function);
	}


	/**
	 * This method extracts the selected Site and the selected TestCase set
	 * @param testAndSite: Contains both the site and the Selected Test Cases Set
	 */
	public void setTestCaseAndSite(String testAndSite){

		int firstIndex=testAndSite.indexOf("-");
		int lastIndex = testAndSite.lastIndexOf("-");
		selectedSet = testAndSite.substring(0,firstIndex);
		selectedTest = testAndSite.substring(firstIndex+1,lastIndex);
		selectedSite = testAndSite.substring(lastIndex+1);
		setParams();


	}

	/**
	 * This function sets the site Paramters and the IMR parameters based on the
	 * selected test case and selected site number for that test case
	 */

	public void setParams() {
		String S = C + ":setParams()";
		if(D) System.out.println(S+"::entering");

		//Gets the siteParamList
		ParameterList siteParams = siteGuiBean.getParameterListEditor().getParameterList();

		// set the distance in control panel
		application.getCalcAdjustableParams().getParameter(HazardCurveCalculator.MAX_DISTANCE_PARAM_NAME).setValue(MAX_DISTANCE);
		application.getCalcAdjustableParams().getParameter(HazardCurveCalculator.INCLUDE_MAG_DIST_FILTER_PARAM_NAME).setValue(false);

		//if set-1 PEER test case is selected
		if(selectedSet.equalsIgnoreCase(PEER_TESTS_SET_ONE))
			set_Set1Params(siteParams);

		//if set-2 PEER test case is selected
		else if(selectedSet.equalsIgnoreCase(PEER_TESTS_SET_TWO))
			set_Set2Params(siteParams);

		// refresh the editor according to parameter values
		imrGuiBean.rebuildGUI();
		imtGuiBean.refreshParamEditor();
		siteGuiBean.getParameterListEditor().refreshParamEditor();
		erfGuiBean.getERFParameterListEditor().refreshParamEditor();
		timeSpanGuiBean.getParameterListEditor().refreshParamEditor();
	}

	/**
	 * sets the parameter values for the selected test cases in Set-1
	 * @param siteParams
	 */
	private void set_Set1Params(ParameterList siteParams){


		// ******* Set the IMR, IMT, & Site-Related Parameters (except lat and lon) first ************

		/*   the following settings apply to most test cases; these are subsequently
        overridded where needed below */
		imrGuiBean.setSelectedSingleIMR(SadighEtAl_1997_AttenRel.NAME);
		ScalarIntensityMeasureRelationshipAPI imr = imrGuiBean.getSelectedIMR();
		imr.getParameter(SigmaTruncTypeParam.NAME).setValue(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_NONE);
		imr.getParameter(StdDevTypeParam.NAME).setValue(StdDevTypeParam.STD_DEV_TYPE_NONE);
		imtGuiBean.getParameterList().getParameter(IMT_GuiBean.IMT_PARAM_NAME).setValue(PGA_Param.NAME);
		siteParams.getParameter(SadighEtAl_1997_AttenRel.SITE_TYPE_NAME).setValue(SadighEtAl_1997_AttenRel.SITE_TYPE_ROCK);

		//if the selected test case is number 8_1
		if(selectedTest.equals(TEST_CASE_EIGHT_A)){
			imr.getParameter(SigmaTruncTypeParam.NAME).setValue(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_NONE);
			imr.getParameter(StdDevTypeParam.NAME).setValue(StdDevTypeParam.STD_DEV_TYPE_TOTAL);
			imtGuiBean.getParameterList().getParameter(IMT_GuiBean.IMT_PARAM_NAME).setValue(PGA_Param.NAME);  // needed because IMT gets reset to SA afer the above
		}

		//if the selected test case is number 8_2
		if(selectedTest.equals(TEST_CASE_EIGHT_B)){
			imr.getParameter(SigmaTruncTypeParam.NAME).setValue(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_1SIDED);
			imr.getParameter(SigmaTruncLevelParam.NAME).setValue(new Double(2.0));
			imr.getParameter(StdDevTypeParam.NAME).setValue(StdDevTypeParam.STD_DEV_TYPE_TOTAL);
			imtGuiBean.getParameterList().getParameter(IMT_GuiBean.IMT_PARAM_NAME).setValue(PGA_Param.NAME);  // needed because IMT gets reset to SA afer the above
		}

		//if the selected test case is number 8_3
		if(selectedTest.equals(TEST_CASE_EIGHT_C)){
			imr.getParameter(SigmaTruncTypeParam.NAME).setValue(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_1SIDED);
			imr.getParameter(SigmaTruncLevelParam.NAME).setValue(new Double(3.0));
			imr.getParameter(StdDevTypeParam.NAME).setValue(StdDevTypeParam.STD_DEV_TYPE_TOTAL);
			imtGuiBean.getParameterList().getParameter(IMT_GuiBean.IMT_PARAM_NAME).setValue(PGA_Param.NAME);  // needed because IMT gets reset to SA afer the above
		}

		//if the selected test case is number 9_1
		if(selectedTest.equals(TEST_CASE_NINE_A)){
			imr.getParameter(IMR_GuiBean.IMR_PARAM_NAME).setValue(SadighEtAl_1997_AttenRel.NAME);
			imr.getParameter(SigmaTruncTypeParam.NAME).setValue(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_1SIDED);
			imr.getParameter(SigmaTruncLevelParam.NAME).setValue(new Double(3.0));
			imr.getParameter(StdDevTypeParam.NAME).setValue(StdDevTypeParam.STD_DEV_TYPE_TOTAL);
			imtGuiBean.getParameterList().getParameter(IMT_GuiBean.IMT_PARAM_NAME).setValue(PGA_Param.NAME);
			siteParams.getParameter(SadighEtAl_1997_AttenRel.SITE_TYPE_NAME).setValue(SadighEtAl_1997_AttenRel.SITE_TYPE_ROCK);
		}

		//if the selected test case is number 9_2
		if(selectedTest.equals(TEST_CASE_NINE_B)){
			imr.getParameter(IMR_GuiBean.IMR_PARAM_NAME).setValue(AS_1997_AttenRel.NAME);
			imr.getParameter(SigmaTruncTypeParam.NAME).setValue(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_NONE);
			imr.getParameter(SigmaTruncLevelParam.NAME).setValue(new Double(3.0)); // this shouldn't matter
			imr.getParameter(StdDevTypeParam.NAME).setValue(StdDevTypeParam.STD_DEV_TYPE_NONE);
			imtGuiBean.getParameterList().getParameter(IMT_GuiBean.IMT_PARAM_NAME).setValue(PGA_Param.NAME);
			siteParams.getParameter(AS_1997_AttenRel.SITE_TYPE_NAME).setValue(AS_1997_AttenRel.SITE_TYPE_ROCK);
		}

		//if the selected test case is number 9_3
		if(selectedTest.equals(TEST_CASE_NINE_C)){
			imr.getParameter(IMR_GuiBean.IMR_PARAM_NAME).setValue(Campbell_1997_AttenRel.NAME);
			imr.getParameter(SigmaTruncTypeParam.NAME).setValue(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_1SIDED);
			imr.getParameter(SigmaTruncLevelParam.NAME).setValue(new Double(3.0));
			imr.getParameter(StdDevTypeParam.NAME).setValue(StdDevTypeParam.STD_DEV_TYPE_TOTAL_PGA_DEP);
			imtGuiBean.getParameterList().getParameter(IMT_GuiBean.IMT_PARAM_NAME).setValue(PGA_Param.NAME);
			siteGuiBean.getParameterListEditor().getParameterList().getParameter(Campbell_1997_AttenRel.SITE_TYPE_NAME).setValue(Campbell_1997_AttenRel.SITE_TYPE_SOFT_ROCK);
			siteParams.getParameter(Campbell_1997_AttenRel.BASIN_DEPTH_NAME).setValue(new Double(2.0));
		}

		//if the selected test case is number 12
		if(selectedTest.equals(TEST_CASE_TWELVE)){
			imr.getParameter(SigmaTruncTypeParam.NAME).setValue(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_1SIDED);
			imr.getParameter(SigmaTruncLevelParam.NAME).setValue(new Double(3.0));
			imr.getParameter(StdDevTypeParam.NAME).setValue(StdDevTypeParam.STD_DEV_TYPE_TOTAL);
			imtGuiBean.getParameterList().getParameter(IMT_GuiBean.IMT_PARAM_NAME).setValue(PGA_Param.NAME);  // needed because IMT gets reset to SA afer the above
		}


		// *********** Now fill in the ERF parameters ************************

		// if it's one of the "PEER fault" problems (cases 1-9 or 12)
		if(!selectedTest.equalsIgnoreCase(TEST_CASE_TEN) && !selectedTest.equalsIgnoreCase(TEST_CASE_ELEVEN)) {

			// set the ERF
			erfGuiBean.getERFParameterList().getParameter(ERF_GuiBean.ERF_PARAM_NAME).setValue(FloatingPoissonFaultERF.NAME);

			// set offset and fault grid spacing (these were determined by trial and error)
			double gridSpacing;
			if(selectedTest.equals(TEST_CASE_ONE) || selectedTest.equals(TEST_CASE_TWO) || selectedTest.equals(TEST_CASE_FOUR) || selectedTest.equals(TEST_CASE_NINE_B) ) {
				gridSpacing = 0.05;
			}
			else if(selectedTest.equals(TEST_CASE_THREE)) {
				gridSpacing = 0.25;
			}
			else {
				gridSpacing = 0.5;
			}

			// set the special cases (improvements found by hand using GUI)
			if(selectedTest.equals(TEST_CASE_EIGHT_C) && selectedSite.equals(SITE_FIVE))
				gridSpacing = 0.05;
			if(selectedTest.equals(TEST_CASE_NINE_C) && selectedSite.equals(SITE_SEVEN))
				gridSpacing = 0.1;
			if(selectedTest.equals(TEST_CASE_TWO) && (selectedSite.equals(SITE_ONE) || selectedSite.equals(SITE_FOUR) || selectedSite.equals(SITE_SIX)))
				gridSpacing = 0.025;


			// set the common parameters like timespan
			erfGuiBean.getERFParameterList().getParameter(FloatingPoissonFaultERF.OFFSET_PARAM_NAME).setValue(new Double(gridSpacing));
			erfGuiBean.getERFParameterList().getParameter(FloatingPoissonFaultERF.MAG_SCALING_REL_PARAM_NAME).setValue(PEER_testsMagAreaRelationship.NAME);
			erfGuiBean.getERFParameterList().getParameter(FloatingPoissonFaultERF.SIGMA_PARAM_NAME).setValue(new Double(0));
			erfGuiBean.getERFParameterList().getParameter(FloatingPoissonFaultERF.ASPECT_RATIO_PARAM_NAME).setValue(new Double(2.0));
			erfGuiBean.getERFParameterList().getParameter(FloatingPoissonFaultERF.MIN_MAG_PARAM_NAME).setValue(new Double(5.0));
			timeSpanGuiBean.getParameterList().getParameter(TimeSpan.DURATION).setValue(new Double(1.0));

			// magScalingSigma parameter is changed if the test case chosen is 3
			if(selectedTest.equals(TEST_CASE_THREE))
				erfGuiBean.getERFParameterList().getParameter(FloatingPoissonFaultERF.SIGMA_PARAM_NAME).setValue(new Double(0.25));

			// set the rake for all cases
			if( selectedTest.equals(TEST_CASE_FOUR) ||
					selectedTest.equals(TEST_CASE_NINE_A) ||
					selectedTest.equals(TEST_CASE_NINE_B) ||
					selectedTest.equals(TEST_CASE_NINE_C) ) {
				erfGuiBean.getERFParameterList().getParameter(FloatingPoissonFaultERF.RAKE_PARAM_NAME).setValue(new Double(90.0));
			}
			else {
				erfGuiBean.getERFParameterList().getParameter(FloatingPoissonFaultERF.RAKE_PARAM_NAME).setValue(new Double(0.0));
			}

			// set the Fault Parameter
			SimpleFaultParameterEditorPanel faultPanel = erfGuiBean.getSimpleFaultParamEditor().getParameterEditorPanel();
			if( selectedTest.equals(TEST_CASE_FOUR) ||
					selectedTest.equals(TEST_CASE_NINE_A) ||
					selectedTest.equals(TEST_CASE_NINE_B) ||
					selectedTest.equals(TEST_CASE_NINE_C) ) {
				faultPanel.setAll(gridSpacing,fault1and2_Lats,fault1and2_Lons,fault2_Dips,fault2_Depths,FAULT_TYPE);
			}
			else {

				faultPanel.setAll(gridSpacing,fault1and2_Lats,fault1and2_Lons,fault1_Dips,fault1_Depths,FAULT_TYPE);
			}
			faultPanel.setEvenlyGriddedSurfaceFromParams();

		}

		// it's an area ERF (case 10 or 11)
		else {
			erfGuiBean.getERFParameterList().getParameter(ERF_GuiBean.ERF_PARAM_NAME).setValue(PEER_AreaForecast.NAME);

			erfGuiBean.getERFParameterList().getParameter(PEER_AreaForecast.DEPTH_UPPER_PARAM_NAME).setValue(new Double(5));
			erfGuiBean.getERFParameterList().getParameter(PEER_AreaForecast.DIP_PARAM_NAME).setValue(new Double(90));
			erfGuiBean.getERFParameterList().getParameter(PEER_AreaForecast.RAKE_PARAM_NAME).setValue(new Double(0));
			timeSpanGuiBean.getParameterList().getParameter(TimeSpan.DURATION).setValue(new Double(1.0));
			if(selectedTest.equals(TEST_CASE_TEN)) {
				erfGuiBean.getERFParameterList().getParameter(PEER_AreaForecast.DEPTH_LOWER_PARAM_NAME).setValue(new Double(5));
				erfGuiBean.getERFParameterList().getParameter(PEER_AreaForecast.GRID_PARAM_NAME).setValue(new Double(1.0));
			}
			else {
				erfGuiBean.getERFParameterList().getParameter(PEER_AreaForecast.DEPTH_LOWER_PARAM_NAME).setValue(new Double(10));
				erfGuiBean.getERFParameterList().getParameter(PEER_AreaForecast.GRID_PARAM_NAME).setValue(new Double(0.25));   	 
			}
		}

		// set magFreqDist parameters using seperate method
		MagFreqDistParameterEditor magDistEditor = erfGuiBean.getMagDistEditor();
		setMagDistParams_Set1(magDistEditor);


		// *********** set the Site latitude and longitude  **************************

		if(!selectedTest.equalsIgnoreCase(TEST_CASE_TEN) && !selectedTest.equalsIgnoreCase(TEST_CASE_ELEVEN)) {

			// for fault site 1
			if(selectedSite.equals(SITE_ONE)) {
				siteGuiBean.getParameterListEditor().getParameterList().getParameter(Site_GuiBean.LATITUDE).setValue(new Double(38.113));
				siteParams.getParameter(Site_GuiBean.LONGITUDE).setValue(new Double(-122.0));
			}
			// for fault site 2
			if(selectedSite.equals(SITE_TWO)) {
				siteParams.getParameter(Site_GuiBean.LATITUDE).setValue(new Double(38.113));
				siteParams.getParameter(Site_GuiBean.LONGITUDE).setValue(new Double(-122.114));

			}
			// for fault site 3
			if(selectedSite.equals(SITE_THREE)) {
				siteParams.getParameter(Site_GuiBean.LATITUDE).setValue(new Double(38.111));
				siteParams.getParameter(Site_GuiBean.LONGITUDE).setValue(new Double(-122.570));

			}
			// for fault site 4
			if(selectedSite.equals(SITE_FOUR)) {
				siteParams.getParameter(Site_GuiBean.LATITUDE).setValue(new Double(38.000));
				siteParams.getParameter(Site_GuiBean.LONGITUDE).setValue(new Double(-122.0));

			}
			// for fault site 5
			if(selectedSite.equals(SITE_FIVE)) {
				siteParams.getParameter(Site_GuiBean.LATITUDE).setValue(new Double(37.910));
				siteParams.getParameter(Site_GuiBean.LONGITUDE).setValue(new Double(-122.0));

			}
			// for fault site 6
			if(selectedSite.equals(SITE_SIX)) {
				siteParams.getParameter(Site_GuiBean.LATITUDE).setValue(new Double(38.225));
				siteParams.getParameter(Site_GuiBean.LONGITUDE).setValue(new Double(-122.0));

			}
			// for fault site 7
			if(selectedSite.equals(SITE_SEVEN)) {
				siteParams.getParameter(Site_GuiBean.LATITUDE).setValue(new Double(38.113));
				siteParams.getParameter(Site_GuiBean.LONGITUDE).setValue(new Double(-121.886));
			}
		} else { // for area sites

			siteParams.getParameter(Site_GuiBean.LONGITUDE).setValue(new Double(-122.0));
			// for area site 1
			if(selectedSite.equals(SITE_ONE))
				siteParams.getParameter(Site_GuiBean.LATITUDE).setValue(new Double(38.0));

			// for area site 2
			if(selectedSite.equals(SITE_TWO))
				siteParams.getParameter(Site_GuiBean.LATITUDE).setValue(new Double(37.550));

			// for area site 3
			if(selectedSite.equals(SITE_THREE))
				siteParams.getParameter(Site_GuiBean.LATITUDE).setValue(new Double(37.099));

			// for area site 4
			if(selectedSite.equals(SITE_FOUR))
				siteParams.getParameter(Site_GuiBean.LATITUDE).setValue(new Double(36.875));
		}
	}



	/**
	 * sets the parameter values for the selected test cases in Set-2
	 * @param siteParams
	 */
	private void set_Set2Params(ParameterList siteParams){


		// ******* Set the IMR, IMT, & Site-Related Parameters (except lat and lon) first ************
		imrGuiBean.setSelectedSingleIMR(SadighEtAl_1997_AttenRel.NAME);
		ScalarIntensityMeasureRelationshipAPI imr = imrGuiBean.getSelectedIMR();
		imr.getParameter(SigmaTruncTypeParam.NAME).setValue(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_NONE);
		imr.getParameter(StdDevTypeParam.NAME).setValue(StdDevTypeParam.STD_DEV_TYPE_NONE);
		imtGuiBean.getParameterList().getParameter(IMT_GuiBean.IMT_PARAM_NAME).setValue(PGA_Param.NAME);
		siteParams.getParameter(SadighEtAl_1997_AttenRel.SITE_TYPE_NAME).setValue(SadighEtAl_1997_AttenRel.SITE_TYPE_ROCK);


		// change IMR sigma if it's Case 2
		if(selectedTest.equalsIgnoreCase(TEST_CASE_TWO) || selectedTest.equalsIgnoreCase(TEST_CASE_FIVE)){
			imr.getParameter(SigmaTruncTypeParam.NAME).setValue(SigmaTruncTypeParam.SIGMA_TRUNC_TYPE_1SIDED);
			imr.getParameter(SigmaTruncLevelParam.NAME).setValue(new Double(3.0));
			imr.getParameter(StdDevTypeParam.NAME).setValue(StdDevTypeParam.STD_DEV_TYPE_TOTAL);

		}


		// ********* set the site latitude and longitude ************
		if(selectedTest.equals(TEST_CASE_ONE) || selectedTest.equals(TEST_CASE_FIVE)){
			if(selectedSite.equals(SITE_ONE) || selectedSite.equals(SITE_FOUR)){
				siteParams.getParameter(Site_GuiBean.LATITUDE).setValue(new Double(38.1126));
				siteParams.getParameter(Site_GuiBean.LONGITUDE).setValue(new Double(-121.8860));
			}
			else if(selectedSite.equalsIgnoreCase(SITE_TWO) || selectedSite.equals(SITE_FIVE)){
				siteParams.getParameter(Site_GuiBean.LATITUDE).setValue(new Double(38.1800));
				siteParams.getParameter(Site_GuiBean.LONGITUDE).setValue(new Double(-121.8860));
			}
			else if(selectedSite.equalsIgnoreCase(SITE_THREE) || selectedSite.equals(SITE_SIX)){
				siteParams.getParameter(Site_GuiBean.LATITUDE).setValue(new Double(38.2696));
				siteParams.getParameter(Site_GuiBean.LONGITUDE).setValue(new Double(-122.1140));
			}
		}
		else if(selectedTest.equalsIgnoreCase(TEST_CASE_TWO)){
			siteParams.getParameter(Site_GuiBean.LONGITUDE).setValue(new Double(-122));
			if(selectedSite.equalsIgnoreCase(SITE_ONE)){
				siteParams.getParameter(Site_GuiBean.LATITUDE).setValue(new Double(37.5495));
			}
			else if(selectedSite.equalsIgnoreCase(SITE_TWO)){
				siteParams.getParameter(Site_GuiBean.LATITUDE).setValue(new Double(37.0990));
			}
			else if(selectedSite.equalsIgnoreCase(SITE_THREE)){
				siteParams.getParameter(Site_GuiBean.LATITUDE).setValue(new Double(36.8737));
			}
		}
		else { // all others have the same set of sites
			if(selectedSite.equalsIgnoreCase(SITE_ONE)){
				siteParams.getParameter(Site_GuiBean.LONGITUDE).setValue(new Double(-121.886));
				siteParams.getParameter(Site_GuiBean.LATITUDE).setValue(new Double(38.1126));
			}
			else if(selectedSite.equalsIgnoreCase(SITE_TWO)){
				siteParams.getParameter(Site_GuiBean.LONGITUDE).setValue(new Double(-122.0));
				siteParams.getParameter(Site_GuiBean.LATITUDE).setValue(new Double(38.2252));
			}
			else if(selectedSite.equalsIgnoreCase(SITE_THREE)){
				siteParams.getParameter(Site_GuiBean.LONGITUDE).setValue(new Double(-122.0));
				siteParams.getParameter(Site_GuiBean.LATITUDE).setValue(new Double(38.0));
			}
		}

		// ************ Set the ERF parameters ********************

		//if test case -1
		if(selectedTest.equalsIgnoreCase(TEST_CASE_ONE)){
			erfGuiBean.getERFParameterList().getParameter(ERF_GuiBean.ERF_PARAM_NAME).setValue(PEER_NonPlanarFaultForecast.NAME);
			// add sigma for maglength(0-1)
			erfGuiBean.getERFParameterList().getParameter(PEER_NonPlanarFaultForecast.SIGMA_PARAM_NAME).setValue(new Double(0));
			timeSpanGuiBean.getParameterList().getParameter(TimeSpan.DURATION).setValue(new Double(1.0));
			erfGuiBean.getERFParameterList().getParameter(PEER_NonPlanarFaultForecast.GRID_PARAM_NAME).setValue(new Double(1.0));
			erfGuiBean.getERFParameterList().getParameter(PEER_NonPlanarFaultForecast.OFFSET_PARAM_NAME).setValue(new Double(1.0));
			erfGuiBean.getERFParameterList().getParameter(PEER_NonPlanarFaultForecast.GR_MAG_UPPER).setValue(new Double(6.95));
			erfGuiBean.getERFParameterList().getParameter(PEER_NonPlanarFaultForecast.SLIP_RATE_NAME).setValue(new Double(2.0));
			erfGuiBean.getERFParameterList().getParameter(PEER_NonPlanarFaultForecast.SEGMENTATION_NAME).setValue(PEER_NonPlanarFaultForecast.SEGMENTATION_NO);
			erfGuiBean.getERFParameterList().getParameter(PEER_NonPlanarFaultForecast.FAULT_MODEL_NAME).setValue(PEER_NonPlanarFaultForecast.FAULT_MODEL_STIRLING);
			// set the dip direction depending on the chosen
			if(selectedSite.equals(SITE_ONE) || selectedSite.equals(SITE_TWO) || selectedSite.equals(SITE_THREE))
				erfGuiBean.getERFParameterList().getParameter(PEER_NonPlanarFaultForecast.DIP_DIRECTION_NAME).setValue(PEER_NonPlanarFaultForecast.DIP_DIRECTION_EAST);
			else
				erfGuiBean.getERFParameterList().getParameter(PEER_NonPlanarFaultForecast.DIP_DIRECTION_NAME).setValue(PEER_NonPlanarFaultForecast.DIP_DIRECTION_WEST);
		}

		//if test case -2
		if(selectedTest.equalsIgnoreCase(TEST_CASE_TWO)){
			erfGuiBean.getERFParameterList().getParameter(ERF_GuiBean.ERF_PARAM_NAME).setValue(PEER_MultiSourceForecast.NAME);

			erfGuiBean.getERFParameterList().getParameter(PEER_MultiSourceForecast.DEPTH_LOWER_PARAM_NAME).setValue(new Double(10));
			erfGuiBean.getERFParameterList().getParameter(PEER_MultiSourceForecast.DEPTH_UPPER_PARAM_NAME).setValue(new Double(5));
			erfGuiBean.getERFParameterList().getParameter(PEER_MultiSourceForecast.GRID_PARAM_NAME).setValue(new Double(1.0));
			erfGuiBean.getERFParameterList().getParameter(PEER_MultiSourceForecast.OFFSET_PARAM_NAME).setValue(new Double(1.0));
			timeSpanGuiBean.getParameterList().getParameter(TimeSpan.DURATION).setValue(new Double(1.0));
		}

		//if test case 3 or 4
		if(selectedTest.equalsIgnoreCase(TEST_CASE_THREE) || selectedTest.equalsIgnoreCase(TEST_CASE_FOUR) ) {

			// set the ERF
			erfGuiBean.getERFParameterList().getParameter(ERF_GuiBean.ERF_PARAM_NAME).setValue(FloatingPoissonFaultERF.NAME);

			erfGuiBean.getERFParameterList().getParameter(FloatingPoissonFaultERF.OFFSET_PARAM_NAME).setValue(new Double(1.0));
			erfGuiBean.getERFParameterList().getParameter(FloatingPoissonFaultERF.MAG_SCALING_REL_PARAM_NAME).setValue(PEER_testsMagAreaRelationship.NAME);
			erfGuiBean.getERFParameterList().getParameter(FloatingPoissonFaultERF.SIGMA_PARAM_NAME).setValue(new Double(0));
			erfGuiBean.getERFParameterList().getParameter(FloatingPoissonFaultERF.ASPECT_RATIO_PARAM_NAME).setValue(new Double(2.0));
			erfGuiBean.getERFParameterList().getParameter(FloatingPoissonFaultERF.MIN_MAG_PARAM_NAME).setValue(new Double(5.0));
			timeSpanGuiBean.getParameterList().getParameter(TimeSpan.DURATION).setValue(new Double(1.0));
			erfGuiBean.getERFParameterList().getParameter(FloatingPoissonFaultERF.RAKE_PARAM_NAME).setValue(new Double(0.0));

			// set the Fault Parameter
			SimpleFaultParameterEditorPanel faultPanel = erfGuiBean.getSimpleFaultParamEditor().getParameterEditorPanel();
			faultPanel.setAll(GRID_SPACING,fault1and2_Lats,fault1and2_Lons,fault1_Dips,fault1_Depths,FAULT_TYPE);
			faultPanel.setEvenlyGriddedSurfaceFromParams();

		}

		//if test case 5
		if(selectedTest.equalsIgnoreCase(TEST_CASE_FIVE) ) {
			erfGuiBean.getERFParameterList().getParameter(ERF_GuiBean.ERF_PARAM_NAME).setValue(PEER_LogicTreeERF_List.NAME);
			erfGuiBean.getERFParameterList().getParameter(PEER_LogicTreeERF_List.FAULT_MODEL_NAME).setValue(PEER_LogicTreeERF_List.FAULT_MODEL_STIRLING);
			erfGuiBean.getERFParameterList().getParameter(PEER_LogicTreeERF_List.OFFSET_PARAM_NAME).setValue(new Double(1));
			erfGuiBean.getERFParameterList().getParameter(PEER_LogicTreeERF_List.GRID_PARAM_NAME).setValue(new Double(1));
			erfGuiBean.getERFParameterList().getParameter(PEER_LogicTreeERF_List.SIGMA_PARAM_NAME).setValue(new Double(0.0));
			timeSpanGuiBean.getParameterList().getParameter(TimeSpan.DURATION).setValue(new Double(1.0));
		}

		//if test case -6
		if(selectedTest.equalsIgnoreCase(TEST_CASE_SIX)){
			// set the ERF
			erfGuiBean.getERFParameterList().getParameter(ERF_GuiBean.ERF_PARAM_NAME).setValue(FloatingPoissonFaultERF.NAME);

			erfGuiBean.getERFParameterList().getParameter(FloatingPoissonFaultERF.OFFSET_PARAM_NAME).setValue(new Double(1.0));
			erfGuiBean.getERFParameterList().getParameter(FloatingPoissonFaultERF.MAG_SCALING_REL_PARAM_NAME).setValue(PEER_testsMagAreaRelationship.NAME);
			erfGuiBean.getERFParameterList().getParameter(FloatingPoissonFaultERF.SIGMA_PARAM_NAME).setValue(new Double(0));
			erfGuiBean.getERFParameterList().getParameter(FloatingPoissonFaultERF.ASPECT_RATIO_PARAM_NAME).setValue(new Double(2.0));
			erfGuiBean.getERFParameterList().getParameter(FloatingPoissonFaultERF.MIN_MAG_PARAM_NAME).setValue(new Double(5.0));
			timeSpanGuiBean.getParameterList().getParameter(TimeSpan.DURATION).setValue(new Double(1.0));
			erfGuiBean.getERFParameterList().getParameter(FloatingPoissonFaultERF.RAKE_PARAM_NAME).setValue(new Double(0.0));

			// set the Fault Parameter
			SimpleFaultParameterEditorPanel faultPanel = erfGuiBean.getSimpleFaultParamEditor().getParameterEditorPanel();
			faultPanel.setAll(GRID_SPACING,faultE_Lats,faultE_Lons,faultE_Dips,faultE_Depths,FAULT_TYPE);
			faultPanel.setEvenlyGriddedSurfaceFromParams();

		}

		// now set the magFreqDist parameters (if there is one) using the separate method
		MagFreqDistParameterEditor magDistEditor =erfGuiBean.getMagDistEditor();
		if(magDistEditor !=null)  setMagDistParams_Set2(magDistEditor);

	}



	/**
	 * Sets the default magdist values for the set 2 (only cases 3, 4, and 6 have magFreqDist as
	 * an adjustable parameter
	 * @param magEditor
	 */
	private void setMagDistParams_Set2(MagFreqDistParameterEditor magEditor){

		// mag dist parameters for test case 3
		if(selectedTest.equalsIgnoreCase(TEST_CASE_THREE)){
			magEditor.getParameter(MagFreqDistParameter.DISTRIBUTION_NAME).setValue(YC_1985_CharMagFreqDist.NAME);
			magEditor.getParameter(MagFreqDistParameter.MIN).setValue(new Double(0.0));
			magEditor.getParameter(MagFreqDistParameter.MAX).setValue(new Double(10));
			magEditor.getParameter(MagFreqDistParameter.NUM).setValue(new Integer(1001));
			magEditor.getParameter(MagFreqDistParameter.GR_BVALUE).setValue(new Double(0.9));
			magEditor.getParameter(MagFreqDistParameter.YC_DELTA_MAG_CHAR).setValue(new Double(.5));
			magEditor.getParameter(MagFreqDistParameter.YC_DELTA_MAG_PRIME).setValue(new Double(1.0));
			magEditor.getParameter(MagFreqDistParameter.GR_MAG_LOWER).setValue(new Double(0.01));
			magEditor.getParameter(MagFreqDistParameter.YC_MAG_PRIME).setValue(new Double(5.95));
			magEditor.getParameter(MagFreqDistParameter.GR_MAG_UPPER).setValue(new Double(6.45));
			magEditor.getParameter(MagFreqDistParameter.SET_ALL_PARAMS_BUT).setValue(MagFreqDistParameter.TOT_MO_RATE);
			magEditor.getParameter(MagFreqDistParameter.YC_TOT_CHAR_RATE).setValue(new Double(1e-3));
		}
		// mag dist parameters for test case 4
		if(selectedTest.equalsIgnoreCase(TEST_CASE_FOUR)){
			magEditor.getParameter(MagFreqDistParameter.DISTRIBUTION_NAME).setValue(GaussianMagFreqDist.NAME);
			magEditor.getParameter(MagFreqDistParameter.MIN).setValue(new Double(0.05));
			magEditor.getParameter(MagFreqDistParameter.MAX).setValue(new Double(9.95));
			magEditor.getParameter(MagFreqDistParameter.NUM).setValue(new Integer(100));
			magEditor.getParameter(MagFreqDistParameter.SET_ALL_PARAMS_BUT).setValue(MagFreqDistParameter.TOT_MO_RATE);
			magEditor.getParameter(MagFreqDistParameter.TOT_CUM_RATE).setValue(new Double(1e-3));
			magEditor.getParameter(MagFreqDistParameter.STD_DEV).setValue(new Double(0.25));
			magEditor.getParameter(MagFreqDistParameter.MEAN).setValue(new Double(6.2));
			magEditor.getParameter(MagFreqDistParameter.TRUNCATION_REQ).setValue(MagFreqDistParameter.TRUNCATE_UPPER_ONLY);
			magEditor.getParameter(MagFreqDistParameter.TRUNCATE_NUM_OF_STD_DEV).setValue(new Double(1.0));
		}

		// mag dist parameters for test case 6
		if(selectedTest.equalsIgnoreCase(TEST_CASE_SIX)){
			magEditor.getParameter(MagFreqDistParameter.DISTRIBUTION_NAME).setValue(GutenbergRichterMagFreqDist.NAME);
			magEditor.getParameter(MagFreqDistParameter.SET_ALL_PARAMS_BUT).setValue(MagFreqDistParameter.TOT_CUM_RATE);
			magEditor.getParameter(MagFreqDistParameter.MIN).setValue(new Double(0.05));
			magEditor.getParameter(MagFreqDistParameter.MAX).setValue(new Double(9.95));
			magEditor.getParameter(MagFreqDistParameter.NUM).setValue(new Integer(100));
			magEditor.getParameter(MagFreqDistParameter.GR_MAG_LOWER).setValue(new Double(0.05));
			magEditor.getParameter(MagFreqDistParameter.GR_MAG_UPPER).setValue(new Double(6.45));
			magEditor.getParameter(MagFreqDistParameter.GR_BVALUE).setValue(new Double(0.9));
			magEditor.getParameter(MagFreqDistParameter.TOT_MO_RATE).setValue(new Double(3.8055e16));
		}

		// now have the editor create the magFreqDist
		magEditor.setMagDistFromParams();
	}


	/**
	 * Sets the default magdist values for the set-1
	 * @param magEditor
	 */
	private void setMagDistParams_Set1(MagFreqDistParameterEditor magEditor){

		// these apply to most (overridden below where not)
		magEditor.getParameter(MagFreqDistParameter.MIN).setValue(new Double(6));
		magEditor.getParameter(MagFreqDistParameter.MAX).setValue(new Double(6.5));
		magEditor.getParameter(MagFreqDistParameter.NUM).setValue(new Integer(6));

		// mag dist parameters for test case 1 & 12
		if(selectedTest.equalsIgnoreCase(TEST_CASE_ONE) || selectedTest.equalsIgnoreCase(TEST_CASE_TWELVE)) {
			magEditor.getParameter(MagFreqDistParameter.DISTRIBUTION_NAME).setValue(SingleMagFreqDist.NAME);
			magEditor.getParameter(MagFreqDistParameter.SINGLE_PARAMS_TO_SET).setValue(MagFreqDistParameter.MAG_AND_MO_RATE);
			magEditor.getParameter(MagFreqDistParameter.MAG).setValue(new Double(6.5));
			magEditor.getParameter(MagFreqDistParameter.MO_RATE).setValue(new Double(1.8e16));
		}

		// mag dist parameters  for test case 2
		else if(selectedTest.equalsIgnoreCase(TEST_CASE_TWO)) {

			magEditor.getParameter(MagFreqDistParameter.DISTRIBUTION_NAME).setValue(SingleMagFreqDist.NAME);
			magEditor.getParameter(MagFreqDistParameter.SINGLE_PARAMS_TO_SET).setValue(MagFreqDistParameter.MAG_AND_MO_RATE);
			magEditor.getParameter(MagFreqDistParameter.MAG).setValue(new Double(6.0));
			magEditor.getParameter(MagFreqDistParameter.MO_RATE).setValue(new Double(1.8e16));
		}

		// mag dist parameters  for test case 3
		else if(selectedTest.equalsIgnoreCase(TEST_CASE_THREE)) {

			magEditor.getParameter(MagFreqDistParameter.DISTRIBUTION_NAME).setValue(SingleMagFreqDist.NAME);
			magEditor.getParameter(MagFreqDistParameter.SINGLE_PARAMS_TO_SET).setValue(MagFreqDistParameter.MAG_AND_MO_RATE);
			magEditor.getParameter(MagFreqDistParameter.MAG).setValue(new Double(6.0));
			magEditor.getParameter(MagFreqDistParameter.MO_RATE).setValue(new Double(1.8e16));
		}

		// mag dist parameters for test case 4
		else if(selectedTest.equalsIgnoreCase(TEST_CASE_FOUR)) {

			magEditor.getParameter(MagFreqDistParameter.DISTRIBUTION_NAME).setValue(SingleMagFreqDist.NAME);
			magEditor.getParameter(MagFreqDistParameter.SINGLE_PARAMS_TO_SET).setValue(MagFreqDistParameter.MAG_AND_MO_RATE);
			magEditor.getParameter(MagFreqDistParameter.MAG).setValue(new Double(6.0));
			magEditor.getParameter(MagFreqDistParameter.MO_RATE).setValue(new Double(1.905e16));
		}

		// mag dist parameters for test case 5
		else if(selectedTest.equalsIgnoreCase(TEST_CASE_FIVE)) {
			magEditor.getParameter(MagFreqDistParameter.DISTRIBUTION_NAME).setValue(GutenbergRichterMagFreqDist.NAME);
			magEditor.getParameter(MagFreqDistParameter.MIN).setValue(new Double(0.005));
			magEditor.getParameter(MagFreqDistParameter.MAX).setValue(new Double(9.995));
			magEditor.getParameter(MagFreqDistParameter.NUM).setValue(new Integer(1000));
			magEditor.getParameter(MagFreqDistParameter.SET_ALL_PARAMS_BUT).setValue(MagFreqDistParameter.TOT_CUM_RATE);
			magEditor.getParameter(MagFreqDistParameter.GR_MAG_LOWER).setValue(new Double(0.005));
			magEditor.getParameter(MagFreqDistParameter.GR_MAG_UPPER).setValue(new Double(6.495));
			magEditor.getParameter(MagFreqDistParameter.GR_BVALUE).setValue(new Double(0.9));
			magEditor.getParameter(MagFreqDistParameter.TOT_MO_RATE).setValue(new Double(1.8e16));
			magEditor.getParameter(MagFreqDistParameter.SET_ALL_PARAMS_BUT).setValue(MagFreqDistParameter.TOT_CUM_RATE);
		}


		// mag dist parameters for test case 6
		else if(selectedTest.equalsIgnoreCase(TEST_CASE_SIX)) {
			magEditor.getParameter(MagFreqDistParameter.DISTRIBUTION_NAME).setValue(GaussianMagFreqDist.NAME);
			magEditor.getParameter(MagFreqDistParameter.MIN).setValue(new Double(0.005));
			magEditor.getParameter(MagFreqDistParameter.MAX).setValue(new Double(9.995));
			magEditor.getParameter(MagFreqDistParameter.NUM).setValue(new Integer(1000));
			magEditor.getParameter(MagFreqDistParameter.SET_ALL_PARAMS_BUT).setValue(MagFreqDistParameter.TOT_CUM_RATE);
			magEditor.getParameter(MagFreqDistParameter.TOT_MO_RATE).setValue(new Double(1.8e16));
			magEditor.getParameter(MagFreqDistParameter.STD_DEV).setValue(new Double(0.25));
			magEditor.getParameter(MagFreqDistParameter.MEAN).setValue(new Double(6.2));
			magEditor.getParameter(MagFreqDistParameter.TRUNCATION_REQ).setValue(MagFreqDistParameter.TRUNCATE_UPPER_ONLY);
			magEditor.getParameter(MagFreqDistParameter.TRUNCATE_NUM_OF_STD_DEV).setValue(new Double(1.19));
		}
		// mag dist parameters for test case 7
		else if(selectedTest.equalsIgnoreCase(TEST_CASE_SEVEN)) {
			magEditor.getParameter(MagFreqDistParameter.DISTRIBUTION_NAME).setValue(YC_1985_CharMagFreqDist.NAME);
			magEditor.getParameter(MagFreqDistParameter.MIN).setValue(new Double(0.005));
			magEditor.getParameter(MagFreqDistParameter.MAX).setValue(new Double(10.005));
			magEditor.getParameter(MagFreqDistParameter.NUM).setValue(new Integer(1001));
			magEditor.getParameter(MagFreqDistParameter.GR_BVALUE).setValue(new Double(0.9));
			magEditor.getParameter(MagFreqDistParameter.YC_DELTA_MAG_CHAR).setValue(new Double(0.49));
			magEditor.getParameter(MagFreqDistParameter.YC_DELTA_MAG_PRIME).setValue(new Double(1.0));
			magEditor.getParameter(MagFreqDistParameter.GR_MAG_LOWER).setValue(new Double(0.005));
			magEditor.getParameter(MagFreqDistParameter.YC_MAG_PRIME).setValue(new Double(5.945));
			magEditor.getParameter(MagFreqDistParameter.GR_MAG_UPPER).setValue(new Double(6.445));
			magEditor.getParameter(MagFreqDistParameter.TOT_MO_RATE).setValue(new Double(1.8e16));
		}

		//mag dist parameters for the test case 8_1
		else if(selectedTest.equalsIgnoreCase(TEST_CASE_EIGHT_A)) {

			magEditor.getParameter(MagFreqDistParameter.DISTRIBUTION_NAME).setValue(SingleMagFreqDist.NAME);
			magEditor.getParameter(MagFreqDistParameter.SINGLE_PARAMS_TO_SET).setValue(MagFreqDistParameter.MAG_AND_MO_RATE);
			magEditor.getParameter(MagFreqDistParameter.MAG).setValue(new Double(6.0));
			magEditor.getParameter(MagFreqDistParameter.MO_RATE).setValue(new Double(1.8e16));
		}

		//mag dist parameters for the test case 8_2
		else if(selectedTest.equalsIgnoreCase(TEST_CASE_EIGHT_B)) {

			magEditor.getParameter(MagFreqDistParameter.DISTRIBUTION_NAME).setValue(SingleMagFreqDist.NAME);
			magEditor.getParameter(MagFreqDistParameter.SINGLE_PARAMS_TO_SET).setValue(MagFreqDistParameter.MAG_AND_MO_RATE);
			magEditor.getParameter(MagFreqDistParameter.MAG).setValue(new Double(6.0));
			magEditor.getParameter(MagFreqDistParameter.MO_RATE).setValue(new Double(1.8e16));
		}

		//mag dist parameters for the test case 8_3
		else if(selectedTest.equalsIgnoreCase(TEST_CASE_EIGHT_C)) {

			magEditor.getParameter(MagFreqDistParameter.DISTRIBUTION_NAME).setValue(SingleMagFreqDist.NAME);
			magEditor.getParameter(MagFreqDistParameter.SINGLE_PARAMS_TO_SET).setValue(MagFreqDistParameter.MAG_AND_MO_RATE);
			magEditor.getParameter(MagFreqDistParameter.MAG).setValue(new Double(6.0));
			magEditor.getParameter(MagFreqDistParameter.MO_RATE).setValue(new Double(1.8e16));
		}

		//mag dist parameters for the test case 9_1
		else if(selectedTest.equalsIgnoreCase(TEST_CASE_NINE_A)) {

			magEditor.getParameter(MagFreqDistParameter.DISTRIBUTION_NAME).setValue(SingleMagFreqDist.NAME);
			magEditor.getParameter(MagFreqDistParameter.SINGLE_PARAMS_TO_SET).setValue(MagFreqDistParameter.MAG_AND_MO_RATE);
			magEditor.getParameter(MagFreqDistParameter.MAG).setValue(new Double(6.0));
			magEditor.getParameter(MagFreqDistParameter.MO_RATE).setValue(new Double(1.905e16));
		}

		//mag dist parameters for the test case 9_2
		else if(selectedTest.equalsIgnoreCase(TEST_CASE_NINE_B)) {

			magEditor.getParameter(MagFreqDistParameter.DISTRIBUTION_NAME).setValue(SingleMagFreqDist.NAME);
			magEditor.getParameter(MagFreqDistParameter.SINGLE_PARAMS_TO_SET).setValue(MagFreqDistParameter.MAG_AND_MO_RATE);
			magEditor.getParameter(MagFreqDistParameter.MAG).setValue(new Double(6.0));
			magEditor.getParameter(MagFreqDistParameter.MO_RATE).setValue(new Double(1.905e16));
		}

		//mag dist parameters for the test case 9_1
		else if(selectedTest.equalsIgnoreCase(TEST_CASE_NINE_C)) {

			magEditor.getParameter(MagFreqDistParameter.DISTRIBUTION_NAME).setValue(SingleMagFreqDist.NAME);
			magEditor.getParameter(MagFreqDistParameter.SINGLE_PARAMS_TO_SET).setValue(MagFreqDistParameter.MAG_AND_MO_RATE);
			magEditor.getParameter(MagFreqDistParameter.MAG).setValue(new Double(6.0));
			magEditor.getParameter(MagFreqDistParameter.MO_RATE).setValue(new Double(1.905e16));
		}

		// mag dist parameters for test case 10
		else if(selectedTest.equalsIgnoreCase(TEST_CASE_TEN)) {
			magEditor.getParameter(MagFreqDistParameter.DISTRIBUTION_NAME).setValue(GutenbergRichterMagFreqDist.NAME);
			magEditor.getParameter(MagFreqDistParameter.MIN).setValue(new Double(0.05));
			magEditor.getParameter(MagFreqDistParameter.MAX).setValue(new Double(9.95));
			magEditor.getParameter(MagFreqDistParameter.NUM).setValue(new Integer(100));
			magEditor.getParameter(MagFreqDistParameter.SET_ALL_PARAMS_BUT).setValue(MagFreqDistParameter.TOT_MO_RATE);
			magEditor.getParameter(MagFreqDistParameter.GR_MAG_LOWER).setValue(new Double(5.05));
			magEditor.getParameter(MagFreqDistParameter.GR_MAG_UPPER).setValue(new Double(6.45));
			magEditor.getParameter(MagFreqDistParameter.GR_BVALUE).setValue(new Double(0.9));
			magEditor.getParameter(MagFreqDistParameter.TOT_CUM_RATE).setValue(new Double(.0395));
		}

		// mag dist parameters for test case 11
		else if(selectedTest.equalsIgnoreCase(TEST_CASE_ELEVEN)) {
			magEditor.getParameter(MagFreqDistParameter.DISTRIBUTION_NAME).setValue(GutenbergRichterMagFreqDist.NAME);
			magEditor.getParameter(MagFreqDistParameter.MIN).setValue(new Double(0.05));
			magEditor.getParameter(MagFreqDistParameter.MAX).setValue(new Double(9.95));
			magEditor.getParameter(MagFreqDistParameter.NUM).setValue(new Integer(100));
			magEditor.getParameter(MagFreqDistParameter.SET_ALL_PARAMS_BUT).setValue(MagFreqDistParameter.TOT_MO_RATE);
			magEditor.getParameter(MagFreqDistParameter.GR_MAG_LOWER).setValue(new Double(5.05));
			magEditor.getParameter(MagFreqDistParameter.GR_MAG_UPPER).setValue(new Double(6.45));
			magEditor.getParameter(MagFreqDistParameter.GR_BVALUE).setValue(new Double(0.9));
			magEditor.getParameter(MagFreqDistParameter.TOT_CUM_RATE).setValue(new Double(.0395));
		}

		// now have the editor create the magFreqDist
		magEditor.setMagDistFromParams();
	}

	/**
	 * This initializes the fault-data vectors needed for the tests that utilize the FloatingPoissonFaultERF
	 */
	private void initializeFaultData() {

		// Set1 faults
		fault1and2_Lats = new ArrayList();
		fault1and2_Lats.add(new Double(38.22480));
		fault1and2_Lats.add(new Double(38.0));

		fault1and2_Lons = new ArrayList();
		fault1and2_Lons.add(new Double(-122.0));
		fault1and2_Lons.add(new Double(-122.0));

		fault1_Dips = new ArrayList();
		fault1_Dips.add(new Double(90.0));

		fault1_Depths = new ArrayList();
		fault1_Depths.add(new Double(0.0));
		fault1_Depths.add(new Double(12.0));

		fault2_Dips = new ArrayList();
		fault2_Dips.add(new Double(60.0));

		fault2_Depths = new ArrayList();
		fault2_Depths.add(new Double(1.0));
		fault2_Depths.add(new Double(12.0));

		// Set2 faults
		faultE_Lats = new ArrayList();
		faultE_Lats.add(new Double(38.0));
		faultE_Lats.add(new Double(38.2248));

		faultE_Lons = new ArrayList();
		faultE_Lons.add(new Double(-122.0));
		faultE_Lons.add(new Double(-122.0));

		faultE_Dips = new ArrayList();
		faultE_Dips.add(new Double(50.0));
		faultE_Dips.add(new Double(20.0));

		faultE_Depths = new ArrayList();
		faultE_Depths.add(new Double(0.0));
		faultE_Depths.add(new Double(6.0));
		faultE_Depths.add(new Double(12.0));

	}


	/**
	 * fill he pick list with the test case numbers and sites
	 */
	private void initializeTestsAndSites() {
		//initializing the values inside the combobox for the supported test cases and sites
		ArrayList<String> v = new ArrayList<String>();

		//test case-1 ,Set-1
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_ONE+"-"+this.SITE_ONE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_ONE+"-"+this.SITE_TWO));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_ONE+"-"+this.SITE_THREE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_ONE+"-"+this.SITE_FOUR));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_ONE+"-"+this.SITE_FIVE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_ONE+"-"+this.SITE_SIX));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_ONE+"-"+this.SITE_SEVEN));


		//test case-2,Set-1
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_TWO+"-"+this.SITE_ONE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_TWO+"-"+this.SITE_TWO));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_TWO+"-"+this.SITE_THREE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_TWO+"-"+this.SITE_FOUR));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_TWO+"-"+this.SITE_FIVE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_TWO+"-"+this.SITE_SIX));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_TWO+"-"+this.SITE_SEVEN));


		//test case-3
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_THREE+"-"+this.SITE_ONE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_THREE+"-"+this.SITE_TWO));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_THREE+"-"+this.SITE_THREE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_THREE+"-"+this.SITE_FOUR));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_THREE+"-"+this.SITE_FIVE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_THREE+"-"+this.SITE_SIX));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_THREE+"-"+this.SITE_SEVEN));


		//test case-4
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_FOUR+"-"+this.SITE_ONE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_FOUR+"-"+this.SITE_TWO));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_FOUR+"-"+this.SITE_THREE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_FOUR+"-"+this.SITE_FOUR));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_FOUR+"-"+this.SITE_FIVE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_FOUR+"-"+this.SITE_SIX));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_FOUR+"-"+this.SITE_SEVEN));


		//test case-5
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_FIVE+"-"+this.SITE_ONE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_FIVE+"-"+this.SITE_TWO));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_FIVE+"-"+this.SITE_THREE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_FIVE+"-"+this.SITE_FOUR));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_FIVE+"-"+this.SITE_FIVE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_FIVE+"-"+this.SITE_SIX));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_FIVE+"-"+this.SITE_SEVEN));

		//test case-6
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_SIX+"-"+this.SITE_ONE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_SIX+"-"+this.SITE_TWO));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_SIX+"-"+this.SITE_THREE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_SIX+"-"+this.SITE_FOUR));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_SIX+"-"+this.SITE_FIVE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_SIX+"-"+this.SITE_SIX));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_SIX+"-"+this.SITE_SEVEN));


		//test case-7
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_SEVEN+"-"+this.SITE_ONE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_SEVEN+"-"+this.SITE_TWO));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_SEVEN+"-"+this.SITE_THREE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_SEVEN+"-"+this.SITE_FOUR));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_SEVEN+"-"+this.SITE_FIVE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_SEVEN+"-"+this.SITE_SIX));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_SEVEN+"-"+this.SITE_SEVEN));

		//test case-8_0sig
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_EIGHT_A+"-"+this.SITE_ONE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_EIGHT_A+"-"+this.SITE_TWO));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_EIGHT_A+"-"+this.SITE_THREE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_EIGHT_A+"-"+this.SITE_FOUR));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_EIGHT_A+"-"+this.SITE_FIVE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_EIGHT_A+"-"+this.SITE_SIX));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_EIGHT_A+"-"+this.SITE_SEVEN));

		//test case-8_1sig
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_EIGHT_B+"-"+this.SITE_ONE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_EIGHT_B+"-"+this.SITE_TWO));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_EIGHT_B+"-"+this.SITE_THREE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_EIGHT_B+"-"+this.SITE_FOUR));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_EIGHT_B+"-"+this.SITE_FIVE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_EIGHT_B+"-"+this.SITE_SIX));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_EIGHT_B+"-"+this.SITE_SEVEN));

		//test case-8_2sig
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_EIGHT_C+"-"+this.SITE_ONE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_EIGHT_C+"-"+this.SITE_TWO));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_EIGHT_C+"-"+this.SITE_THREE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_EIGHT_C+"-"+this.SITE_FOUR));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_EIGHT_C+"-"+this.SITE_FIVE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_EIGHT_C+"-"+this.SITE_SIX));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_EIGHT_C+"-"+this.SITE_SEVEN));


		//test case-9_Sa97
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_NINE_A+"-"+this.SITE_ONE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_NINE_A+"-"+this.SITE_TWO));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_NINE_A+"-"+this.SITE_THREE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_NINE_A+"-"+this.SITE_FOUR));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_NINE_A+"-"+this.SITE_FIVE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_NINE_A+"-"+this.SITE_SIX));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_NINE_A+"-"+this.SITE_SEVEN));

		//test case-9_SA97
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_NINE_B+"-"+this.SITE_ONE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_NINE_B+"-"+this.SITE_TWO));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_NINE_B+"-"+this.SITE_THREE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_NINE_B+"-"+this.SITE_FOUR));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_NINE_B+"-"+this.SITE_FIVE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_NINE_B+"-"+this.SITE_SIX));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_NINE_B+"-"+this.SITE_SEVEN));

		//test case-9_Ca97
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_NINE_C+"-"+this.SITE_ONE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_NINE_C+"-"+this.SITE_TWO));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_NINE_C+"-"+this.SITE_THREE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_NINE_C+"-"+this.SITE_FOUR));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_NINE_C+"-"+this.SITE_FIVE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_NINE_C+"-"+this.SITE_SIX));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_NINE_C+"-"+this.SITE_SEVEN));

		//test case-10
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_TEN+"-"+this.SITE_ONE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_TEN+"-"+this.SITE_TWO));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_TEN+"-"+this.SITE_THREE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_TEN+"-"+this.SITE_FOUR));


		//test case-11
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_ELEVEN+"-"+this.SITE_ONE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_ELEVEN+"-"+this.SITE_TWO));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_ELEVEN+"-"+this.SITE_THREE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_ELEVEN+"-"+this.SITE_FOUR));

		//test case-12
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_TWELVE+"-"+this.SITE_ONE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_TWELVE+"-"+this.SITE_TWO));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_TWELVE+"-"+this.SITE_THREE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_TWELVE+"-"+this.SITE_FOUR));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_TWELVE+"-"+this.SITE_FIVE));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_TWELVE+"-"+this.SITE_SIX));
		v.add(new String(this.PEER_TESTS_SET_ONE +"-"+this.TEST_CASE_TWELVE+"-"+this.SITE_SEVEN));


		//adding the SET ONE PEER test cases to the set one vector
		int size = v.size();
		for(int i=0;i<size;++i)
			this.peerTestSetOne.add(v.get(i));

		v.clear();
		//test case-1 , Set-2
		v.add(new String(this.PEER_TESTS_SET_TWO +"-"+this.TEST_CASE_ONE+"-"+this.SITE_ONE));
		v.add(new String(this.PEER_TESTS_SET_TWO +"-"+this.TEST_CASE_ONE+"-"+this.SITE_TWO));
		v.add(new String(this.PEER_TESTS_SET_TWO +"-"+this.TEST_CASE_ONE+"-"+this.SITE_THREE));
		v.add(new String(this.PEER_TESTS_SET_TWO +"-"+this.TEST_CASE_ONE+"-"+this.SITE_FOUR));
		v.add(new String(this.PEER_TESTS_SET_TWO +"-"+this.TEST_CASE_ONE+"-"+this.SITE_FIVE));
		v.add(new String(this.PEER_TESTS_SET_TWO +"-"+this.TEST_CASE_ONE+"-"+this.SITE_SIX));

		//test case-2 , Set-2
		v.add(new String(this.PEER_TESTS_SET_TWO +"-"+this.TEST_CASE_TWO+"-"+this.SITE_ONE));
		v.add(new String(this.PEER_TESTS_SET_TWO +"-"+this.TEST_CASE_TWO+"-"+this.SITE_TWO));
		v.add(new String(this.PEER_TESTS_SET_TWO +"-"+this.TEST_CASE_TWO+"-"+this.SITE_THREE));

		//test case-3 , Set-2
		v.add(new String(this.PEER_TESTS_SET_TWO +"-"+this.TEST_CASE_THREE+"-"+this.SITE_ONE));
		v.add(new String(this.PEER_TESTS_SET_TWO +"-"+this.TEST_CASE_THREE+"-"+this.SITE_TWO));
		v.add(new String(this.PEER_TESTS_SET_TWO +"-"+this.TEST_CASE_THREE+"-"+this.SITE_THREE));


		//test case-4 , Set-2
		v.add(new String(this.PEER_TESTS_SET_TWO +"-"+this.TEST_CASE_FOUR+"-"+this.SITE_ONE));
		v.add(new String(this.PEER_TESTS_SET_TWO +"-"+this.TEST_CASE_FOUR+"-"+this.SITE_TWO));
		v.add(new String(this.PEER_TESTS_SET_TWO +"-"+this.TEST_CASE_FOUR+"-"+this.SITE_THREE));

		//test case-5 , Set-2
		v.add(new String(this.PEER_TESTS_SET_TWO +"-"+this.TEST_CASE_FIVE+"-"+this.SITE_ONE));
		v.add(new String(this.PEER_TESTS_SET_TWO +"-"+this.TEST_CASE_FIVE+"-"+this.SITE_TWO));
		v.add(new String(this.PEER_TESTS_SET_TWO +"-"+this.TEST_CASE_FIVE+"-"+this.SITE_THREE));

		//test case-6 , Set-2
		v.add(new String(this.PEER_TESTS_SET_TWO +"-"+this.TEST_CASE_SIX+"-"+this.SITE_ONE));
		v.add(new String(this.PEER_TESTS_SET_TWO +"-"+this.TEST_CASE_SIX+"-"+this.SITE_TWO));
		v.add(new String(this.PEER_TESTS_SET_TWO +"-"+this.TEST_CASE_SIX+"-"+this.SITE_THREE));

		//adding the SET TWO PEER test cases to the set two vector
		size = v.size();
		for(int i=0;i<size;++i)
			this.peerTestSetTwo.add(v.get(i));


		size = this.peerTestSetOne.size();
		for(int i=0;i<size;++i)
			this.testCaseComboBox.addItem(peerTestSetOne.get(i));


		size = this.peerTestSetTwo.size();
		for(int i=0;i<size;++i)
			this.testCaseComboBox.addItem(peerTestSetTwo.get(i));
	}

	/**
	 * this sets the test case params in the GUI
	 * @param e
	 */
	void testCaseComboBox_actionPerformed(ActionEvent e) {
		String testSelected = this.testCaseComboBox.getSelectedItem().toString();
		setTestCaseAndSite(testSelected);
	}

	/**
	 *
	 * @returns the ArrayList of the PEER Test Case set One
	 */
	public ArrayList<String> getPEER_SetOneTestCasesNames(){
		return this.peerTestSetOne;
	}


	/**
	 *
	 * @returns the ArrayList of the PEER Test Case set Two
	 */
	public ArrayList<String> getPEER_SetTwoTestCasesNames(){
		return this.peerTestSetTwo;
	}

	@Override
	public Window getComponent() {
		return frame;
	}
}
