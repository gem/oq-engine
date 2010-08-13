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
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.ParameterAPI;

/**
 * <b>Title:</b> DoubleParameterEditor<p>
 *
 * <b>Description:</b> Subclass of ParameterEditor for editing DoubleParameters.
 * The widget is an DoubleTextField so that only numbers can be typed in. <p>
 *
 * The main functionality overidden from the parent class to achive Double
 * cusomization are the setWidgetObject() and AddWidget() functions. The parent's
 * class JComponent valueEditor field becomes an NumericTextField,  a subclass
 * of a JTextField.
 * Note: We have to create a double parameter with constraints if we want to reflect the constarints
 *       as the tooltip text in the GUI. Because when we editor is created for that
 *       double parameter, it creates a constraint double parameter and then we can
 *       change the constraint and it will be reflected in the tool tip text.
 * <p>
 *
 * @author Steven W. Rock
 * @version 1.0
 */
public class DoubleParameterEditor extends ParameterEditor
{

    /** Class name for debugging. */
    protected final static String C = "DoubleParameterEditor";
    /** If true print out debug statements. */
    protected final static boolean D = false;

    /** No-Arg constructor calls parent constructtor */
    public DoubleParameterEditor() { super(); }

    /**
     * Constructor that sets the parameter that it edits.
     *
     * Note: When calling the super() constuctor addWidget() is called
     * which configures the NumericTextField as the editor widget. <p>
     */
     public DoubleParameterEditor(ParameterAPI model) throws Exception {

        super(model);

        String S = C + ": Constructor(model): ";
        if(D) System.out.println(S + "Starting");

        this.setParameter(model);

        if(D) System.out.println(S + "Ending");

    }

    /**
     * The parameter is checked that it is not null and a
     * DoubleDiscreteParameter. If any of these fails an error is thrown.
     */
    private void verifyModel(ParameterAPI model) throws ConstraintException{

        String S = C + ": Constructor(model): ";
        if(D) System.out.println(S + "Starting");

        if (model == null) {
            throw new NullPointerException(S + "Input Parameter model cannot be null");
        }

        if (!(model instanceof DoubleParameter))
            throw new ConstraintException(S + "Input model parameter must be a DoubleParameter.");

        if(D) System.out.println(S + "Ending");
    }


    /** Currently does nothing */
    public void setAsText(String string) throws IllegalArgumentException { }

    /** Passes in a new Parameter with name to set as the parameter to be editing */
    protected void setWidgetObject(String name, Object obj) {
        String S = C + ": setWidgetObject(): ";
        if(D) System.out.println(S + "Starting");


        super.setWidgetObject(name, obj);

        if ( ( obj != null ) &&  ( valueEditor != null ) )
            ((NumericTextField) valueEditor).setText(obj.toString());

        if(D) System.out.println(S + "Ending");
    }

    /** Allwos customization of the NumericTextField border */
    public void setWidgetBorder(Border b){
        ((NumericTextField)valueEditor).setBorder(b);
    }

    /** This is where the NumericTextField is defined and configured. */
    protected void addWidget() {
        String S = C + "DoubleParameterEditor: addWidget(): ";
        if(D) System.out.println(S + "Starting");

        valueEditor = new NumericTextField();
        valueEditor.setMinimumSize( LABEL_DIM );
        valueEditor.setPreferredSize( LABEL_DIM );
        valueEditor.setBorder(ETCHED);
        valueEditor.setFont(this.DEFAULT_FONT);

        valueEditor.addFocusListener( this );
        valueEditor.addKeyListener( this );

        widgetPanel.add(valueEditor, ParameterEditor.WIDGET_GBC);

        if(D) System.out.println(S + "Ending");
    }

    /**
     * Called everytime a key is typed in the text field to validate it
     * as a valid number character ( digits, - sign in first position, etc. ).
     */
    public void keyTyped(KeyEvent e) throws NumberFormatException {

        String S = C + ": keyTyped(): ";
        if(D) System.out.println(S + "Starting");
        super.keyTyped(e);

        keyTypeProcessing = false;
        if( focusLostProcessing == true ) return;


        if (e.getKeyChar() == '\n') {
            keyTypeProcessing = true;
            if(D) System.out.println(S + "Return key typed");
            String value = ((NumericTextField) valueEditor).getText();

            if(D) System.out.println(S + "New Value = " + value);
            try {
                Double d = null;
                 if( !value.equals( "" ) ) d = new Double(value);
                setValue(d);
                refreshParamEditor();
                valueEditor.validate();
                valueEditor.repaint();
            }
            catch (ConstraintException ee) {
                if(D) System.out.println(S + "Error = " + ee.toString());

                Object obj = getValue();
                if( obj != null )
                    ((NumericTextField) valueEditor).setText(obj.toString());
                else ((NumericTextField) valueEditor).setText( "" );

                if( !catchConstraint ){ this.unableToSetValue(value); }
                keyTypeProcessing = false;
            }
            catch (NumberFormatException ee) {
                if(D) System.out.println(S + "Error = " + ee.toString());

                Object obj = getValue();
                if( obj != null )
                    ((NumericTextField) valueEditor).setText(obj.toString());
                else ((NumericTextField) valueEditor).setText( "" );

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
    public void focusLost(FocusEvent e)throws ConstraintException {


        String S = C + ": focusLost(): ";
        if(D) System.out.println(S + "Starting");
        focusLostProcessing = false;
        if( keyTypeProcessing == true ) return;
        focusLostProcessing = true;

        String value = ((NumericTextField) valueEditor).getText();
        try {

            Double d = null;
            if( !value.equals( "" ) ) d = new Double(value);
            setValue(d);
            refreshParamEditor();
            valueEditor.validate();
            valueEditor.repaint();
        }
        catch (ConstraintException ee) {
            if(D) System.out.println(S + "Error = " + ee.toString());

            Object obj = getValue();
            if( obj != null )
                ((NumericTextField) valueEditor).setText(obj.toString());
            else ((NumericTextField) valueEditor).setText( "" );

            if( !catchConstraint ){ this.unableToSetValue(value); }
            focusLostProcessing = false;
        }
        catch (NumberFormatException ee) {
                if(D) System.out.println(S + "Error = " + ee.toString());

                Object obj = getValue();
                if( obj != null )
                    ((NumericTextField) valueEditor).setText(obj.toString());
                else ((NumericTextField) valueEditor).setText( "" );

                if( !catchConstraint ){ this.unableToSetValue(value); }
                keyTypeProcessing = false;
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
        if(D) System.out.println(S + "Starting");

        super.setParameter(model);
        ((NumericTextField) valueEditor).setToolTipText("No Constraints");

        String info = model.getInfo();
        if( (info != null ) && !( info.equals("") ) ){
            this.nameLabel.setToolTipText( info );
        }
        else this.nameLabel.setToolTipText( null);


        if(D) System.out.println(S + "Ending");
    }

    /**
     * Updates the NumericTextField string with the parameter value. Used when
     * the parameter is set for the first time, or changed by a background
     * process independently of the GUI. This could occur with a ParameterChangeFail
     * event.
     */
    public void refreshParamEditor(){

        Object obj = model.getValue();
        if( obj != null )
            ((NumericTextField) valueEditor).setText( obj.toString() );

        else ((NumericTextField) valueEditor).setText( "" ) ;

    }
}
