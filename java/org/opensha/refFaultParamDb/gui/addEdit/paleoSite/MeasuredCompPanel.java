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

package org.opensha.refFaultParamDb.gui.addEdit.paleoSite;

import java.awt.GridBagConstraints;
import java.awt.Insets;
import java.util.ArrayList;

import javax.swing.JPanel;

import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.editor.ConstrainedStringParameterEditor;
import org.opensha.refFaultParamDb.gui.infotools.GUI_Utils;

/**
 * <p>Title: SenseOfMotion_MeasuredCompPanel.java </p>
 * <p>Description: this panel can be added to various GUI componenets where
 * we need Measured Component of Slip Parameters.</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class MeasuredCompPanel extends JPanel  {
  private final static String MEASURED_COMP_PARAM_NAME = "Measured Component";
  private final static String UNKNOWN  = "Unknown";
  private StringParameter measuredCompParam; // measured component pick list

  private ConstrainedStringParameterEditor measuredCompParamEditor;

  public MeasuredCompPanel() {
    this.setLayout(GUI_Utils.gridBagLayout);
    initParamListAndEditor();
    addEditorsToGUI();
  }

  private void initParamListAndEditor() {
    try {
      // measured component
      ArrayList allowedMeasuredComps = getAllowedMeasuredComponents();
      measuredCompParam = new StringParameter(MEASURED_COMP_PARAM_NAME,
                                              allowedMeasuredComps,
                                              (String) allowedMeasuredComps.get(
          0));
      measuredCompParamEditor = new ConstrainedStringParameterEditor(measuredCompParam);
    }catch(Exception e) {
      e.printStackTrace();
    }
  }

  /**
   * Set the value for measured component of slip
   *
   * @param value
   */
  public void setMeasuredCompVal(String value) {
    if(value==null) value=this.UNKNOWN;
    measuredCompParam.setValue(value);
    measuredCompParamEditor.refreshParamEditor();
  }

  private void addEditorsToGUI() {
    int yPos=0;
    this.add(measuredCompParamEditor,new GridBagConstraints(0, yPos++, 1, 1, 1.0, 1.0
        , GridBagConstraints.CENTER, GridBagConstraints.BOTH, new Insets(0, 0, 0, 0), 0, 0));
  }

  /**
   * Get the allowed measured components
   * @return
   */
  private ArrayList getAllowedMeasuredComponents() {
    ArrayList measuredComps = new ArrayList();
    measuredComps.add(UNKNOWN);
    measuredComps.add("Total");
    measuredComps.add("Vertical");
    measuredComps.add("Horizontal,Trace-Parallel");
    measuredComps.add("Horizontal,Trace-NORMAL");
    return measuredComps;
  }

  /**
  * Get the measured component qualitative value
  * If it Unknown or if rake is provided, null is returned
  * @return
  */
 public String getMeasuredComp() {
   String value = (String)this.measuredCompParam.getValue();
   if(value.equalsIgnoreCase(UNKNOWN)) return null;
   return value;
 }
}
