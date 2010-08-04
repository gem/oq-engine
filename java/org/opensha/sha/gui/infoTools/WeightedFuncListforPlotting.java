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

package org.opensha.sha.gui.infoTools;

import org.opensha.commons.data.function.WeightedFuncList;


/**
 * <p>Title: WeightedFuncListforPlotting</p>
 * <p>Description: This class creates the plotting capabilities for Weighted function
 * as required by our wrapper to Jfreechart.</p>
 * @author : Ned Field, Nitin Gupta
 * @version 1.0
 */

public class WeightedFuncListforPlotting extends WeightedFuncList{


  private boolean individualCurvesToPlot = true;
  private boolean fractilesToPlot = true;
  private boolean meantoPlot = true;




  /**
   * Sets boolean based on if application needs to plot individual curves
   * @param toPlot
   */
  public void setIndividualCurvesToPlot(boolean toPlot){
    individualCurvesToPlot = toPlot;
  }


  /**
   * Sets boolean based on if application needs to plot fractiles
   * @param toPlot
   */
  public void setFractilesToPlot(boolean toPlot){
    fractilesToPlot = toPlot;
  }

  /**
   * Sets boolean based on if application needs to plot mean curve
   * @param toPlot
   */
  public void setMeanToPlot(boolean toPlot){
    meantoPlot = toPlot;
  }

  /**
   *
   * @returns true if individual plots need to be plotted , else return false
   */
  public boolean areIndividualCurvesToPlot(){
    return individualCurvesToPlot;
  }

  /**
   *
   * @returns true if fractile plots need to be plotted, else return false
   */
  public boolean areFractilesToPlot(){
    return fractilesToPlot;
  }

  /**
   *
   * @returns true if mean curve needs to be plotted, else return false.
   */
  public boolean isMeanToPlot(){
    return meantoPlot;
  }



}
