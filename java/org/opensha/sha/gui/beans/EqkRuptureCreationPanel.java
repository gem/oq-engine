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

package org.opensha.sha.gui.beans;


import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.util.ArrayList;
import java.util.ListIterator;

import javax.swing.JPanel;

import org.opensha.commons.geo.Location;
import org.opensha.commons.param.BooleanParameter;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.LocationParameter;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ParameterEditor;
import org.opensha.commons.param.editor.ParameterListEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;
import org.opensha.sha.faultSurface.PointSurface;
import org.opensha.sha.param.SimpleFaultParameter;

/**
 * <p>Title: EqkRuptureCreationPanel</p>
 * <p>Description: </p>
 * @author : Ned Field, Nitin Gupta and Vipin Gupta
 * @version 1.0
 */

public class EqkRuptureCreationPanel
    extends JPanel implements EqkRupSelectorGuiBeanAPI, ParameterChangeListener {

  // mag parameter stuff
  public final static String MAG_PARAM_NAME = "Magnitude";
  private final static String MAG_PARAM_INFO = "The  magnitude of the rupture";
  private final static String MAG_PARAM_UNITS = null;
  private Double MAG_PARAM_MIN = new Double(0);
  private Double MAG_PARAM_MAX = new Double(10);
  private Double MAG_PARAM_DEFAULT = new Double(7.0);

  // rake parameter stuff
  public final static String RAKE_PARAM_NAME = "Rake";
  private final static String RAKE_PARAM_INFO =
      "The rake of the rupture (direction of slip)";
  private final static String RAKE_PARAM_UNITS = "degrees";
  private Double RAKE_PARAM_MIN = new Double( -180);
  private Double RAKE_PARAM_MAX = new Double(180);
  private Double RAKE_PARAM_DEFAULT = new Double(0.0);

  // dip parameter stuff
  public final static String DIP_PARAM_NAME = "Dip";
  private final static String DIP_PARAM_INFO = "The dip of the rupture surface";
  private final static String DIP_PARAM_UNITS = "degrees";
  private Double DIP_PARAM_MIN = new Double(0);
  private Double DIP_PARAM_MAX = new Double(90);
  private Double DIP_PARAM_DEFAULT = new Double(90);

  // the source-location parameters (this should be a location parameter)
  public final static String SRC_LAT_PARAM_NAME = "Source Latitude";
  private Double SRC_LAT_PARAM_DEFAULT = new Double(35.71);

  public final static String SRC_LON_PARAM_NAME = "Source Longitude";

  private Double SRC_LON_PARAM_DEFAULT = new Double( -121.1);

  public final static String SRC_DEPTH_PARAM_NAME = "Source Depth";
   private Double SRC_DEPTH_PARAM_DEFAULT = new Double(7.6);

  //Param to select "kind of rupture", finite or point rupture
  public final static String SRC_TYP_PARAM_NAME = "Rupture Type";
  private final static String SRC_TYP_PARAM_INFO = "Type of rupture";
  public final static String POINT_SRC_NAME = "Point source rupture";
  public final static String FINITE_SRC_NAME = "Finite source rupture";

  //Finite rupture parameters
  public final static String FAULT_PARAM_NAME = "Set Fault Surface";
  private final static String FAULT_PARAM_INFO =
      "Source location parameters for finite rupture";


  //Location Parameter
  public final static String LOCATION_PARAM_NAME = "Location";
  private final static String LOCATION_PARAM_INFO =
      "Set Location for the point source";

  //Hypocenter Location Parameter
  public final static String HYPOCENTER_LOCATION_PARAM_NAME = "Hypocenter Location";

  //Boolean parameter to decide, whether to show hypocenter or not
  public final static String SHOW_HYPOCENTER_LOCATION_PARAM_NAME = "Set Hypocenter Location";


  //Null hypocenter String
  public final static String NULL_HYPOCENTER_STRING = "Null Hypocenter";


  //title for this ParamerterListEditor
  private final static String TITLE = "";

  //Parameter declarations
  private StringParameter sourceTypeParam;
  private DoubleParameter magParam;
  private DoubleParameter dipParam;
  private DoubleParameter rakeParam;
  private LocationParameter locationParam;
  private LocationParameter hypocenterLocationParam;
  private BooleanParameter showHypocenterLocationParam = new
      BooleanParameter(SHOW_HYPOCENTER_LOCATION_PARAM_NAME,new Boolean(false));
  private SimpleFaultParameter faultParam;

  //boolean to check if any parameter has been changed
  private boolean parameterChangeFlag = true;

  private ParameterList parameterList;
  private ParameterListEditor listEditor;
  //EqkRupture Object
  private EqkRupture eqkRupture;

  private GridBagLayout gridBagLayout1 = new GridBagLayout();


  //Hypocenter Location List
  private ArrayList hypocenterList;

  //gridded rupture surface
  private EvenlyGriddedSurfaceAPI ruptureSurface = null;

  public EqkRuptureCreationPanel() {

    // create the mag param
    magParam = new DoubleParameter(MAG_PARAM_NAME, MAG_PARAM_MIN,
                                   MAG_PARAM_MAX, MAG_PARAM_UNITS,
                                   MAG_PARAM_DEFAULT);
    magParam.setInfo(MAG_PARAM_INFO);

    // create the rake param
    rakeParam = new DoubleParameter(RAKE_PARAM_NAME, RAKE_PARAM_MIN,
                                    RAKE_PARAM_MAX, RAKE_PARAM_UNITS,
                                    RAKE_PARAM_DEFAULT);
    rakeParam.setInfo(RAKE_PARAM_INFO);

    // create the rake param
    dipParam = new DoubleParameter(DIP_PARAM_NAME, DIP_PARAM_MIN,
                                   DIP_PARAM_MAX, DIP_PARAM_UNITS,
                                   DIP_PARAM_DEFAULT);
    dipParam.setInfo(DIP_PARAM_INFO);

    // create src location param for the point source
    locationParam = new LocationParameter(LOCATION_PARAM_NAME,SRC_LAT_PARAM_NAME,
                                          SRC_LON_PARAM_NAME,SRC_DEPTH_PARAM_NAME,
                                          SRC_LAT_PARAM_DEFAULT,SRC_LON_PARAM_DEFAULT,
                                          SRC_DEPTH_PARAM_DEFAULT);


    //creating the Fault Rupture Parameter
    faultParam = new SimpleFaultParameter(FAULT_PARAM_NAME);
    faultParam.setInfo(FAULT_PARAM_INFO);

    //creating the parameter to choose the type of rupture (finite or point src rupture)
    ArrayList ruptureTypeList = new ArrayList();
    ruptureTypeList.add(POINT_SRC_NAME);
    ruptureTypeList.add(FINITE_SRC_NAME);

    sourceTypeParam = new StringParameter(SRC_TYP_PARAM_NAME, ruptureTypeList,
                                          (String) ruptureTypeList.get(0));
    sourceTypeParam.setInfo(SRC_TYP_PARAM_INFO);

    parameterList = new ParameterList();
    // add the adjustable parameters to the list
    parameterList.addParameter(sourceTypeParam);
    parameterList.addParameter(magParam);
    parameterList.addParameter(rakeParam);
    parameterList.addParameter(dipParam);
    parameterList.addParameter(faultParam);
    parameterList.addParameter(locationParam);
    parameterList.addParameter(showHypocenterLocationParam);

    sourceTypeParam.addParameterChangeListener(this);
    magParam.addParameterChangeListener(this);
    rakeParam.addParameterChangeListener(this);
    locationParam.addParameterChangeListener(this);
    dipParam.addParameterChangeListener(this);
    faultParam.addParameterChangeListener(this);
    showHypocenterLocationParam.addParameterChangeListener(this);

    createGriddedRuptureSurface();
    listEditor = new ParameterListEditor(parameterList);
    listEditor.setTitle(TITLE);
    try {
      jbInit();
    }
    catch (Exception e) {
      e.printStackTrace();
    }
    this.validate();
    this.repaint();
    setParameterVisibleBasedOnSelectedRuptureType();
    setHypocenterLocationParamVisible();
  }



  private void jbInit() throws Exception {
    this.setLayout(gridBagLayout1);
    this.add(listEditor, new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
                                                , GridBagConstraints.CENTER,
                                                GridBagConstraints.BOTH,
                                                new Insets(4, 4, 4, 4), 0, 0));
  }


  /*
   * Creates the griddded surface area for the rupture
   */
  private void createGriddedRuptureSurface(){
    //if(parameterChangeFlag){
      String ruptureType = (String) sourceTypeParam.getValue();

      if (ruptureType.equals(this.POINT_SRC_NAME)) {
        ruptureSurface = new PointSurface( (Location) locationParam.getValue());
        double aveDip = ( (Double) dipParam.getValue()).doubleValue();
        ((PointSurface)ruptureSurface).setAveDip(aveDip);
      }
      else if (ruptureType.equals(this.FINITE_SRC_NAME)) {
        faultParam.setEvenlyGriddedSurfaceFromParams();
        ruptureSurface = (EvenlyGriddedSurfaceAPI) faultParam.getValue();
      }

      // The first row of all the rupture surfaces is the list of their hypocenter locations
      ListIterator hypoLocationsIt = ruptureSurface.getColumnIterator(0);
      Location loc;
      if (hypocenterList == null) {
        hypocenterList = new ArrayList();
      }
      else {
        hypocenterList.clear();
      }
      while (hypoLocationsIt.hasNext()) {
        //getting the object of Location from the HypocenterLocations and formatting its string to 3 placees of decimal
        loc = (Location) hypoLocationsIt.next();
        hypocenterList.add(loc);
      }
      //creating the hypocenter location parameter
      hypocenterLocationParam = new LocationParameter(
          HYPOCENTER_LOCATION_PARAM_NAME,
          hypocenterList);

      //adding hypocenter location parameter to the list of parameters.
      //if it already exists as the parameter then replace that parameter with a new one.
      if (parameterList.containsParameter(hypocenterLocationParam))
        listEditor.replaceParameterForEditor(HYPOCENTER_LOCATION_PARAM_NAME,
                                             hypocenterLocationParam);
      else
        parameterList.addParameter(hypocenterLocationParam);
      if (listEditor != null)
        listEditor.getParameterEditor(this.SHOW_HYPOCENTER_LOCATION_PARAM_NAME).
            setValue(new Boolean(false));
    //}
  }


  /*
   * Create the EqkRupture Object
   */
  private void createRupture() {
    if (parameterChangeFlag) {

      eqkRupture = new EqkRupture();
      eqkRupture.setMag( ( (Double) magParam.getValue()).doubleValue());
      eqkRupture.setAveRake( ( (Double) rakeParam.getValue()).doubleValue());
      eqkRupture.setRuptureSurface(ruptureSurface);
      boolean hypocenterLocVisible = ((Boolean)showHypocenterLocationParam.getValue()).booleanValue();
      if(hypocenterLocVisible)
        eqkRupture.setHypocenterLocation(getHypocenterLocation());
      parameterChangeFlag = false;
    }
  }


  /**
   *  This is the main function of this interface. Any time a control
   *  paramater or independent paramater is changed by the user in a GUI this
   *  function is called, and a paramater change event is passed in. This
   *  function then determines what to do with the information ie. show some
   *  paramaters, set some as invisible, basically control the paramater
   *  lists.
   *
   * @param  event
   */
  public void parameterChange(ParameterChangeEvent event) {

    String name1 = event.getParameterName();
    if (name1.equals(this.SRC_TYP_PARAM_NAME)) {
      setParameterVisibleBasedOnSelectedRuptureType();
      createGriddedRuptureSurface();
      this.updateUI();
    }
    else if (name1.equals(this.LOCATION_PARAM_NAME) ||
             name1.equals(this.FAULT_PARAM_NAME))
      createGriddedRuptureSurface();
    else if (name1.equals(this.SHOW_HYPOCENTER_LOCATION_PARAM_NAME)) {
      setHypocenterLocationParamVisible();
    }
    parameterChangeFlag = true;
    listEditor.refreshParamEditor();
  }

  /**
   *
   * @returns the Hypocenter Location if selected else return null
   */
  public Location getHypocenterLocation() {
    return (Location)hypocenterLocationParam.getValue();
  }

  /**
   * Makes Hypocenter Location Parameter visible if hypocenter needs to be set
   * else removes it from the list of visible parameters.
   *
   */
  private void setHypocenterLocationParamVisible() {
    boolean hypocenterLocVisible = ((Boolean)showHypocenterLocationParam.getValue()).booleanValue();
    listEditor.getParameterEditor(HYPOCENTER_LOCATION_PARAM_NAME).setVisible(hypocenterLocVisible);
  }

  /**
   *
   * @returns the EqkRupture Object
   */
  public EqkRupture getRupture() {
    createRupture();
    return eqkRupture;
  }

  /**
   *
   * @returns the timespan Metadata for the selected Rupture.
   * If no timespan exists for the rupture then it returns the Message:
   * "No Timespan exists for the selected Rupture".
   */
  public String getTimespanMetadataString() {
    return "No Timespan exists for the selected Rupture";
  }

  /**
   * This function makes the those parameters visible which pertains to the
   * selected Rupture type and removes the rest from the list of visible parameters
   *
   */
  private void setParameterVisibleBasedOnSelectedRuptureType() {
    String selectedRuptureType = (String) sourceTypeParam.getValue();
    if (selectedRuptureType.equals(POINT_SRC_NAME)) {
      listEditor.setParameterVisible(LOCATION_PARAM_NAME, true);
      listEditor.setParameterVisible(DIP_PARAM_NAME, true);
      listEditor.setParameterVisible(FAULT_PARAM_NAME, false);
    }
    else if (selectedRuptureType.equals(FINITE_SRC_NAME)) {
      listEditor.setParameterVisible(LOCATION_PARAM_NAME, false);
      listEditor.setParameterVisible(DIP_PARAM_NAME, false);
      listEditor.setParameterVisible(FAULT_PARAM_NAME, true);
    }
    listEditor.refreshParamEditor();
    this.validate();
    this.repaint();
  }



  /**
   *
   * @returns the panel which allows user to select Eqk rupture from existing
   * ERF models
   */
  public EqkRupSelectorGuiBeanAPI getEqkRuptureSelectorPanel() {
    return this;
  }

  /**
   *
   * @returns the Metadata String of parameters that constitute the making of this
   * ERF_RupSelectorGUI  bean.
   */
  public String getParameterListMetadataString() {
    String metadata = "<br><br>Custom Eqk Rupture Param List: <br>\n" +
        "-------------------------<br>\n" +
        listEditor.getVisibleParameters().getParameterListMetadataString();
//      + "<br>" + "<br>\nRupture Info: " + eqkRupture.getInfo();
    return metadata;
  }

  /**
   *
   * @param paramName
   * @returns the parameter from the parameterList with paramName.
   */
  public ParameterAPI getParameter(String paramName) {
    if (parameterList.containsParameter(paramName)) {
      if (listEditor.getParameterEditor(paramName).isVisible()) {
        return parameterList.getParameter(paramName);
      }
    }

    return null;
  }

  /**
   *
   * @param paramName
   * @returns the ParameterEditor associated with paramName
   */
  public ParameterEditor getParameterEditor(String paramName) {
    if (parameterList.containsParameter(paramName)) {
      if (listEditor.getParameterEditor(paramName).isVisible()) {
        return listEditor.getParameterEditor(paramName);
      }
    }
    return null;
  }

  /**
   *
   * @returns the visible parameters in the list
   */
  public ParameterList getVisibleParameterList() {
    return listEditor.getVisibleParameters();
  }

  /**
   *
   * @returns the parameterlist editor
   */
  public ParameterListEditor getParameterListEditor() {
    return listEditor;
  }


}
