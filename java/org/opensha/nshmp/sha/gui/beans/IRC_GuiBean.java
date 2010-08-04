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
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.rmi.RemoteException;
import java.util.ArrayList;
import java.util.ListIterator;

import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JSplitPane;
import javax.swing.border.Border;
import javax.swing.border.TitledBorder;

import org.opensha.commons.exceptions.RegionConstraintException;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.Region;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ConstrainedStringParameterEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.nshmp.exceptions.AnalysisOptionNotSupportedException;
import org.opensha.nshmp.exceptions.ZipCodeErrorException;
import org.opensha.nshmp.sha.data.DataGenerator_IRC;
import org.opensha.nshmp.sha.data.api.DataGeneratorAPI_NEHRP;
import org.opensha.nshmp.sha.gui.api.ProbabilisticHazardApplicationAPI;
import org.opensha.nshmp.util.GlobalConstants;
import org.opensha.nshmp.util.LocationUtil;
import org.opensha.nshmp.util.RegionUtil;
import org.opensha.sha.gui.infoTools.ExceptionWindow;




/**
 * <p>Title: IRC_GuiBean</p>
 *
 * <p>Description: This class creates the GUI interface for the International
 * Residential Code.</p>
 * @author Ned Field, Nitin Gupta and E.V.Leyendecker
 * @version 1.0
 */


