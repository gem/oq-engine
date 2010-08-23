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
import java.awt.event.ItemEvent;
import java.awt.event.ItemListener;
import java.util.ListIterator;
import java.util.Vector;

import javax.swing.JComboBox;

import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterConstraintAPI;
import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.StringParameter;

/**
 * <b>Title:</b> ConstrainedStringParameterEditor<p>
 *
 * <b>Description:</b> This editor is for editing
 * ConstrainedStringParameters. Recall a ConstrainedStringParameter
 * contains a list of the only allowed values. Therefore this editor
 * presents a picklist of those allowed values, instead of a
 * JTextField or subclass. <p>
 *
 * @author Steven W. Rock
 * @version 1.0
 */

public class ConstrainedStringParameterEditor
    extends ParameterEditor
    implements ItemListener
{

    /** Class name for debugging. */
    protected final static String C = "ConstrainedStringParameterEditor";
    /** If true print out debug statements. */
    protected final static boolean D = false;


    /** No-Arg constructor calls parent constructtor */
    public ConstrainedStringParameterEditor() {

        super();

        String S = C + ": Constructor(): ";
        if(D) System.out.println(S + "Starting");

        if(D) System.out.println(S + "Ending");
    }

    /**
     * Sets the model in this constructor. The parameter is checked that it is a
     * StringParameter, and the constraint is checked that it is a
     * StringConstraint. Then the constraints are checked that
     * there is at least one. If any of these fails an error is thrown. <P>
     *
     * The widget is then added to this editor, based on the number of
     * constraints. If only one the editor is made into a non-editable label,
     * else a picklist of values to choose from are presented to the user.
     * A tooltip is given to the name label if model info is available.
     */
    public ConstrainedStringParameterEditor(ParameterAPI model)
	    throws ConstraintException {

        super(model);

        String S = C + ": Constructor(model): ";
        if(D) System.out.println(S + "Starting");

        setParameter(model);

        if(D) System.out.println(S + "Ending");
    }

    /**
     * Can change the parameter of this editor. Usually called once when
     * initializing the editor. The parameter is checked that it is a
     * StringParameter, and the constraint is checked that it is a
     * StringConstraint. Then the constraints are checked that
     * there is at least one. If any of these fails an error is thrown.
     * <P>
     * The widget is then added to this editor, based on the number of
     * constraints. If only one the editor is made into a non-editable label,
     * else a picklist of values to choose from are presented to the user.
     * A tooltip is given to the name label if model info is available.
     */
    public void setParameter(ParameterAPI model){

        String S = C + ": setParameter(): ";
        verifyModel(model);
        this.model = model;

        String name = model.getName();
        Object value = model.getValue();

        removeWidget();
	    addWidget();

        setWidgetObject(name, value);

    }

    /**
     * The parameter is checked that it is a
     * DoubleDiscreteParameter, and the constraint is checked that it is a
     * DoubleDiscreteConstraint. Then the constraints are checked that
     * there is at least one. If any of these fails an error is thrown.
     */
    protected void verifyModel(ParameterAPI model) throws ConstraintException{

        String S = C + ": Constructor(model): ";
        if(D) System.out.println(S + "Starting");

        if (model == null) {
            throw new NullPointerException(S + "Input Parameter model cannot be null");
        }

        if (!(model instanceof StringParameter))
            throw new ConstraintException(S + "Input model parameter must be a StringParameter.");

        ParameterConstraintAPI constraint = model.getConstraint();

        if (!(constraint instanceof StringConstraint))
            throw new ConstraintException(S + "Input model constraints must be a StringConstraint.");

        int numConstriants = ((StringConstraint)constraint).size();
        if(numConstriants < 1)
            throw new ConstraintException(S + "There are no constraints present, unable to build editor selection list.");

        if(D) System.out.println(S + "Ending");
    }


     /** Not implemented */
    public void setAsText(String string) throws IllegalArgumentException { }

    /**
     * Set's the name label, and the picklist value from the passed in
     * values, i.e. model sets the gui
     */
    protected void setWidgetObject(String name, Object obj) {
        String S = C + ": setWidgetObject(): ";
        if(D) System.out.println(S + "Starting: Name = " + name + ": Object = " + obj.toString());

        super.setWidgetObject(name, obj);

        if ( ( obj != null ) && ( valueEditor != null ) && ( valueEditor instanceof JComboBox ) )
            ((JComboBox) valueEditor).setSelectedItem(obj.toString());

        if(D) System.out.println(S + "Ending");
    }

    /**
     * This is where the JComboBox picklist is defined and configured.
     * This function adds a little more intellegence in that if there
     * is only one constraint, it only adds a lable instead of a picklist.
     * No need to give a list of choices when there is only one allowed
     * value.
     */
    protected void addWidget() {
        String S = C + ": addWidget(): ";
        if(D) System.out.println(S + "Starting");

        //if(widgetPanel != null) widgetPanel.removeAll();
        if (model != null) {

            StringConstraint con =
                (StringConstraint) ((StringParameter) model).getConstraint();

            ListIterator it = con.listIterator();
            Vector strs = new Vector();
            while (it.hasNext()) {
                String str = it.next().toString();
                if (!strs.contains(str)) strs.add(str);
            }

            if(strs.size() > 1){
            	JComboBox jcb = new JComboBox(strs);
            	jcb.setMaximumRowCount(32);
                valueEditor = jcb;
                valueEditor.setPreferredSize(JCOMBO_DIM);
                valueEditor.setMinimumSize(JCOMBO_DIM);
                valueEditor.setFont(JCOMBO_FONT);
                //valueEditor.setBackground(this.BACK_COLOR);
                ((JComboBox) valueEditor).addItemListener(this);
                valueEditor.addFocusListener( this );
                widgetPanel.add(valueEditor, COMBO_WIDGET_GBC);
                widgetPanel.setBackground(null);
                widgetPanel.validate();
                widgetPanel.repaint();
            }
            else{
                valueEditor = makeConstantEditor( strs.get(0).toString() );
                widgetPanel.setBackground(STRING_BACK_COLOR);
                 widgetPanel.add(valueEditor, WIDGET_GBC);
            }


            //widgetPanel.add(valueEditor,
              //      new GridBagConstraints(0, 0, 1, 1, 1.0, 0.0, 10, 2,
                //               new Insets(1, 1, 0, 1), 0,
                  //             0));

        }

        if(D) System.out.println(S + "Ending");
    }

    /**
     * Updates the JComboBox selected value with the parameter value. Used when
     * the parameter is set for the first time, or changed by a background
     * process independently of the GUI. This could occur with a
     * ParameterChangeFail event.
     */
    public void refreshParamEditor(){
        if( valueEditor instanceof JComboBox ){

            Object obj = model.getValue();
            if( obj != null )
                ((JComboBox)valueEditor).setSelectedItem( obj.toString() );
        }
    }

    /**
     * Called whenever a user picks a new value in the picklist, i.e.
     * synchronizes the model to the new GUI value. This is where the
     * picklist value is set in the ParameterAPI of this editor.
     */
    public void itemStateChanged(ItemEvent e) {
        String S = C + ": itemStateChanged(): ";
        if(D) System.out.println(S + "Starting: " + e.toString());

        String value = ((JComboBox) valueEditor).getSelectedItem().toString();
        if(D) System.out.println(S + "New Value = " + (value) );
        this.setValue(value);

        if(D) System.out.println(S + "Ending");
    }




    /**
     * Called everytime a key is typed in the text field to validate it
     * as a valid integer character ( digits and - sign in first position ).
     */
    public void focusGained(FocusEvent e) { super.focusGained(e); }

    /**
     * Called when the user clicks on another area of the GUI outside
     * this editor panel. This synchornizes the editor text field
     * value to the internal parameter reference.
     */
    public void focusLost(FocusEvent e) { super.focusLost(e); }


}
