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

package org.opensha.refFaultParamDb.gui.view;

import java.awt.GridBagConstraints;
import java.awt.Insets;

import javax.swing.JPanel;

import org.opensha.commons.data.estimate.Estimate;
import org.opensha.commons.gui.LabeledBoxPanel;
import org.opensha.commons.param.StringParameter;
import org.opensha.refFaultParamDb.gui.CommentsParameterEditor;
import org.opensha.refFaultParamDb.gui.infotools.GUI_Utils;
import org.opensha.refFaultParamDb.gui.infotools.InfoLabel;
import org.opensha.refFaultParamDb.vo.CombinedSlipRateInfo;
import org.opensha.refFaultParamDb.vo.EstimateInstances;

/**
 * <p>Title: ViewSlipRate.java </p>
 * <p>Description: View Slip Rate Information for a  site for a specific time period </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class ViewSlipRate extends LabeledBoxPanel {
  private final static String SLIP_RATE_TITLE = "Slip Rate";
  private final static String SLIP_RATE_PANEL_TITLE = "Slip Rate Estimate(mm/yr)";
  private final static String ASEISMIC_PANEL_TITLE = "Aseismic Slip Factor(0-1, 1=all aseismic)";
  private final static String MEASURED_COMP_SLIP_TITLE = "Measured Component of Slip";
  private final static String SENSE_OF_MOTION_TITLE="Sense of Motion";

  private final static String SLIP_RATE = "Slip Rate";
  private final static String ASEISMIC_SLIP_FACTOR = "Aseismic Slip Factor";
  private final static String PROB = "Prob this is correct value";
  private final static String RAKE = "Rake";
  private final static String QUALITATIVE = "Qualitative";

  // various labels to provide the information
  private InfoLabel slipRateEstimateLabel = new InfoLabel();
  private InfoLabel aSesimicSlipFactorLabel = new InfoLabel();
  private InfoLabel senseOfMotionRakeLabel = new InfoLabel();
  private InfoLabel senseOfMotionQualLabel = new InfoLabel();
  private InfoLabel measuredCompQualLabel = new InfoLabel();
  private StringParameter commentsParam = new StringParameter("Slip Rate Comments");
  private CommentsParameterEditor commentsParameterEditor;

  public ViewSlipRate() {
    super(GUI_Utils.gridBagLayout);
    try {
      viewSlipRateForTimePeriod();
      setTitle(this.SLIP_RATE_TITLE);
    }catch(Exception e) {
      e.printStackTrace();
    }
  }

  /**
  * Show info about slip rate
  *
  * @param combinedDisplacementInfo
  */
 public void setInfo(CombinedSlipRateInfo combinedSlipRateInfo) {
   if(combinedSlipRateInfo ==null) setInfo(null, null, null, null, null, null);
   else {
     EstimateInstances aseismicSlipEstInstance = combinedSlipRateInfo.getASeismicSlipFactorEstimateForSlip();
     Estimate aseismicSlipEst = null;
     if(aseismicSlipEstInstance!=null) aseismicSlipEst = aseismicSlipEstInstance.getEstimate();
     setInfo(combinedSlipRateInfo.getSlipRateEstimate().getEstimate(),
             aseismicSlipEst,
             combinedSlipRateInfo.getSlipRateComments(),
             combinedSlipRateInfo.getSenseOfMotionRake(),
             combinedSlipRateInfo.getSenseOfMotionQual(),
             combinedSlipRateInfo.getMeasuredComponentQual());
   }
 }

  /**
   * Set the info about the slip rate, aseismic slip factor, comments and references
   *
   * @param slipRateEstimate
   * @param aSeismicSlipFactorEstimate
   * @param comments
   * @param references
   */
  private void setInfo(Estimate slipRateEstimate, Estimate aSeismicSlipFactorEstimate,
                       String comments, EstimateInstances rakeForSenseOfMotion, String senseOfMotionQual,
                       String measuredSlipQual) {
   slipRateEstimateLabel.setTextAsHTML(slipRateEstimate, SLIP_RATE, PROB);
   aSesimicSlipFactorLabel.setTextAsHTML(aSeismicSlipFactorEstimate, this.ASEISMIC_SLIP_FACTOR, PROB);
   commentsParam.setValue(comments);
   commentsParameterEditor.refreshParamEditor();
   this.measuredCompQualLabel.setTextAsHTML(this.QUALITATIVE, measuredSlipQual);
   // check whether sense of motion is available
   Estimate rakeEst = null;
   if(rakeForSenseOfMotion!=null) rakeEst = rakeForSenseOfMotion.getEstimate();
   this.senseOfMotionRakeLabel.setTextAsHTML(rakeEst, RAKE, PROB);
   this.senseOfMotionQualLabel.setTextAsHTML(this.QUALITATIVE,  senseOfMotionQual);
 }

  /**
   * display the slip Rate info for the selected time period
   */
  private void viewSlipRateForTimePeriod() throws Exception {
    JPanel slipRateEstimatePanel = GUI_Utils.getPanel(slipRateEstimateLabel,
                                            SLIP_RATE_PANEL_TITLE);
    JPanel aseismicPanel = GUI_Utils.getPanel(aSesimicSlipFactorLabel,
                                    ASEISMIC_PANEL_TITLE);
    JPanel senseOfMotionPanel = GUI_Utils.getPanel(this.SENSE_OF_MOTION_TITLE);
    JPanel measuredSlipCompPanel = GUI_Utils.getPanel(this.MEASURED_COMP_SLIP_TITLE);
    commentsParameterEditor = new CommentsParameterEditor(commentsParam);
    commentsParameterEditor.setEnabled(false);
    // sense of motion panel
    senseOfMotionPanel.add(this.senseOfMotionRakeLabel, new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
        , GridBagConstraints.CENTER, GridBagConstraints.BOTH,
        new Insets(0, 0, 0, 0), 0, 0));
    senseOfMotionPanel.add(this.senseOfMotionQualLabel, new GridBagConstraints(0, 1, 1, 1, 1.0, 1.0
        , GridBagConstraints.CENTER, GridBagConstraints.BOTH,
        new Insets(0, 0, 0, 0), 0, 0));
    // measured component of slip panel
    measuredSlipCompPanel.add(this.measuredCompQualLabel, new GridBagConstraints(0, 0, 1, 1, 1.0, 1.0
        , GridBagConstraints.CENTER, GridBagConstraints.BOTH,
        new Insets(0, 0, 0, 0), 0, 0));

    // add the slip rate info the panel
    int yPos = 0;
    add(slipRateEstimatePanel, new GridBagConstraints(0, yPos++, 1, 1, 1.0, 1.0
        , GridBagConstraints.CENTER, GridBagConstraints.BOTH,
        new Insets(0, 0, 0, 0), 0, 0));
    add(measuredSlipCompPanel, new GridBagConstraints(0, yPos++, 1, 1, 1.0, 1.0
        , GridBagConstraints.CENTER, GridBagConstraints.BOTH,
        new Insets(0, 0, 0, 0), 0, 0));
    add(senseOfMotionPanel, new GridBagConstraints(0, yPos++, 1, 1, 1.0, 1.0
            , GridBagConstraints.CENTER, GridBagConstraints.BOTH,
            new Insets(0, 0, 0, 0), 0, 0));
    add(aseismicPanel, new GridBagConstraints(0, yPos++, 1, 1, 1.0, 1.0
                                              , GridBagConstraints.CENTER,
                                              GridBagConstraints.BOTH,
                                              new Insets(0, 0, 0, 0), 0, 0));
    add(commentsParameterEditor, new GridBagConstraints(0, yPos++, 1, 1, 1.0, 1.0
                                              , GridBagConstraints.CENTER,
                                              GridBagConstraints.BOTH,
                                              new Insets(0, 0, 0, 0), 0, 0));
  }
}
