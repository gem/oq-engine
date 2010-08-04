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

import scratch.matt.calc.CompletenessMagCalc;
import scratch.matt.calc.MaxLikeGR_Calc;
import scratch.matt.calc.MaxLikeOmori_Calc;
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
public class SequenceAfterHypoMagFreqDistForecast
    extends STEP_AftershockForecast {
  private double seqNodeCompletenessMag;
  private double aVal_Sequence, bVal_Sequence, pVal_Sequence, cVal_Sequence,
      kVal_Sequence;
  private int numGridLocs;
  private double[] grid_Seq_kVal, grid_Seq_aVal, grid_Seq_bVal, grid_Seq_cVal,
      grid_Seq_pVal;
  public MaxLikeOmori_Calc omoriCalc;
  private double[] kScaler;
  private double dayStart, dayEnd;
  private ArrayList gridMagForecast;
  private HypoMagFreqDistAtLoc magDistLoc;
  private GriddedRegion aftershockZone;
  
  public SequenceAfterHypoMagFreqDistForecast(ObsEqkRupture mainshock,
                                              GriddedRegion
                                              aftershockZone,
                                              ObsEqkRupList aftershocks) {
    /**
     * initialise the aftershock zone and mainshock for this model
     */
    this.setMainShock(mainshock);
    setRegion(aftershockZone);
    //this.region = aftershockZone;
    this.afterShocks = aftershocks;
    this.aftershockZone = aftershockZone;

    numGridLocs = aftershockZone.getNodeCount();
    grid_Seq_aVal = new double[numGridLocs];
    grid_Seq_bVal = new double[numGridLocs];
    grid_Seq_cVal = new double[numGridLocs];
    grid_Seq_pVal = new double[numGridLocs];
    grid_Seq_kVal = new double[numGridLocs];

    omoriCalc = new MaxLikeOmori_Calc();

  }


  /**
   * set_SequenceRJParms
   */
  public void set_SequenceRJParms() {
        ObsEqkRupList aftershockListComplete =
        this.afterShocks.getObsEqkRupsAboveMag(seqNodeCompletenessMag);
    MaxLikeGR_Calc.setMags(aftershockListComplete);
    aVal_Sequence = MaxLikeGR_Calc.get_aValueMaxLike();
    bVal_Sequence = MaxLikeGR_Calc.get_bValueMaxLike();
  }

  /**
   * set_SequenceOmoriParms
   */
  public void set_SequenceOmoriParms() {

    ObsEqkRupList aftershockListComplete =
        this.afterShocks.getObsEqkRupsAboveMag(seqNodeCompletenessMag);
    if (this.useFixed_cValue) {
      omoriCalc.set_AfterShockListFixed_c(aftershockListComplete);
    }
    else {
      omoriCalc.set_AfterShockList(aftershockListComplete);
    }

    pVal_Sequence = omoriCalc.get_p_value();
    cVal_Sequence = omoriCalc.get_c_value();
    kVal_Sequence = omoriCalc.get_k_value();
  }

  /**
   * fillGridWithParms
   */
  public void fillGridWithSeqParms() {
	numGridLocs =  getRegion().getNodeCount();
	  grid_Seq_aVal = new double[numGridLocs];
	  grid_Seq_bVal = new double[numGridLocs];
	  grid_Seq_cVal = new double[numGridLocs];
	  grid_Seq_pVal = new double[numGridLocs];
	  grid_Seq_kVal = new double[numGridLocs];
	  
    this.set_Gridded_Seq_aValue();
    this.set_Gridded_Seq_bValue();
    this.set_Gridded_Seq_cValue();
    this.set_Gridded_Seq_kValue();
    this.set_Gridded_Seq_pValue();
  }

  /**
     * set_kScaler
     */
    public void set_kScaler(double[] kScaler) {
      this.kScaler = kScaler;
  }


  /**
   * set_k_value
   * This will taper the  k value.  Each grid node will be assigned
   * a k value based on the distance from the fault.
   */

  public void set_Gridded_Seq_kValue() {

    int numInd = kScaler.length;

    for (int indLoop = 0; indLoop < numInd - 1; ++indLoop) {
      grid_Seq_kVal[indLoop] = this.kVal_Sequence * this.kScaler[indLoop];
    }
  }

  /**
   * getSeqForecast
   * This calculates the forecast for the entire grid.  It returns an array
   * list where each entry in the array is a double[] containing the forecast
   * for all magnitudes
   */

 private ArrayList getSeqMagForecast() {
   double[] rjParms = new double[4];
   double[] forecastDays = new double[2];
   int numNodes = grid_Seq_kVal.length;
   double totalForecast;
   double[] magForecast;
   OmoriRate_Calc omoriCalc = new OmoriRate_Calc();
   forecastDays[0] = this.dayStart;
   forecastDays[1] = this.dayEnd;
   rjParms[1] = cVal_Sequence;
   rjParms[2] = pVal_Sequence;
   omoriCalc.setTimeParms(forecastDays);
   int numForecastMags = 1 +
       (int) ( (this.maxForecastMag - this.minForecastMag) /
              this.deltaForecastMag);
   magForecast = new double[numForecastMags];

   for (int nodeLoop = 0; nodeLoop < numNodes; numNodes++) {
     rjParms[0] = grid_Seq_kVal[nodeLoop];
     omoriCalc.set_OmoriParms(rjParms);
     // first get the total number of events given by omori for the time period
     totalForecast = omoriCalc.get_OmoriRate();

     GutenbergRichterMagFreqDist GR_Dist =
         new GutenbergRichterMagFreqDist(aVal_Sequence, totalForecast,
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
    int numNodes = grid_Seq_kVal.length;
    double totalForecast;
    ;
    OmoriRate_Calc omoriCalc = new OmoriRate_Calc();
    forecastDays[0] = this.dayStart;
    forecastDays[1] = this.dayEnd;
    rjParms[1] = cVal_Sequence;
    rjParms[2] = pVal_Sequence;
    omoriCalc.setTimeParms(forecastDays);
    int numForecastMags = 1 +
        (int) ( (this.maxForecastMag - this.minForecastMag) /
               this.deltaForecastMag);
    //for (int nodeLoop = 0; nodeLoop < numNodes; numNodes++) {
      rjParms[0] = grid_Seq_kVal[gridIndex];
      omoriCalc.set_OmoriParms(rjParms);
      // first get the total number of events given by omori for the time period
      totalForecast = omoriCalc.get_OmoriRate();

      GutenbergRichterMagFreqDist GR_Dist =
          new GutenbergRichterMagFreqDist(aVal_Sequence, totalForecast,
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
   * set_Gridded_aValue
   */
  public void set_Gridded_Seq_aValue() {
    java.util.Arrays.fill(grid_Seq_aVal, aVal_Sequence);
  }

  /**
   * set_Gridded_bValue
   */
  public void set_Gridded_Seq_bValue() {
    java.util.Arrays.fill(grid_Seq_bVal, bVal_Sequence);
  }

  /**
   * set_Gridded_pValue
   */
  public void set_Gridded_Seq_pValue() {
    java.util.Arrays.fill(grid_Seq_pVal, pVal_Sequence);
  }

  /**
   * set_Gridded_cValue
   */
  public void set_Gridded_Seq_cValue() {
    java.util.Arrays.fill(grid_Seq_cVal, cVal_Sequence);
  }

  /**
   * for the generic case, the min completeness mag Mc is the
   * same as the min forecast mag.
   */

  public void calc_SeqNodeCompletenessMag() {
    CompletenessMagCalc.setMcBest(this.getAfterShocks());
    seqNodeCompletenessMag = CompletenessMagCalc.getMcBest();
    seqNodeCompletenessMag = seqNodeCompletenessMag + RegionDefaults.addToMc;
  }



  /**
   * get_aValSequence
   */
  public double get_aValSequence() {
    return aVal_Sequence;
  }

  /**
   * get_bValSequence
   */
  public double get_bValSequence() {
    return bVal_Sequence;
  }

  /**
   * get_pValSequence
   */
  public double get_pValSequence() {
    return pVal_Sequence;
  }

  /**
   * get_cVal_Sequence
   */
  public double get_cVal_Sequence() {
    return cVal_Sequence;
  }
  
  public double get_kVal_SequenceAtLoc(int ithLocation){
	  return grid_Seq_kVal[ithLocation];
  }

  /**
   * getSeqNodeCompletenessMag
   */
  public double getSeqNodeCompletenessMag() {
    return seqNodeCompletenessMag;
  }

  //public HypoMagFreqDistAtLoc getHypoMagFreqDistAtLoc(int ithLocation) {
  //  return null;
  //}
}
