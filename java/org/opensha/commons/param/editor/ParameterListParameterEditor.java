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

package org.opensha.commons.param.editor;


import java.awt.Color;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ListIterator;

import javax.swing.JButton;
import javax.swing.JDialog;

import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.ParameterListParameter;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.param.event.ParameterChangeListener;





/**
 * <p>Title: ParameterListParameterEditor</p>
 * <p>Description: This class is more like a parameterList consisting of any number of
 * parameters. This parameterList considered as a single Parameter.
 * This parameter editor will show up as the button on th GUI interface and
 * when the user punches the button, all the parameters will pop up in a seperate window
 * showing all the parameters contained within this parameter.</p>
 * @author : Ned Field, Nitin Gupta and Vipin Gupta
 * @created : Aug 14,2003
 * @version 1.0
 */

public class ParameterListParameterEditor extends ParameterEditor implements
ActionListener,ParameterChangeListener{

  /** Class name for debugging. */
  protected final static String C = "ParameterListParameterEditor";
  /** If true print out debug statements. */
  protected final static boolean D = false;
  private Insets defaultInsets = new Insets( 4, 4, 4, 4 );

  protected ParameterListParameter param ;
  //Editor to hold all the parameters in this parameter
  protected ParameterListEditor editor;

  //Instance for the framee to show the all parameters in this editor
  protected JDialog frame;

  //checks if parameter has been changed
  protected boolean parameterChangeFlag=true;

  //default class constructor
  public ParameterListParameterEditor() {}

  public ParameterListParameterEditor(ParameterAPI model){
    super(model);
  }


  /**
   * Set the values in the parameters in this parameterList parameter
   */
  public void setParameter(ParameterAPI param)  {
    setParameterInEditor(param);
    valueEditor = new JButton(param.getName());
    ((JButton)valueEditor).addActionListener(this);
    add(valueEditor,  new GridBagConstraints( 0, 0, 1, 1, 1.0, 0.0
        , GridBagConstraints.CENTER, GridBagConstraints.HORIZONTAL, new Insets( 0, 0, 0, 0 ), 0, 0 ) );
    String S = C + ": Constructor(): ";
    if ( D ) System.out.println( S + "Starting:" );

    // remove the previous editor
    //removeAll();
    this.param = (ParameterListParameter) param;

    // make the params editor
    initParamListAndEditor();
    // All done
    if ( D ) System.out.println( S + "Ending:" );
  }


  /**
   * creating the GUI parameters elements for the parameterlistparameter Param
   */
  protected void initParamListAndEditor(){
    ParameterList paramList = (ParameterList)param.getValue();
    ListIterator it = paramList.getParametersIterator();
    while(it.hasNext())
      ((ParameterAPI)it.next()).addParameterChangeListener(this);
    editor = new ParameterListEditor(paramList);
    editor.setTitle("Set "+param.getName());
  }

  /**
  * It enables/disables the editor according to whether user is allowed to
  * fill in the values.
  */
 public void setEnabled(boolean isEnabled) {
   this.editor.setEnabled(isEnabled);
 }


  /**
   * sets the title for this editor
   * @param title
   */
  public void setEditorTitle(String title){
    editor.setTitle(title);
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
    *  Hides or shows one of the ParameterEditors in the ParameterList. setting
    *  the boolean parameter to true shows the panel, setting it to false hides
    *  the panel. <p>
    *
    * @param  parameterName  The parameter editor to toggle on or off.
    * @param  visible      The boolean flag. If true editor is visible.
    */
   public void setParameterVisible( String parameterName, boolean visible ) {
     editor.setParameterVisible(parameterName, visible);
   }



  /**
   * Called when the parameter has changed independently from
   * the editor, such as with the ParameterWarningListener.
   * This function needs to be called to to update
   * the GUI component ( text field, picklist, etc. ) with
   * the new parameter value.
   */
  public void refreshParamEditor(){
    editor.refreshParamEditor();
  }

  /**
   * gets the Parameter for the given paramName
   * @param paramName : Gets the parameter from this paramList
   */
  public ParameterAPI getParameter(String paramName){
    return editor.getParameterList().getParameter(paramName);
  }

  /**
   *
   * @returns the parameterList contained in this editor.
   */
  public ParameterList getParameterList(){
    return editor.getParameterList();
  }

  /**
   * Keeps track when parameter has been changed
   * @param event
   */
  public void parameterChange(ParameterChangeEvent event){
    parameterChangeFlag = true;
  }

  /**
   * This function is called when the user click for the ParameterListParameterEditor Button
   *
   * @param ae
   */
  public void actionPerformed(ActionEvent ae ) {

      frame = new JDialog();
      frame.setModal(true);
      frame.setSize(300,400);
      frame.setTitle(param.getName());
      frame.getContentPane().setLayout(new GridBagLayout());
      frame.getContentPane().add(editor,new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
          ,GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(4, 4, 4, 4), 0, 0));

      //Adding Button to update the forecast
      JButton button = new JButton();
      button.setText("Update "+param.getName());
      button.setForeground(new Color(80,80,133));
      button.addActionListener(new java.awt.event.ActionListener() {
        public void actionPerformed(ActionEvent e) {
          button_actionPerformed(e);
        }
      });
      frame.getContentPane().add(button,new GridBagConstraints(0, 1, 1, 1, 0.0, 0.0
          ,GridBagConstraints.CENTER, GridBagConstraints.NONE, new Insets(4, 4, 4, 4), 0, 0));
      frame.setVisible(true);
      frame.pack();
  }


  /**
   * This function is called when user punches the button to update the ParameterList Parameter
   * @param e
   */
  protected void button_actionPerformed(ActionEvent e) {
    ParameterList paramList = editor.getParameterList();
    if(parameterChangeFlag){
      param.setValue(paramList);
      parameterChangeFlag = false;
    }
    frame.dispose();
  }
}
