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

import java.util.ArrayList;
import java.util.ListIterator;
import java.util.Vector;

import javax.swing.JList;
import javax.swing.JScrollPane;
import javax.swing.ListModel;
import javax.swing.event.ListSelectionEvent;
import javax.swing.event.ListSelectionListener;

import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterConstraintAPI;
import org.opensha.commons.param.StringListConstraint;
import org.opensha.commons.param.StringListParameter;

/**
 * <b>Title:</b> ConstrainedStringParameterEditor<p>
 *
 * <b>Description:</b> This editor is for editing
 * ConstrainedStringListParameters. Recall a ConstrainedStringListParameter
 * contains a list of the only allowed values and user can select multiple
 * values from this list . Therefore this editor
 * presents a picklist of those allowed values using JList. <p>
 *
 * @author
 * @version 1.0
 */

public class ConstrainedStringListParameterEditor
    extends ParameterEditor
    implements ListSelectionListener
{

    /** Class name for debugging. */
    protected final static String C = "ConstrainedStringListParameterEditor";
    /** If true print out debug statements. */
    protected final static boolean D = false;



    /** No-Arg constructor calls parent constructtor */
    public ConstrainedStringListParameterEditor() {

        super();

        String S = C + ": Constructor(): ";
        if(D) System.out.println(S + "Starting");

        if(D) System.out.println(S + "Ending");
    }

    /**
     * Sets the model in this constructor. The parameter is checked that it is a
     * StringListParameter, and the constraint is checked that it is a
     * StringListConstraint. Then the constraints are checked that
     * there is at least one. If any of these fails an error is thrown. <P>
     *
     * A tooltip is given to the name label if model info is available.
     */
    public ConstrainedStringListParameterEditor(ParameterAPI model)
            throws ConstraintException {

        super(model);

        String S = C + ": Constructor(model): ";
        if(D) System.out.println(S + "Starting");

        if(D) System.out.println(S + "Ending");
    }

    /**
     * Can change the parameter of this editor. Usually called once when
     * initializing the editor. The parameter is checked that it is a
     * StringListParameter, and the constraint is checked that it is a
     * StringListConstraint. Then the constraints are checked that
     * there is at least one.
     * <P>
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
     * StringListParameter, and the constraint is checked that it is a
     * StringListConstraint. Then the constraints are checked that
     * there is at least one. If any of these fails an error is thrown.
     */
    private void verifyModel(ParameterAPI model) throws ConstraintException{

        String S = C + ": Constructor(model): ";
        if(D) System.out.println(S + "Starting");

        if (model == null) {
            throw new NullPointerException(S + "Input Parameter model cannot be null");
        }

        if (!(model instanceof StringListParameter))
            throw new ConstraintException(S + "Input model parameter must be a StringListParameter.");

        ParameterConstraintAPI constraint = model.getConstraint();

        if (!(constraint instanceof StringListConstraint))
            throw new ConstraintException(S + "Input model constraints must be a StringListConstraint.");

        int numConstriants = ((StringListConstraint)constraint).size();
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

        if ( ( obj != null ) && ( valueEditor != null ) && ( valueEditor instanceof JList ) ) {
           setSelectedItems((ArrayList)obj);
        }

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

            StringListConstraint con =
                (StringListConstraint) ((StringListParameter) model).getConstraint();

            ListIterator it = con.listIterator();
            Vector strs = new Vector();
            while (it.hasNext()) {
                String str = it.next().toString();
                if (!strs.contains(str)) strs.add(str);
            }


            valueEditor = new JList(strs);
            valueEditor.setFont(DEFAULT_FONT);
            JScrollPane scrollPane= new JScrollPane(valueEditor);
            scrollPane.setPreferredSize(JLIST_DIM);
            scrollPane.setMinimumSize(JLIST_DIM);
            widgetPanel.setPreferredSize(JLIST_DIM);
            widgetPanel.setMinimumSize(JLIST_DIM);

            ( (JList) valueEditor).addListSelectionListener(this);
            widgetPanel.add(scrollPane, WIDGET_GBC);
            widgetPanel.setBackground(null);
            widgetPanel.validate();
            widgetPanel.repaint();
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
        if( valueEditor instanceof JList ) {
            ArrayList list = (ArrayList)model.getValue();
            if( list != null ) setSelectedItems(list);
        }
    }

    /**
     * It accepts the list of Strings and marks them as selected in the JList
     *
     * @param selectItemsList
     */
    private void setSelectedItems(ArrayList selectItemsList) {
      int size = selectItemsList.size();
      StringListConstraint stringListConstraint  = (StringListConstraint)this.model.getConstraint();
      ArrayList allowedVals = stringListConstraint.getAllowedValues();
      int selectedIndices[] = new int[size];
      int index;
      for(int i=0; i<size; ++i ) {
        index = allowedVals.indexOf(selectItemsList.get(i));
        if(index>=0) selectedIndices[i] = index;
        else new ConstraintException (selectItemsList.get(i).toString()+" is not allowed");
      }
      ((JList)valueEditor).setSelectedIndices(selectedIndices);
    }


    /**
     * This method is called when a selection is changed in the JList
     * @param event
     */
    public void valueChanged(ListSelectionEvent event) {
      int[] selectedIndices = ((JList)valueEditor).getSelectedIndices();
      ListModel listModel = ((JList)valueEditor).getModel();
      ArrayList list = new ArrayList();
      for(int i=0; i<selectedIndices.length; ++i)
        list.add(listModel.getElementAt(selectedIndices[i]));
      model.setValue(list);
    }


}
