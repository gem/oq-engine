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

package org.opensha.sha.gui.controls;



/**
 * <p>Title: PlotColorAndLineTypeSelectorControlPanelAPI</p>
 * <p>Description: Application using PlotColorAndLineTypeSelectorControlPanel
 * implements this interface, so if control panel needs to call a
 * method of application, it can do that without knowing which class method
 * needs to be called.</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author unascribed
 * @version 1.0
 */

public interface PlotColorAndLineTypeSelectorControlPanelAPI {

  /**
   * plots the curves with defined color,line width and shape.
   *
   */
   public void plotGraphUsingPlotPreferences();

   /**
    *
    * @returns the X Axis Label
    */
   public String getXAxisLabel();

   /**
    *
    * @returns Y Axis Label
    */
   public String getYAxisLabel();

   /**
    *
    * @returns plot Title
    */
   public String getPlotLabel();

   /**
    *
    * sets  X Axis Label
    */
   public void setXAxisLabel(String xAxisLabel);

   /**
    *
    * sets Y Axis Label
    */
   public void setYAxisLabel(String yAxisLabel);

   /**
    *
    * sets plot Title
    */
   public void setPlotLabel(String plotTitle);
}
