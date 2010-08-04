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

package org.opensha.nshmp.param.editor;

import javax.swing.JComboBox;

import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.editor.ConstrainedStringParameterEditor;

/**
 * <p>Title: EditableConstrainedStringParameterEditor.java </p>
 * <p>Description: This is same as ConstrainedStringParameterEditor. Only difference
 * here is that the comboBox is editable in this case. </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class EditableConstrainedStringParameterEditor extends ConstrainedStringParameterEditor {

  /**
   * Constructor
   */
  public EditableConstrainedStringParameterEditor() {
  }

  /**
   *
   * @param model
   * @throws ConstraintException
   */
  public EditableConstrainedStringParameterEditor(ParameterAPI model) throws ConstraintException {
    super(model);
  }

  /**
   * The implementation is same as for ConstrainedStringParameterEditor. The only
   * addition here is that JComboBox has been made editable in this case.
   */
  protected void addWidget() {
    super.addWidget();
		this.valueEditor.setSize(1000,50);
    if(this.valueEditor instanceof JComboBox) {
      JComboBox pickList = (JComboBox)valueEditor;
      pickList.setEditable(true);
    }
  }
}
