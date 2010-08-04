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

import javax.swing.border.Border;

import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.exceptions.WarningException;
import org.opensha.commons.param.IntegerParameter;
import org.opensha.commons.param.ParameterAPI;



/**
 * <b>Title:</b> IntegerParameterEditor<p>
 *
 * <b>Description:</b> Subclass of ParameterEditor for editing IntegerParameters.
 * The widget is an IntegerTextField so that only integers can be typed in. <p>
 *
 * The main functionality overidden from the parent class to achive Integer
 * cusomization are the setWidgetObject() and AddWidget() functions. The parent's
 * class JComponent valueEditor field becomes an IntegerTextField,  a subclass
 * of a JTextField. <p>
 *
 * @author Steven W. Rock
 * @version 1.0
 */
public class IntegerParameterEditor extends ParameterEditor
{

    /** Class name for debugging. */
    protected final static String C = "IntegerParameterEditor";
    /** If true print out debug statements. */
    protected final static boolean D = false;

    /** No-Arg constructor calls parent constructor */
    public IntegerParameterEditor() { super(); }

    /**
     * Constructor that sets the parameter that it edits. An
     * Exception is thrown if the model is not an IntegerParameter.
     * It it is then the updateNameLabel is called which
     * inderectly calls addWidget. <p>
     *
     * Note: When calling the super() constuctor addWidget() is called
     * which configures the IntegerTextField as the editor widget. <p>
     */
     public IntegerParameterEditor(ParameterAPI model) throws Exception {

        super(model);

        String S = C + ": Constructor(model): ";
        if(D) System.out.println(S + "Starting");

        if ( (model != null ) && !(model instanceof IntegerParameter))
            throw new Exception( S + "Input model parameter must be a IntegerParameter.");

        //addWidget();
        updateNameLabel( model.getName() );
        this.setParameter(model);
        if(D) System.out.println(S.concat("Ending"));

    }

    /** Currently does nothing */
    public void setAsText(String string) throws IllegalArgumentException { }

    /** Passes in a new Parameter with name to set as the parameter to be editing */
    protected void setWidgetObject(String name, Object obj) {
        String S = C + ": setWidgetObject(): ";
        if(D) System.out.println(S + "Starting");

        super.setWidgetObject(name, obj);

        if ( ( obj != null ) && ( valueEditor != null ) )
            ((IntegerTextField) valueEditor).setText(obj.toString());
        else if ( valueEditor != null )
            ((IntegerTextField) valueEditor).setText(" ");


        if(D) System.out.println(S.concat("Ending"));
    }


    /** Allows customization of the IntegerTextField border */
    public void setWidgetBorder(Border b){
        ((IntegerTextField)valueEditor).setBorder(b);
    }

    /** This is where the IntegerTextField is defined and configured. */
    protected void addWidget() {

        String S = C + ": addWidget(): ";
        if(D) System.out.println(S + "Starting");

        valueEditor = new IntegerTextField();
        valueEditor.setMinimumSize( LABEL_DIM );
        valueEditor.setPreferredSize( LABEL_DIM );
        valueEditor.setBorder(ETCHED);
        valueEditor.setFont(this.DEFAULT_FONT);

        valueEditor.addFocusListener( this );
        valueEditor.addKeyListener( this );

        widgetPanel.add(valueEditor, ParameterEditor.WIDGET_GBC);
        widgetPanel.setBackground(null);
        widgetPanel.validate();
        widgetPanel.repaint();
        if(D) System.out.println(S + "Ending");
    }


    /**
     * Called everytime a key is typed in the text field to validate it
     * as a valid integer character ( digits and - sign in first position ).
     */
     public void keyTyped(KeyEvent e) throws NumberFormatException {

        String S = C + ": valueEditor_keyTyped(): ";
        super.keyTyped(e);

        keyTypeProcessing = false;
        if( focusLostProcessing == true ) return;

        if (e.getKeyChar() == '\n') {

            keyTypeProcessing = true;
            if(D) System.out.println(S + "Return key typed");
            String value = ((IntegerTextField) valueEditor).getText();

            if(D) System.out.println(S + "New Value = " + value);

            try {
                Integer d = null;
                if( !value.trim().equals( "" ) ) d = new Integer(value);
                setValue(d);
                refreshParamEditor();
                valueEditor.validate();
                valueEditor.repaint();
            }
            catch (ConstraintException ee) {
                if(D) System.out.println(S + "Error = " + ee.toString());

                Object obj = getValue();
                if( obj != null )
                    ((IntegerTextField) valueEditor).setText(obj.toString());
                else ((IntegerTextField) valueEditor).setText( " " );

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
    }

    /**
     * Called when the user clicks on another area of the GUI outside
     * this editor panel. This synchornizes the editor text field
     * value to the internal parameter reference.
     */
    public void focusLost(FocusEvent e) throws ConstraintException {

        String S = C + ": focusLost(): ";
        if(D) System.out.println(S + "Starting");

        super.focusLost(e);

        focusLostProcessing = false;
        if( keyTypeProcessing == true ) return;
        focusLostProcessing = true;

        String value = ((IntegerTextField) valueEditor).getText();
        try {

            Integer d = null;
            if( !value.trim().equals( "" ) ) d = new Integer(value);
            setValue(d);
            refreshParamEditor();
            valueEditor.validate();
            valueEditor.repaint();
        }
        catch (ConstraintException ee) {
            if(D) System.out.println(S + "Error = " + ee.toString());

            Object obj = getValue();
            if( obj != null )
                ((IntegerTextField) valueEditor).setText(obj.toString());
            else ((IntegerTextField) valueEditor).setText( " " );

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
        String S = C + ": setParameter(): ";
        if(D) System.out.println(S.concat("Starting"));

        super.setParameter(model);
        ((IntegerTextField) valueEditor).setToolTipText("No Constraints");

        String info = model.getInfo();
        if( (info != null ) && !( info.equals("") ) ){
            this.nameLabel.setToolTipText( info );
        }
        else this.nameLabel.setToolTipText( null);


        if(D) System.out.println(S.concat("Ending"));
    }

    /**
     * Updates the IntegerTextField string with the parameter value. Used when
     * the parameter is set for the first time, or changed by a background
     * process independently of the GUI. This could occur with a ParameterChangeFail
     * event.
     */
    public void refreshParamEditor(){
        Object obj = model.getValue();
        if ( obj != null )
            ((IntegerTextField) valueEditor).setText( obj.toString() );

        else ((IntegerTextField) valueEditor).setText( " " );

    }
}
