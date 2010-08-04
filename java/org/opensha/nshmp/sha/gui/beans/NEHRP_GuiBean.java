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
import org.opensha.nshmp.exceptions.LocationErrorException;
import org.opensha.nshmp.exceptions.ZipCodeErrorException;
import org.opensha.nshmp.sha.data.DataGenerator_NEHRP;
import org.opensha.nshmp.sha.data.api.DataGeneratorAPI_NEHRP;
import org.opensha.nshmp.sha.gui.api.ProbabilisticHazardApplicationAPI;
import org.opensha.nshmp.sha.gui.infoTools.GraphWindow;
import org.opensha.nshmp.sha.gui.infoTools.SiteCoefficientInfoWindow;
import org.opensha.nshmp.util.GlobalConstants;
import org.opensha.nshmp.util.LocationUtil;
import org.opensha.nshmp.util.RegionUtil;
import org.opensha.sha.gui.infoTools.ExceptionWindow;


/**
 * <p>Title:NEHRP_GuiBean</p>
 *
 * <p>Description: This option sets the parameter for the NEHRP analysis option.</p>
 * @author Ned Field, Nitin Gupta and E.V.Leyendecker
 * @version 1.0
 */
public class NEHRP_GuiBean
    extends JPanel implements ParameterChangeListener,
    AnalysisOptionsGuiBeanAPI {
  // First 7 digits of MD5('nehrp') in Hex.
  private static final long serialVersionUID = 0xEB31117;
  
  //Dataset selection Gui instance
  protected DataSetSelectionGuiBean datasetGui;
  protected BatchLocationBean locGuiBean;
  JSplitPane mainSplitPane = new JSplitPane();
  JSplitPane locationSplitPane = new JSplitPane();
  JSplitPane buttonsSplitPane = new JSplitPane();
  JPanel regionPanel = new JPanel();
  JPanel basicParamsPanel = new JPanel();
  JPanel responseSpectraButtonPanel = new JPanel();
  JButton ssButton = new JButton();
  JButton smSDButton = new JButton();
  Border border9 = BorderFactory.createLineBorder(new Color(80,80,140),1);
  TitledBorder responseSpecBorder = new TitledBorder(border9,
      "Response Spectra");

  TitledBorder basicParamBorder = new TitledBorder(border9, "Basic Parameters");
  TitledBorder regionBorder = new TitledBorder(border9,
                                               "Region and DataSet Selection");
  JButton mapSpecButton = new JButton();
  JButton smSpecButton = new JButton();
  JButton sdSpecButton = new JButton();
  JButton viewButton = new JButton();

	//some labels for the tooltips for the buttons.
	protected String mapSpecToolTip = "Calculate the MCE map spectrum for the "+
		"reference Site Class B based on Ss and S1.";
	protected String smSpecToolTip = "Calculate the site-modified specturm " +
		"for the selected Site Class based on Sms and Sm.1";
	protected String sdSpecToolTip = "Calculate the design spectrum for the " +
		"selected Site Class based on Sds and Sd1.";
	protected String viewToolTip = "View the graphs of the response spectra " +
		"for the Site Class B, the site-modified values.";
	protected String ssToolTip = "Calculate spectral accelerations for " +
		"the values of Ss and S1 for Site Class B.";
	protected String smSDToolTip = "Calculate the site-modified spectral " +
		"accelerations Sms and Sm1, and the design spectral accelerations " +
		"for 0.2 sec and 1.0 sec perioeds.";

	//some booleans to control when buttons have been clicked
	protected boolean ssButtonClicked = false;
	protected boolean smSDButtonClicked = false;
	protected boolean mapSpecButtonClicked = false;
	protected boolean smSpecButtonClicked = false;
	protected boolean sdSpecButtonClicked = false;

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

  protected DataGeneratorAPI_NEHRP dataGenerator = new DataGenerator_NEHRP();

  //site coeffiecient window instance
  SiteCoefficientInfoWindow siteCoefficientWindow;

  //instance of the application using this GUI bean
  protected ProbabilisticHazardApplicationAPI application;

  protected boolean mapSpectrumCalculated, smSpectrumCalculated,
  	sdSpectrumCalculated;
	
  protected String selectedRegion, selectedEdition, spectraType;
  protected boolean siteCoeffWindowShow = false;
	protected boolean viewSitePopUp = true;

  public NEHRP_GuiBean(ProbabilisticHazardApplicationAPI api) {
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
      createLocation();
      locationSplitPane.setDividerLocation(140);
      createGroundMotionParameter();
      jbInit();

    } catch (Exception exception) {
      exception.printStackTrace();
    }

    basicParamsPanel.add(groundMotionParamEditor,
                         new GridBagConstraints(0, 0, 2, 1, 1.0, 1.0
                                                , GridBagConstraints.NORTH,
                                                GridBagConstraints.HORIZONTAL,
                                                new Insets(4, 4, 4, 4), 0, 0));

    regionPanel.add(datasetGui.getDatasetSelectionEditor(),
                    new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
                                           , GridBagConstraints.CENTER,
                                           GridBagConstraints.BOTH,
                                           new Insets(4, 4, 4, 4), 0, 0));
    updateUI();

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
			"The parameter shown is the only selection available for new structures.");
    spectraType = (String) groundMotionParam.getValue();
  }

  protected ArrayList getSupportedSpectraTypes() {
    ArrayList<String> supportedSpectraTypes = new ArrayList<String>();
    if (selectedEdition.equals(GlobalConstants.NEHRP_2009)) {
    	supportedSpectraTypes.add(GlobalConstants.RTE_GROUND_MOTION);
    } else {
    	supportedSpectraTypes.add(GlobalConstants.MCE_GROUND_MOTION);
    }
    return supportedSpectraTypes;
  }

  protected void jbInit() throws Exception {
    this.setLayout(borderLayout1);
    mainSplitPane.setOrientation(JSplitPane.VERTICAL_SPLIT);
    locationSplitPane.setOrientation(JSplitPane.VERTICAL_SPLIT);
    buttonsSplitPane.setOrientation(JSplitPane.VERTICAL_SPLIT);
    basicParamsPanel.setLayout(gridBagLayout4);
    basicParamsPanel.setBorder(basicParamBorder);
    basicParamBorder.setTitleColor(Color.RED);
    ssButton.setText("   Calculate Ss & S1   ");
		ssButton.setToolTipText(ssToolTip);
    ssButton.addActionListener(new ActionListener() {
      public void actionPerformed(ActionEvent actionEvent) {
        ssButton_actionPerformed(actionEvent);
      }
    });


    /*
     * 07/29/08 -- EMM: The default is now 2007 which has a different process
     * and uses different text.
     */
    smSDButton.setText("Calculate SM & SD Values");
    //smSDButton.setText("Calculate SR and SD Values");
		smSDButton.setToolTipText(smSDToolTip);
    smSDButton.addActionListener(new ActionListener() {
      public void actionPerformed(ActionEvent actionEvent) {
        smSDButton_actionPerformed(actionEvent);
      }
    });
    responseSpectraButtonPanel.setBorder(responseSpecBorder);
    responseSpecBorder.setTitleColor(Color.RED);
    responseSpectraButtonPanel.setLayout(gridBagLayout3);

    /*
     *  08/13/08 -- EMM: Default is now 2009 which does not have this button. 
     */
	// mapSpecButton.setVisible(false); // 09/24/2008 -- EMM: Visible again for quick release.
    mapSpecButton.setText("      Map Spectrum      ");
	mapSpecButton.setToolTipText(mapSpecToolTip);
    mapSpecButton.addActionListener(new ActionListener() {
      public void actionPerformed(ActionEvent actionEvent) {
        mapSpecButton_actionPerformed(actionEvent);
      }
    });

    /*
     *  08/13/08 -- EMM: Default is now 2009 which is labeled differently.
     */
    smSpecButton.setText(" Site Modified Spectrum ");
    //smSpecButton.setText("       RTE Spectrum     ");
		smSpecButton.setToolTipText(smSpecToolTip);
    smSpecButton.addActionListener(new ActionListener() {
      public void actionPerformed(ActionEvent actionEvent) {
        smSpecButton_actionPerformed(actionEvent);
      }
    });


    sdSpecButton.setText("    Design Spectrum    ");
		sdSpecButton.setToolTipText(sdSpecToolTip);
    sdSpecButton.addActionListener(new ActionListener() {
      public void actionPerformed(ActionEvent actionEvent) {
        sdSpecButton_actionPerformed(actionEvent);
      }
    });


    viewButton.setText("       View Spectra       ");
		viewButton.setToolTipText(viewToolTip);
    viewButton.addActionListener(new ActionListener() {
      public void actionPerformed(ActionEvent actionEvent) {
        viewButton_actionPerformed(actionEvent);
      }
    });

    regionPanel.setBorder(regionBorder);
    regionBorder.setTitleColor(Color.RED);
    regionPanel.setLayout(gridBagLayout2);

    mainSplitPane.add(locationSplitPane, JSplitPane.TOP);
    mainSplitPane.add(buttonsSplitPane, JSplitPane.BOTTOM);
    locationSplitPane.add(regionPanel, JSplitPane.TOP);

    buttonsSplitPane.add(basicParamsPanel, JSplitPane.TOP);
    buttonsSplitPane.add(responseSpectraButtonPanel, JSplitPane.BOTTOM);

    responseSpectraButtonPanel.add(viewButton,
                                   new GridBagConstraints(1, 1, 1, 1, 0.0, 0.0
        , GridBagConstraints.CENTER, GridBagConstraints.NONE,
        new Insets(2, 0, 0, 2), 0, 0));
    responseSpectraButtonPanel.add(mapSpecButton,
                                   new GridBagConstraints(0, 0, 1, 1, 0.0, 0.0
        , GridBagConstraints.CENTER, GridBagConstraints.NONE,
        new Insets( 2, 0, 0, 2), 0, 0));
    responseSpectraButtonPanel.add(smSpecButton,
                                   new GridBagConstraints(1, 0, 1, 1, 0.0, 0.0
        , GridBagConstraints.CENTER, GridBagConstraints.NONE,
        new Insets( 2, 0, 0, 2), 0, 0));

    responseSpectraButtonPanel.add(sdSpecButton,
                                   new GridBagConstraints(0, 1, 1, 1, 0.0, 0.0
        , GridBagConstraints.CENTER, GridBagConstraints.NONE,
        new Insets( 2, 0, 0, 2), 0, 0));
    basicParamsPanel.add(ssButton, new GridBagConstraints(0, 1, 1, 1, 1.0, 1.0
        , GridBagConstraints.EAST, GridBagConstraints.NONE,
        new Insets(2, 2, 2, 2), 0, 0));
    basicParamsPanel.add(smSDButton,
                         new GridBagConstraints(1, 1, 1, 1, 1.0, 1.0
                                                , GridBagConstraints.WEST,
                                                GridBagConstraints.NONE,
                                                new Insets(2, 2, 2, 2), 0,
                                                0));

    this.add(mainSplitPane, java.awt.BorderLayout.CENTER);
    mainSplitPane.setDividerLocation(290);
    buttonsSplitPane.setDividerLocation(120);
    basicParamsPanel.setMinimumSize(new Dimension(0,0));
    regionPanel.setMinimumSize(new Dimension(0,0));
    responseSpectraButtonPanel.setMinimumSize(new Dimension(0,0));
    setButtonsEnabled(true);
  }

  protected void setButtonsEnabled(boolean enableButtons) {
    smSDButton.setEnabled(true);  //was (enableButtons) instead of static true
    mapSpecButton.setEnabled(true);
    smSpecButton.setEnabled(true);
    sdSpecButton.setEnabled(true);
    viewButton.setEnabled(true);  //was hardcoded 'false'
    siteCoeffWindowShow = false;
		viewSitePopUp = true;
    if (enableButtons == false) {
      mapSpectrumCalculated = smSpectrumCalculated = sdSpectrumCalculated = false;
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
   * Removes all the output from the window
   */
  public void clearData() {
    dataGenerator.clearData();
		setButtonsEnabled(false);
		resetButtons();
  }

	public void resetButtons() {
	  ssButtonClicked = false;
		smSDButtonClicked = false;
		mapSpecButtonClicked = false;
		smSpecButtonClicked = false;
		sdSpecButtonClicked = false;
  }

  /**
   * If GuiBean parameter is changed.
   * @param event ParameterChangeEvent
   */
  public void parameterChange(ParameterChangeEvent event) {
		siteCoefficientWindow = null; //So Fa/Fv/Class are reset when any parameter
																	//changes
    String paramName = event.getParameterName();

    if (paramName.equals(DataSetSelectionGuiBean.GEOGRAPHIC_REGION_SELECTION_PARAM_NAME)) {
      selectedRegion = datasetGui.getSelectedGeographicRegion();
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

      setButtonsEnabled(false);
		resetButtons();

		/*if (!locationVisible) {
			dataGenerator.setNoLocation();
    		smSDButton.setEnabled(false);  
    		mapSpecButton.setEnabled(false);
    		smSpecButton.setEnabled(false);
    		sdSpecButton.setEnabled(false);
    		viewButton.setEnabled(false); 
    		siteCoeffWindowShow = false;
		}*/
			
    }
    else if (paramName.equals(DataSetSelectionGuiBean.EDITION_PARAM_NAME)) {
      selectedEdition = datasetGui.getSelectedDataSetEdition();
      setButtonsEnabled(false);
      ArrayList supportedGroundMotion = getSupportedSpectraTypes();
      groundMotionParam = new StringParameter(GROUND_MOTION_PARAM_NAME,
                                              supportedGroundMotion,
                                              (String) supportedGroundMotion.get(
          0));
      groundMotionParamEditor.setParameter(groundMotionParam);
      groundMotionParamEditor.refreshParamEditor();

      /*
       * 07/29/08 -- EMM: The NEHRP 2007 editions uses different text for the
       * site modified values button. We have to make sure the text is correct.
       */
      if (selectedEdition.equals(GlobalConstants.NEHRP_2009)) {
    	  mapSpecButton.setVisible(false);
    	  smSpecButton.setText("       RTE Spectrum     ");
    	  smSDButton.setText("Calculate SR and SD Values");
      } else {
    	  mapSpecButton.setVisible(true);
    	  smSpecButton.setText(" Site Modified Spectrum ");
    	  smSDButton.setText("Calculate SM and SD Values");
      }
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
			resetButtons();
		/*if (!locationVisible) {
			dataGenerator.setNoLocation();
    		smSDButton.setEnabled(false);  
    		mapSpecButton.setEnabled(false);
    		smSpecButton.setEnabled(false);
    		sdSpecButton.setEnabled(false);
    		viewButton.setEnabled(false); 
    		siteCoeffWindowShow = false;
		}*/
    }
    else if (paramName.equals(BatchLocationBean.PARAM_LAT) ||
             paramName.equals(BatchLocationBean.PARAM_LON) ||
             paramName.equals(BatchLocationBean.PARAM_ZIP)) {
      setButtonsEnabled(false);
			resetButtons();
		/*if (!locationVisible) {
			dataGenerator.setNoLocation();
    		smSDButton.setEnabled(false);  
    		mapSpecButton.setEnabled(false);
    		smSpecButton.setEnabled(false);
    		sdSpecButton.setEnabled(false);
    		viewButton.setEnabled(false); 
    		siteCoeffWindowShow = false;
		}*/
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

      locationVisible = true;
    }
    else if (region == null) {
      locGuiBean.createNoLocationGUI();
      locationVisible = false;
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
        selectedEdition.equals(GlobalConstants.NEHRP_2003)) {

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

    //supportedEditionList.add(GlobalConstants.NEHRP_2009);
    supportedEditionList.add(GlobalConstants.NEHRP_2003);
    supportedEditionList.add(GlobalConstants.NEHRP_2000);
    supportedEditionList.add(GlobalConstants.NEHRP_1997);
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
        getSupportedGeographicalRegions(GlobalConstants.NEHRP);
    datasetGui.createGeographicRegionSelectionParameter(supportedRegionList);
    datasetGui.getGeographicRegionSelectionParameter().
        addParameterChangeListener(this);
    selectedRegion = datasetGui.getSelectedGeographicRegion();
  }

	/**
	 * Creates header information to include with all the datasets.
	 *
	 * @return metaData String - Representing the header info for all
	 * datasets.
	 */
	/*public String createMetaDataForPlots() {
		String metaData = "";
		metaData += selectedRegion + "\n";
		metaData += selectedEdition + "\n";
		try {
			if (locGuiBean.getLocationMode()) { //meaning Lat-Lon option is seleced.
				Location curLoc = locGuiBean.getSelectedLocation();
				metaData += "Latitude = " + curLoc.getLatitude() + "\n" +
										"Longitude = " + curLoc.getLongitude() + "\n";
			} else {
				metaData += "Zip Code = " + locGuiBean.getZipCode() + "\n";
			}
		} catch (Exception e) {
			//e.printStackTrace();
			return "";
		}
		System.out.println(metaData);
		return metaData;
	}
	*/	

  /**
   * Gets the SA Period and Values from datafiles
   */
  protected void getDataForSA_Period() throws ZipCodeErrorException,
  		LocationErrorException,RemoteException {

	dataGenerator.setSpectraType(spectraType);
	dataGenerator.setRegion(selectedRegion);
	dataGenerator.setEdition(selectedEdition);

	//doing the calculation if not territory and Location GUI is visible
	if (locationVisible && locGuiBean.hasLocation()) {
		int locationMode = locGuiBean.getLocationMode();
		if (locationMode == BatchLocationBean.GEO_MODE) {
			Location loc = locGuiBean.getSelectedLocation();
			double lat = loc.getLatitude();
			double lon = loc.getLongitude();
			dataGenerator.calculateSsS1(lat, lon);
		} else if (locationMode == BatchLocationBean.ZIP_MODE) {
			String zipCode = locGuiBean.getZipCode();
			dataGenerator.calculateSsS1(zipCode);
		} else if (locationMode == BatchLocationBean.BAT_MODE) {
			Thread t = new Thread(new Runnable() {
				public void run() {
					try {
						ArrayList<Location> locations = locGuiBean.getBatchLocations();
						if(locations.size() > 1000) {
							// We have an arbitrary 1,000 row limit.  Die if too many.
							JOptionPane.showMessageDialog(null, "Batch mode is currently limited to 1,000 records " +
									"at one time.\nPlease reduce the number of rows in your input file and " +
									"try again.", "Too Many Records", JOptionPane.ERROR_MESSAGE);
							return;
						}
						dataGenerator.calculateSsS1(locations, locGuiBean.getOutputFile());
						application.setDataInWindow(getData());
					} catch (NullPointerException npx) {
						System.err.println("Error");
					}
				}
			});
			t.start();
		}
	} else { // if territory and location Gui is not visible
		try {
			dataGenerator.calculateSsS1();
		} catch (RemoteException e) {
			JOptionPane.showMessageDialog(this, e.getMessage() + "\n" +
			"Please check your network connection", "Server Connection Error",
			JOptionPane.ERROR_MESSAGE);
			return;
		} // catch
	} //if
	}

	protected boolean locationReady() {
		boolean r = locGuiBean.hasLocation();
    	if (!r) {
	 		if ( !(selectedRegion.equals(GlobalConstants.CONTER_48_STATES) || //e.g. it is a PRVI area
				 	 selectedRegion.equals(GlobalConstants.ALASKA) ||
				 	 selectedRegion.equals(GlobalConstants.HAWAII)) &&  // AND
					 
					(selectedEdition.equals(GlobalConstants.NEHRP_1997) || //e.g it is an edtion with constant
				 	 selectedEdition.equals(GlobalConstants.NEHRP_2000) || //     spectral values
				 	 selectedEdition.equals(GlobalConstants.ASCE_1998) ||
				 	 selectedEdition.equals(GlobalConstants.ASCE_2002) ||
				 	 selectedEdition.equals(GlobalConstants.IBC_2000) ||
				 	 selectedEdition.equals(GlobalConstants.IBC_2003) ||
				 	 selectedEdition.equals(GlobalConstants.IBC_2004) ||
				 	 selectedEdition.equals(GlobalConstants.NFPA_2003)) ) {

				r = true; // location is ready 
			} else if ( selectedRegion.equals(GlobalConstants.GUAM) || 
						selectedRegion.equals(GlobalConstants.TUTUILA) ) {
				r = true; // location is ready
		   } else if (locGuiBean.getLocationMode() == BatchLocationBean.BAT_MODE &&
				      !locGuiBean.inputFileExists()) {
			   JOptionPane.showMessageDialog(this, "The input file was not found.",
					   "File Not Found", JOptionPane.ERROR_MESSAGE);
		   } else {
				JOptionPane.showMessageDialog(this, "Location not specified!\n" +
					"Please fill in the location parameter.", "Location Error",
           	JOptionPane.OK_OPTION);
			}
		}
		return r;
	}	

  protected void ssButton_actionPerformed(ActionEvent actionEvent) {
		ssButtonClicked = false;
		smSDButtonClicked = false;
		mapSpecButtonClicked = false;
		smSpecButtonClicked = false;
		sdSpecButtonClicked = false;
		if (locationReady() ) {
			ssButton_doActions();
		}
	}

	protected boolean ssButton_doActions() {
		if (ssButtonClicked) { return true; }
		try {
      getDataForSA_Period();
    }
    catch (ZipCodeErrorException ee) {
      JOptionPane.showMessageDialog(this, ee.getMessage(), "Zip Code Error",
                                    JOptionPane.OK_OPTION);
      return false;
    }
    catch (LocationErrorException ee) {
      JOptionPane.showMessageDialog(this, ee.getMessage(), "Location Error",
                                    JOptionPane.OK_OPTION);
      return false;
    }
    catch (RemoteException ee) {
      JOptionPane.showMessageDialog(this,
                                    ee.getMessage() + "\n" +
                                    "Please check your network connection",
                                    "Server Connection Error",
                                    JOptionPane.ERROR_MESSAGE);
      return false;
    }
    application.setDataInWindow(getData());
    ssButtonClicked = true;
		return ssButtonClicked;
    //setButtonsEnabled(true);
  }

  /**
   *
   * @return String
   */
  public String getData() {
    return dataGenerator.getDataInfo();
  }

	/**
	 * Shows a popup dialog asking user if they would like to change the site
	 * coefficients before continuing.  On cancel, nothing is done; on yes, the
	 * site coefficient window is shown.
	 */
	protected void showSitePopUp() {	
		String infoMsg = "The site coefficients have already\n" +
							"been calculated for this location.\n" +
							"Would you like to recalculate these now?";
		int answer = JOptionPane.showConfirmDialog(this, infoMsg, 
																	"Change Site Coefficients?",
																	JOptionPane.YES_NO_OPTION);
		if ( answer == JOptionPane.YES_OPTION ) {
			 siteCoeffWindowShow = false;
		} else {
			 siteCoeffWindowShow = true;
		}
	}
	
  /**
   * This function pops up the site coefficient window and allows user to set
   * Site coefficient for the calculation.
   */
  protected void setSiteCoeff(){
		if (ssButton_doActions()) {
    	if(!viewSitePopUp){showSitePopUp();}
			viewSitePopUp = false;
    	if(!siteCoeffWindowShow){
				//ssButtonClicked = false;
				smSDButtonClicked = false;
				mapSpecButtonClicked = false;
				smSpecButtonClicked = false;
				sdSpecButtonClicked = false;
      	//pops up the window that allows the user to set the Site Coefficient
      	if (siteCoefficientWindow == null) {
        	siteCoefficientWindow = new SiteCoefficientInfoWindow(dataGenerator.
            	getSs(),
            	dataGenerator.getSa(), dataGenerator.getSelectedSiteClass());
      	}
      	siteCoefficientWindow.setVisible(true);
	
      	dataGenerator.setFa(siteCoefficientWindow.getFa());
      	dataGenerator.setFv(siteCoefficientWindow.getFv());
      	dataGenerator.setSiteClass(siteCoefficientWindow.getSelectedSiteClass());
      	siteCoeffWindowShow = true;
    	}
		}
  }


  protected void smSDButton_actionPerformed(ActionEvent actionEvent) {
		smSDButtonClicked = false;
		mapSpecButtonClicked = false;
		smSpecButtonClicked = false;
		sdSpecButtonClicked = false;
		if (locationReady() ) {
			if(!usingBatchMode())
				setSiteCoeff();
			smSDButton_doActions();
		}
	}
  	
	protected boolean smSDButton_doActions() {
	  if (smSDButtonClicked) { return true; }
		if (usingBatchMode() || ssButton_doActions()) {
    	try {
    		if(usingBatchMode()) {
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
    	    			ArrayList<String> conditions = locGuiBean.getBatchSiteConditions();
    	    			String outfile = locGuiBean.getOutputFile();
    	    			dataGenerator.setSpectraType(spectraType);
    	    			dataGenerator.setRegion(selectedRegion);
    	    			dataGenerator.setEdition(selectedEdition);
	    	    		dataGenerator.calculateSMsSm1SDsSD1(locations,
	    	    					conditions, outfile);
    	    			application.setDataInWindow(getData());
    				}
    			});
    			t.start();
    		} else if(locGuiBean.getLocationMode()==BatchLocationBean.ZIP_MODE){ 
    			dataGenerator.calculateSMSsS1(selectedEdition, selectedRegion, 
    					locGuiBean.getZipCode(), 
    					dataGenerator.getSelectedSiteClass()
    				);
    			
    		
    			dataGenerator.calculateSDSsS1(selectedEdition, selectedRegion,
    					locGuiBean.getZipCode(),
    					dataGenerator.getSelectedSiteClass()
    				);
    			
    		} else {
				dataGenerator.calculateSMSsS1();
				dataGenerator.calculatedSDSsS1();
			}
    	}
    	catch (RemoteException e) {
      	JOptionPane.showMessageDialog(this,
                                    	e.getMessage() + "\n" +
                                    	"Please check your network connection",
                                    	"Server Connection Error",
                                    	JOptionPane.ERROR_MESSAGE);
      	return false;
    	}
    	application.setDataInWindow(getData());
			smSDButtonClicked = true;
		} else {
			smSDButtonClicked = false;
		}
		return smSDButtonClicked;
  }

  protected void mapSpecButton_actionPerformed(ActionEvent actionEvent) {
		mapSpecButtonClicked = false;
		smSpecButtonClicked = false;
		sdSpecButtonClicked = false;
		if (locationReady() ) {
			if(!usingBatchMode())
				setSiteCoeff();
				mapSpecButton_doActions();
		}
	}

	protected boolean mapSpecButton_doActions() {
	  if (mapSpecButtonClicked) { return true; }
		if (usingBatchMode() || smSDButton_doActions() ) {
			
			try {
				if(usingBatchMode()) {
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
			    			String outfile = locGuiBean.getOutputFile();
			    			dataGenerator.setSpectraType(spectraType);
			    			dataGenerator.setRegion(selectedRegion);
			    			dataGenerator.setEdition(selectedEdition);
			    			dataGenerator.calculateMapSpectrum(locations, outfile);
			    			application.setDataInWindow(getData());
						}
					});
					t.start();
				} else {
					dataGenerator.calculateMapSpectrum();
				}
    	}
    	catch (RemoteException e) {
      	JOptionPane.showMessageDialog(this,
                                    	e.getMessage() + "\n" +
                                    	"Please check your network connection",
                                    	"Server Connection Error",
                                    	JOptionPane.ERROR_MESSAGE);
      	return false;
    	}
	
    	application.setDataInWindow(getData());
    	if (!viewButton.isEnabled()) {
      	viewButton.setEnabled(true);
    	}
    	mapSpectrumCalculated = true;
			mapSpecButtonClicked = true;
		} else {
			mapSpecButtonClicked = false;
		}
		return mapSpecButtonClicked;
  }

  protected void smSpecButton_actionPerformed(ActionEvent actionEvent) {
		smSpecButtonClicked = false;
		sdSpecButtonClicked = false;
		if (locationReady()) {
			if(!usingBatchMode())
				setSiteCoeff();
			smSpecButton_doActions();
		}
	}

	protected boolean smSpecButton_doActions() {
	  if (smSpecButtonClicked) { return true; }
		if (usingBatchMode() || mapSpecButton_doActions()) { 
			try {
				if(usingBatchMode()) {
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
			    			ArrayList<String> conditions = locGuiBean.getBatchSiteConditions();
			    			String outfile = locGuiBean.getOutputFile();
			    			dataGenerator.setSpectraType(spectraType);
			    			dataGenerator.setRegion(selectedRegion);
			    			dataGenerator.setEdition(selectedEdition);
			    			dataGenerator.calculateSMSpectrum(locations, conditions, outfile);
			    			application.setDataInWindow(getData());
						}
					});
	    			t.start();
				} else {
					dataGenerator.calculateSMSpectrum();
				}
    	}
    	catch (RemoteException e) {
      	JOptionPane.showMessageDialog(this,
                                    e.getMessage() + "\n" +
                                    "Please check your network connection",
                                    "Server Connection Error",
                                    JOptionPane.ERROR_MESSAGE);
      	return false;
    	}

    	application.setDataInWindow(getData());
    	if (!viewButton.isEnabled()) {
      	viewButton.setEnabled(true);
    	}
    	smSpectrumCalculated = true;
			smSpecButtonClicked = true;
		} else { 
			smSpecButtonClicked = false;
		}
		return smSpecButtonClicked;
  }

  protected void sdSpecButton_actionPerformed(ActionEvent actionEvent) {
		sdSpecButtonClicked = false;
		if (locationReady()) {
			if(!usingBatchMode())
				setSiteCoeff();
			sdSpecButton_doActions();
		}
	}
	
	protected boolean sdSpecButton_doActions() {
		if (sdSpecButtonClicked) { return true; }
    if (usingBatchMode() || smSpecButton_doActions()) {
		try {
			if(usingBatchMode()) {
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
		    			ArrayList<String> conditions = locGuiBean.getBatchSiteConditions();
		    			String outfile = locGuiBean.getOutputFile();
		    			dataGenerator.setSpectraType(spectraType);
		    			dataGenerator.setRegion(selectedRegion);
		    			dataGenerator.setEdition(selectedEdition);
		    			dataGenerator.calculateSDSpectrum(locations, conditions, outfile);
		    			application.setDataInWindow(getData());
					}
				});
    			t.start();
			} else {
				dataGenerator.calculateSDSpectrum();
			}
    }
    catch (RemoteException e) {
      JOptionPane.showMessageDialog(this,
                                    e.getMessage() + "\n" +
                                    "Please check your network connection",
                                    "Server Connection Error",
                                    JOptionPane.ERROR_MESSAGE);
      return false;
    }

    application.setDataInWindow(getData());
    if (!viewButton.isEnabled()) {
      viewButton.setEnabled(true);
    }
    sdSpectrumCalculated = true;
		sdSpecButtonClicked = true;
		} else {
			sdSpecButtonClicked = false;
		}
		return sdSpecButtonClicked;
  }

  protected void viewButton_actionPerformed(ActionEvent actionEvent) {
		if (locationReady()) {
			if(!usingBatchMode()) {
				setSiteCoeff();
				if (sdSpecButton_doActions()) {
				ArrayList functions = dataGenerator.getFunctionsToPlotForSA(
	      	mapSpectrumCalculated, sdSpectrumCalculated, smSpectrumCalculated);
	    		GraphWindow window = new GraphWindow(functions);
	    		window.setVisible(true);
				}
			} else {	
				JOptionPane.showMessageDialog(null, "Due to the nature of using a batch output " +
						"this feature is not currently enabled.\nPlease view the Excel Output file " +
						"to create your own plots.", "Option Not Available", JOptionPane.INFORMATION_MESSAGE);
			}
		}
  }

  private boolean usingBatchMode() {
	  return locGuiBean.getLocationMode() == BatchLocationBean.BAT_MODE;
  }
}
