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
import org.opensha.sha.earthquake.observedEarthquake.ObsEqkRupture;
import org.opensha.sha.faultSurface.SimpleFaultData;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;

import scratch.matt.calc.OmoriRate_Calc;
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
public class GenericAfterHypoMagFreqDistForecast
    extends STEP_AftershockForecast {

  private double a_valueGeneric = -1.67;
  private double b_valueGeneric = 0.91;
  private double c_valueGeneric = 0.05;
  private double p_valueGeneric = 1.08;
  private double genNodeCompletenessMag;
  private SimpleFaultData mainshockFault;
  private double[] grid_Gen_kVal, grid_Gen_aVal, grid_Gen_bVal, grid_Gen_cVal,
      grid_Gen_pVal;
  int numGridLocs;
  private double[] rateForecastGrid, kScaler;
  private RegionDefaults rDefs;
  //private double dayStart, dayEnd;
  private ArrayList gridMagForecast;
  private HypoMagFreqDistAtLoc magDistLoc;
//  private EvenlyGriddedCircularGeographicRegion castCircularRegion;
//  private EvenlyGriddedSausageGeographicRegion castSausageRegion;

  public GenericAfterHypoMagFreqDistForecast
      (ObsEqkRupture mainshock, GriddedRegion aftershockZone,
       double[] kScaler) {

    /**
     * initialise the aftershock zone and mainshock for this model
     */
    this.setMainShock(mainshock);
    setRegion(aftershockZone);
//    if(region instanceof EvenlyGriddedCircularGeographicRegion)
//    	castCircularRegion = (EvenlyGriddedCircularGeographicRegion)this.region;
//    if(region instanceof EvenlyGriddedSausageGeographicRegion)
//    	castSausageRegion = (EvenlyGriddedSausageGeographicRegion)this.region;
    
    
    numGridLocs = aftershockZone.getNodeCount();
    
    this.calc_GenNodeCompletenessMag();
    this.set_Gridded_Gen_bValue();
    this.set_Gridded_Gen_cValue();
    this.set_Gridded_Gen_pValue();

    this.set_kScaler(kScaler);
    this.set_Gridded_Gen_kValue();

  }



  /**
   * set_GenReasenbergJonesParms
   */
  public void set_GenReasenbergJonesParms(double[] rjParms) {
    a_valueGeneric = rjParms[0];
    b_valueGeneric = rjParms[1];
    c_valueGeneric = rjParms[2];
    p_valueGeneric = rjParms[3];
  }
  
  

  public int getNumGridLocs() {
	return numGridLocs;
}



public void setNumGridLocs() {
	 numGridLocs = getRegion().getNodeCount();
}



/**
   * set_kScaler
   */
  public void set_kScaler(double[] kScaler) {
    this.kScaler = kScaler;
  }

  /**
   * set_Gridded_kValue
   * This will taper the generic k value.  Each grid node will be assigned
   * a k value based on the distance from the fault.
   */

  public void set_Gridded_Gen_kValue() {
	   grid_Gen_kVal = new double[numGridLocs];
    double rightSide = a_valueGeneric + b_valueGeneric *
        (this.mainShock.getMag() - this.genNodeCompletenessMag);
    double generic_k = Math.pow(10, rightSide);
    int numInd = kScaler.length;
    double totK = 0;
    for (int indLoop = 0; indLoop < numInd - 1; ++indLoop) {
      grid_Gen_kVal[indLoop] = generic_k * this.kScaler[indLoop];
      // test to see if kScaler is correct
      //totK += this.kScaler[indLoop];
    }
    //System.out.println("Total k scaler " +totK);
  }

  /**
   * set_Gridded_aValue
   */
  public void set_Gridded_Gen_aValue() {
	  grid_Gen_aVal = new double[numGridLocs];
    java.util.Arrays.fill(grid_Gen_aVal, a_valueGeneric);
  }

  /**
   * set_Gridded_bValue
   */
  public void set_Gridded_Gen_bValue() {
	  grid_Gen_bVal = new double[numGridLocs];
    java.util.Arrays.fill(grid_Gen_bVal, b_valueGeneric);
  }

  /**
   * set_Gridded_pValue
   */
  public void set_Gridded_Gen_pValue() {
	  grid_Gen_pVal = new double[numGridLocs];
    java.util.Arrays.fill(grid_Gen_pVal, p_valueGeneric);
  }

  /**
   * set_Gridded_cValue
   */
  public void set_Gridded_Gen_cValue() {
	   grid_Gen_cVal = new double[numGridLocs];
    java.util.Arrays.fill(grid_Gen_cVal, c_valueGeneric);
  }

  /**
   * set_GriddedRateForecast
   */
  public void set_GriddedRateForecast(double[] rateForecastGrid) {
    this.rateForecastGrid = rateForecastGrid;
  }


  /**
   * calcGenMagForecast
   * this will calculate  the incremental forecast and return it in an arraylist
   */
  public ArrayList getGenMagForecast() {
    double[] rjParms = new double[4];
    double[] forecastDays = new double[2];
    int numNodes = grid_Gen_kVal.length;
    double totalForecast;
    double[] magForecast;
    OmoriRate_Calc omoriCalc = new OmoriRate_Calc();
    forecastDays[0] = this.dayStart;
    forecastDays[1] = this.dayEnd;
    rjParms[1] = grid_Gen_cVal[0];
    rjParms[2] = grid_Gen_pVal[0];
    omoriCalc.setTimeParms(forecastDays);
    int numForecastMags = 1 +
        (int) ( (this.maxForecastMag - this.minForecastMag) /
               this.deltaForecastMag);
    magForecast = new double[numForecastMags];

    for (int nodeLoop = 0; nodeLoop < numNodes; numNodes++) {
      rjParms[0] = grid_Gen_kVal[nodeLoop];
      omoriCalc.set_OmoriParms(rjParms);
      // first get the total number of events given by omori for the time period
      totalForecast = omoriCalc.get_OmoriRate();

      GutenbergRichterMagFreqDist GR_Dist =
          new GutenbergRichterMagFreqDist(this.a_valueGeneric, totalForecast,
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
   * calcHypoMagFreqDist
   * this calculates the forecast and places it into a
   * HypoMagFreqDistForecastAtLoc object
   */
  public HypoMagFreqDistAtLoc calcHypoMagFreqDist(int gridIndex) {
    double[] rjParms = new double[4];
    double[] forecastDays = new double[2];
    //int numNodes = grid_Gen_kVal.length;
    double totalForecast;
    ;
    OmoriRate_Calc omoriCalc = new OmoriRate_Calc();
    forecastDays[0] = this.dayStart;
    forecastDays[1] = this.dayEnd;
    rjParms[1] = grid_Gen_cVal[0];
    rjParms[2] = grid_Gen_pVal[0];
    omoriCalc.setTimeParms(forecastDays);
    int numForecastMags = 1 +
        (int) ( (this.maxForecastMag - this.minForecastMag) /
               this.deltaForecastMag);
    //for (int nodeLoop = 0; nodeLoop < numNodes; numNodes++) {
      rjParms[0] = grid_Gen_kVal[gridIndex];
      omoriCalc.set_OmoriParms(rjParms);
      // first get the total number of events given by omori for the time period
      totalForecast = omoriCalc.get_OmoriRate();

      GutenbergRichterMagFreqDist GR_Dist =
          new GutenbergRichterMagFreqDist(this.b_valueGeneric, totalForecast,
                                          this.minForecastMag,
                                          this.maxForecastMag, numForecastMags);
      // this must be added to an array so that it can be added to
      // HypoMagFreqDistAtLoc
      IncrementalMagFreqDist[] dist = new IncrementalMagFreqDist[1];
      dist[0] = GR_Dist;
      Location gridLoc;
      
      gridLoc = getRegion().locationForIndex(gridIndex);
      magDistLoc = new HypoMagFreqDistAtLoc(dist,
          gridLoc);
      return magDistLoc;
    //}
  }



  /**
   * get_a_valueGeneric
   */
  public double get_a_valueGeneric() {
    return a_valueGeneric;
  }

  /**
   * get_b_valueGeneric
   */
  public double get_b_valueGeneric() {
    return b_valueGeneric;
  }

  /**
   * get_c_valueGeneric
   */
  public double get_c_valueGeneric() {
    return c_valueGeneric;
  }

  /**
   * get_p_valueGeneric
   */
  public double get_p_valueGeneric() {
    return p_valueGeneric;
  }
  
  public double get_k_valueGenericAtLoc(int ithLocation){
	  return grid_Gen_kVal[ithLocation];
  }

  /**
   * getGridded_k_value_generic
   */
  public double[] getGridded_k_value_generic() {
    return grid_Gen_kVal;
  }

  /**
   * get_GenNodeCompletenessMag
   */
  public double get_genNodeCompletenessMag() {
    return genNodeCompletenessMag;
  }

  /**
   * for the generic case, the min completeness mag Mc is the
   * same as the min forecast mag.
   */

  public void calc_GenNodeCompletenessMag() {
    genNodeCompletenessMag = rDefs.minForecastMag;
  }

  /**
   * getRateForecastGrid
   */
  public double[] getRateForecastGrid() {
    return rateForecastGrid;
  }
  
  public Location getLocInGrid(int ithLocation){
	  return getRegion().locationForIndex(ithLocation);
//	  if(region instanceof EvenlyGriddedCircularGeographicRegion)
//	    	return this.castCircularRegion.getGridLocation(ithLocation);
//	  else if(region instanceof EvenlyGriddedSausageGeographicRegion)
//		  	return this.castSausageRegion.getGridLocation(ithLocation);
//	  else
//		  return null; // WHAT SHOULD I DO HERE?
	  
  }

  //public HypoMagFreqDistAtLoc getHypoMagFreqDistAtLoc(int ithLocation) {
  //  return ;
  //}


}
