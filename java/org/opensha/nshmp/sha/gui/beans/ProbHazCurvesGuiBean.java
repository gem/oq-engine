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

package org.opensha.nshmp.sha.gui.beans;

import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Component;
import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.rmi.RemoteException;
import java.util.ArrayList;
import java.util.ListIterator;

import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JSplitPane;
import javax.swing.JTabbedPane;
import javax.swing.border.Border;
import javax.swing.border.TitledBorder;

import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.exceptions.RegionConstraintException;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.Region;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ConstrainedStringParameterEditor;
import org.opensha.commons.param.editor.DoubleParameterEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.nshmp.exceptions.AnalysisOptionNotSupportedException;
import org.opensha.nshmp.exceptions.LocationErrorException;
import org.opensha.nshmp.exceptions.ZipCodeErrorException;
import org.opensha.nshmp.param.EditableStringConstraint;
import org.opensha.nshmp.param.editor.EditableConstrainedStringParameterEditor;
import org.opensha.nshmp.sha.data.DataGenerator_HazardCurves;
import org.opensha.nshmp.sha.data.api.DataGeneratorAPI_HazardCurves;
import org.opensha.nshmp.sha.gui.api.ProbabilisticHazardApplicationAPI;
import org.opensha.nshmp.sha.gui.infoTools.GraphWindow;
import org.opensha.nshmp.util.GlobalConstants;
import org.opensha.nshmp.util.LocationUtil;
import org.opensha.nshmp.util.RegionUtil;
import org.opensha.sha.gui.infoTools.ExceptionWindow;



/**
 * <p>Title:ProbHazCurvesGuiBean</p>
 *
 * <p>Description: This option sets the parameter for the NEHRP analysis option.</p>
 * @author Ned Field, Nitin Gupta and E.V.Leyendecker
 * @version 1.0
 */
