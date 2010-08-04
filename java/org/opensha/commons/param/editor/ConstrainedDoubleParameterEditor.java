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

import javax.swing.border.Border;

import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.WarningParameterAPI;
import org.opensha.commons.util.ParamUtils;

/**
 * <b>Title:</b> ConstrainedDoubleParameterEditor<p>
 *
 * <b>Description:</b> Special ParameterEditor for editing Constrained
 * DoubleParameters. The widget is a NumericTextField so that only
 * numbers can be typed in. When hitting <enter> or moving the
 * mouse away from the NumericField, the value will change back to the
 * original if the new number is outside the constraints range. The constraints
 * also appear as a tool tip when you hold the mouse cursor over
 * the NumericTextField. <p>
 *
 * @author Steven W. Rock
 * @version 1.0
 */
public class ConstrainedDoubleParameterEditor extends DoubleParameterEditor{

    /** Class name for debugging. */
    protected final static String C = "ConstrainedDoubleParameterEditor";
    /** If true print out debug statements. */
    protected final static boolean D = false;


    /** No-Arg constructor calls parent constructtor */
    public ConstrainedDoubleParameterEditor() { super(); }

    /**
     * Constructor that sets the parameter that it edits.
     * Only calls the super() function.
     */
    public ConstrainedDoubleParameterEditor(ParameterAPI model)
	    throws Exception {
      super(model);
      this.setParameter(model);
    }

    /**
     * Calls the super().;setFunction() and uses the constraints
     * to set the JTextField tooltip to show the constraint values.
     */
    public void setParameter(ParameterAPI model) {

        String S = C + ": setParameter(): ";
        if(D)System.out.println(S + "Starting");
        super.setParameter(model);
        setToolTipText();
        this.setNameLabelToolTip(model.getInfo());
        if(D) System.out.println(S + "Ending");
    }

    public void setWidgetBorder(Border b){
        ((NumericTextField)valueEditor).setBorder(b);
    }

    /** This is where the NumericTextField for the Constraint DoubleParameter
     * It checks if the min and max constraint value are same then change the
     * font and size of the valueEditor and widgetPanel
     * is defined and configured. */
    protected void addWidget() {
      String S = C + "ConstrainedDoubleParameterEditor: addWidget(): ";
      if(D) System.out.println(S + "Starting");
      super.addWidget();
      DoubleConstraint constraint =getConstraint();
      if(constraint.getMax().doubleValue()==constraint.getMin().doubleValue()){
        if (  valueEditor != null ) {
            ((NumericTextField) valueEditor).setEditable(false);
            ((NumericTextField) valueEditor).setMinimumSize( LABEL_DIM );
            ((NumericTextField) valueEditor).setFont( JCOMBO_FONT );
            ((NumericTextField) valueEditor).setForeground( Color.blue );
            ((NumericTextField) valueEditor).setBorder( CONST_BORDER );
            widgetPanel.setBackground(STRING_BACK_COLOR);
            widgetPanel.setForeground( Color.blue );
        }
      }

      if(D) System.out.println(S + "Ending");
    }


    /**
     * @returns the DoubleConstraint
     */
    protected DoubleConstraint getConstraint(){
      //Double constraint declaration
      DoubleConstraint constraint;
      if( ParamUtils.isWarningParameterAPI( model ) ){
        constraint = (DoubleConstraint)((WarningParameterAPI)model).getWarningConstraint();
        if( constraint == null ) constraint = (DoubleConstraint) model.getConstraint();
      }
      else constraint = (DoubleConstraint) model.getConstraint();
      return constraint;
    }

    /**
     * Updates the NumericTextField string with the parameter value. Used when
     * the parameter is set for the first time, or changed by a background
     * process independently of the GUI. This could occur with a ParameterChangeFail
     * event.
     */
    public void refreshParamEditor(){
       super.refreshParamEditor();
       setToolTipText();
    }

    /**
     * set the tool tip contraint text
     */
    private  void setToolTipText() {
      DoubleConstraint constraint =getConstraint();
      valueEditor.setToolTipText( "Min = " + constraint.getMin().toString() + "; Max = " + constraint.getMax().toString() );
    }

}
