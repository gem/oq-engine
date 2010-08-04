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

package org.opensha.sha.param.editor;

import java.util.ListIterator;
import java.util.Vector;

import javax.swing.JComboBox;

import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterConstraintAPI;
import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ConstrainedStringParameterEditor;
import org.opensha.sha.magdist.SummedMagFreqDist;
import org.opensha.sha.param.MagDistStringParameter;

/**
 * <b>Title:</b> MagDistStringParameterEditor<p>
 *
 * <b>Description:</b> This editor is for editing
 * MagDistStringParameters. Recall a MagDistStringParameter
 * contains a list of the only allowed values. Therefore this editor
 * presents a picklist of those allowed values, instead of a
 * JTextField or subclass. <p>
 *
 * @author Steven W. Rock
 * @version 1.0
 */

public class MagDistStringParameterEditor extends
		ConstrainedStringParameterEditor {

	public MagDistStringParameterEditor() {
		super();
	}
	
	public MagDistStringParameterEditor(ParameterAPI param) {
		super(param);
	}
	
   /**
     * The parameter is checked that it is a
     * MagDistStringParameter, and the constraint is checked that it is a
     * StringConstraint. Then the constraints are checked that
     * there is at least one. If any of these fails an error is thrown.
     */
    protected void verifyModel(ParameterAPI model) throws ConstraintException{

        String S = C + ": Constructor(model): ";
        if(D) System.out.println(S + "Starting");

        if (model == null) {
            throw new NullPointerException(S + "Input Parameter model cannot be null");
        }

        if (!(model instanceof MagDistStringParameter))
            throw new ConstraintException(S + "Input model parameter must be a MagDistStringParameter.");

        ParameterConstraintAPI constraint = model.getConstraint();

        if (!(constraint instanceof StringConstraint))
            throw new ConstraintException(S + "Input model constraints must be a StringConstraint.");

        int numConstriants = ((StringConstraint)constraint).size();
        if(numConstriants < 1)
            throw new ConstraintException(S + "There are no constraints present, unable to build editor selection list.");

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
                if(!str.trim().equals(SummedMagFreqDist.NAME))
                  if (!strs.contains(str)) strs.add(str);
            }

            if(strs.size() > 1){

                valueEditor = new JComboBox(strs);
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

    
    
	
}
