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

import java.awt.event.FocusEvent;
import java.awt.event.KeyEvent;

import javax.swing.JTextField;
import javax.swing.border.Border;

import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.exceptions.WarningException;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.StringParameter;



/**
 * <b>Title:</b> IntegerParameterEditor<p>
 *
 * <b>Description:</b> Subclass of ParameterEditor for editing StringParameters.
 * The widget is an JTextField. <p>
 *
 * The main functionality overidden from the parent class to achive Integer
 * cusomization are the setWidgetObject() and AddWidget() functions. The parent's
 * class JComponent valueEditor field becomes an IntegerTextField,  a subclass
 * of a JTextField. <p>
 *
 * @author Steven W. Rock
 * @version 1.0
 */
public class StringParameterEditor
    extends ParameterEditor
{

    /** Class name for debugging. */
    protected final static String C = "StringParameterEditor";
    /** If true print out debug statements. */
    protected final static boolean D = false;

    /** No-Arg constructor calls parent constructtor */
    public StringParameterEditor() { super(); }

    /**
     * Constructor that sets the parameter that it edits. An
     * Exception is thrown if the model is not an StringParameter.
     *
     * Note: When calling the super() constuctor addWidget() is called
     * which configures the IntegerTextField as the editor widget. <p>
     */
    public StringParameterEditor(ParameterAPI model) throws Exception{

        super(model);

        if ( ( model != null ) &&  !( model instanceof StringParameter) ) {
            String S = C + ": Constructor(model): ";
            throw new Exception(S + "Input model parameter must be a StringParameter.");
        }

        //addWidget();
    }

    /** Currently does nothing */
    public void setAsText(String string) throws IllegalArgumentException{}

    /** Passes in a new Parameter with name to set as the parameter to be editing */
    protected void setWidgetObject(String name, Object obj){

        super.setWidgetObject(name, obj);
        if( ( obj != null ) && ( valueEditor != null ) ) ((JTextField)valueEditor).setText(obj.toString());

    }

    /** Allows customization of the IntegerTextField border */
    public void setWidgetBorder(Border b){
        ((JTextField)valueEditor).setBorder(b);
    }

    /** This is where the JTextField is defined and configured. */
    protected void addWidget(){

        valueEditor = new JTextField();
        valueEditor.setPreferredSize(LABEL_DIM);
	    valueEditor.setMinimumSize(LABEL_DIM);
        valueEditor.setBorder(ETCHED);

        valueEditor.addFocusListener( this );
        valueEditor.addKeyListener(this);

        ((JTextField)valueEditor).setText(ParameterEditor.DATA_TEXT);
        widgetPanel.add(valueEditor, ParameterEditor.WIDGET_GBC);

    }

    /**
     * Called everytime a key is typed in the text field to validate it
     * as a valid integer character ( digits and - sign in first position ).
     */
    public void keyTyped(KeyEvent e) {


        String S = C + ": keyTyped(): ";
        if(D) System.out.println(S + "Starting");
        super.keyTyped(e);

        keyTypeProcessing = false;
        if( focusLostProcessing == true ) return;


        if (e.getKeyChar() == '\n') {
            keyTypeProcessing = true;
            if(D) System.out.println(S + "Return key typed");
            String value = ((JTextField) valueEditor).getText();

            if(D) System.out.println(S + "New Value = " + value);
            try {
                String d = "";
                if( !value.equals( "" ) ) d = value;
                setValue(d);
                refreshParamEditor();
                valueEditor.validate();
                valueEditor.repaint();
            }
            catch (ConstraintException ee) {
                if(D) System.out.println(S + "Error = " + ee.toString());

                Object obj = getValue();
                if( obj != null )
                    ((JTextField) valueEditor).setText(obj.toString());
                else ((JTextField) valueEditor).setText( "" );

                if( !catchConstraint ){ this.unableToSetValue(value); }
                keyTypeProcessing = false;
            }
            catch (WarningException ee){
                keyTypeProcessing = false;
                refreshParamEditor();
                valueEditor.validate();
                valueEditor.repaint();
            }
        }

        keyTypeProcessing = false;
        if(D) System.out.println(S + "Ending");


    }

    /**
     * Called when the user clicks on another area of the GUI outside
     * this editor panel. This synchornizes the editor text field
     * value to the internal parameter reference.
     */
    public void focusLost(FocusEvent e) {

        String S = C + ": focusLost(): ";
        if(D) System.out.println(S + "Starting");

        super.focusLost(e);

        focusLostProcessing = false;
        if( keyTypeProcessing == true ) return;
        focusLostProcessing = true;

        String value = ((JTextField) valueEditor).getText();
        try {

            String d = "";
            if( !value.equals( "" ) ) d = value;
            setValue(d);
            refreshParamEditor();
            valueEditor.validate();
            valueEditor.repaint();
        }
        catch (ConstraintException ee) {
            if(D) System.out.println(S + "Error = " + ee.toString());

            Object obj = getValue();
            if( obj != null )
                ((JTextField) valueEditor).setText(obj.toString());
            else ((JTextField) valueEditor).setText( "" );

            if( !catchConstraint ){ this.unableToSetValue(value); }
            focusLostProcessing = false;
        }
        catch (WarningException ee){
            focusLostProcessing = false;
            refreshParamEditor();
            valueEditor.validate();
            valueEditor.repaint();
        }


        focusLostProcessing = false;
        if(D) System.out.println(S + "Ending");

    }

    /** Sets the parameter to be edited. */
    public void setParameter(ParameterAPI model) {

        String S = "StringParameterEditor: setParameter(): ";
        if(D) System.out.println(S + "Starting");
        super.setParameter(model);
        ((JTextField) valueEditor).setToolTipText("No Constraints");

        if(D) System.out.println(S + "Ending");
    }

    /**
     * Updates the JTextField string with the parameter value. Used when
     * the parameter is set for the first time, or changed by a background
     * process independently of the GUI. This could occur with a ParameterChangeFail
     * event.
     */
    public void refreshParamEditor(){
        Object obj = model.getValue();

        if ( obj != null )
            ((JTextField)valueEditor).setText( obj.toString() );
    }
}
