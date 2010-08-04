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

package org.opensha.sha.param.editor.gui;

import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;
import java.util.ListIterator;

import javax.swing.JOptionPane;

import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.IntegerParameter;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterConstraintAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.ParameterListParameter;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ConstrainedDoubleParameterEditor;
import org.opensha.commons.param.editor.ConstrainedStringParameterEditor;
import org.opensha.commons.param.editor.IntegerParameterEditor;
import org.opensha.commons.param.editor.ParameterEditor;
import org.opensha.commons.param.editor.ParameterListEditor;
import org.opensha.commons.param.editor.ParameterListParameterEditor;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeFailEvent;
import org.opensha.commons.param.event.ParameterChangeFailListener;
import org.opensha.commons.param.event.ParameterChangeListener;
import org.opensha.sha.param.SimpleFaultParameter;


/**
 * <p>Title: SimpleFaultParameterEditorPanel</p>
 * <p>Description: It is a more general parameter than just a Simple Fault Parameter
 * Editor because actually inside it creates an object of the EvenlyGriddedSurface1EvenlyGriddedSurface1.</p>
 * @author : Edward Field, Nitin Gupta and Vipin Gupta
 * @created : July 31, 2003
 * @version 1.0
 */

public class SimpleFaultParameterEditorPanel extends ParameterEditor
    implements ParameterChangeListener,
    ParameterChangeFailListener,
    ActionListener {


  /** Class name for debugging. */
  protected final static String C = "SimpleFaultParameterEditorPanel";
  /** If true print out debug statements. */
  protected final static boolean D = false;
  private Insets defaultInsets = new Insets( 4, 4, 4, 4 );


  // title of Parameter List Editor
  public static final String SIMPLE_FAULT_EDITOR_TITLE = new String("Simple Fault Editor");

  //boolean for the FaultName to be shown
  boolean showFaultName = false;

  //boolean for the Evenly Gridded Param
  boolean evenlyGriddedParamChange = true;



  //Reference to the EvenlyGriddedSurface Param
  private SimpleFaultParameter surfaceParam;


  /**
   * ParameterListEditor for holding parameters
   */
  private ParameterListEditor editor;

  /**
   * ParameterListEditor for holding parameterListForLats
   */
  private ParameterListParameterEditor editorForLats;

  /**
   * ParameterListEditor for holding parameterListForLons
   */
  private ParameterListParameterEditor editorForLons;

  /**
   * ParameterListEditor for holding parameterListForDips
   */
  private ParameterListParameterEditor editorForDips;

  /**
   * ParameterListEditor for holding parameterListForDepths
   */
  private ParameterListParameterEditor editorForDepths;

  /**
   * IntegerParameterEditor for Number of Dips
   */
  private IntegerParameterEditor numDipsEditor;

  /**
   * StringParameter for the Fault type
   */
  private ConstrainedStringParameterEditor faultTypeEditor;


  /**
   * DoubleParameter for Ave. Dip LocationVector, if the person has selected
   * Stirling Fault Model
   */
  private ConstrainedDoubleParameterEditor dipDirectionParamEditor ;


  public SimpleFaultParameterEditorPanel() {}

  //constructor taking the Parameter as the input argument
   public SimpleFaultParameterEditorPanel(ParameterAPI model){
     super(model);
  }

  /**
   * Set the values in the Parameters for the EvenlyGridded Surface
   */
  public void setParameter(ParameterAPI param)  {

    String S = C + ": Constructor(): ";
    if ( D ) System.out.println( S + "Starting:" );
    // remove the previous editor
    setParameterInEditor(param);
    removeAll();
    surfaceParam = (SimpleFaultParameter) param;
    
    // make the params editor
    initParamListAndEditor();

    //by default the showFaultName is false so the fault name parameter is not visible
    if(!showFaultName)
      this.editor.getParameterEditor(SimpleFaultParameter.FAULT_NAME).setVisible(false);

    //Make the Dip LocationVector parameter visible only if Fault type selected is Stirling
    if(faultTypeEditor.isVisible()){
      if(((String)faultTypeEditor.getParameter().getValue()).equals(SimpleFaultParameter.STIRLING))
        dipDirectionParamEditor.setVisible(true);
      else
        dipDirectionParamEditor.setVisible(false);
    }

    //Border border = BorderFactory.createBevelBorder(BevelBorder.RAISED,Color.white,Color.white,new Color(98, 98, 112),new Color(140, 140, 161));
    //button.setBorder(border);
    add(editor,new GridBagConstraints( 0, 0, 0, 1, 1.0, 0.0
        , GridBagConstraints.NORTH, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ) );

    /**
     * showing the Lats and Lons in the tabular format
     */
    add(this.editorForLats,new GridBagConstraints( 0, 1, 0, 1, 1.0, 0.0
        , GridBagConstraints.WEST, GridBagConstraints.WEST, new Insets( 0, 0, 0, 0 ), 0, 0 ) );

    add(this.editorForLons,new GridBagConstraints( 0, 1, 0, 1, 1.0, 0.0
        , GridBagConstraints.EAST, GridBagConstraints.EAST, new Insets( 0, 0, 0, 0 ), 0, 0 ) );

    add(this.numDipsEditor,new GridBagConstraints( 0, 2, 0, 1, 1.0, 0.0
        , GridBagConstraints.NORTH, GridBagConstraints.HORIZONTAL, new Insets( 0, 0, 0, 0 ), 0, 0 ) );

    add(this.editorForDips,new GridBagConstraints( 0, 3, 0, 1, 1.0, 0.0
        , GridBagConstraints.NORTH, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ) );

    add(this.editorForDepths,new GridBagConstraints( 0, 4, 0, 1, 1.0, 0.0
        , GridBagConstraints.NORTH, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ) );
    add(this.faultTypeEditor,new GridBagConstraints( 0, 5, 0, 1, 1.0, 0.0
        , GridBagConstraints.NORTH, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ) );

    //add the dipDirectionParamter to the panel if it is visible
    if(dipDirectionParamEditor.isVisible())
      add(this.dipDirectionParamEditor,new GridBagConstraints( 0, 6, 0, 1, 1.0, 0.0
          , GridBagConstraints.NORTH, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ) );

    // All done
    if ( D ) System.out.println( S + "Ending:" );
  }

  /**
   * Called when the parameter has changed independently from
   * the editor, such as with the ParameterWarningListener.
   * This function needs to be called to to update
   * the GUI component ( text field, picklist, etc. ) with
   * the new parameter value.
   */
  public void refreshParamEditor() {
    editor.refreshParamEditor();
    editorForLats.refreshParamEditor();
    editorForLons.refreshParamEditor();
    numDipsEditor.refreshParamEditor();
    editorForDips.refreshParamEditor();
    editorForDepths.refreshParamEditor();
    faultTypeEditor.refreshParamEditor();
    if(dipDirectionParamEditor.isVisible())
      dipDirectionParamEditor.refreshParamEditor();
  }

  /**
   * creating the GUI parameters elemenst for the EvenlyGriddedSurface Param
   */
  private void initParamListAndEditor(){

    //surfaceParam.initParamList();

    ParameterList paramList = surfaceParam.getFaultTraceParamList();
    ListIterator it  = paramList.getParametersIterator();
    while (it.hasNext())
      ((ParameterAPI)it.next()).addParameterChangeListener(this);
    editor = new ParameterListEditor(paramList);
    editor.setTitle(SIMPLE_FAULT_EDITOR_TITLE);

    //creating the table for the Lat and Lon of the FltTrace
    setLatLon();

    //creating the Double parameter for the Dips
    IntegerParameter dipParam = (IntegerParameter)surfaceParam.getNumDipParam();
    dipParam.addParameterChangeListener(this);
    try{
      numDipsEditor = new IntegerParameterEditor(dipParam);
    }catch(Exception ee){
      ee.printStackTrace();
    }
    //creating the table for the Dips
    setDips();

    //creating the table for the Depths
    setDepths();

    //create the String parameter if the dip is one
    StringParameter faultTypeParam = (StringParameter)surfaceParam.getFaultTypeParam();
    faultTypeParam.addParameterChangeListener(this);
    //getting the Dip LocationVector Parameter
    DoubleParameter dipDirectionParam = (DoubleParameter)surfaceParam.getDipDirectionParam();
    dipDirectionParam.addParameterChangeFailListener(this);
    dipDirectionParam.addParameterChangeListener(this);
    try{
    faultTypeEditor = new ConstrainedStringParameterEditor(faultTypeParam);
    //creating the dipDirectionParamterEditor
    dipDirectionParamEditor = new ConstrainedDoubleParameterEditor(dipDirectionParam);
    }catch(Exception ee){
      ee.printStackTrace();
    }
  }

  /**
   * Sets the Lat and Lon for the faultTrace
   */
  private void setLatLon(){

    surfaceParam.initLatLonParamList();
    ParameterListParameter latParam = (ParameterListParameter)surfaceParam.getLatParam();
    ListIterator it = latParam.getParametersIterator();
    while(it.hasNext())
      ((ParameterAPI)it.next()).addParameterChangeListener(this);
    editorForLats = new ParameterListParameterEditor(latParam);
    //editorForLats.setTitle(this.LAT_EDITOR_TITLE);

    ParameterListParameter lonParam = (ParameterListParameter)surfaceParam.getLonParam();
    it = lonParam.getParametersIterator();
    while(it.hasNext())
      ((ParameterAPI)it.next()).addParameterChangeListener(this);
    editorForLons = new ParameterListParameterEditor(lonParam);
    //editorForLons.setTitle(this.LON_EDITOR_TITLE);
    editorForLats.validate();
    editorForLats.repaint();
    editorForLons.validate();
    editorForLons.repaint();
  }

  /**
   * This sets all the fault data needed to make a evenly discretized fault
   * @param name : Name of the fault
   * @param gridSpacing
   * @param lats : ArrayList of Latitudes for the discretized fault
   * @param lons : ArrayList of Longitudes for the discretized fault
   * @param dips : ArrayList of Dips
   * @param depths : ArrayList of Depths, which are one more then the number of dips
   * @param faultType : STIRLING or FRANKEL fault
   */
  public void setAll(String name, double gridSpacing, ArrayList lats, ArrayList lons,
                     ArrayList dips, ArrayList depths, String faultType) {
    surfaceParam.setAll(name, gridSpacing, lats, lons, dips, depths, faultType);
    refreshParamEditor();
  }


  /**
   * This sets all the fault data needed to make a evenly discretized fault
   * @param gridSpacing
   * @param lats : ArrayList of Latitudes for the discretized fault
   * @param lons : ArrayList of Longitudes for the discretized fault
   * @param dips : ArrayList of Dips
   * @param depths : ArrayList of Depths, which are one more then the number of dips
   * @param faultType : STIRLING or FRANKEL fault
   */
  public void setAll(double gridSpacing, ArrayList lats, ArrayList lons,
                     ArrayList dips, ArrayList depths, String faultType) {
    surfaceParam.setAll(gridSpacing,lats,lons,dips,depths,faultType);
    refreshParamEditor();
  }


  /**
   *Sets the Dip
   */
  private void setDips(){
    surfaceParam.initDipParamList();
    ParameterListParameter parameterListParameterForDips = (ParameterListParameter)surfaceParam.getDipParam();
    ListIterator it = parameterListParameterForDips.getParametersIterator();
    while(it.hasNext())
      ((ParameterAPI)it.next()).addParameterChangeListener(this);
    editorForDips = new ParameterListParameterEditor(parameterListParameterForDips);
    editorForDips.validate();
    editorForDips.revalidate();
    editorForDips.repaint();
  }


  /**
   * Sets the Depths
   */
  private void setDepths(){
    surfaceParam.initDepthParamList();
    ParameterListParameter parameterListParameterForDepths = (ParameterListParameter)surfaceParam.getDepthParam();
    ListIterator it = parameterListParameterForDepths.getParametersIterator();
    while(it.hasNext())
      ((ParameterAPI)it.next()).addParameterChangeListener(this);
    editorForDepths = new ParameterListParameterEditor(parameterListParameterForDepths);
    editorForDepths.validate();
    editorForDepths.revalidate();
    editorForDepths.repaint();
  }

  /**
   * Sets the Average Dip LocationVector for the evenly discritized fault.
   * By Default its value is NaN and its value can only be set if one has
   * selected the Fault type to be Stirling
   */
  public void setDipDirection(double value){
    if(faultTypeEditor.isVisible())
        surfaceParam.setDipDirection(value);
    refreshParamEditor();
  }

  /**
   * Main GUI Initialization point. This block of code is updated by JBuilder
   * when using it's GUI Editor.
   */
  protected void jbInit() throws Exception {
    // Main component
    this.setLayout( new GridBagLayout());
  }

  /**
   * Sets the visibility for the fault name param
   * @param flag
   */
  public void setFaultNameVisible(boolean flag){
    showFaultName = flag;
    this.editor.getParameterEditor(SimpleFaultParameter.FAULT_NAME).setVisible(flag);
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
  public void parameterChange( ParameterChangeEvent event ) {

    String S = C + ": parameterChange(): ";
    if ( D )
      System.out.println( "\n" + S + "starting: " );

    //System.out.println("Parameter Channged: "+event.getParameterName());

    //System.out.println("param change");
    String name1 = event.getParameterName();

    /**
     * If the changed parameter is the number of the fault trace param
     */
    if(name1.equalsIgnoreCase(SimpleFaultParameter.NUMBER_OF_FAULT_TRACE)){
      //surfaceParam.getLatParamVals().clear();
      //surfaceParam.getLonParamVals().clear();
      //System.out.println("Inside the Fault Trace param change");
     // ListIterator it = editorForLats.getParameterList().getParametersIterator();
      //saving the previous lat values in the vector
     /* while(it.hasNext()){
        ParameterAPI param = (ParameterAPI)it.next();
        if(param.getValue()!=null)
          surfaceParam.getLatParamVals().add(param.getValue());
      }
      //saving the previous lon values in the vector
      it = editorForLons.getParameterList().getParametersIterator();
      while(it.hasNext()){
        ParameterAPI param = (ParameterAPI)it.next();
        if(param.getValue()!=null)
          surfaceParam.getLonParamVals().add(param.getValue());
      }*/

      //removing the lats and Lons editor from the Applet
      remove(editorForLats);
      remove(editorForLons);
      //System.out.println("Calling the set LAt lon from Parameter change");
      //if the user has changed the values for the Number of the fault trace
      this.setLatLon();

      /**
       * showing the Lats and Lons in the tabular format
       * Adding the lats and lons editor to the Parameter editor
       */
      add(this.editorForLats,new GridBagConstraints( 0, 1, 0, 1, 1.0, 0.0
          , GridBagConstraints.WEST, GridBagConstraints.WEST, new Insets( 0, 0, 0, 0 ), 0, 0 ) );

      add(this.editorForLons,new GridBagConstraints( 0, 1, 0, 1, 1.0, 0.0
          , GridBagConstraints.EAST, GridBagConstraints.EAST, new Insets( 0, 0, 0, 0 ), 0, 0 ) );
    }

    /**
     * If the changed parameter is the number of the Dips
     */
    if(name1.equalsIgnoreCase(SimpleFaultParameter.NUM_DIPS)) {
      //System.out.println("Inside the Num dips param change");
     /* surfaceParam.getDipParamVals().clear();
      surfaceParam.getDepthParamVals().clear();
      ListIterator it = editorForDips.getParameterList().getParametersIterator();
      //saving the previous Dip values in the vector
      while(it.hasNext()){
        ParameterAPI param = (ParameterAPI)it.next();
        if(param.getValue()!=null)
          surfaceParam.getDipParamVals().add(param.getValue());
      }

      //saving the previous Depths values in the vector
      it = editorForDepths.getParameterList().getParametersIterator();
      while(it.hasNext()){
        ParameterAPI param = (ParameterAPI)it.next();
        if(param.getValue()!=null)
          surfaceParam.getDepthParamVals().add(param.getValue());
      }*/

      //removing the dips and depth editor from the applet
      remove(editorForDips);
      remove(editorForDepths);
      setDips();
      setDepths();

      //Adding the dips and depth editor to the parameter editor
      add(this.editorForDips,new GridBagConstraints( 0, 3, 0, 1, 1.0, 0.0
          , GridBagConstraints.NORTH, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ) );

      add(this.editorForDepths,new GridBagConstraints( 0, 4, 0, 1, 1.0, 0.0
          , GridBagConstraints.NORTH, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ) );

      if(((Integer)numDipsEditor.getParameter().getValue()).intValue() !=1){
        faultTypeEditor.setVisible(false);
        dipDirectionParamEditor.setVisible(false);
      }

      if(((Integer)numDipsEditor.getParameter().getValue()).intValue() ==1)
        this.faultTypeEditor.setVisible(true);
    }
    //if the Fault type Parameter is changed
    if(name1.equalsIgnoreCase(SimpleFaultParameter.FAULT_TYPE_TITLE)){
      //if the fault type parameter selected value is STIRLING then show the dip direction parameter.
      if(((String)faultTypeEditor.getParameter().getValue()).equals(SimpleFaultParameter.STIRLING)){
        dipDirectionParamEditor.setVisible(true);
        add(dipDirectionParamEditor,new GridBagConstraints( 0, 6, 0, 1, 1.0, 0.0
          , GridBagConstraints.NORTH, GridBagConstraints.BOTH, new Insets( 0, 0, 0, 0 ), 0, 0 ) );
      }
      else{
        dipDirectionParamEditor.setVisible(true);
        remove(dipDirectionParamEditor);
      }
    }
    this.validate();
    this.revalidate();
    this.repaint();
    evenlyGriddedParamChange = true;
  }

  /**
   *  Shown when a Constraint error is thrown on a ParameterEditor
   *
   * @param  e  Description of the Parameter
   */
  public void parameterChangeFailed( ParameterChangeFailEvent e ) {

    String S = C + " : parameterChangeWarning(): ";
    if(D) System.out.println(S + "Starting");


    StringBuffer b = new StringBuffer();

    ParameterAPI param = ( ParameterAPI ) e.getSource();
    ParameterConstraintAPI constraint = param.getConstraint();
    String oldValueStr = e.getOldValue().toString();
    String badValueStr = e.getBadValue().toString();
    String name = param.getName();


    b.append( "The value ");
    b.append( badValueStr );
    b.append( " is not permitted for '");
    b.append( name );
    b.append( "'.\n" );

    b.append( "Resetting to ");
    b.append( oldValueStr );
    b.append( ". The constraints are: \n");
    b.append( constraint.toString() );
    b.append( "\n" );

    JOptionPane.showMessageDialog(
        this, b.toString(),
        "Cannot Change Value", JOptionPane.INFORMATION_MESSAGE
        );

    if(D) System.out.println(S + "Ending");

  }


  /**
   * creates the evenly gridded surface from the fault parameter.
   * This function has to be called explicitly in order to Create/Update or it can
   * updated when the user press the "Update Surface" button
   * the  gridded surface.
   * @throws RuntimeException
   */
  public void setEvenlyGriddedSurfaceFromParams()throws RuntimeException{

    //checks if any parameter has been only then updates the Griddedsurface
    if(evenlyGriddedParamChange){
      surfaceParam.setEvenlyGriddedSurfaceFromParams();
      evenlyGriddedParamChange = false;
    }
  }


  /**
   * This function is called when Update  Surface button is pressed
   *
   * @param ae
   */
  public void actionPerformed(ActionEvent ae ) {
    try{
      setEvenlyGriddedSurfaceFromParams();
    }catch(RuntimeException e){
      JOptionPane.showMessageDialog(this,e.getMessage(),"Incorrect Values",JOptionPane.ERROR_MESSAGE);
    }
  }
}



