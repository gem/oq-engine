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

import java.awt.Color;

/**
 * <p>Title: PlotCurveCharacterstics</p>
 * <p>Description: This class handle characterstic feature of each curve, like
 * its color, linetype(rendrer type), width</p>
 * @author : Nitin Gupta
 * @version 1.0
 */

public class PlotCurveCharacterstics {

  //shape of curve while plotting it
  private String curveType;
  //color of the color
  private Color curveColor;
  //width of the curve when plotted
  private double curveWidth;

  //name of selected curve
  private String curveName = "Data";

  //num of continuous curves with same characterstics as above
  private int numCurvesWithSamePlottingFeatures =1;

  public PlotCurveCharacterstics() {};

  /**
   *
   * @param lineType
   * @param lineColor
   * @param lineWidth
   */
  public PlotCurveCharacterstics(String lineType,Color lineColor,double lineWidth){
    curveType =lineType;
    curveColor =lineColor;
    curveWidth =lineWidth;
  }

  /**
   * @param lineName
   * @param lineType
   * @param lineColor
   * @param lineWidth
   */
  public PlotCurveCharacterstics(String lineName,String lineType,Color lineColor,double lineWidth){
    curveName = lineName;
    curveType =lineType;
    curveColor =lineColor;
    curveWidth =lineWidth;
  }

  /**
   *
   * @param lineType
   * @param lineColor
   * @param lineWidth
   * @param numConsecutiveCurvesWithSamePlotFeatures
   */
  public PlotCurveCharacterstics(String lineType,Color lineColor,double lineWidth,
                                 int numConsecutiveCurvesWithSamePlotFeatures){
    curveType =lineType;
    curveColor =lineColor;
    curveWidth =lineWidth;
    numCurvesWithSamePlottingFeatures = numConsecutiveCurvesWithSamePlotFeatures;
  }

  /**
   * @param lineName
   * @param lineType
   * @param lineColor
   * @param lineWidth
   * @param numConsecutiveCurvesWithSamePlotFeatures
   */
  public PlotCurveCharacterstics(String lineName,String lineType,Color lineColor,
                                 double lineWidth,int numConsecutiveCurvesWithSamePlotFeatures){
    curveName = lineName;
    curveType =lineType;
    curveColor =lineColor;
    curveWidth =lineWidth;
    numCurvesWithSamePlottingFeatures = numConsecutiveCurvesWithSamePlotFeatures;
  }


  /**
   * Sets the shape of curve
   * @param curveType
   */
  public void setCurveType(String curveType){
    this.curveType = curveType;
  }


  /**
   * Set curve color
   * @param curveColor
   */
  public void setCurveColor(Color curveColor){
    this.curveColor = curveColor;
  }

  /**
   * set the curve line width
   * @param width
   */
  public void setCurveWidth(double width){
    curveWidth =width;
  }

  /**
   * set the curve characterstics for plotting
   * @param lineType
   * @param lineColor
   * @param lineWidth
   */
  public void setCurveCharacterstics(String lineType,Color lineColor,double lineWidth){
    curveType = lineType;
    curveColor = lineColor;
    curveWidth = lineWidth;
  }


  /**
   * set the curve characterstics for plotting
   * @param lineName
   * @param lineType
   * @param lineColor
   * @param lineWidth
   */
  public void setCurveCharacterstics(String lineName,String lineType,Color lineColor,double lineWidth){
    curveName = lineName;
    curveType = lineType;
    curveColor = lineColor;
    curveWidth = lineWidth;
  }

  /**
   * set the curve characterstics for plotting
   * @param lineName
   * @param lineType
   * @param lineColor
   * @param lineWidth
   * @param numConsecutiveCurvesWithSamePlotFeatures
   */
  public void setCurveCharacterstics(String lineName,String lineType,Color lineColor,
                                     double lineWidth,int numConsecutiveCurvesWithSamePlotFeatures){
    curveName = lineName;
    curveType = lineType;
    curveColor = lineColor;
    curveWidth = lineWidth;
    numCurvesWithSamePlottingFeatures = numConsecutiveCurvesWithSamePlotFeatures;
  }

  /**
   * set the curve characterstics for plotting
   * @param lineType
   * @param lineColor
   * @param lineWidth
   * @param numConsecutiveCurvesWithSamePlotFeatures
   */
  public void setCurveCharacterstics(String lineType,Color lineColor,double lineWidth,
                                     int numConsecutiveCurvesWithSamePlotFeatures){
    curveType = lineType;
    curveColor = lineColor;
    curveWidth = lineWidth;
    numCurvesWithSamePlottingFeatures = numConsecutiveCurvesWithSamePlotFeatures;
  }

  /**
   *
   * @returns the shape of curve like line, dashed, triangle
   */
  public String getCurveType(){
    return curveType;
  }

  /**
   *
   * @returns the curve color
   */
  public Color getCurveColor(){
    return curveColor;
  }

  /**
   *
   * @returns the curve line width
   */
  public double getCurveWidth(){
    return curveWidth;
  }


  /**
   * Sets the name of the plot curve
   * @param name
   */
  public void setCurveName(String name){
    curveName = name;
  }

  /**
   *
   * @returns the name of curve
   */
  public String getCurveName(){
    return curveName;
  }


  /**
   * Set the number of continuous curves with same number of plotting characterstics.
   * eg: can be of weighted functionlist in which all the individual curves
   * have same plotting characterstics.
   * @param num
   */
  public void setNumContinuousCurvesWithSameCharaceterstics(int num){
    numCurvesWithSamePlottingFeatures = num;
  }

  /**
   *
   * @returns the number of curves with same number curve plotting characterstics
   */
  public int getNumContinuousCurvesWithSameCharacterstics(){
    return numCurvesWithSamePlottingFeatures;
  }


}
