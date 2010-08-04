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

import java.awt.Color;
import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

import javax.swing.BorderFactory;
import javax.swing.ButtonGroup;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JRadioButton;
import javax.swing.JTextArea;
import javax.swing.border.Border;
import javax.swing.border.TitledBorder;

import org.opensha.commons.geo.Location;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterConstraintAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ConstrainedDoubleParameterEditor;
import org.opensha.commons.param.editor.StringParameterEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeFailEvent;
import org.opensha.commons.param.event.ParameterChangeFailListener;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.nshmp.exceptions.LocationErrorException;

/**
 * <p>Title: LocationGuiBean</p>
 *
 * <p>Description: This gui allows user to select location.</p>
 *
 * @author not attributable
 * @version 1.0
 */
public class LocationGuiBean
    extends JPanel implements ParameterChangeListener,
    ParameterChangeFailListener {


  public static final String ZIP_CODE_PARAM_NAME = "5-digit Zip Code";
  public static final String LAT_PARAM_NAME = "Latitude";
  public static final String LON_PARAM_NAME = "Longitude";



  Border border9 = BorderFactory.createLineBorder(new Color(80,80,140),1);
  TitledBorder locationBorder = new TitledBorder(border9,
                                                 "Select Site Location");

  private static final String DEFAULT_ZIP_CODE = "91104";
  private static final double DEFAULT_LAT = 34.1670;
  private static final double DEFAULT_LON = -118.27;

  private ParameterList parameterList;
  private GridBagLayout gridBagLayout1 = new GridBagLayout();


  //ZipCode, Lat, Lon editor
  private StringParameterEditor zipCodeEditor;
  private ConstrainedDoubleParameterEditor latEditor;
  private ConstrainedDoubleParameterEditor lonEditor;
  //private JLabel noLocationSupportedLabel = new JLabel("Calculations are constant across this region\nso no specific location needs to be specified.\nClick the calculate button below to view the data for this region.") ;
  private JTextArea noLocationSupportedText = new JTextArea("Spectral values are constant for this region.\n\nClick the button below to view data for all\nlocations within this region.");

  private JPanel locationPanel = new JPanel();
  private JPanel noLocationPanel = new JPanel();

	private String latLonToolTip = "Click to locate site by latitude-longitude";
	private String zipCodeToolTip = "Click to locate site by Zip Code";
  private JRadioButton latLonButton = new JRadioButton("Lat-Lon (Recommended)");
  private JRadioButton zipCodeButton = new JRadioButton("Zip-Code");

  //Label to show the Lat and Lon Constraints
  private JLabel latConstraintsLabel;
  private JLabel lonConstraintsLabel;

  private boolean latLonSelected = true;

  private ButtonGroup buttonGroup = new ButtonGroup();

  public LocationGuiBean() {

    try {
      jbInit();
    }
    catch (Exception ex) {
      ex.printStackTrace();
    }
  }

  /**
   * Returns the Location object
   * @return Location
   */
  public Location getSelectedLocation() throws LocationErrorException {
    Double latObj = (Double) parameterList.getParameter(LAT_PARAM_NAME).
        getValue();
    Double lonObj = (Double) parameterList.getParameter(LON_PARAM_NAME).
        getValue();

    if (latObj == null || lonObj == null) {
      throw new LocationErrorException(
          "Location not specified!\nPlease fill in the location parameter.");
    }
    else {
      double lat = latObj.doubleValue();
      double lon = lonObj.doubleValue();
      return new Location(lat, lon);
    }
  }

  /**
   * Returns the parameters constituting the location gui bean.
   * @return ParameterList
   */
  public ParameterList getLocationParameters() {
    return parameterList;
  }

  /**
   * Returns true if user has choosen to set the location using the Lat-Lon.
   * @return boolean
   */
  public boolean getLocationMode() {
    return latLonSelected;
  }


	public boolean hasLocation() {
		boolean r = true;
		try {
			if (getLocationMode()) {
				getSelectedLocation();
			} else {
				getZipCode();
			}
		} catch (Exception e) {
			r = false;
		} 

		return r;
	}
	
  /**
   * Returns zip code
   * @return String
   */
  public String getZipCode() throws LocationErrorException {

    String zipCode = (String) parameterList.getParameter(ZIP_CODE_PARAM_NAME).
        getValue();

    if (zipCode == null) {
      throw new LocationErrorException(
          "Zip Code not specified!\nPlease fill in the valid location.");
    }

    return zipCode;
  }



  /**
   * This function is called whenever location setting are not supported by the
   * selected Region.
   */
  public  void createNoLocationGUI(){
    this.removeAll();
    this.add(noLocationPanel,
             new GridBagConstraints(0, 0, 2, 2, 1.0, 1.0
                                    , GridBagConstraints.CENTER,
                                    GridBagConstraints.BOTH,
                                    new Insets(0, 0, 0, 0), 0, 0));
    this.updateUI();
  }


  /**
   *
   */
  public void createLocationGUI(double minLat, double maxLat, double minLon,
                                double maxLon, boolean isZipCodeSupported) {


    DoubleParameter latParam = new DoubleParameter(LAT_PARAM_NAME, minLat,
        maxLat, "Degrees");
    DoubleParameter lonParam = new DoubleParameter(LON_PARAM_NAME, minLon,
        maxLon, "Degrees");


  //removing the existing panel from the gui.
    this.removeAll();
    //remove the lat,lon and Zip code editors from the parameters, as we will be
    //creating new editors with new constraints,whenever this function is called.
    if(parameterList !=null){
      locationPanel.remove(latEditor);
      locationPanel.remove(lonEditor);
      locationPanel.remove(latConstraintsLabel);
      locationPanel.remove(lonConstraintsLabel);
      if (parameterList.containsParameter(ZIP_CODE_PARAM_NAME)) {
        locationPanel.remove(zipCodeEditor);
      }
    }

    //add the zip code in the location mode selection only if it is supported.
    createLocationModeParam(isZipCodeSupported);

    parameterList = new ParameterList();
    parameterList.addParameter(latParam);
    parameterList.addParameter(lonParam);
    latParam.addParameterChangeFailListener(this);
    lonParam.addParameterChangeFailListener(this);
    try {

      latEditor = new ConstrainedDoubleParameterEditor(latParam);
      lonEditor = new ConstrainedDoubleParameterEditor(lonParam);

      locationPanel.add(latEditor, new GridBagConstraints(0, 1, 1, 1, 1.0, 1.0
          , GridBagConstraints.NORTH, GridBagConstraints.WEST,
          new Insets(1, -5, 1, 40), 0, 0));
      latConstraintsLabel = new JLabel("("+minLat+","+maxLat+")");
      latConstraintsLabel.setForeground(new Color(80,80,133));
      locationPanel.add(latConstraintsLabel, new GridBagConstraints(0, 2, 1, 1, 1.0, 1.0
          , GridBagConstraints.NORTH, GridBagConstraints.WEST,
          new Insets(1, -5, 1, 40), 0, 0));

      locationPanel.add(lonEditor, new GridBagConstraints(1, 1, 1, 1, 1.0, 1.0
          , GridBagConstraints.NORTH, GridBagConstraints.WEST,
          new Insets(1, 10, 1, 20), 0, 0));

      lonConstraintsLabel = new JLabel("(" + minLon + "," + maxLon + ")");
      lonConstraintsLabel.setForeground(new Color(80,80,133));
      locationPanel.add(lonConstraintsLabel,
                        new GridBagConstraints(1, 2, 1, 1, 1.0, 1.0
                                               , GridBagConstraints.NORTH,
                                               GridBagConstraints.WEST,
                                               new Insets(1, 10, 1, 20), 0, 0));

    }
    catch (Exception e) {
      e.printStackTrace();
    }

    StringParameter zipParam = null;
    if (isZipCodeSupported) {
      zipParam = new StringParameter(ZIP_CODE_PARAM_NAME, "");
      zipParam.addParameterChangeListener(this);
      parameterList.addParameter(zipParam);
      try{
        zipCodeEditor = new StringParameterEditor(zipParam);
        locationPanel.add(zipCodeEditor, new GridBagConstraints(0, 1, 2, 1, 1.0, 1.0
          , GridBagConstraints.NORTH, GridBagConstraints.BOTH,
          new Insets(1, 1, 1, 1), 0, 0));
      }catch(Exception e){
        e.printStackTrace();
      }
    }
    buttonGroup.setSelected(latLonButton.getModel(), true);
    latLonSelected = true;
    this.add(locationPanel,
             new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
                                    , GridBagConstraints.CENTER,
                                    GridBagConstraints.BOTH,
                                    new Insets(2, 2, 2, 2), 0, 0));

    locationPanel.setMinimumSize(new Dimension(0,0));
    setVisibleParameters();
    this.updateUI();
  }

  /**
   * Creates the LocationMode selection parameter by checking if
   * Zip code is supported by selected geographic region for the selected data edition.
   */
  private void createLocationModeParam(boolean showZipCodeOption) {
    if (showZipCodeOption)
      zipCodeButton.setEnabled(true);
    else
      zipCodeButton.setEnabled(false);
  }

  /**
   * If user changes the location selection mode.
   * @param event ParameterChangeEvent
   */
  public void parameterChange(ParameterChangeEvent event) {
    String paramName = event.getParameterName();

    if (paramName.equals(ZIP_CODE_PARAM_NAME)) {
      try {
        String zip = (String) parameterList.getParameter(ZIP_CODE_PARAM_NAME).
            getValue();
        if (zip.length() != 5) {
          throw new RuntimeException(
              "Please enter valid 5 digit numeric zip code");
        }
        long zipCode = Long.parseLong(zip);
      }
      catch (NumberFormatException e) {
        JOptionPane.showMessageDialog(this,
            "Please enter valid 5 digit numeric zip code", "Zip Code Error",
                                      JOptionPane.ERROR_MESSAGE);
      }
      catch (RuntimeException e) {
        JOptionPane.showMessageDialog(this, e.getMessage(), "Zip Code Error",
                                      JOptionPane.ERROR_MESSAGE);
      }
    }
    this.updateUI();
  }

  public void parameterChangeFailed(ParameterChangeFailEvent event) {

    StringBuffer b = new StringBuffer();

    ParameterAPI param = (ParameterAPI) event.getSource();
    Object oldValue = event.getOldValue();
    String oldValueStr = null;
    if (oldValue != null) {
      oldValueStr = oldValue.toString();
    }

    String badValueStr = event.getBadValue().toString();
    String name = param.getName();

    //if Lat and Lon parameter constraints are violated
    if (!name.equals(ZIP_CODE_PARAM_NAME)) {
      ParameterConstraintAPI constraint = param.getConstraint();
      b.append("The value ");
      b.append(badValueStr);
      b.append(" is not permitted for '");
      b.append(name);
      b.append("'.\n");
      b.append("Resetting to ");
      if (oldValueStr != null) {
        b.append(oldValueStr);
      }
      else {
        b.append("Null");
      }
      b.append(". The constraints are: \n");
      b.append(constraint.toString());

      JOptionPane.showMessageDialog(
          this, b.toString(),
          "Cannot Change Value", JOptionPane.INFORMATION_MESSAGE
          );
    }
  }

  /*
   * Makes the parameter visible based on the choice of location selection made by the user
   */
  private void setVisibleParameters() {


    if (parameterList.containsParameter(ZIP_CODE_PARAM_NAME))
      zipCodeEditor.setVisible(!latLonSelected);

    lonEditor.setVisible(latLonSelected);
    latEditor.setVisible(latLonSelected);
    latConstraintsLabel.setVisible(latLonSelected);
    lonConstraintsLabel.setVisible(latLonSelected);
  }

  private void jbInit() throws Exception {
    this.setLayout(gridBagLayout1);
    this.setBorder(locationBorder);
    locationBorder.setTitleColor(Color.RED);
    locationPanel.setLayout(gridBagLayout1);
    this.add(locationPanel,
             new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
                                    , GridBagConstraints.CENTER,
                                    GridBagConstraints.BOTH,
                                    new Insets(4, 4, 4, 4), 0, 0));
    noLocationPanel.setLayout(gridBagLayout1);
    //noLocationPanel.add(noLocationSupportedLabel,
                        //new GridBagConstraints(0, 0, 2, 2, 1.0, 1.0
                                               //, GridBagConstraints.CENTER,
                                               //GridBagConstraints.BOTH,
                                               //new Insets(0, 0, 0, 0), 0, 0));
	noLocationPanel.add(noLocationSupportedText,
							new GridBagConstraints(0, 0, 2, 2, 1.0, 1.0,
														GridBagConstraints.CENTER,
														GridBagConstraints.BOTH,
														new Insets(0, 0, 0, 0), 0, 0));
	
	noLocationSupportedText.setBackground(new Color(240, 240, 240));
	noLocationSupportedText.setEditable(false);

    locationPanel.add(latLonButton, new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
        , GridBagConstraints.NORTH, GridBagConstraints.WEST,
        new Insets(1, -10, 1, 20), 0, 0));
    locationPanel.add(zipCodeButton,
                      new GridBagConstraints(1, 0, 1, 1, 1.0, 1.0
                                             , GridBagConstraints.NORTH, GridBagConstraints.WEST,
                                             new Insets(1, -10, 1, 25), 0, 0));
		
		latLonButton.setToolTipText(latLonToolTip);
    latLonButton.addActionListener(new ActionListener() {
      public void actionPerformed(ActionEvent actionEvent) {
        latLonButton_actionPerformed(actionEvent);
      }
    });
		zipCodeButton.setToolTipText(zipCodeToolTip);
    zipCodeButton.addActionListener(new ActionListener() {
      public void actionPerformed(ActionEvent actionEvent) {
        zipCodeButton_actionPerformed(actionEvent);
      }
    });

    buttonGroup.add(latLonButton);
    buttonGroup.add(zipCodeButton);
    buttonGroup.setSelected(latLonButton.getModel(), true);

  }


  private void latLonButton_actionPerformed(ActionEvent e){
    latLonSelected = true;
    this.setVisibleParameters();
  }

  private void zipCodeButton_actionPerformed(ActionEvent e){
    latLonSelected = false;
    this.setVisibleParameters();
  }

}
