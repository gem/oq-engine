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

import java.util.ArrayList;


/**
 * <p>Title: GraphWindowAPI</p>
 * <p>Description: This interface has to be implemented by the application that uses
 * GraphWindow class</p>
 * @author : Nitin Gupta
 * @version 1.0
 */

public interface GraphWindowAPI {



  /**
   *
   * @returns the List for all the ArbitrarilyDiscretizedFunctions and Weighted Function list.
   */
  public ArrayList getCurveFunctionList();

  /**
   *
   * @returns the boolean: Log for X-Axis Selected
   */
  public boolean getXLog();

  /**
   *
   * @returns the boolean: Log for Y-Axis Selected
   */
  public boolean getYLog();

  //get Y axis Label
  public String getXAxisLabel();

  //gets X Axis Label
  public String getYAxisLabel();

  /**
   *
   * @returns the plotting feature like width, color and shape type of each
   * curve in list.
   */
   public ArrayList getPlottingFeatures();


  /**
   *
   * @returns boolean: Checks if Custom Axis is selected
   */
  public boolean isCustomAxis();

  /**
   *
   * @returns the Min X-Axis Range Value, if custom Axis is choosen
   */
  public double getMinX();

  /**
   *
   * @returns the Max X-Axis Range Value, if custom axis is choosen
   */
  public double getMaxX();

  /**
   *
   * @returns the Min Y-Axis Range Value, if custom axis is choosen
   */
  public double getMinY();

  /**
   *
   * @returns the Max Y-Axis Range Value, if custom axis is choosen
   */
  public double getMaxY();


}
