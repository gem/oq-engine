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

package org.opensha.sha.earthquake.griddedForecast;

import java.util.ArrayList;

import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;
import org.opensha.sha.earthquake.observedEarthquake.ObsEqkRupList;
import org.opensha.sha.earthquake.observedEarthquake.ObsEqkRupture;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;

import scratch.matt.calc.MaxLikeOmori_Calc;
import scratch.matt.calc.OmoriRate_Calc;
import scratch.matt.calc.ReasenbergJonesGriddedParms_Calc;
import scratch.matt.calc.RegionDefaults;

/**
 * <p>Title: </p>
 *
 * <p>Description: </p>
 *
 * <p>Copyright: Copyright (c) 2002</p>
 *
 * <p>Company: </p>
 *
 * @author not attributable
 * @version 1.0
 */
public class SpatialAfterHypoMagFreqDistForecast
    extends STEP_AftershockForecast {
  private double[] spaNodeCompletenessMag;
  private double[] grid_Spa_kValue, grid_Spa_aValue, grid_Spa_bValue,
      grid_Spa_cValue, grid_Spa_pValue;
  public MaxLikeOmori_Calc omoriCalc;
  private ArrayList rjParms;
  private ReasenbergJonesGriddedParms_Calc rjcalc;
  private GriddedRegion aftershockZone;
  private ObsEqkRupList aftershocks;
  private double dayStart, dayEnd;
  private ArrayList gridMagForecast;
  private HypoMagFreqDistAtLoc magDistLoc;
  private double searchRadius;

  public SpatialAfterHypoMagFreqDistForecast(ObsEqkRupture mainshock,
                                             GriddedRegion
                                             aftershockZone,
                                             ObsEqkRupList aftershocks) {

    /**
     * initialise the aftershock zone and mainshock for this model
     */
    this.setMainShock(mainshock);
    setRegion(aftershockZone);
    //this.region = aftershockZone;
    this.aftershocks = aftershocks;
    this.aftershockZone = aftershockZone;

  }



  /**
   * calc_GriddedRJParms
   * this calculates a, b, c, p, k and completeness magnitude for all grid nodes.
   */
  public void calc_GriddedRJParms() {

    if (this.useFixed_cValue) {
      rjcalc = new ReasenbergJonesGriddedParms_Calc(this.aftershockZone,
          this.aftershocks);
      this.searchRadius = rjcalc.getGridSearchRadius();
      
    }
    else {
      rjcalc = new ReasenbergJonesGriddedParms_Calc(this.aftershockZone,
          this.aftershocks,
          this.useFixed_cValue);
      this.searchRadius = rjcalc.getGridSearchRadius();
    }

    rjcalc.set_constantAddToCompleteness(RegionDefaults.addToMc);
    // returns an array list with all parms in it
    rjParms = rjcalc.getAllGriddedVals();

  }

  /**
   * setAllGridedRJ_Parms
   */
  public void setAllGridedRJ_Parms() {
    grid_Spa_aValue = (double[]) rjParms.get(0);
    grid_Spa_bValue = (double[]) rjParms.get(1);
    grid_Spa_pValue = (double[]) rjParms.get(2);
    grid_Spa_cValue = (double[]) rjParms.get(4);
    grid_Spa_kValue = (double[]) rjParms.get(3);
    spaNodeCompletenessMag = (double[]) rjParms.get(5);
  }

  /**
   * set_Gridded_aValue
   */
  public void set_Gridded_Spa_aValue() {
    grid_Spa_aValue = (double[]) rjParms.get(0);
  }

  /**
   * set_Gridded_bValue
   */
  public void set_Gridded_Spa_bValue() {
    grid_Spa_bValue = (double[]) rjParms.get(1);
  }

  /**
   * set_Gridded_pValue
   */
  public void set_Gridded_Spa_pValue() {
    grid_Spa_pValue = (double[]) rjParms.get(2);
  }

  /**
   * set_Gridded_cValue
   */
  public void set_Gridded_Spa_cValue() {
    grid_Spa_cValue = (double[]) rjParms.get(4);
  }

  /**
   * set_Gridded_kValue
   */
  public void set_Gridded_Spa_kValue() {
    grid_Spa_kValue = (double[]) rjParms.get(3);
  }

  /**
   * This has already been calculated when calculating the
   * RJ parms on a grid, so it does not need to be recalculated
   * here - it is available in the rjParms ArrayList
   */

  public void calc_spaNodeCompletenessMag() {
    spaNodeCompletenessMag = (double[]) rjParms.get(5);
  }

  /**
  * getSpaForecast
  * This calculates the forecast for the entire grid.  It returns an array
  * list where each entry in the array is a double[] containing the forecast
  * for all magnitudes
  */

  private ArrayList getSpaMagForecast() {
    double[] rjParms = new double[4];
    double[] forecastDays = new double[2];
    int numNodes = grid_Spa_kValue.length;
    double totalForecast;
    double[] magForecast;
    OmoriRate_Calc omoriCalc = new OmoriRate_Calc();
    forecastDays[0] = this.dayStart;
    forecastDays[1] = this.dayEnd;

    omoriCalc.setTimeParms(forecastDays);
    int numForecastMags = 1 +
        (int) ( (this.maxForecastMag - this.minForecastMag) /
               this.deltaForecastMag);
    magForecast = new double[numForecastMags];

    for (int nodeLoop = 0; nodeLoop < numNodes; numNodes++) {
      rjParms[0] = grid_Spa_kValue[nodeLoop];
      rjParms[1] = grid_Spa_cValue[nodeLoop];
      rjParms[2] = grid_Spa_pValue[nodeLoop];
      omoriCalc.set_OmoriParms(rjParms);
      // first get the total number of events given by omori for the time period
      totalForecast = omoriCalc.get_OmoriRate();

      GutenbergRichterMagFreqDist GR_Dist =
          new GutenbergRichterMagFreqDist(grid_Spa_aValue[nodeLoop],
                                          totalForecast,
                                          this.minForecastMag,
                                          this.maxForecastMag, numForecastMags);
      // calculate the incremental forecast for each mag
      for (int magLoop = 0; magLoop < numForecastMags; magLoop++) {
        magForecast[magLoop] = GR_Dist.getIncrRate(magLoop);
      }
      // add the array of doubles ( each forecast mag) to the list of forecasts
      // for all grid nodes
      gridMagForecast.add(magForecast);
    }
    return gridMagForecast;
  }

  /**
  * getHypoMagFreqDistAtLoc
  * this will return a single HypoMagFreqDistAtLoc - this is only one location
  * the entire grid is not calculated
  */

  public HypoMagFreqDistAtLoc calcHypoMagFreqDistAtLoc(int gridIndex) {

    double[] rjParms = new double[4];
    double[] forecastDays = new double[2];
    int numNodes = grid_Spa_kValue.length;
    double totalForecast;

    OmoriRate_Calc omoriCalc = new OmoriRate_Calc();
    forecastDays[0] = this.dayStart;
    forecastDays[1] = this.dayEnd;

    omoriCalc.setTimeParms(forecastDays);
    int numForecastMags = 1 +
        (int) ( (this.maxForecastMag - this.minForecastMag) /
               this.deltaForecastMag);
    //for (int nodeLoop = 0; nodeLoop < numNodes; numNodes++) {
      rjParms[0] = grid_Spa_kValue[gridIndex];
      rjParms[1] = grid_Spa_cValue[gridIndex];
      rjParms[2] = grid_Spa_pValue[gridIndex];
      omoriCalc.set_OmoriParms(rjParms);
      // first get the total number of events given by omori for the time period
      totalForecast = omoriCalc.get_OmoriRate();

      GutenbergRichterMagFreqDist GR_Dist =
          new GutenbergRichterMagFreqDist(grid_Spa_aValue[gridIndex],
                                          totalForecast,
                                          this.minForecastMag,
                                          this.maxForecastMag, numForecastMags);

      // this must be added to an array so that it can be added to
      // HypoMagFreqDistAtLoc
      IncrementalMagFreqDist[] dist = new IncrementalMagFreqDist[1];
      dist[0] = GR_Dist;
      Location gridLoc;
      gridLoc = getRegion().locationForIndex(gridIndex);
      magDistLoc = new HypoMagFreqDistAtLoc(dist,gridLoc);
      return magDistLoc;
    //}
  }



  /**
   * get_gridded_aValue
   */
  public double[] get_gridded_Spa_aValue() {
    return grid_Spa_aValue;
  }

  /**
   * get_gridded_bValue
   */
  public double[] get_gridded_Spa_bValue() {
    return grid_Spa_bValue;
  }

  /**
   * get_gridded_pValue
   */
  public double[] get_gridded_Spa_pValue() {
    return grid_Spa_pValue;
  }

  /**
   * get_gridded_kValue
   */
  public double[] get_gridded_Spa_kValue() {
    return grid_Spa_kValue;
  }

  /**
   * get_gridded_cValue
   */
  public double[] get_gridded_Spa_cValue() {
    return grid_Spa_cValue;
  }

  /**
   * getGriddedCompletenessMag
   */
  public double[] getGriddedCompletenessMag() {
    return spaNodeCompletenessMag;
  }
  
  /**
   * get_Spa_aValueAtLoc
   */
  public double get_Spa_aValueAtLoc(int ithLocation) {
    return grid_Spa_aValue[ithLocation];
  }

  /**
   * get_Spa_bValueAtLoc
   */
  public double get_Spa_bValueAtLoc(int ithLocation) {
    return grid_Spa_bValue[ithLocation];
  }

  /**
   * get_Spa_pValueAtLoc
   */
  public double get_Spa_pValueAtLoc(int ithLocation) {
    return grid_Spa_pValue[ithLocation];
  }

  /**
   * get_Spa_kValueAtLoc
   */
  public double get_Spa_kValueAtLoc(int ithLocation) {
    return grid_Spa_kValue[ithLocation];
  }

  /**
   * get_Spa_cValueAtLoc
   */
  public double get_Spa_cValueAtLoc(int ithLocation) {
    return grid_Spa_cValue[ithLocation];
  }

  /**
   * getCompletenessMagAtLoc
   */
  public double getCompletenessMagAtLoc(int ithLocation) {
    return spaNodeCompletenessMag[ithLocation];
  }
  
  /**
   * getGridSearchRadius
   * @return double
   * get the radius that was used in calculating the Reasenberg & Jones params
   */
  public double getGridSearchRadius(){
	  return this.searchRadius;
  }

  //public HypoMagFreqDistAtLoc getHypoMagFreqDistAtLoc(int ithLocation) {
  //  return null;
  //}

}