public class IRC_GuiBean
    extends JPanel implements ParameterChangeListener,
    AnalysisOptionsGuiBeanAPI {

	private static final long serialVersionUID = 0x407BDEC;
	
  //Dataset selection Gui instance
  protected DataSetSelectionGuiBean datasetGui;
  protected BatchLocationBean locGuiBean;
  JSplitPane mainSplitPane = new JSplitPane();
  JSplitPane locationSplitPane = new JSplitPane();
  JPanel regionPanel = new JPanel();
  JPanel basicParamsPanel = new JPanel();

  JButton residentialSiteCategoryButton = new JButton();

  Border border9 = BorderFactory.createLineBorder(new Color(80,80,140),1);
  TitledBorder basicParamBorder = new TitledBorder(border9,
      "Calculate IRC site Values");
  TitledBorder regionBorder = new TitledBorder(border9,
                                               "Region and DataSet Selection");

  GridBagLayout gridBagLayout1 = new GridBagLayout();
  GridBagLayout gridBagLayout2 = new GridBagLayout();
  GridBagLayout gridBagLayout3 = new GridBagLayout();

  GridBagLayout gridBagLayout4 = new GridBagLayout();
  BorderLayout borderLayout1 = new BorderLayout();

  protected boolean locationVisible;

  //creating the Ground Motion selection parameter
  protected StringParameter groundMotionParam;
  protected ConstrainedStringParameterEditor groundMotionParamEditor;
  protected static final String GROUND_MOTION_PARAM_NAME = "Ground Motion";

  protected DataGeneratorAPI_NEHRP dataGenerator = new DataGenerator_IRC();

  //instance of the application using this GUI bean
  protected ProbabilisticHazardApplicationAPI application;

  protected String selectedRegion, selectedEdition, spectraType;

  public IRC_GuiBean(ProbabilisticHazardApplicationAPI api) {
    application = api;
    try {

      datasetGui = new DataSetSelectionGuiBean();
      locGuiBean = new BatchLocationBean();
      try {
        createGeographicRegionSelectionParameter();
      }
      catch (AnalysisOptionNotSupportedException ex) {
        JOptionPane.showMessageDialog(this, ex.getMessage(),
                                      "Analysis Option selection error",
                                      JOptionPane.ERROR_MESSAGE);
        return;
      }
      createEditionSelectionParameter();
      //creating the datasetEditor to show the geographic region and edition dataset.
      datasetGui.createDataSetEditor();
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
      locationSplitPane.add((Component) locGuiBean.getVisualization(GuiBeanAPI.EMBED), JSplitPane.BOTTOM);
      createGroundMotionParameter();
      jbInit();
    }
    catch (Exception exception) {
      exception.printStackTrace();
    }

    basicParamsPanel.add(groundMotionParamEditor,
                         new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
                                                , GridBagConstraints.NORTH,
                                                GridBagConstraints.HORIZONTAL,
                                                new Insets(2, 2, 2, 2), 0, 0));

    regionPanel.add(datasetGui.getDatasetSelectionEditor(),
                    new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
                                           , GridBagConstraints.CENTER,
                                           GridBagConstraints.BOTH,
                                           new Insets(0, 0, 0, 0), 0, 0));
    this.updateUI();
  }

  protected void createGroundMotionParameter() {

    ArrayList supportedGroundMotion = getSupportedSpectraTypes();
    groundMotionParam = new StringParameter(GROUND_MOTION_PARAM_NAME,
                                            supportedGroundMotion,
                                            (String) supportedGroundMotion.get(
        0));
    groundMotionParamEditor = new ConstrainedStringParameterEditor(
        groundMotionParam);
		groundMotionParamEditor.getValueEditor().setToolTipText(
			"The parameter shown is the only selection available for " +
			"new structures.");

    spectraType = (String) groundMotionParam.getValue();
  }

  protected ArrayList getSupportedSpectraTypes() {
    ArrayList<String> supportedSpectraTypes = new ArrayList<String>();
    supportedSpectraTypes.add(GlobalConstants.MCE_GROUND_MOTION);
    return supportedSpectraTypes;
  }

  protected void jbInit() throws Exception {
    this.setLayout(borderLayout1);
    mainSplitPane.setOrientation(JSplitPane.VERTICAL_SPLIT);
    locationSplitPane.setOrientation(JSplitPane.VERTICAL_SPLIT);

    basicParamsPanel.setLayout(gridBagLayout4);
    basicParamsPanel.setBorder(basicParamBorder);
    basicParamBorder.setTitleColor(Color.RED);

    residentialSiteCategoryButton.setText(
		"Seismic Design Category");
		residentialSiteCategoryButton.setToolTipText(
			"View the graphs of the response spectra for the Site Class B, " +
			"the site-modified values, and the design values.");
        //"Calc site coeff.");
    residentialSiteCategoryButton.addActionListener(new ActionListener() {
      public void actionPerformed(ActionEvent actionEvent) {
        residentialSiteCategoryButton_actionPerformed(actionEvent);
      }
    });

    regionPanel.setBorder(regionBorder);
    regionBorder.setTitleColor(Color.RED);
    regionPanel.setLayout(gridBagLayout2);

    mainSplitPane.add(locationSplitPane, JSplitPane.TOP);
    mainSplitPane.add(basicParamsPanel, JSplitPane.BOTTOM);
    locationSplitPane.add(regionPanel, JSplitPane.TOP);

    basicParamsPanel.add(residentialSiteCategoryButton,
                         new GridBagConstraints(0, 1, 1, 1, 1.0, 1.0
                                                , GridBagConstraints.NORTH,
                                                GridBagConstraints.NONE,
                                                new Insets(4, 60, 4,90), 0, 0));
    this.add(mainSplitPane, java.awt.BorderLayout.CENTER);
    mainSplitPane.setDividerLocation(340);
    locationSplitPane.setDividerLocation(180);
  }

  /**
   * Removes all the output from the window
   */
  public void clearData() {
    dataGenerator.clearData();

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
   * If GuiBean parameter is changed.
   * @param event ParameterChangeEvent
   */
  public void parameterChange(ParameterChangeEvent event) {

    String paramName = event.getParameterName();

	if (paramName.equals(DataSetSelectionGuiBean.GEOGRAPHIC_REGION_SELECTION_PARAM_NAME)) {
      selectedRegion = datasetGui.getSelectedGeographicRegion();
      createEditionSelectionParameter();
      try {
        createLocation();
      } catch (RegionConstraintException ex) {
        ExceptionWindow bugWindow = new ExceptionWindow(this, ex.getStackTrace(),
            "Exception occured while initializing the  region parameters in NSHMP application." +
            "Parameters values have not been set yet.");
        bugWindow.setVisible(true);
        bugWindow.pack();
      }
	} else if (paramName.equals(DataSetSelectionGuiBean.EDITION_PARAM_NAME)) {
      selectedEdition = datasetGui.getSelectedDataSetEdition();
      try {
        createLocation();
      } catch (RegionConstraintException ex) {
        ExceptionWindow bugWindow = new ExceptionWindow(this, ex.getStackTrace(),
            "Exception occured while initializing the  region parameters in NSHMP application." +
            "Parameters values have not been set yet.");
        bugWindow.setVisible(true);
        bugWindow.pack();

      }
    }
	if (!locationVisible) {
		dataGenerator.setNoLocation();
	}
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
  protected void createLocation() throws RegionConstraintException {
	  Region region = getRegionConstraint();
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
   *
   * @return RectangularGeographicRegion
   */
  protected Region getRegionConstraint() throws
      RegionConstraintException {

    if (selectedRegion.equals(GlobalConstants.CONTER_48_STATES) ||
        selectedRegion.equals(GlobalConstants.ALASKA) ||
        selectedRegion.equals(GlobalConstants.HAWAII) ||
		  selectedEdition.equals(GlobalConstants.IRC_2006)) {

      return RegionUtil.getRegionConstraint(selectedRegion);
    }

    return null;
  }

  /**
   * Creates the Parameter that allows user to select  the Editions based on the
   * selected Analysis and choosen geographic region.
   */
  protected void createEditionSelectionParameter() {

    ArrayList<String> supportedEditionList = new ArrayList<String>();

/*	if (!selectedRegion.equals(GlobalConstants.ALASKA) &&
        !selectedRegion.equals(GlobalConstants.HAWAII)) {
      supportedEditionList.add(GlobalConstants.IRC_2006);
      supportedEditionList.add(GlobalConstants.IRC_2004);
   } */
	if (selectedRegion.equals(GlobalConstants.CONTER_48_STATES) ||
			selectedRegion.equals(GlobalConstants.ALASKA) ||
	 	  	selectedRegion.equals(GlobalConstants.HAWAII)) {
		supportedEditionList.add(GlobalConstants.IRC_2006);
		supportedEditionList.add(GlobalConstants.IRC_2004);
  		supportedEditionList.add(GlobalConstants.IRC_2003);
  		supportedEditionList.add(GlobalConstants.IRC_2000);
	} else {
    supportedEditionList.add(GlobalConstants.IRC_2006);
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
  protected void createGeographicRegionSelectionParameter() throws
      AnalysisOptionNotSupportedException {

    ArrayList supportedRegionList = RegionUtil.
        getSupportedGeographicalRegions(GlobalConstants.INTL_RESIDENTIAL_CODE);
    datasetGui.createGeographicRegionSelectionParameter(supportedRegionList);
    datasetGui.getGeographicRegionSelectionParameter().
        addParameterChangeListener(this);
    selectedRegion = datasetGui.getSelectedGeographicRegion();
  }

  /**
   * Gets the SA Period and Values from datafiles
   */
  protected void getDataForSA_Period() {

    dataGenerator.setSpectraType(spectraType);
    dataGenerator.setRegion(selectedRegion);
    dataGenerator.setEdition(selectedEdition);

    //doing the calculation if not territory and Location GUI is visible
    if (locationVisible) {
    	int locationMode = locGuiBean.getLocationMode();
      if (locationMode == BatchLocationBean.GEO_MODE) {
        try {
          Location loc = locGuiBean.getSelectedLocation();
          double lat = loc.getLatitude();
          double lon = loc.getLongitude();
          dataGenerator.calculateSsS1(lat, lon);
        } catch (RemoteException e) {
          JOptionPane.showMessageDialog(this,
                                        e.getMessage() + "\n" +
                                        "Please check your network connection",
                                        "Server Connection Error",
                                        JOptionPane.ERROR_MESSAGE);
          return;
        }

      } else if(locationMode == BatchLocationBean.ZIP_MODE) {
        try {
          String zipCode = locGuiBean.getZipCode();
          dataGenerator.calculateSsS1(zipCode);
        }
        catch (ZipCodeErrorException e) {
          JOptionPane.showMessageDialog(this, e.getMessage(), "Zip Code Error",
                                        JOptionPane.OK_OPTION);
          return;
        } catch (RemoteException e) {
          JOptionPane.showMessageDialog(this,
                                        e.getMessage() + "\n" +
                                        "Please check your network connection",
                                        "Server Connection Error",
                                        JOptionPane.ERROR_MESSAGE);
          return;
        }
      } else if (locationMode == BatchLocationBean.BAT_MODE) {
    	  ArrayList<Location> locations = locGuiBean.getBatchLocations();
    	  if(locations.size() > 1000) {
				// We have an arbitrary 1,000 row limit.  Die if too many.
				JOptionPane.showMessageDialog(null, "Batch mode is currently limited to 1,000 records " +
						"at one time.\nPlease reduce the number of rows in your input file and " +
						"try again.", "Too Many Records", JOptionPane.ERROR_MESSAGE);
				return;
			}
    	  String outFile = locGuiBean.getOutputFile();
    	  dataGenerator.calculateSsS1(locations, outFile);
      }
    } else { // if territory and location Gui is not visible
      try {
        dataGenerator.calculateSsS1();
      }
      catch (RemoteException e) {
        JOptionPane.showMessageDialog(this,
                                      e.getMessage() + "\n" +
                                      "Please check your network connection",
                                      "Server Connection Error",
                                      JOptionPane.ERROR_MESSAGE);
        return;
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

  protected void residentialSiteCategoryButton_actionPerformed(ActionEvent
      actionEvent) {
	Thread t = new Thread(new Runnable() {
		public void run() {
		    getDataForSA_Period();
		    application.setDataInWindow(getData());
		}
	});
	t.start();
  }
}
