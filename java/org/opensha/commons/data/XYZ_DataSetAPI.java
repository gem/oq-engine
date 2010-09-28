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

package org.opensha.commons.data;

import java.util.ArrayList;
/**
 * <p>Title: XYZ_DataSetAPI</p>
 * <p>Description: This interface defines the DataSet for the X,Y and Z.
 * It is the quick and dirty solution for the time being, and we need to fix
 * it with the same fuctionality as our 2-D representation of the data based
 * on the requirement.</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author : Ned Field, Nitin Gupta and Vipin Gupta
 * @version 1.0
 */

public interface XYZ_DataSetAPI extends java.io.Serializable{


  //gets the Min of the  X values
  public double getMinX();

  //gets the Max of the X values
  public double getMaxX();

  //gets the Min of the Y values
  public double getMinY();

  //gets the Max of the Y values
  public double getMaxY();

  //gets the Min of the Z values
  public double getMinZ();

  //gets the Max of the Z values
  public double getMaxZ();

  //sets the X, Y , Z values as the vector of double
  public void setXYZ_DataSet(ArrayList<Double> xVals, ArrayList<Double> yVals,ArrayList<Double> zVals);

  //gets the X values dataSet
  public ArrayList<Double> getX_DataSet();

  //gets the Y values dataSet
  public ArrayList<Double> getY_DataSet();

  //gets the Z values dataSet
  public ArrayList<Double> getZ_DataSet();

  //returns true if size ArrayList for X,Y and Z dataset values is equal else return false
  public boolean checkXYZ_NumVals();
  
  public void addValue(double xVal, double yVal, double zVal);
}