public class ProbHazCurvesGuiBean
    extends JPanel implements ParameterChangeListener,
    AnalysisOptionsGuiBeanAPI {
	private static final long serialVersionUID = 0x06B4735;
	
  //Dataset selection Gui instance
  private DataSetSelectionGuiBean datasetGui;
  //private LocationGuiBean locGuiBean;
  private BatchLocationBean locGuiBean;
  JSplitPane mainSplitPane = new JSplitPane();
  JSplitPane locationSplitPane = new JSplitPane();
  JSplitPane buttonsSplitPane = new JSplitPane();
  JPanel regionPanel = new JPanel();
  JPanel basicParamsPanel = new JPanel();
  JPanel singleHazardValPanel = new JPanel();
  Border border9 = BorderFactory.createLineBorder(new Color(80,80,140),1);
  TitledBorder responseSpecBorder = new TitledBorder(border9,
      "Single Hazard Curve Value");

  TitledBorder basicParamBorder = new TitledBorder(border9,
      "Basic Hazard Curve");
  TitledBorder regionBorder = new TitledBorder(border9,
                                               "Region and DataSet Selection");
  private GridBagLayout gridBagLayout2 = new GridBagLayout();
  private GridBagLayout gridBagLayout4 = new GridBagLayout();
  private GridBagLayout gridBagLayout3 = new GridBagLayout();

	private boolean calcButtonClicked = false;
  private boolean locationVisible;
  private JButton hazCurveCalcButton = new JButton();
  private JButton viewCurveButton = new JButton();
  private JButton singleHazardCurveValButton = new JButton();
  private BorderLayout borderLayout1 = new BorderLayout();

	//Some tooltip text for these buttons
	private String hazCurveCalcToolTip = "Calculate the seismic hazard curve " +
																				"for the B/C boundary.";
	private String viewCurveToolTip = "View the graph for seismic hazard " +
																			"for the B/C boundary.";
	private String singleHazardCurveValToolTip = "Calculate the values of the " +
		"selected parameter for the specified measure of probability as a " +
		"return period of frequency of exceedance in a specified exposure time.";

  //creating the Hazard curve selection parameter
  StringParameter hazardCurveIMTPeriodSelectionParam;
  ConstrainedStringParameterEditor hazardCurveIMTPeriodSelectionParamEditor;
  private static final String HAZ_CURVE_IMT_PERIOD_PARAM_NAME =
      "Select Hazard Curve";

  private DataGeneratorAPI_HazardCurves dataGenerator = new
      DataGenerator_HazardCurves();



  private static final String RETURN_PERIOD_PARAM_NAME = "Return Period";
  private static final String PROB_EXCEED_PARAM_NAME   = "Prob. of Exceedance";
  private static final String EXP_TIME_PARAM_NAME      = "Exposure Time";
  private static final String GROUND_MOTION_PARAM_NAME = "Ground Motion";

  private static final int returnPeriodIdx = 0;
  private static final int probInTimeIdx   = 1;
  private static final int groundMotionIdx = 2;
  
  private JTabbedPane singleHazardValEditorPanel;
  private EditableConstrainedStringParameterEditor returnPdEditor;
  private EditableConstrainedStringParameterEditor exceedProbEditor;
  private EditableConstrainedStringParameterEditor expTimeEditor;
  private DoubleParameterEditor groundMotionEditor;

  //instance of the application using this GUI bean
  private ProbabilisticHazardApplicationAPI application;

  private String selectedRegion, selectedEdition, imt, returnPeriod,
      exceedProbVal, expTimeVal;
  private double groundMotionVal;
  //checks if Single Value for the Hazard Curve has to be computed using Return Pd.
  private boolean returnPdSelected = true;

  public ProbHazCurvesGuiBean(ProbabilisticHazardApplicationAPI api) {
    application = api;
    try {
      createSingleHazardValEditor();
      jbInit();

      datasetGui = new DataSetSelectionGuiBean();
      locGuiBean = new BatchLocationBean();
    }
    catch (Exception exception) {
      exception.printStackTrace();
    }

    try {
      createGeographicRegionSelectionParameter();
    }
    catch (AnalysisOptionNotSupportedException ex) {
      JOptionPane.showMessageDialog(this, ex.getMessage(),
                                    "Analysis Option selection error",
                                    JOptionPane.ERROR_MESSAGE);
    }
    createIMT_PeriodsParameter();
    createEditionSelectionParameter();
    //creating the datasetEditor to show the geographic region and edition dataset.
    datasetGui.createDataSetEditor();
    try {
      createLocation();
    }
    catch (RegionConstraintException ex1) {
      ExceptionWindow bugWindow = new ExceptionWindow(this, ex1.getStackTrace(),
          "Exception occured while initializing the  region parameters in NSHMP application." +
          "Parameters values have not been set yet.");
      bugWindow.setVisible(true);
      bugWindow.pack();

    }
    locationSplitPane.add((Component) locGuiBean.getVisualization(GuiBeanAPI.EMBED), JSplitPane.BOTTOM);
    locationSplitPane.setDividerLocation(120);
    regionPanel.add(datasetGui.getDatasetSelectionEditor(),
                    new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
                                           , GridBagConstraints.CENTER,
                                           GridBagConstraints.BOTH,
                                           new Insets(0, 0, 0, 0), 0, 0));


    this.updateUI();
  }

  private void createIMT_PeriodsParameter() {
    if (hazardCurveIMTPeriodSelectionParamEditor != null) {
      basicParamsPanel.remove(hazardCurveIMTPeriodSelectionParamEditor);
    }
    ArrayList supportedImtPeriods = RegionUtil.getSupportedIMT_PERIODS(
        selectedRegion);
    hazardCurveIMTPeriodSelectionParam = new StringParameter(
        HAZ_CURVE_IMT_PERIOD_PARAM_NAME,
        supportedImtPeriods,
        (String) supportedImtPeriods.get(0));
    hazardCurveIMTPeriodSelectionParam.addParameterChangeListener(this);
    hazardCurveIMTPeriodSelectionParamEditor = new
        ConstrainedStringParameterEditor(hazardCurveIMTPeriodSelectionParam);
		hazardCurveIMTPeriodSelectionParamEditor.getValueEditor().setToolTipText(
			"Select the parameter of interest from the list.");
    hazardCurveIMTPeriodSelectionParamEditor.refreshParamEditor();
    imt = (String) hazardCurveIMTPeriodSelectionParam.getValue();

    basicParamsPanel.add(hazardCurveIMTPeriodSelectionParamEditor,
                         new GridBagConstraints(0, 0, 2, 1, 1.0, 1.0
                                                , GridBagConstraints.CENTER,
                                                GridBagConstraints.HORIZONTAL,
                                                new Insets(4, 4, 4, 4), 0, 0));

  }

  private void createSingleHazardValEditor() {
    ArrayList supportedReturnPds = GlobalConstants.getSupportedReturnPeriods();
    EditableStringConstraint returnPdConstraint = new EditableStringConstraint(
        supportedReturnPds);
    StringParameter returnPeriodParam = new StringParameter(
        RETURN_PERIOD_PARAM_NAME, returnPdConstraint,
        "Years", (String) supportedReturnPds.get(0));

    ArrayList exceedProbsList = GlobalConstants.getSupportedExceedanceProb();
    EditableStringConstraint exceedProbParamConstraint = new EditableStringConstraint(exceedProbsList);
    StringParameter exceedProbParam = new StringParameter(
        PROB_EXCEED_PARAM_NAME, exceedProbParamConstraint, (String) exceedProbsList.get(0));

    ArrayList supportedExpTimeList = GlobalConstants.getSupportedExposureTime();
    EditableStringConstraint expTimeConstraint = new EditableStringConstraint(
        supportedExpTimeList);
    StringParameter expTimeParam = new StringParameter(
        EXP_TIME_PARAM_NAME, expTimeConstraint,
        "Years", (String) supportedExpTimeList.get(0));

    DoubleParameter groundMotionParam = new DoubleParameter(
    		GROUND_MOTION_PARAM_NAME, 0.000001, 100.0, "g"
    	);

    returnPeriod = (String) returnPeriodParam.getValue();
    exceedProbVal = (String) exceedProbParam.getValue();
    expTimeVal = (String) expTimeParam.getValue();
    groundMotionVal = 0.1;



    returnPeriodParam.addParameterChangeListener(this);
    exceedProbParam.addParameterChangeListener(this);
    expTimeParam.addParameterChangeListener(this);
    groundMotionParam.addParameterChangeListener(this);

    try{
      returnPdEditor = new EditableConstrainedStringParameterEditor(returnPeriodParam);
      exceedProbEditor = new EditableConstrainedStringParameterEditor(exceedProbParam);
      expTimeEditor = new EditableConstrainedStringParameterEditor(expTimeParam);
      groundMotionEditor = new DoubleParameterEditor(groundMotionParam);

      singleHazardValEditorPanel =new JTabbedPane(JTabbedPane.TOP, JTabbedPane.SCROLL_TAB_LAYOUT);
     // singleHazardValEditorPanel.setLayout(new GridBagLayout());

      
      JPanel panel0 = new JPanel(new GridBagLayout());
      panel0.add(returnPdEditor, new GridBagConstraints(
    		  0, 0, 1, 1, 1.0, 1.0, GridBagConstraints.NORTH, GridBagConstraints.HORIZONTAL,
          new Insets(1,1,1,1), 0, 0));
      singleHazardValEditorPanel.addTab("Return Period", panel0);

      
      JPanel panel1 = new JPanel(new GridBagLayout());
      panel1.add(exceedProbEditor, new GridBagConstraints(
    		  0, 0, 1, 1, 1.0, 1.0, GridBagConstraints.NORTH, GridBagConstraints.HORIZONTAL,
    		  new Insets(1, 1, 1, 1), 0, 0));
      panel1.add(expTimeEditor, new GridBagConstraints(
    		  1, 0, 1, 1, 1.0, 1.0, GridBagConstraints.NORTH, GridBagConstraints.HORIZONTAL,
    		  new Insets(1, 1, 1, 1), 0, 0));
      singleHazardValEditorPanel.addTab("Prob. & Time", panel1);
      
      JPanel panel2 = new JPanel(new GridBagLayout());
      panel2.add(groundMotionEditor, new GridBagConstraints(
    		  0, 0, 1, 1, 1.0, 1.0, GridBagConstraints.NORTH, GridBagConstraints.HORIZONTAL,
    		  new Insets(1, 1, 1, 1), 0, 0));
      singleHazardValEditorPanel.addTab("Ground Motion", groundMotionEditor);
      
      singleHazardValEditorPanel.setSize(new Dimension(100, 100));
      singleHazardValEditorPanel.setPreferredSize(new Dimension(100, 100));
      
      
      singleHazardValEditorPanel.setToolTipTextAt(0, "Select to calculate a hazard value using " +
    		  "the ground motion return period in years.");
      singleHazardValEditorPanel.setToolTipTextAt(1, "Select to calculate the " +
    		  "hazard value using the Probability of Exceedance and Exposure Time.");
      singleHazardValEditorPanel.setToolTipTextAt(2, "Select to calculate the " +
    		  "Frequency of Exceedance using the ground motion value.");
    }
    catch (Exception e) {
      e.printStackTrace();
    }
    singleHazardValPanel.updateUI();
  }

  private void jbInit() throws Exception {
    this.setLayout(borderLayout1);
    mainSplitPane.setOrientation(JSplitPane.VERTICAL_SPLIT);
    locationSplitPane.setOrientation(JSplitPane.VERTICAL_SPLIT);
    buttonsSplitPane.setOrientation(JSplitPane.VERTICAL_SPLIT);
    basicParamsPanel.setLayout(gridBagLayout3);
    basicParamsPanel.setBorder(basicParamBorder);
    basicParamBorder.setTitleColor(Color.RED);
    singleHazardValPanel.setBorder(responseSpecBorder);
    responseSpecBorder.setTitleColor(Color.RED);
    singleHazardValPanel.setLayout(gridBagLayout4);
    regionPanel.setBorder(regionBorder);
    regionBorder.setTitleColor(Color.RED);
    regionPanel.setLayout(gridBagLayout2);
    hazCurveCalcButton.setText("Calculate");
		hazCurveCalcButton.setToolTipText(hazCurveCalcToolTip);
    hazCurveCalcButton.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        hazCurveCalcButton_actionPerformed(e);
      }
    });
    viewCurveButton.setText("  View  ");
		viewCurveButton.setToolTipText(viewCurveToolTip);
    viewCurveButton.addActionListener(new java.awt.event.ActionListener() {
      public void actionPerformed(ActionEvent e) {
        viewCurveButton_actionPerformed(e);
      }
    });
    singleHazardCurveValButton.setText(
        "Calculate");
		singleHazardCurveValButton.setToolTipText(singleHazardCurveValToolTip);
    singleHazardCurveValButton.addActionListener(new java.awt.event.
                                                 ActionListener() {
      public void actionPerformed(ActionEvent e) {
        singleHazardCurveValButton_actionPerformed(e);
      }
    });

    mainSplitPane.add(locationSplitPane, JSplitPane.TOP);
    mainSplitPane.add(buttonsSplitPane, JSplitPane.BOTTOM);
    locationSplitPane.add(regionPanel, JSplitPane.TOP);

    buttonsSplitPane.add(basicParamsPanel, JSplitPane.TOP);
    buttonsSplitPane.add(singleHazardValPanel, JSplitPane.BOTTOM);

    this.add(mainSplitPane, BorderLayout.CENTER);
    basicParamsPanel.add(hazCurveCalcButton,
                         new GridBagConstraints(1, 1, 1, 1, 0.0, 0.0
                                                , GridBagConstraints.CENTER,
                                                GridBagConstraints.NONE,
                                                new Insets(4, 0, 4, 100), 0,0));
    basicParamsPanel.add(viewCurveButton,
                         new GridBagConstraints(1, 1, 1, 1, 0.0, 0.0
                                                , GridBagConstraints.CENTER,
                                                GridBagConstraints.NONE,
                                                new Insets(4, 100, 4, 0), 0,0));
    
    
    
    
    singleHazardValPanel.add(singleHazardValEditorPanel,
                             new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
        , GridBagConstraints.NORTH, GridBagConstraints.HORIZONTAL,
        new Insets(0, 0, 0, 0), 0,0 ));
    
    singleHazardValPanel.add(singleHazardCurveValButton,
                             new GridBagConstraints(0, 1, 1, 1, 1.0, 1.0
        , GridBagConstraints.CENTER, GridBagConstraints.NONE,
        new Insets(0, 0, 0, 0), 0, 0));

    mainSplitPane.setDividerLocation(260);
    buttonsSplitPane.setDividerLocation(117);
    singleHazardCurveValButton.setEnabled(true);
    viewCurveButton.setEnabled(true);
		calcButtonClicked = false;
    singleHazardValPanel.setMinimumSize(new Dimension(0,0));
    basicParamsPanel.setMinimumSize(new Dimension(0,0));
    regionPanel.setMinimumSize(new Dimension(0,0));
  }

  /**
   * Removes all the output from the window
   */
  public void clearData() {
    dataGenerator.clearData();
    //singleHazardCurveValButton.setEnabled(false);
		calcButtonClicked = false;
  }

  /**
   * If GuiBean parameter is changed.
   * @param event ParameterChangeEvent
   */
  public void parameterChange(ParameterChangeEvent event) {

    String paramName = event.getParameterName();

    if (paramName.equals(DataSetSelectionGuiBean.GEOGRAPHIC_REGION_SELECTION_PARAM_NAME)) {
      selectedRegion = datasetGui.getSelectedGeographicRegion();
      //creating the edition parameter when user changes the region
      createEditionSelectionParameter();
      selectedEdition = datasetGui.getSelectedDataSetEdition();
      try {
        createLocation();
      }
      catch (RegionConstraintException ex) {
        ExceptionWindow bugWindow = new ExceptionWindow(this, ex.getStackTrace(),
            "Exception occured while initializing the  region parameters in NSHMP application." +
            "Parameters values have not been set yet.");
        bugWindow.setVisible(true);
        bugWindow.pack();
      }
      createIMT_PeriodsParameter();
      //viewCurveButton.setEnabled(false);
      //singleHazardCurveValButton.setEnabled(false);
			calcButtonClicked = false;
    }
    else if (paramName.equals(DataSetSelectionGuiBean.EDITION_PARAM_NAME)) {
      selectedEdition = datasetGui.getSelectedDataSetEdition();
      //viewCurveButton.setEnabled(false);
      //singleHazardCurveValButton.setEnabled(false);
			calcButtonClicked = false;
    }

    else if (paramName.equals(HAZ_CURVE_IMT_PERIOD_PARAM_NAME)) {
      imt = (String) hazardCurveIMTPeriodSelectionParam.getValue();
      //viewCurveButton.setEnabled(false);
      //singleHazardCurveValButton.setEnabled(false);
			calcButtonClicked = false;
    }
    else if (paramName.equals(RETURN_PERIOD_PARAM_NAME)) {
      returnPeriod = (String)returnPdEditor.getValue();
    }
    else if (paramName.equals(PROB_EXCEED_PARAM_NAME)) {
      exceedProbVal = (String) exceedProbEditor.getValue();
    }
    else if (paramName.equals(EXP_TIME_PARAM_NAME)) {
      expTimeVal = (String) expTimeEditor.getValue();
    }
    else if (paramName.equals(BatchLocationBean.PARAM_LAT) ||
             paramName.equals(BatchLocationBean.PARAM_LON) ||
             paramName.equals(BatchLocationBean.PARAM_ZIP)) {
			calcButtonClicked = false;
    } else if (paramName.equals(GROUND_MOTION_PARAM_NAME)) {
    	groundMotionVal = Double.parseDouble(
    			groundMotionEditor.getValue().toString());
    }

    this.updateUI();
  }

  /**
   * Returns the instance of itself
   * @return JPanel
   */
  public JPanel getGuiBean() {
    return this;
  }

  /**
   * Creating the location gui bean
   */
  private void createLocation() throws RegionConstraintException {
	  Region region = RegionUtil.getRegionConstraint(
        selectedRegion);
    if (region != null) {
      locationVisible = true;
      //checking if Zip code is supported by the selected choice
      boolean zipCodeSupported = LocationUtil.
          isZipCodeSupportedBySelectedEdition(selectedRegion);
      locGuiBean.updateGuiParams(region.getMinLat(), region.getMaxLat(),
                                   region.getMinLon(), region.getMaxLon(),
                                   zipCodeSupported);
      ParameterList paramList = locGuiBean.getLocationParameters();
      ListIterator it = paramList.getParametersIterator();
      while (it.hasNext()) {
        ParameterAPI param = (ParameterAPI) it.next();
        param.addParameterChangeListener(this);
      }


    }
    else if (region == null) {
      locationVisible = false;
      locGuiBean.createNoLocationGUI();

    }

  }


  /**
   * Returns the selected Region
   * @return String
   */
  public String getSelectedRegion(){
    return selectedRegion;
  }

  /**
   * Returns the selected data edition
   * @return String
   */
  public String getSelectedDataEdition(){
    return selectedEdition;
  }


  /**
   * Creates the Parameter that allows user to select  the Editions based on the
   * selected Analysis and choosen geographic region.
   */
  private void createEditionSelectionParameter() {

    ArrayList<String> supportedEditionList = new ArrayList<String>();
    if (selectedRegion.equals(GlobalConstants.CONTER_48_STATES)) {
      supportedEditionList.add(GlobalConstants.data_2002);
      supportedEditionList.add(GlobalConstants.data_1996);
    }
    else if (selectedRegion.equals(GlobalConstants.ALASKA) ||
             selectedRegion.equals(GlobalConstants.HAWAII)) {
      supportedEditionList.add(GlobalConstants.data_1998);
    }
    /*else if (selectedRegion.equals(GlobalConstants.INDONESIA)) {
    	supportedEditionList.add(GlobalConstants.data_2007);
    }*/
    else {
      supportedEditionList.add(GlobalConstants.data_2003);
    }

    datasetGui.createEditionSelectionParameter(supportedEditionList);
    datasetGui.getEditionSelectionParameter().addParameterChangeListener(this);
    selectedEdition = datasetGui.getSelectedDataSetEdition();
  }

  /**
   *
   * Creating the parameter that allows user to choose the geographic region list
   * if selected Analysis option is NEHRP.
   *
   */
  private void createGeographicRegionSelectionParameter() throws
      AnalysisOptionNotSupportedException {
    ArrayList supportedRegionList = RegionUtil.
        getSupportedGeographicalRegions(GlobalConstants.PROB_HAZ_CURVES);
    datasetGui.createGeographicRegionSelectionParameter(supportedRegionList);
    datasetGui.getGeographicRegionSelectionParameter().
        addParameterChangeListener(this);
    selectedRegion = datasetGui.getSelectedGeographicRegion();
  }

  /**
   * Gets the SA Period and Values from datafiles
   */
  private void getDataForSA_Period() throws ZipCodeErrorException,
      LocationErrorException,
      RemoteException {

    dataGenerator.setRegion(selectedRegion);
    dataGenerator.setEdition(selectedEdition);

    //doing the calculation if not territory and Location GUI is visible
    if (locationVisible) {
      int locationMode = locGuiBean.getLocationMode();
      if (locationMode == BatchLocationBean.GEO_MODE) {
        Location loc = locGuiBean.getSelectedLocation();
        double lat = loc.getLatitude();
        double lon = loc.getLongitude();
        dataGenerator.calculateHazardCurve(lat, lon, imt);

      } else if(locationMode == BatchLocationBean.ZIP_MODE) {
        String zipCode = locGuiBean.getZipCode();
        dataGenerator.calculateHazardCurve(zipCode, imt);
      } else if (locationMode == BatchLocationBean.BAT_MODE) {
    	  Thread t = new Thread(new Runnable() {
    		  public void run() {
    			  ArrayList<Location> locations = locGuiBean.getBatchLocations();
    			  if(locations.size() > 1000) {
						// We have an arbitrary 1,000 row limit.  Die if too many.
						JOptionPane.showMessageDialog(null, "Batch mode is currently limited to 1,000 records " +
								"at one time.\nPlease reduce the number of rows in your input file and " +
								"try again.", "Too Many Records", JOptionPane.ERROR_MESSAGE);
						return;
					}
    	    	  dataGenerator.calculateHazardCurve(locations, imt, locGuiBean.getOutputFile());
    	    	  application.setDataInWindow(getData());
    		  }
    	  });
    	  t.start();
      }
    }
  }


  /**
   *
   * @return String
   */
  public String getData() {
    return dataGenerator.getDataInfo();
  }

  void viewCurveButton_actionPerformed(ActionEvent e) {
	    if(locGuiBean.getLocationMode() == BatchLocationBean.BAT_MODE) {
	    	JOptionPane.showMessageDialog(this, "This option is not available for batch output.\n" +
	    			"Please open the Excel output file and\n create your own plots.",
	    			"Option Unavailable", JOptionPane.INFORMATION_MESSAGE);
	    	return;
	    }
		if (!calcButtonClicked) hazCurveCalcButton_actionPerformed(e);
		if (!calcButtonClicked) { //if call to hazCurvCalcButton exited abnormally
			return;
		}
	
    GraphWindow window = new GraphWindow(dataGenerator.getHazardCurveFunction());
    window.setVisible(true);
  }

  void hazCurveCalcButton_actionPerformed(ActionEvent e) {
    try{
      getDataForSA_Period();
    }
    catch (ZipCodeErrorException ee) {
      JOptionPane.showMessageDialog(this, ee.getMessage(), "Zip Code Error",
                                    JOptionPane.OK_OPTION);
      return;
    }
    catch (LocationErrorException ee) {
      JOptionPane.showMessageDialog(this, ee.getMessage(), "Location Error",
                                    JOptionPane.OK_OPTION);
      return;
    }
    catch (RemoteException ee) {
      JOptionPane.showMessageDialog(this,
                                    ee.getMessage() + "\n" +
                                    "Please check your network connection",
                                    "Server Connection Error",
                                    JOptionPane.ERROR_MESSAGE);
      return;
    }

    application.setDataInWindow(getData());
    //viewCurveButton.setEnabled(true);
    //singleHazardCurveValButton.setEnabled(true);
		calcButtonClicked = true;
  }

  /**
   * Calculates the Single Hazard Curve Value
   * @param e ActionEvent
   */
  void singleHazardCurveValButton_actionPerformed(ActionEvent e) {
	  

	int locationMode = locGuiBean.getLocationMode();
	dataGenerator.setRegion(selectedRegion);
	dataGenerator.setEdition(selectedEdition);

    //linear interpolation in case if the selected data edition is 1996 or 1998
    final boolean isLogInterpolation = !(
    		selectedEdition.equals(GlobalConstants.data_1996) || 
    		selectedEdition.equals(GlobalConstants.data_1998)
    	);
    
    // else always perform the log interpolation
    int calcMode = singleHazardValEditorPanel.getSelectedIndex();
    
    if (calcMode == probInTimeIdx) {
      try {
        final double exceedProb = Double.parseDouble(exceedProbVal);
        final double expTime = Double.parseDouble(expTimeVal);
        if (locationMode == BatchLocationBean.BAT_MODE) {
      	  Thread t = new Thread(new Runnable() {
      		  public void run() {
      			  ArrayList<Location> locations = locGuiBean.getBatchLocations();
      			  if(locations.size() > 1000) {
  						// We have an arbitrary 1,000 row limit.  Die if too many.
  						JOptionPane.showMessageDialog(null, "Batch mode is currently limited to 1,000 records " +
  								"at one time.\nPlease reduce the number of rows in your input file and " +
  								"try again.", "Too Many Records", JOptionPane.ERROR_MESSAGE);
  						return;
  					}
      	    	  try {
	                dataGenerator.calcSingleValueHazard(locations, imt,
	                		  locGuiBean.getOutputFile(), exceedProb, expTime,
	                		  isLogInterpolation);
                } catch (RemoteException ex) {
	                ex.printStackTrace(System.err);
                }
      	    	  application.setDataInWindow(getData());
      		  }
      	  });
      	  t.start();
        } else {
      	
      	if (!calcButtonClicked) hazCurveCalcButton_actionPerformed(e);
     		if (!calcButtonClicked) { //if call to hazCurvCalcButton exited abnormally
     			return;
     		}
     		
        	dataGenerator.calcSingleValueHazardCurveUsingPEandExptime(
        			exceedProb, expTime, isLogInterpolation);
        	application.setDataInWindow(getData());
        }
      } catch(NumberFormatException eee){
        JOptionPane.showMessageDialog(this,"Please enter a valid Exceed Prob. "+
                                      "and Exposure Time","Input Error",
            JOptionPane.ERROR_MESSAGE);
        return;
      } catch (RemoteException ee) {
        JOptionPane.showMessageDialog(this,
                                      ee.getMessage() + "\n" +
                                      "Please check your network connection",
                                      "Server Connection Error",
                                      JOptionPane.ERROR_MESSAGE);
        return;
      }
    } else if (calcMode == returnPeriodIdx) {
      try {
        final double returnPd = Double.parseDouble(returnPeriod);
        if (locationMode == BatchLocationBean.BAT_MODE) {
        	  Thread t = new Thread(new Runnable() {
        		  public void run() {
        			  ArrayList<Location> locations = locGuiBean.getBatchLocations();
        			  if(locations.size() > 1000) {
    						// We have an arbitrary 1,000 row limit.  Die if too many.
    						JOptionPane.showMessageDialog(null, "Batch mode is currently limited to 1,000 records " +
    								"at one time.\nPlease reduce the number of rows in your input file and " +
    								"try again.", "Too Many Records", JOptionPane.ERROR_MESSAGE);
    						return;
    					}
        	    	  try {
	                    dataGenerator.calcSingleValueHazard(locations, imt,
	                    		  locGuiBean.getOutputFile(), returnPd,
	                    		  isLogInterpolation);
                   } catch (RemoteException ex) {
	                    ex.printStackTrace(System.err);
                    }
        	    	  application.setDataInWindow(getData());
        		  }
        	  });
        	  t.start();
          } else {
         	  if (!calcButtonClicked) hazCurveCalcButton_actionPerformed(e);
       		  if (!calcButtonClicked) { //if call to hazCurvCalcButton exited abnormally
       			  return;
       		  }
            	dataGenerator.calcSingleValueHazardCurveUsingReturnPeriod(
            			returnPd, isLogInterpolation);
            	application.setDataInWindow(getData());
          }
      } catch(NumberFormatException eee){
        JOptionPane.showMessageDialog(this,"Please enter a valid Return Pd","Input Error",
            JOptionPane.ERROR_MESSAGE);
        return;
      } catch (RemoteException ee) {
        JOptionPane.showMessageDialog(this,
                                      ee.getMessage() + "\n" +
                                      "Please check your network connection",
                                      "Server Connection Error",
                                      JOptionPane.ERROR_MESSAGE);
        return;
      } catch (InvalidRangeException ex) {
							System.out.println(ex.getMessage());
							ex.printStackTrace();
					return;
			}
    } else if (calcMode == groundMotionIdx) {
    	try {
            if (locationMode == BatchLocationBean.BAT_MODE) {
          	  Thread t = new Thread(new Runnable() {
          		  public void run() {
          			  ArrayList<Location> locations = locGuiBean.getBatchLocations();
          			  if(locations.size() > 1000) {
      						// We have an arbitrary 1,000 row limit.  Die if too many.
      						JOptionPane.showMessageDialog(null, "Batch mode is currently limited to 1,000 records " +
      								"at one time.\nPlease reduce the number of rows in your input file and " +
      								"try again.", "Too Many Records", JOptionPane.ERROR_MESSAGE);
      						return;
      					}
          	    	  try {
    	                dataGenerator.calcSingleValueFEX(locations, imt,
    	                		  locGuiBean.getOutputFile(), groundMotionVal,
    	                		  isLogInterpolation);
                    } catch (RemoteException ex) {
    	                ex.printStackTrace(System.err);
                    }
          	    	  application.setDataInWindow(getData());
          		  }
          	  });
          	  t.start();
            } else {
            	// Doing single location. Zip vs. Lat/Lng is handled separately, we are just going
            	// to use the currently computed hazard curve to compute the single value off it.
          	
          	if (!calcButtonClicked) hazCurveCalcButton_actionPerformed(e);
         		if (!calcButtonClicked) { //if call to hazCurvCalcButton exited abnormally
         			return;
         		}
         		
            	dataGenerator.calcSingleValueFEXUsingGroundMotion(
            			groundMotionVal, isLogInterpolation);
            	application.setDataInWindow(getData());
            }
          } catch(NumberFormatException eee){
            JOptionPane.showMessageDialog(this,"Please enter a valid Exceed Prob. "+
                                          "and Exposure Time","Input Error",
                JOptionPane.ERROR_MESSAGE);
            return;
          } catch (RemoteException ee) {
            JOptionPane.showMessageDialog(this,
                                          ee.getMessage() + "\n" +
                                          "Please check your network connection",
                                          "Server Connection Error",
                                          JOptionPane.ERROR_MESSAGE);
            return;
          }
    }
    
  }

}
