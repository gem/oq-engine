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

import javax.swing.border.Border;

import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.param.DoubleConstraint;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.TranslatedWarningDoubleParameter;
import org.opensha.commons.param.WarningParameterAPI;
import org.opensha.commons.param.translate.TranslatorAPI;
import org.opensha.commons.util.ParamUtils;



/**
 * <b>Title:</b> TranslatedWarningDoubleParameterEditor<p>
 *
 * <b>Description:</b> Special ParameterEditor for editing
 * TranslatedWarningDoubleParameter. The widget is a NumericTextField
 * so that only numbers can be typed in. When hitting <enter> or moving the
 * mouse away from the NumericField, the value will change back to the
 * original if the new number is outside the constraints range. The constraints
 * also appear as a tool tip when you hold the mouse cursor over
 * the NumericTextField. <p>
 *
 * This type of editor is unique in that the parameter model contains two types
 * of constraints, warning and absolute. So this class actually will fire
 * warning events when exceeded and all listeners registered with the referenced
 * parameter will be notified. Other than that there is nothing more unique about
 * this editor from the ConstrainedDoubleParameterEditor. <p>
 *
 * @see ParameterEditor
 * @author Steven W. Rock
 * @version 1.0
 */
public class TranslatedWarningDoubleParameterEditor extends ConstrainedDoubleParameterEditor {

    /** Class name for debugging. */
    protected final static String C = "TranslatedWarningDoubleParameterEditor";
    /** If true print out debug statements. */
    protected final static boolean D = false;

    /** No-Arg constructor calls parent constructtor */
    public TranslatedWarningDoubleParameterEditor() { super(); }

    /**
     * Constructor that sets the parameter that it edits. An
     * Exception is thrown if the model is not an DoubleParameter.
     * This function only calls the super constructor. <p>
     *
     * Note: When calling the super() constuctor addWidget() is called
     * which configures the IntegerTextField as the editor widget. <p>
     */
    public TranslatedWarningDoubleParameterEditor(ParameterAPI model)
	    throws Exception
    { super(model); }

    /**
     * Sets the parameter to be edited. This class sets the NumericTextField's
     * tooltips to the warning constraint min an max, not the absolute constraint.
     * This function calls removeWidget(), addWidget() then setWidgetObject()
     * to update the GUI with the new values. <p>
     *
     * Note: With this function a programmer can add TranslatedWarningDoubleParameter,
     * WarningParameterAPI, and DoubleParameter objects. It transparently
     * acts like it's ancestor classes when the input parameter is one of the
     * simpler models.
     *
     */
    public void setParameter(ParameterAPI model) throws ParameterException {

        String S = C + ": setParameter(): ";
        if(D)System.out.println(S + "Starting");

        if ( model == null ) throw new NullPointerException( S + "Input Parameter data cannot be null" );
        else this.model = model;

        String name = "";
        name = model.getName();
        Object value = model.getValue();

        removeWidget();
        addWidget();

        setWidgetObject( name, value );


        DoubleConstraint constraint;

        if( model instanceof TranslatedWarningDoubleParameter){

            TranslatedWarningDoubleParameter param1 = (TranslatedWarningDoubleParameter)model;
            try{
                valueEditor.setToolTipText( "Min = " + param1.getWarningMin().toString() + "; Max = " + param1.getWarningMax().toString() );
                this.setNameLabelToolTip(model.getInfo());
            }
            catch( Exception e ){
                throw new ParameterException(e.toString());
            }



        }
        else if( ParamUtils.isWarningParameterAPI( model ) ){
            constraint = (DoubleConstraint)((WarningParameterAPI)model).getWarningConstraint();
            if( constraint == null ) constraint = (DoubleConstraint) model.getConstraint();

            valueEditor.setToolTipText( "Min = " + constraint.getMin().toString() + "; Max = " + constraint.getMax().toString() );
            this.setNameLabelToolTip(model.getInfo());

        }

        else {
            constraint = (DoubleConstraint) model.getConstraint();
            valueEditor.setToolTipText( "Min = " + constraint.getMin().toString() + "; Max = " + constraint.getMax().toString() );
            this.setNameLabelToolTip(model.getInfo());
        }



        if(D) System.out.println(S + "Ending");
    }

    /** Allows customization of the IntegerTextField border */
    public void setWidgetBorder(Border b){
        ((NumericTextField)valueEditor).setBorder(b);
    }




    /**
     *  Needs to be called by subclasses when editable widget field change fails
     *  due to constraint problems. This class implements this by
     *  translating the TranslatedWarningDOubleParameters using it's
     *  translator before firing the ParameterChangeFailEvent and notifying
     *  listeners.
     *
     * @param  value                    The value object the parameter rejected
     */
    public void unableToSetValue( Object value ) throws ConstraintException {

        String S = C + ": unableToSetValue():";
        if(D) System.out.println(S + "New Value = " + value.toString());


        if( value instanceof String){
            try{ value = new Double(value.toString()); }
            catch( NumberFormatException ee){}
        }

        if ( ( value != null ) && ( model != null ) && value instanceof Double) {


            Object obj = model.getValue();

            if( obj != null && obj instanceof Double && model instanceof TranslatedWarningDoubleParameter){

                TranslatedWarningDoubleParameter param = (TranslatedWarningDoubleParameter)model;
                TranslatorAPI trans = param.getTrans();

                if( trans != null || param.isTranslate() ){

                    Double dUntranslated = (Double)value;
                    Double dTranslated = new Double( trans.translate( dUntranslated.doubleValue() ) );
                    Double oldUntranslated = (Double)param.getValue();

                    if ( D ) System.out.println( S + "Old Value = " + obj.toString() );

                    if ( !dUntranslated.toString().equals( oldUntranslated.toString() ) ) {
                        org.opensha.commons.param.event.ParameterChangeFailEvent event = new org.opensha.commons.param.event.ParameterChangeFailEvent(
                            param,
                            param.getName(),
                            oldUntranslated,
                            dUntranslated
                        );

                        param.firePropertyChangeFailed( event );
                    }
                }
            }
        }
    }



}


